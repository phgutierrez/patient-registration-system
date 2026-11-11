(() => {
  'use strict';

  // Assistência ao preenchimento da solicitação cirúrgica:
  // obrigatórios marcados, progresso por seção, validação antes do envio,
  // rascunho automático (localStorage), atalhos de duração/data e
  // proteção contra duplo envio. O servidor continua validando tudo.
  const app = document.getElementById('surgeryRequestApp');
  if (!app) return;
  const form = app.querySelector('.surgery-form');
  if (!form) return;

  const REQUIRED = {
    peso: 'Peso (kg)',
    sinais_sintomas: 'Sinais e sintomas clínicos',
    condicoes_justificativa: 'Condições que justificam a cirurgia',
    resultados_diagnosticos: 'Resultados de provas diagnósticas',
    procedimento_solicitado: 'Procedimento solicitado',
    tipo_cirurgia: 'Tipo de cirurgia',
    data_cirurgia: 'Data da cirurgia',
    hora_cirurgia: 'Hora da cirurgia',
    assistente: 'Assistente',
    duracao_prevista: 'Duração prevista',
  };
  const SKIP_DRAFT = new Set(['csrf_token', 'submit']);
  const isEdit = app.dataset.editMode === '1';
  const hasServerErrors = app.dataset.hasErrors === '1';
  const draftKey = `cirurgiaRascunho:${app.dataset.specialty}:u${app.dataset.userId}:p${app.dataset.patientId}`;

  const fieldsByName = name => [...form.querySelectorAll(`[name="${name}"]`)];

  function isFilled(name) {
    const fields = fieldsByName(name);
    if (!fields.length) return true;
    if (fields[0].type === 'radio') return fields.some(field => field.checked);
    return String(fields[0].value || '').trim() !== '';
  }

  function sectionOf(name) {
    return fieldsByName(name)[0]?.closest('.form-section') || null;
  }

  // ── Marcação de obrigatórios ────────────────────────────────────────
  function markRequired() {
    Object.keys(REQUIRED).forEach(name => {
      const field = fieldsByName(name)[0];
      if (!field) return;
      fieldsByName(name).forEach(item => item.setAttribute('aria-required', 'true'));
      const label = field.closest('.field')?.querySelector('.form-label');
      label?.classList.add('is-required');
    });
  }

  // ── Progresso por seção na navegação lateral ────────────────────────
  function updateProgress() {
    const missing = {};
    Object.keys(REQUIRED).forEach(name => {
      const section = sectionOf(name);
      if (!section) return;
      missing[section.id] = (missing[section.id] || 0) + (isFilled(name) ? 0 : 1);
    });
    document.querySelectorAll('.section-nav a').forEach(link => {
      const id = (link.getAttribute('href') || '').slice(1);
      let badge = link.querySelector('.nav-progress');
      if (!badge) {
        badge = document.createElement('em');
        badge.className = 'nav-progress';
        link.appendChild(badge);
      }
      const count = missing[id] || 0;
      badge.classList.toggle('is-done', count === 0);
      badge.textContent = count === 0 ? '✓' : `faltam ${count}`;
      badge.title = count === 0 ? 'Seção completa' : `${count} campo(s) obrigatório(s) pendente(s)`;
    });
  }

  // ── Validação antes do envio ────────────────────────────────────────
  function clearInvalid(name) {
    fieldsByName(name).forEach(field => {
      if (field.dataset.clientInvalid === '1') {
        field.classList.remove('is-invalid');
        delete field.dataset.clientInvalid;
      }
    });
  }

  function validate() {
    const missing = Object.keys(REQUIRED).filter(name => !isFilled(name));
    const summary = document.getElementById('clientErrorSummary');
    const list = document.getElementById('clientErrorList');
    Object.keys(REQUIRED).forEach(clearInvalid);
    if (!missing.length) {
      if (summary) summary.hidden = true;
      return true;
    }
    missing.forEach(name => fieldsByName(name).forEach(field => {
      if (field.type !== 'radio') {
        field.classList.add('is-invalid');
        field.dataset.clientInvalid = '1';
      }
    }));
    if (summary && list) {
      list.replaceChildren(...missing.map(name => {
        const item = document.createElement('li');
        const link = document.createElement('a');
        const field = fieldsByName(name)[0];
        link.href = `#${field.id}`;
        link.textContent = REQUIRED[name];
        link.addEventListener('click', event => {
          event.preventDefault();
          field.scrollIntoView({behavior: 'smooth', block: 'center'});
          field.focus({preventScroll: true});
        });
        item.appendChild(link);
        return item;
      }));
      summary.hidden = false;
      summary.scrollIntoView({behavior: 'smooth', block: 'start'});
      summary.focus({preventScroll: true});
    }
    return false;
  }

  // ── Rascunho automático ─────────────────────────────────────────────
  function readDraft() {
    try {
      const parsed = JSON.parse(localStorage.getItem(draftKey) || 'null');
      return parsed && typeof parsed === 'object' && parsed.data ? parsed : null;
    } catch {
      return null;
    }
  }

  function clearDraft() {
    try { localStorage.removeItem(draftKey); } catch { /* armazenamento indisponível */ }
  }

  function collectAll() {
    const data = {};
    [...form.elements].forEach(field => {
      if (!field.name || SKIP_DRAFT.has(field.name) || field.type === 'submit') return;
      if (field.type === 'checkbox') {
        if (field.name === 'opme_items') {
          data[field.name] = data[field.name] || [];
          if (field.checked) data[field.name].push(field.value);
        } else {
          data[field.name] = field.checked;
        }
      } else if (field.type === 'radio') {
        if (field.checked) data[field.name] = field.value;
      } else {
        data[field.name] = field.value;
      }
    });
    return data;
  }

  function hasMeaningfulContent(data) {
    return Object.entries(data).some(([name, value]) => (
      name !== 'codigo_procedimento'
      && (Array.isArray(value) ? value.length : (typeof value === 'boolean' ? value : String(value).trim()))
    ));
  }

  let saveTimer = null;
  function scheduleSave() {
    if (isEdit) return;
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      const data = collectAll();
      if (!hasMeaningfulContent(data)) return;
      try {
        localStorage.setItem(draftKey, JSON.stringify({savedAt: new Date().toISOString(), data}));
        const status = document.getElementById('draftStatus');
        if (status) {
          status.textContent = `Rascunho salvo às ${new Date().toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'})}`;
        }
      } catch { /* armazenamento indisponível */ }
    }, 700);
  }

  function restoreDraft(draft) {
    Object.entries(draft.data).forEach(([name, value]) => {
      const fields = fieldsByName(name);
      if (!fields.length) return;
      if (name === 'opme_items') {
        fields.forEach(field => { field.checked = Array.isArray(value) && value.includes(field.value); });
      } else if (fields[0].type === 'radio') {
        fields.forEach(field => { field.checked = field.value === value; });
      } else if (fields[0].type === 'checkbox') {
        fields[0].checked = Boolean(value);
      } else {
        fields[0].value = value ?? '';
      }
    });
    // Recalcula código SUS, bloco de sangue e regras de OPME do script principal.
    ['procedimento_select', 'reserva_sangue_check'].forEach(id => {
      document.getElementById(id)?.dispatchEvent(new Event('change', {bubbles: true}));
    });
    updateProgress();
  }

  function offerDraft() {
    if (isEdit || hasServerErrors) return;
    const draft = readDraft();
    const banner = document.getElementById('draftBanner');
    if (!draft || !banner) return;
    const stamp = document.getElementById('draftTimestamp');
    if (stamp && draft.savedAt) {
      stamp.textContent = `Salvo em ${new Date(draft.savedAt).toLocaleString('pt-BR')}.`;
    }
    banner.hidden = false;
    document.getElementById('restoreDraftButton')?.addEventListener('click', () => {
      restoreDraft(draft);
      banner.hidden = true;
    });
    document.getElementById('discardDraftButton')?.addEventListener('click', () => {
      clearDraft();
      banner.hidden = true;
    });
  }

  // ── Atalhos de preenchimento ────────────────────────────────────────
  function chipRow(items, onPick) {
    const row = document.createElement('div');
    row.className = 'quick-chips';
    items.forEach(([label, value]) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'quick-chip';
      button.textContent = label;
      button.addEventListener('click', () => onPick(value));
      row.appendChild(button);
    });
    return row;
  }

  function setValue(field, value) {
    field.value = value;
    field.dispatchEvent(new Event('input', {bubbles: true}));
    field.dispatchEvent(new Event('change', {bubbles: true}));
  }

  function isoDate(offsetDays) {
    const date = new Date();
    date.setDate(date.getDate() + offsetDays);
    const pad = number => String(number).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  }

  function addShortcuts() {
    const duration = fieldsByName('duracao_prevista')[0];
    if (duration) {
      duration.after(chipRow(
        [['1 h', '1 hora'], ['2 h', '2 horas'], ['3 h', '3 horas'], ['4 h', '4 horas']],
        value => setValue(duration, value),
      ));
    }
    const dateField = fieldsByName('data_cirurgia')[0];
    if (dateField) {
      dateField.after(chipRow(
        [['Amanhã', 1], ['+7 dias', 7], ['+15 dias', 15]],
        offset => setValue(dateField, isoDate(offset)),
      ));
    }
    const timeField = fieldsByName('hora_cirurgia')[0];
    if (timeField) {
      timeField.after(chipRow(
        [['07:00', '07:00'], ['13:00', '13:00']],
        value => setValue(timeField, value),
      ));
    }
  }

  // Busca de procedimento: Enter escolhe quando sobra 1 opção; Esc limpa.
  function enhanceProcedureSearch() {
    const search = document.getElementById('procedureSearch');
    const select = document.getElementById('procedimento_select');
    if (!search || !select) return;
    search.addEventListener('keydown', event => {
      if (event.key === 'Enter') {
        event.preventDefault();
        const visible = [...select.options].filter((option, index) => index > 0 && !option.hidden);
        if (visible.length === 1) {
          select.value = visible[0].value;
          select.dispatchEvent(new Event('change', {bubbles: true}));
          select.focus();
        } else if (visible.length > 1) {
          select.focus();
        }
      } else if (event.key === 'Escape' && search.value) {
        event.preventDefault();
        search.value = '';
        search.dispatchEvent(new Event('input', {bubbles: true}));
      }
    });
  }

  // ── Inicialização ───────────────────────────────────────────────────
  function init() {
    markRequired();
    addShortcuts();
    enhanceProcedureSearch();
    updateProgress();
    offerDraft();

    form.addEventListener('input', event => {
      if (event.target.name) clearInvalid(event.target.name);
      updateProgress();
      scheduleSave();
    });
    form.addEventListener('change', event => {
      if (event.target.name) clearInvalid(event.target.name);
      updateProgress();
      scheduleSave();
    });

    form.addEventListener('submit', event => {
      if (form.dataset.submitting === '1') {
        event.preventDefault();
        return;
      }
      if (!validate()) {
        event.preventDefault();
        return;
      }
      form.dataset.submitting = '1';
      clearTimeout(saveTimer);
      clearDraft();
      const button = form.querySelector('[type="submit"]');
      if (button) {
        button.dataset.originalValue = button.value;
        button.value = 'Salvando…';
        button.setAttribute('aria-disabled', 'true');
        button.classList.add('disabled');
      }
    });

    // Foco no primeiro obrigatório vazio em uma solicitação nova (sem erros do servidor).
    if (!isEdit && !hasServerErrors) {
      const firstEmpty = Object.keys(REQUIRED).find(name => !isFilled(name));
      const field = firstEmpty && fieldsByName(firstEmpty)[0];
      if (field && field.type !== 'radio') field.focus({preventScroll: true});
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, {once: true});
  } else {
    init();
  }
})();
