import React from 'react';
import { Sun, Moon, CalendarPlus, Clock, Users, AlertCircle } from 'lucide-react';

const UpcomingShifts = () => {
  return (
    <div className="space-y-4">
      {/* Today's Shift */}
      <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-100">
        <div className="flex items-center space-x-4">
          <div className="bg-blue-500 p-2 rounded-lg">
            <Sun className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Day Shift</h3>
            <p className="text-sm text-gray-500">Today, 8:00 AM - 4:00 PM</p>
          </div>
        </div>
        <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
          Active
        </span>
      </div>

      {/* Tomorrow's Shift */}
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-100">
        <div className="flex items-center space-x-4">
          <div className="bg-indigo-500 p-2 rounded-lg">
            <Moon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Night Shift</h3>
            <p className="text-sm text-gray-500">Tomorrow, 4:00 PM - 12:00 AM</p>
          </div>
        </div>
        <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm font-medium">
          Upcoming
        </span>
      </div>
    </div>
  );
};

const QuickActions = () => {
  return (
    <div className="mt-8">
      <h2 className="text-xl font-bold text-gray-800 mb-4">Quick Actions</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button className="p-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl hover:shadow-lg transition-all">
          <div className="flex items-center justify-center space-x-2">
            <CalendarPlus className="w-5 h-5" />
            <span>Schedule Shift</span>
          </div>
        </button>

        <button className="p-4 bg-gradient-to-r from-indigo-500 to-indigo-600 text-white rounded-xl hover:shadow-lg transition-all">
          <div className="flex items-center justify-center space-x-2">
            <Users className="w-5 h-5" />
            <span>Team View</span>
          </div>
        </button>

        <button className="p-4 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl hover:shadow-lg transition-all">
          <div className="flex items-center justify-center space-x-2">
            <AlertCircle className="w-5 h-5" />
            <span>Request Time Off</span>
          </div>
        </button>
      </div>
    </div>
  );
};

// Add these components to the main Dashboard
const DashboardEnhanced = () => {
  return (
    <div className="p-6">
      {/* Previous content from Part 1 */}
      
      {/* Add these new sections */}
      <UpcomingShifts />
      <QuickActions />
    </div>
  );
};

export default DashboardEnhanced;