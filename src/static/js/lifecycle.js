(() => {
    'use strict';

    const body = document.body;
    const settings = {
        desktopMode: body.dataset.desktopMode === 'true',
        shutdownUrl: body.dataset.shutdownUrl,
        shutdownStatusUrl: body.dataset.shutdownStatusUrl,
    };

    function csrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.content || '';
    }

    function showShutdownScreen(finished) {
        document.body.innerHTML = `<div class="shutdown-screen"><div class="shutdown-card"><div class="${finished ? 'shutdown-done' : 'spinner-border text-primary'}">${finished ? '&#10003;' : ''}</div><h2 class="shutdown-title">${finished ? 'Sistema encerrado' : 'Encerrando sistema...'}</h2><p class="shutdown-text">${finished ? 'Esta aba já pode ser fechada.' : 'Aguarde enquanto o servidor finaliza as tarefas em andamento.'}</p></div></div>`;
    }

    async function pollShutdownStatus() {
        const deadline = Date.now() + 12000;
        while (Date.now() < deadline) {
            await new Promise(resolve => setTimeout(resolve, 500));
            try {
                const response = await fetch(settings.shutdownStatusUrl, {cache: 'no-store'});
                if (response.ok && (await response.json()).state !== 'stopped') continue;
            } catch (_) {
                showShutdownScreen(true);
                return;
            }
            break;
        }
        showShutdownScreen(true);
    }

    window.shutdownServer = async function shutdownServer(button) {
        if (button?.disabled || !confirm('Deseja encerrar o sistema neste computador?')) return;
        const original = button ? button.innerHTML : '';
        if (button) {
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm"></span><span class="sidebar-logout-text">Encerrando...</span>';
        }
        try {
            const response = await fetch(settings.shutdownUrl, {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken()},
                body: '{}',
                credentials: 'same-origin',
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok || !data.success) throw new Error(data.error || 'Não foi possível solicitar o encerramento.');
            showShutdownScreen(false);
            pollShutdownStatus();
        } catch (error) {
            if (button) {
                button.disabled = false;
                button.innerHTML = original;
            }
            alert(error.message || 'Não foi possível encerrar o sistema.');
        }
    };

})();
