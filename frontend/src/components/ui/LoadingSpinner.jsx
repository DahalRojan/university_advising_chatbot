import React from 'react';

const LoadingSpinner = ({ size = 'md', text = '', className = '' }) => {
  // Size classes for the spinner using the standardized pattern
  const spinnerSizes = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12'
  };

  // Size classes for text
  const textSizes = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl'
  };

  return (
    <div className={`flex flex-col items-center justify-center space-y-3 ${className}`}>
      {/* Standardized Spinner - matches App.jsx pattern */}
      <div className={`animate-spin rounded-full ${spinnerSizes[size]} border-b-2 border-red-600`}></div>
      
      {/* Text */}
      {text && (
        <p className={`text-gray-600 ${textSizes[size]} font-medium animate-pulse`}>
          {text}
        </p>
      )}
    </div>
  );
};

// Full page loading component
export const FullPageLoader = ({ text = 'Loading...' }) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        {/* Standardized spinner for full page loader */}
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-6"></div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          {text}
        </h2>
        <div className="flex space-x-1 justify-center">
          <div className="w-2 h-2 bg-red-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-red-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-red-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  );
};

// Inline loading for chat messages
export const ChatLoader = () => {
  return (
    <div className="flex items-center space-x-2 text-gray-500">
      <div className="flex space-x-1">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
      </div>
      <span className="text-sm">Advisor is typing...</span>
    </div>
  );
};

export default LoadingSpinner;