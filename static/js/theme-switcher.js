/**
 * Theme Switcher — lightweight, no dependencies.
 * - Applies saved theme on load (blocks FOUC)
 * - Persists to localStorage
 * - Dispatches 'themeChanged' event for any listeners
 */
(function () {
    var STORAGE_KEY = 'tracker-theme';
    var DEFAULT_THEME = 'light';
    var themes = ['light', 'dark', 'ocean', 'emerald', 'corporate'];

    function getSavedTheme() {
        try { return localStorage.getItem(STORAGE_KEY); } catch (e) { return null; }
    }

    function saveTheme(name) {
        try { localStorage.setItem(STORAGE_KEY, name); } catch (e) { /* ignore */ }
    }

    function applyTheme(name) {
        if (themes.indexOf(name) === -1) name = DEFAULT_THEME;
        document.documentElement.setAttribute('data-theme', name);
        saveTheme(name);
        // Dispatch event so Alpine/hyperscript can react if needed
        document.documentElement.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: name } }));
    }

    // Apply saved theme immediately (blocks FOUC)
    var saved = getSavedTheme();
    if (saved) {
        applyTheme(saved);
    }

    // Expose globally
    window.trackerTheme = {
        current: function () { return document.documentElement.getAttribute('data-theme') || DEFAULT_THEME; },
        set: applyTheme,
        themes: themes,
        labels: {
            light: 'Light',
            dark: 'Dark',
            ocean: 'Ocean',
            emerald: 'Emerald',
            corporate: 'Corporate'
        },
        icons: {
            light: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>',
            dark: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>',
            ocean: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>',
            emerald: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
            corporate: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>'
        }
    };
})();
