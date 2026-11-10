(() => {
  'use strict';

  // Configurações de especialidades (antes script inline no template).
  // Estado local "origem do Access (rede/local)" via Alpine.js (build CSP);
  // o servidor já renderiza o estado inicial, então a página funciona sem JS.
  document.addEventListener('alpine:init', () => {
    window.Alpine.data('accessSource', () => ({
      source: 'network',
      init() {
        this.source = this.$el.dataset.initialSource === 'local' ? 'local' : 'network';
      },
      get isLocal() {
        return this.source === 'local';
      },
      get isNetwork() {
        return this.source !== 'local';
      },
      get networkOptionClass() {
        return this.isNetwork ? 'border-primary bg-primary-subtle' : '';
      },
      get localOptionClass() {
        return this.isLocal ? 'border-primary bg-primary-subtle' : '';
      },
    }));
  });

  function csrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content || '';
  }

  function escapeAccessText(value) {
    const node = document.createElement('span');
    node.textContent = String(value ?? '');
    return node.innerHTML;
  }

  function setBusy(button, label) {
    const original = button.innerHTML;
    button.disabled = true;
    button.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span>${label}`;
    return () => {
      button.disabled = false;
      button.innerHTML = original;
    };
  }

  async function selectLocalFile(button) {
    const form = button.closest('form');
    const pathInput = form.querySelector('input[name="access_local_path"]');
    const result = form.querySelector('[id^="access-test-result-"]');
    const restore = setBusy(button, 'Aguardando seleção...');
    try {
      const response = await fetch(button.dataset.url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
        credentials: 'same-origin',
        body: JSON.stringify({ initial_path: pathInput.value }),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.message || 'Não foi possível abrir a janela de arquivos.');
      }
      if (data.selected) {
        pathInput.value = data.path;
        result.innerHTML = `<div class="alert alert-info py-2 mb-0">Arquivo selecionado: <strong>${escapeAccessText(data.filename)}</strong>. Salve as configurações para ativá-lo.</div>`;
      }
    } catch (error) {
      result.innerHTML = `<div class="alert alert-danger py-2 mb-0">${escapeAccessText(error.message)}</div>`;
    } finally {
      restore();
    }
  }

  async function testConnection(button) {
    const form = button.closest('form');
    const result = document.getElementById(button.dataset.result);
    const restore = setBusy(button, 'Testando...');
    result.innerHTML = '';
    try {
      const response = await fetch(button.dataset.url, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-CSRFToken': csrfToken() },
        credentials: 'same-origin',
      });
      const data = await response.json();
      const type = response.ok && data.ok ? 'success' : 'danger';
      const timing = data.query_time_ms !== undefined ? ` (${escapeAccessText(data.query_time_ms)} ms)` : '';
      result.innerHTML = `<div class="alert alert-${type} py-2 mb-0"><strong>${escapeAccessText(data.message || 'Falha ao testar.')}</strong>${timing}<br><small>${escapeAccessText(data.hint || '')}</small></div>`;
    } catch (error) {
      result.innerHTML = '<div class="alert alert-danger py-2 mb-0">Não foi possível comunicar com o servidor da aplicação.</div>';
    } finally {
      restore();
    }
  }

  document.addEventListener('click', (event) => {
    const selectButton = event.target.closest('.select-local-access-btn');
    if (selectButton) {
      selectLocalFile(selectButton);
      return;
    }
    const testButton = event.target.closest('.test-access-btn');
    if (testButton) testConnection(testButton);
  });
})();
