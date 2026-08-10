(() => {
  'use strict';

  const search = document.getElementById('procedureCatalogSearch');
  const rows = [...document.querySelectorAll('[data-procedure-row]')];
  const count = document.getElementById('procedureCatalogCount');
  const empty = document.getElementById('procedureCatalogEmpty');

  function normalize(value) {
    return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
  }

  function filterCatalog() {
    const query = normalize(search?.value);
    let visible = 0;
    rows.forEach((row) => {
      const match = !query || normalize(row.dataset.search).includes(query);
      row.classList.toggle('d-none', !match);
      if (match) visible += 1;
    });
    if (count) count.textContent = `${visible} procedimento(s)`;
    empty?.classList.toggle('d-none', visible !== 0);
  }

  search?.addEventListener('input', filterCatalog);
  document.querySelectorAll('[data-confirm-delete]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!window.confirm(`Remover o procedimento “${form.dataset.confirmDelete}”?`)) event.preventDefault();
    });
  });
})();
