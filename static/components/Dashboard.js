import React from 'react';
import { Calendar, Clock, Users, Bell, ChevronRight, Zap } from 'lucide-react';

const Dashboard = () => {
  return (
    <div className="p-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-8 text-white mb-8">
        <h1 className="text-3xl font-bold mb-2">Welcome Back, User!</h1>
        <p className="text-blue-100">Here's your shift overview for this week</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-blue-100 p-3 rounded-lg">
              <Calendar className="w-6 h-6 text-blue-600" />
            </div>
            <span className="text-sm text-gray-500">This Week</span>
          </div>
          <h3 className="text-2xl font-bold text-gray-800 mb-1">5 Shifts</h3>
          <p className="text-gray-500 text-sm">3 Day, 2 Night shifts</p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-indigo-100 p-3 rounded-lg">
              <Clock className="w-6 h-6 text-indigo-600" />
            </div>
            <span className="text-sm text-gray-500">Hours</span>
          </div>
          <h3 className="text-2xl font-bold text-gray-800 mb-1">40h</h3>
          <p className="text-gray-500 text-sm">Total scheduled hours</p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-green-100 p-3 rounded-lg">
              <Users className="w-6 h-6 text-green-600" />
            </div>
            <span className="text-sm text-gray-500">Team</span>
          </div>
          <h3 className="text-2xl font-bold text-gray-800 mb-1">4 Active</h3>
          <p className="text-gray-500 text-sm">Team members on shift</p>
        </div>
      </div>

      {/* Upcoming Shifts Preview */}
      <div className="bg-white rounded-xl p-6 shadow-md mb-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-800">Upcoming Shifts</h2>
          <button className="text-blue-600 hover:text-blue-700 flex items-center">
            View All <ChevronRight className="w-4 h-4 ml-1" />
          </button>
        </div>
        <div className="space-y-4">
          {/* Continue in Part 2... */}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
