(() => {
  'use strict';

  // Lista de pacientes. A busca e a paginação são server-side; com HTMX a
  // área #patient-results é atualizada sem recarregar a página.
  function focusSearch() {
    const search = document.querySelector('.patients-toolbar input[name="q"]');
    if (search && !search.value) search.focus({ preventScroll: true });
  }

  // Delegação: continua funcionando após a troca parcial da lista.
  document.addEventListener('click', (event) => {
    const button = event.target.closest('[data-delete-patient]');
    if (!button) return;
    const name = button.dataset.patientName || 'este paciente';
    if (window.confirm(`Excluir o paciente "${name}"? Esta ação não pode ser desfeita.`)) {
      document.getElementById(`delete-form-${button.dataset.deletePatient}`)?.submit();
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', focusSearch, { once: true });
  } else {
    focusSearch();
  }
})();
