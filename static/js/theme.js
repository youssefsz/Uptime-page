(function () {
    const switcher = document.getElementById('themeSwitcher');
    if (!switcher) return;

    const btns = switcher.querySelectorAll('.theme-btn');
    const html = document.documentElement;

    /**
     * Updates the sliding indicator position and width based on the active button.
     */
    const updateSlider = () => {
        const activeBtn = switcher.querySelector('.theme-btn.active');
        if (activeBtn) {
            switcher.style.setProperty('--switcher-pos', `${activeBtn.offsetLeft}px`);
            switcher.style.setProperty('--switcher-width', `${activeBtn.offsetWidth}px`);
        }
    };

    /**
     * Applies the selected theme and updates the UI switcher buttons.
     * @param {string} theme - 'light', 'dark', or 'system'
     */
    const setTheme = (theme) => {
        localStorage.setItem('theme', theme);

        if (theme === 'system') {
            const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            html.setAttribute('data-theme', isDark ? 'dark' : 'light');
        } else {
            html.setAttribute('data-theme', theme);
        }

        // Update active class
        btns.forEach(btn => {
            if (btn.getAttribute('data-theme-val') === theme) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Update the slider position
        updateSlider();

        // Dispatch event for components that might need it (like Chart.js)
        window.dispatchEvent(new CustomEvent('themechanged', { detail: { theme } }));
    };

    // Initialize switcher state
    const currentTheme = localStorage.getItem('theme') || 'system';

    // Wait for fonts/layout to stabilize for accurate slider position on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => setTheme(currentTheme));
    } else {
        setTheme(currentTheme);
    }

    // Event Listeners
    btns.forEach(btn => {
        btn.addEventListener('click', () => {
            const val = btn.getAttribute('data-theme-val');
            setTheme(val);
        });
    });

    // Listen for system changes to keep UI in sync if in system mode
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (localStorage.getItem('theme') === 'system') {
            setTheme('system');
        }
    });

    // Update slider on resize
    window.addEventListener('resize', updateSlider);

    // Initial update to catch any layout shifts
    setTimeout(updateSlider, 100);
})();
