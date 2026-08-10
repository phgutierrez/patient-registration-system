(() => {
  'use strict';

  function openRequest(row) {
    const url = row?.dataset.requestUrl;
    if (url) window.location.assign(url);
  }

  document.querySelectorAll('[data-request-url]').forEach((row) => {
    row.addEventListener('click', (event) => {
      if (event.target.closest('a, button, form, input, select, textarea')) return;
      openRequest(row);
    });
    row.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      if (event.target.closest('a, button, form, input, select, textarea')) return;
      event.preventDefault();
      openRequest(row);
    });
  });
})();
