(() => {
  'use strict';

  // Configuração comum do HTMX (carregado localmente pelos bundles do Vite).
  // Sem HTMX, os links e formulários marcados com hx-* continuam funcionando
  // como navegação tradicional (GET/POST com recarregamento completo).
  const htmx = window.htmx;
  if (!htmx) return;

  Object.assign(htmx.config, {
    selfRequestsOnly: true,
    allowEval: false,
    allowScriptTags: false,
    includeIndicatorStyles: false, // evita <style> inline (CSP)
    // Não guarda HTML de páginas (dados clínicos) no sessionStorage.
    historyCacheSize: 0,
    refreshOnHistoryMiss: true,
    defaultFocusScroll: false,
  });

  function csrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content || '';
  }

  function targetOf(event) {
    return event.detail?.target || event.target;
  }

  document.addEventListener('htmx:configRequest', (event) => {
    const verb = (event.detail.verb || 'get').toLowerCase();
    if (verb !== 'get') event.detail.headers['X-CSRFToken'] = csrfToken();
  });

  document.addEventListener('htmx:beforeRequest', (event) => {
    const target = targetOf(event);
    target?.setAttribute('aria-busy', 'true');
  });

  document.addEventListener('htmx:afterRequest', (event) => {
    const target = targetOf(event);
    target?.removeAttribute('aria-busy');
  });

  function showError(event, message) {
    const target = targetOf(event);
    if (!target) return;
    const region = target.closest('[data-hx-error-region]') || target;
    region.querySelector('[data-hx-error]')?.remove();
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger d-flex flex-wrap align-items-center gap-2 mt-2';
    alert.setAttribute('role', 'alert');
    alert.dataset.hxError = '';
    const text = document.createElement('span');
    text.textContent = message;
    const reload = document.createElement('a');
    reload.href = event.detail?.pathInfo?.requestPath || window.location.href;
    reload.className = 'alert-link';
    reload.textContent = 'Recarregar a página';
    alert.append(text, reload);
    region.prepend(alert);
  }

  document.addEventListener('htmx:responseError', (event) => {
    const status = event.detail?.xhr?.status;
    if (status === 401 || status === 403) {
      showError(event, 'Sua sessão expirou ou você não tem permissão. Recarregue a página.');
    } else {
      showError(event, 'Não foi possível atualizar esta área agora.');
    }
  });

  document.addEventListener('htmx:sendError', (event) => {
    showError(event, 'Sem comunicação com o servidor do sistema.');
  });
})();
