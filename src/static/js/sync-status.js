(() => {
  'use strict';

  function initializeSyncStatus() {
    const indicator = document.getElementById('syncStatusIndicator');
    if (!indicator) return;
    const statusUrl = indicator.dataset.statusUrl;
    const syncUrl = indicator.dataset.syncUrl;
    let running = false;

    function render(data) {
      indicator.classList.remove('is-ok', 'is-pending', 'is-error');
      const label = indicator.querySelector('.sync-status-label');
      if (!data.enabled) {
        indicator.hidden = true;
        return;
      }
      indicator.hidden = false;
      if (data.last_error || !data.ready) {
        indicator.classList.add('is-error');
        label.textContent = data.pairing_required ? 'Parear estação' : 'Sincronização indisponível';
        indicator.title = data.last_error || 'A estação ainda não está pronta.';
      } else if ((data.pending || 0) > 0) {
        indicator.classList.add('is-pending');
        label.textContent = `${data.pending} pendente${data.pending === 1 ? '' : 's'}`;
        indicator.title = 'Alterações salvas localmente e aguardando publicação.';
      } else {
        indicator.classList.add('is-ok');
        label.textContent = 'Sincronizado';
        indicator.title = 'Dados publicados na pasta compartilhada.';
      }
    }

    async function refresh(force = false) {
      if (running) return;
      running = true;
      try {
        const csrf = document.querySelector('meta[name="csrf-token"]')?.content;
        const response = await fetch(force ? syncUrl : statusUrl, {
          method: force ? 'POST' : 'GET',
          headers: force && csrf ? { 'X-CSRFToken': csrf } : {},
          cache: 'no-store',
        });
        render(await response.json());
      } catch (_error) {
        render({ enabled: true, ready: false, last_error: 'Falha ao consultar a sincronização.' });
      } finally {
        running = false;
      }
    }

    indicator.addEventListener('click', () => refresh(true));
    window.addEventListener('focus', () => refresh(true));
    refresh(false);
    window.setInterval(() => refresh(false), 5000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSyncStatus, { once: true });
  } else {
    initializeSyncStatus();
  }
})();
