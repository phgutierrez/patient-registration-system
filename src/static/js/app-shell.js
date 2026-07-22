(() => {
  'use strict';

  const DESKTOP_BREAKPOINT = 768;
  const SIDEBAR_KEY = 'sidebarPinned';

  function initializeShell() {
    const body = document.body;
    const sidebar = document.getElementById('appSidebar');
    const menuToggle = document.getElementById('menuToggle');
    const pinToggle = document.getElementById('sidebarPinToggle');
    const backdrop = document.getElementById('sidebarBackdrop');

    const isDesktop = () => window.innerWidth > DESKTOP_BREAKPOINT;

    function updatePinButton(expanded) {
      if (!pinToggle) return;
      pinToggle.setAttribute('aria-pressed', expanded ? 'true' : 'false');
      pinToggle.setAttribute('aria-label', expanded ? 'Recolher menu' : 'Expandir menu');
      pinToggle.title = expanded ? 'Recolher menu' : 'Expandir menu';
      const icon = pinToggle.querySelector('i');
      if (icon) {
        icon.classList.toggle('fa-angles-left', expanded);
        icon.classList.toggle('fa-angles-right', !expanded);
      }
    }

    function setDesktopExpanded(expanded, persist = true) {
      body.classList.toggle('sidebar-pinned', expanded);
      body.classList.toggle('sidebar-collapsed', !expanded);
      if (persist) localStorage.setItem(SIDEBAR_KEY, expanded ? '1' : '0');
      updatePinButton(expanded);
    }

    function setMobileOpen(open) {
      if (!sidebar || isDesktop()) return;
      sidebar.classList.toggle('active', open);
      backdrop?.classList.toggle('active', open);
      body.classList.toggle('sidebar-mobile-open', open);
      menuToggle?.setAttribute('aria-expanded', open ? 'true' : 'false');
      sidebar.setAttribute('aria-hidden', open ? 'false' : 'true');
    }

    const storedState = localStorage.getItem(SIDEBAR_KEY);
    setDesktopExpanded(storedState === null ? true : storedState === '1', false);
    if (!isDesktop() && sidebar) sidebar.setAttribute('aria-hidden', 'true');

    pinToggle?.addEventListener('click', () => {
      setDesktopExpanded(!body.classList.contains('sidebar-pinned'));
    });

    menuToggle?.addEventListener('click', () => {
      setMobileOpen(!sidebar?.classList.contains('active'));
    });

    backdrop?.addEventListener('click', () => setMobileOpen(false));
    sidebar?.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => setMobileOpen(false));
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') setMobileOpen(false);
    });

    window.addEventListener('resize', () => {
      if (isDesktop()) {
        sidebar?.classList.remove('active');
        backdrop?.classList.remove('active');
        body.classList.remove('sidebar-mobile-open');
        sidebar?.removeAttribute('aria-hidden');
        menuToggle?.setAttribute('aria-expanded', 'false');
      } else if (sidebar && !sidebar.classList.contains('active')) {
        sidebar.setAttribute('aria-hidden', 'true');
      }
    });

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (csrfToken) {
      document.querySelectorAll('form[method="POST"]').forEach((form) => {
        if (form.querySelector('input[name="csrf_token"]')) return;
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'csrf_token';
        input.value = csrfToken;
        form.appendChild(input);
      });
    }

    document.querySelectorAll('.message').forEach((message) => {
      window.setTimeout(() => {
        message.classList.add('is-hiding');
        window.setTimeout(() => message.remove(), 250);
      }, 5000);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeShell, { once: true });
  } else {
    initializeShell();
  }
})();
