// Add to app.js or create a new file called dark-mode.js

/**
 * Dark Mode Functionality
 * - Persists user preference in localStorage
 * - Respects system preference when no user choice is made
 * - Smoothly transitions between light and dark modes
 */

// Function to set the theme mode
function setThemeMode(mode) {
    // Add transition class for smooth transition
    document.documentElement.classList.add('color-theme-in-transition');
    
    // Set the theme attribute
    document.documentElement.setAttribute('data-bs-theme', mode);
    
    // Store the user preference
    localStorage.setItem('preferredTheme', mode);
    
    // Remove transition class after transition completes
    setTimeout(() => {
        document.documentElement.classList.remove('color-theme-in-transition');
    }, 800);
    
    // Update chart colors if any charts exist
    updateChartColors(mode);
}

// Function to toggle between light and dark mode
function toggleDarkMode() {
    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setThemeMode(newTheme);
}

// Function to initialize the theme based on user preference or system setting
function initializeTheme() {
    // Check if user has saved a preference
    const savedTheme = localStorage.getItem('preferredTheme');
    
    if (savedTheme) {
        // Use saved preference
        setThemeMode(savedTheme);
    } else {
        // Check for system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            setThemeMode('dark');
        } else {
            setThemeMode('light');
        }
    }
    
    // Listen for system preference changes
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            // Only apply system preference if user hasn't set a preference
            if (!localStorage.getItem('preferredTheme')) {
                setThemeMode(e.matches ? 'dark' : 'light');
            }
        });
    }
}

// Function to update chart colors for dark mode
function updateChartColors(mode) {
    if (typeof Chart === 'undefined') return;
    
    if (mode === 'dark') {
        Chart.defaults.color = '#e3e3e3';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
    } else {
        Chart.defaults.color = '#666';
        Chart.defaults.borderColor = 'rgba(0, 0, 0, 0.1)';
    }
    
    // Update any active charts
    Chart.instances.forEach(chart => {
        chart.update();
    });
}

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    
    // Add event listener to the toggle button
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }
});