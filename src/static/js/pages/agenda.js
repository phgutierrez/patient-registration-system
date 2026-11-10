(() => {
  'use strict';

  const app = document.getElementById('agendaApp');
  if (!app) return;
  // #agendaApp é substituído pelo HTMX (outerHTML) ao filtrar/navegar; os
  // dados estáveis (usuário, especialidade, endpoints) são lidos uma vez e a
  // visualização atual é sempre lida do elemento vigente.
  const currentApp = () => document.getElementById('agendaApp') || app;

  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const modalElement = document.getElementById('eventModal');
  const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
  const form = document.getElementById('eventStatusForm');
  let activeEvent = null;

  const preferenceKey =
    `agendaView:${app.dataset.specialtyId}:u${app.dataset.userId}`;
  const params = new URLSearchParams(location.search);
  const savedView = localStorage.getItem(preferenceKey);
  if (!params.has('view') && savedView && savedView !== app.dataset.view) {
    params.set('view', savedView);
    location.replace(`${location.pathname}?${params}`);
    return;
  }
  localStorage.setItem(preferenceKey, app.dataset.view);
  document.addEventListener('htmx:afterSettle', () => {
    localStorage.setItem(preferenceKey, currentApp().dataset.view);
  });

  function toast(message, type = 'success') {
    const region = document.getElementById('agendaToastRegion');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    region.append(alert);
    setTimeout(() => alert.remove(), 5000);
  }

  function toggleReason() {
    const status = form.querySelector('[name="eventStatus"]:checked')?.value;
    document.getElementById('suspensionReasonGroup').hidden =
      status !== 'SUSPENSA';
  }

  function fillModal(trigger) {
    activeEvent = {
      uid: trigger.dataset.eventUid,
      date: trigger.dataset.eventDate,
    };
    document.getElementById('eventModalTitle').textContent =
      trigger.dataset.eventTitle;
    document.getElementById('eventModalDate').textContent =
      trigger.dataset.eventAllday === 'true'
        ? trigger.dataset.eventStart.split(' ')[0] + ' · Dia inteiro'
        : `${trigger.dataset.eventStart} até ${trigger.dataset.eventEnd}`;

    const locationGroup = document.getElementById('eventModalLocationGroup');
    locationGroup.hidden = !trigger.dataset.eventLocation;
    document.getElementById('eventModalLocation').textContent =
      trigger.dataset.eventLocation || '—';
    document.getElementById('eventModalDescription').textContent =
      trigger.dataset.eventDescription || 'Sem descrição.';

    const status = trigger.dataset.eventStatus || 'PENDENTE';
    form.querySelector(
      `[name="eventStatus"][value="${status}"]`,
    ).checked = true;
    document.getElementById('suspensionReason').value =
      trigger.dataset.eventReason || '';
    document.getElementById('eventStatusFeedback').innerHTML = '';
    toggleReason();
    modal.show();
  }

  function statusLabel(status) {
    if (status === 'REALIZADA') return 'Realizada';
    if (status === 'SUSPENSA') return 'Suspensa';
    return 'Pendente';
  }

  function updateEventElements(status, reason) {
    const activeFilter =
      new URLSearchParams(location.search).get('status') || 'todos';
    document.querySelectorAll('[data-event-uid]').forEach(element => {
      if (element.dataset.eventUid !== activeEvent.uid) return;
      element.dataset.eventStatus = status;
      element.dataset.eventReason = reason || '';
      if (!element.hasAttribute('data-event-container')) return;
      element.classList.remove(
        'status-pendente',
        'status-realizada',
        'status-suspensa',
      );
      element.classList.add(`status-${status.toLowerCase()}`);
      element.querySelector('.event-status-label')
        ?.replaceChildren(statusLabel(status));
      if (
        activeFilter !== 'todos'
        && activeFilter !== status.toLowerCase()
      ) {
        element.hidden = true;
      }
    });
  }

  async function saveStatus(event) {
    event.preventDefault();
    const status = form.querySelector(
      '[name="eventStatus"]:checked',
    )?.value;
    if (!status || !activeEvent) return;

    const button = document.getElementById('saveEventStatus');
    button.disabled = true;
    button.innerHTML =
      '<span class="spinner-border spinner-border-sm"></span> Salvando';
    const reason = status === 'SUSPENSA'
      ? document.getElementById('suspensionReason').value.trim()
      : '';

    try {
      const response = await fetch(app.dataset.statusEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf,
        },
        body: JSON.stringify({
          event_uid: activeEvent.uid,
          event_date: activeEvent.date,
          status,
          reason,
        }),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || 'Não foi possível salvar.');
      }
      updateEventElements(data.status, data.reason);
      const syncMessage = data.request_sync?.matched
        ? 'Solicitação vinculada atualizada.'
        : 'Status salvo somente na agenda; nenhuma solicitação foi vinculada com segurança.';
      document.getElementById('eventStatusFeedback').innerHTML =
        `<div class="alert alert-success py-2 mb-0">${syncMessage}</div>`;
      toast('Status do procedimento atualizado.');
      setTimeout(() => modal.hide(), 700);
    } catch (error) {
      const feedback = document.getElementById('eventStatusFeedback');
      feedback.innerHTML =
        '<div class="alert alert-danger py-2 mb-0"></div>';
      feedback.querySelector('.alert').textContent = error.message;
    } finally {
      button.disabled = false;
      button.innerHTML = `${window.appIcon('save')} Salvar status`;
    }
  }

  function reloadAgendaContent() {
    // Atualiza somente a grade/lista; sem HTMX, recarrega a página inteira.
    if (window.htmx) {
      window.htmx.ajax('GET', location.pathname + location.search, {
        target: '#agendaApp',
        swap: 'outerHTML',
      });
    } else {
      location.reload();
    }
  }

  async function refreshAgenda() {
    const button = document.getElementById('refreshAgendaButton');
    if (!button || !app.dataset.refreshEndpoint) return;
    button.disabled = true;
    button.classList.add('is-spinning');
    try {
      const response = await fetch(app.dataset.refreshEndpoint, {
        method: 'POST',
        headers: {'X-CSRFToken': csrf},
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || 'Falha ao atualizar.');
      }
      toast('Agenda atualizada.');
      setTimeout(reloadAgendaContent, 400);
    } catch (error) {
      toast(error.message, 'danger');
    } finally {
      button.disabled = false;
      button.classList.remove('is-spinning');
    }
  }

  document.addEventListener('click', event => {
    const trigger = event.target.closest('[data-event-trigger]');
    if (trigger) fillModal(trigger);
    if (event.target.closest('#refreshAgendaButton')) refreshAgenda();
  });
  form.addEventListener('change', event => {
    if (event.target.name === 'eventStatus') toggleReason();
  });
  form.addEventListener('submit', saveStatus);
})();

