import React, { useState } from 'react';
import { Bell, User, Settings, LogOut, Check, X } from 'lucide-react';

const NotificationSystem = () => {
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: 'shift',
      message: 'Your shift schedule for next week has been approved',
      time: '2 hours ago',
      unread: true
    },
    {
      id: 2,
      type: 'alert',
      message: 'Please submit your availability for next month',
      time: '1 day ago',
      unread: false
    }
  ]);

  const [showNotifications, setShowNotifications] = useState(false);

  const markAsRead = (id) => {
    setNotifications(notifications.map(n => 
      n.id === id ? {...n, unread: false} : n
    ));
  };

  return (
    <div className="relative">
      <button 
        onClick={() => setShowNotifications(!showNotifications)}
        className="relative p-2 hover:bg-gray-100 rounded-full"
      >
        <Bell className="w-6 h-6" />
        {notifications.some(n => n.unread) && (
          <span className="absolute top-0 right-0 w-3 h-3 bg-red-500 rounded-full"></span>
        )}
      </button>

      {showNotifications && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-gray-100 z-50">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Notifications</h3>
              <button className="text-sm text-blue-600 hover:text-blue-700">
                Mark all as read
              </button>
            </div>

            <div className="space-y-3">
              {notifications.map(notification => (
                <div 
                  key={notification.id}
                  className={`p-3 rounded-lg ${notification.unread ? 'bg-blue-50' : 'bg-gray-50'}`}
                >
                  <div className="flex items-start justify-between">
                    <p className="text-sm text-gray-800">{notification.message}</p>
                    <button 
                      onClick={() => markAsRead(notification.id)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{notification.time}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const ProfileMenu = () => {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div className="relative">
      <button 
        onClick={() => setShowMenu(!showMenu)}
        className="flex items-center space-x-2 p-2 hover:bg-gray-100 rounded-lg"
      >
        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white">
          <User className="w-5 h-5" />
        </div>
        <span className="font-medium">John Doe</span>
      </button>

      {showMenu && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-xl border border-gray-100 z-50">
          <div className="p-2">
            <button className="w-full flex items-center space-x-2 p-2 hover:bg-gray-100 rounded-lg">
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </button>
            <button className="w-full flex items-center space-x-2 p-2 hover:bg-gray-100 rounded-lg text-red-600">
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Add these components to your navbar or dashboard as needed
export { NotificationSystem, ProfileMenu };