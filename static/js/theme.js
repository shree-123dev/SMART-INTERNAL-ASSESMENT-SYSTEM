/* =========================================================
   SIAMS — Theme Switcher (Dark Mode / Light Mode)
   ========================================================= */

(function () {
    // 1. Initialize Theme from localStorage or default
    const savedTheme = localStorage.getItem('siams_theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('siams_theme', newTheme);
        updateToggleIcons(newTheme);
    }

    function updateToggleIcons(theme) {
        const toggleButtons = document.querySelectorAll('.theme-toggle-btn');
        toggleButtons.forEach(btn => {
            if (theme === 'dark') {
                btn.innerHTML = '<i class="fas fa-sun"></i>';
                btn.setAttribute('title', 'Switch to Light Mode');
                btn.setAttribute('aria-label', 'Switch to Light Mode');
            } else {
                btn.innerHTML = '<i class="fas fa-moon"></i>';
                btn.setAttribute('title', 'Switch to Dark Mode');
                btn.setAttribute('aria-label', 'Switch to Dark Mode');
            }
        });
    }

    // 2. Ensure floating toggle button exists on every page
    document.addEventListener('DOMContentLoaded', function () {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        
        // If no floating toggle exists, insert one
        if (!document.getElementById('floating-theme-toggle')) {
            const floatBtn = document.createElement('button');
            floatBtn.id = 'floating-theme-toggle';
            floatBtn.className = 'theme-toggle-btn floating-theme-btn';
            floatBtn.setAttribute('type', 'button');
            floatBtn.innerHTML = currentTheme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
            floatBtn.setAttribute('title', currentTheme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode');
            floatBtn.addEventListener('click', toggleTheme);
            document.body.appendChild(floatBtn);
        }

        // Attach listeners to any static theme toggle buttons
        document.querySelectorAll('.theme-toggle-btn').forEach(btn => {
            btn.addEventListener('click', toggleTheme);
        });

        updateToggleIcons(currentTheme);
    });

    // Expose toggle function globally
    window.toggleSIAMSTheme = toggleTheme;
})();
