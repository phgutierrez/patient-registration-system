(() => {
  'use strict';

  // Exclusão de solicitação cirúrgica: botão [data-delete-surgery="<id>"] e
  // formulário oculto #delete-surgery-form-<id> (com csrf_token). Delegação no
  // document para continuar funcionando após trocas parciais (HTMX).
  if (window.__confirmDeleteSurgeryBound) return;
  window.__confirmDeleteSurgeryBound = true;

  document.addEventListener('click', (event) => {
    const button = event.target.closest('[data-delete-surgery]');
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();
    const label = button.dataset.surgeryLabel || 'esta solicitação';
    let message = `Excluir a solicitação "${label}"? Esta ação não pode ser desfeita.`;
    if (button.dataset.scheduled === '1') {
      message += '\n\nATENÇÃO: ela já foi enviada à agenda. O evento no Google Agenda '
        + 'NÃO será removido automaticamente — exclua-o manualmente depois.';
    }
    if (window.confirm(message)) {
      document.getElementById(`delete-surgery-form-${button.dataset.deleteSurgery}`)?.submit();
    }
  }, true);
})();
