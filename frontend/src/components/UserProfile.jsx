import React, { useState, useEffect } from 'react';
import { User, LogOut, ChevronDown } from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';
import { CONFIG } from '../config/constants';

const UserProfile = ({ onLogout }) => {
  const [user, setUser] = useState(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      console.log('👤 Fetching user profile from:', `${CONFIG.API_BASE_URL}/user/profile`);
      const token = localStorage.getItem('jwt_token');
      const headers = {};
      
      // Add Authorization header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${CONFIG.API_BASE_URL}/user/profile`, {
        method: 'GET',
        headers: headers,
      });
      console.log('👤 User profile response:', response.status, response.statusText);
      
      if (response.ok) {
        const userData = await response.json();
        console.log('👤 User profile data:', userData);
        setUser(userData);
      } else {
        console.error('👤 User profile fetch failed:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${CONFIG.API_BASE_URL}/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      setUser(null);
      if (onLogout) onLogout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2 px-3 py-2 bg-gray-100 rounded-lg">
        <LoadingSpinner size="sm" />
        <span className="text-sm text-gray-600">Loading profile...</span>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className="group flex items-center space-x-3 px-4 py-2.5 bg-white/80 backdrop-blur-md border border-gray-100 rounded-2xl hover:bg-white hover:shadow-lg hover:shadow-gray-200/50 transition-all duration-200 w-full hover:scale-[1.02]"
      >
        <div className="relative">
          <div className="w-9 h-9 bg-gradient-to-br from-red-800 to-red-900 rounded-2xl flex items-center justify-center text-white font-semibold text-sm shadow-lg shadow-red-800/25">
            {user.name ? user.name.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
          </div>
          <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-white shadow-sm"></div>
        </div>
        <div className="flex-1 text-left min-w-0">
          <div className="text-sm font-semibold text-gray-900 truncate">
            {user.name || 'User'}
          </div>
          <div className="text-xs text-gray-500 truncate">
            {user.email}
          </div>
        </div>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-all duration-200 group-hover:text-gray-600 ${isDropdownOpen ? 'rotate-180' : ''}`} />
      </button>

      {isDropdownOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white/95 backdrop-blur-md border border-gray-100 rounded-2xl shadow-xl shadow-gray-200/50 z-50 overflow-hidden">
          <div className="px-4 py-4 border-b border-gray-100/50 bg-gradient-to-r from-gray-50/50 to-white/50">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-red-800 to-red-900 rounded-2xl flex items-center justify-center text-white font-semibold shadow-lg shadow-red-800/25">
                {user.name ? user.name.charAt(0).toUpperCase() : <User className="w-5 h-5" />}
              </div>
              <div>
                <div className="text-sm font-semibold text-gray-900">{user.name}</div>
                <div className="text-xs text-gray-500">{user.email}</div>
              </div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full px-4 py-3 text-left text-sm text-red-800 hover:bg-red-50 flex items-center space-x-3 transition-all duration-200 font-medium hover:text-red-900"
          >
            <div className="w-8 h-8 bg-red-100 rounded-xl flex items-center justify-center">
              <LogOut className="w-4 h-4" />
            </div>
            <span>Sign out</span>
          </button>
        </div>
      )}

      {/* Click outside to close dropdown */}
      {isDropdownOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsDropdownOpen(false)}
        />
      )}
    </div>
  );
};

export default UserProfile;