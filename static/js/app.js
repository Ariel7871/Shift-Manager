document.addEventListener('DOMContentLoaded', function() {
    // Mount Notification System
    const notificationRoot = document.getElementById('notification-root');
    if (notificationRoot) {
        ReactDOM.render(<NotificationSystem />, notificationRoot);
    }

    // Mount Profile Menu
    const profileRoot = document.getElementById('profile-root');
    if (profileRoot) {
        ReactDOM.render(<ProfileMenu />, profileRoot);
    }

    // Mount Enhanced Dashboard if on dashboard page
    const dashboardRoot = document.getElementById('dashboard-root');
    if (dashboardRoot) {
        ReactDOM.render(<EnhancedDashboard />, dashboardRoot);
    }
});