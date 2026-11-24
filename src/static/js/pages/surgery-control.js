// Controle de cirurgias: leva o foco ao painel do dia depois que o HTMX o carrega.
(function () {
  'use strict';

  document.addEventListener('htmx:afterSwap', (event) => {
    const target = event.detail && event.detail.target;
    if (!target || target.id !== 'scDayPanel') return;
    const panel = target.querySelector('.sc-day');
    if (!panel) return;
    panel.focus({ preventScroll: true });
    panel.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  });
})();
