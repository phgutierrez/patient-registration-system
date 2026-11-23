// Pacientes do dia: abre o modal de ações ao clicar no nome (lista trocada via HTMX).
(function () {
  'use strict';

  function modalElements() {
    const modal = document.getElementById('todayPatientModal');
    if (!modal) return null;
    return {
      modal,
      name: document.getElementById('todayPatientName'),
      prontuario: document.getElementById('todayPatientProntuario'),
      input: document.getElementById('todaySurgeryProntuario'),
      notice: document.getElementById('todayRecordNotice'),
    };
  }

  document.addEventListener('click', (event) => {
    const trigger = event.target.closest('[data-today-patient]');
    if (trigger) {
      const els = modalElements();
      if (!els || !window.bootstrap) return;
      els.name.textContent = trigger.dataset.nome || '';
      els.prontuario.textContent = trigger.dataset.prontuario || '';
      els.input.value = trigger.dataset.prontuario || '';
      els.notice.classList.add('d-none');
      window.bootstrap.Modal.getOrCreateInstance(els.modal).show();
      return;
    }
    if (event.target.closest('#todayRecordButton')) {
      const els = modalElements();
      if (els) els.notice.classList.remove('d-none');
    }
  });

  document.addEventListener('submit', (event) => {
    if (event.target.id !== 'todaySurgeryForm') return;
    const button = event.target.querySelector('button[type="submit"]');
    if (button) {
      button.disabled = true;
      button.setAttribute('aria-busy', 'true');
    }
  });
})();
