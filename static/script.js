// Handle navbar transparency on scroll
document.addEventListener('DOMContentLoaded', function() {
    const navbar = document.querySelector('.navbar-glass');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        } else {
            navbar.style.background = 'rgba(255, 255, 255, 0.8)';
        }
    });

    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // Handle shift selection with animation
    const shiftButtons = document.querySelectorAll('.shift-btn');
    shiftButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons in the same group
            const groupButtons = this.closest('.btn-group').querySelectorAll('.shift-btn');
            groupButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Add animation
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 200);
        });
    });

    // Add loading states
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
            }
        });
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Add fade out animation to alerts before they're removed
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        const closeBtn = alert.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                alert.style.transition = 'opacity 0.3s ease';
                alert.style.opacity = '0';
                setTimeout(() => {
                    alert.remove();
                }, 300);
            });
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // Time zone selector functionality
    const timezoneSelect = document.querySelector('.toolbar-select');
    if (timezoneSelect) {
        timezoneSelect.addEventListener('change', function(e) {
            // Implement timezone change logic here
            console.log('Selected timezone:', e.target.value);
        });
    }

    // Notification system
    const notificationBtn = document.querySelector('.toolbar-btn i.fa-bell').parentElement;
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function() {
            // Toggle notification panel
            toggleNotificationPanel();
        });
    }

    // Settings panel
    const settingsBtn = document.querySelector('.toolbar-btn i.fa-gear').parentElement;
    if (settingsBtn) {
        settingsBtn.addEventListener('click', function() {
            // Toggle settings panel
            toggleSettingsPanel();
        });
    }

    // Profile menu
    const profileSection = document.querySelector('.toolbar-profile');
    if (profileSection) {
        profileSection.addEventListener('click', function() {
            // Toggle profile menu
            toggleProfileMenu();
        });
    }
});

// Notification Panel Toggle
function toggleNotificationPanel() {
    // Create notification panel if it doesn't exist
    let panel = document.getElementById('notification-panel');
    if (!panel) {
        panel = document.createElement('div');
        panel.id = 'notification-panel';
        panel.className = 'notification-panel';
        panel.innerHTML = `
            <div class="notification-header">
                <h3>Notifications</h3>
                <button onclick="toggleNotificationPanel()">
                    <i class="fa-solid fa-times"></i>
                </button>
            </div>
            <div class="notification-content">
                <div class="notification-item">
                    <i class="fa-solid fa-info-circle"></i>
                    <div class="notification-text">
                        <p>Your schedule for next week has been approved</p>
                        <span>2 hours ago</span>
                    </div>
                </div>
                <!-- Add more notification items here -->
            </div>
        `;
        document.body.appendChild(panel);
    }

    panel.classList.toggle('show');
}

// Settings Panel Toggle
function toggleSettingsPanel() {
    let panel = document.getElementById('settings-panel');
    if (!panel) {
        panel = document.createElement('div');
        panel.id = 'settings-panel';
        panel.className = 'settings-panel';
        panel.innerHTML = `
            <div class="settings-header">
                <h3>Settings</h3>
                <button onclick="toggleSettingsPanel()">
                    <i class="fa-solid fa-times"></i>
                </button>
            </div>
            <div class="settings-content">
                <!-- Add settings options here -->
                <div class="settings-item">
                    <label>Theme</label>
                    <select>
                        <option>Light</option>
                        <option>Dark</option>
                    </select>
                </div>
            </div>
        `;
        document.body.appendChild(panel);
    }

    panel.classList.toggle('show');
}

// Profile Menu Toggle
function toggleProfileMenu() {
    let menu = document.getElementById('profile-menu');
    if (!menu) {
        menu = document.createElement('div');
        menu.id = 'profile-menu';
        menu.className = 'profile-menu';
        menu.innerHTML = `
            <div class="profile-menu-item">
                <i class="fa-solid fa-user"></i>
                <span>My Profile</span>
            </div>
            <div class="profile-menu-item">
                <i class="fa-solid fa-calendar"></i>
                <span>My Schedule</span>
            </div>
            <div class="profile-menu-item">
                <i class="fa-solid fa-sign-out"></i>
                <span>Logout</span>
            </div>
        `;
        document.body.appendChild(menu);
    }

    menu.classList.toggle('show');
}

// Function to show toast notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    document.body