// === Persistent Session Bar & Clock ===
// Runs on every page. Reads timer state from localStorage.

(function () {
    // --- Clock ---
    function updateClock() {
        const el = document.getElementById('nav-clock');
        if (!el) return;
        const now = new Date();
        el.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
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
            'Session #' + state.sessionId + (state.sessionName ? ' — ' + state.sessionName : '');

        // Activity badge
        const badge = document.getElementById('bar-activity-badge');
        if (state.currentEntryId && state.activityName) {
            badge.textContent = state.activityName + ' running...';
            badge.style.background = state.activityColor || '#999';
        } else {
            badge.textContent = 'Paused';
            badge.style.background = '#607D8B';
        }

        // Timer
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
})();
