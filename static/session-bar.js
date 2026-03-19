// === Persistent Session Bar, Clock & Server Health ===

(function () {
    // --- Clock ---
    function updateClock() {
        const el = document.getElementById('nav-clock');
        if (!el) return;
        el.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
    updateClock();
    setInterval(updateClock, 1000);

    // --- Session Bar ---
    function getSessionState() {
        try {
            const raw = localStorage.getItem('tw_session');
            return raw ? JSON.parse(raw) : null;
        } catch { return null; }
    }

    function updateBar() {
        const state = getSessionState();
        const bar = document.getElementById('session-bar');
        if (!bar) return;

        if (!state || !state.sessionId) {
            bar.style.display = 'none';
            return;
        }

        bar.style.display = 'flex';
        document.getElementById('bar-session-label').textContent =
            'Session #' + state.sessionId + (state.sessionName ? ' \u2014 ' + state.sessionName : '');

        const badge = document.getElementById('bar-activity-badge');
        if (state.currentEntryId && state.activityName) {
            badge.textContent = state.activityName + ' running...';
            badge.style.background = state.activityColor || '#999';
        } else {
            badge.textContent = 'Paused';
            badge.style.background = '#607D8B';
        }

        if (state.currentEntryStart) {
            const elapsed = (Date.now() - new Date(state.currentEntryStart).getTime()) / 1000;
            const h = Math.floor(elapsed / 3600);
            const m = Math.floor((elapsed % 3600) / 60);
            const s = Math.floor(elapsed % 60);
            document.getElementById('bar-timer').textContent =
                String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
        } else {
            document.getElementById('bar-timer').textContent = '00:00:00';
        }
    }

    updateBar();
    setInterval(updateBar, 500);

    // --- Server version polling ---
    let _initialHash = null;

    async function checkServerVersion() {
        const alertBar = document.getElementById('server-alert-bar');
        if (!alertBar) return;
        try {
            const r = await fetch('/api/version');
            if (!r.ok) throw new Error('down');
            const data = await r.json();
            if (!_initialHash) {
                _initialHash = data.source_hash;
            } else if (data.source_hash !== _initialHash) {
                alertBar.textContent = 'Server has been updated. Please reload the page for the latest version.';
                alertBar.style.display = 'block';
                alertBar.className = 'server-alert-bar alert-warn';
            }
            // Clear any "server down" message
            if (alertBar.classList.contains('alert-error')) {
                alertBar.style.display = 'none';
            }
        } catch {
            alertBar.textContent = 'Cannot reach server. Is TestWatch running?';
            alertBar.style.display = 'block';
            alertBar.className = 'server-alert-bar alert-error';
        }
    }

    setTimeout(checkServerVersion, 2000);
    setInterval(checkServerVersion, 30000);
})();
