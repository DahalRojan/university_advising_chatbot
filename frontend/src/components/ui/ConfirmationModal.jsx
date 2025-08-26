import React from 'react';
import { Trash2, X, AlertTriangle } from 'lucide-react';

function ConfirmationModal({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title = "Confirm Action", 
  message = "Are you sure you want to proceed?",
  type = "danger",
  confirmText = "Yes",
  cancelText = "No"
}) {
  if (!isOpen) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div className="relative mx-4 w-full max-w-md animate-in zoom-in-95 duration-200">
        {/* Background decoration */}
        <div className="absolute inset-0 bg-gradient-to-br from-red-800/10 to-red-900/10 rounded-3xl blur-xl"></div>
        
        <div className="relative bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl shadow-gray-900/20 border border-gray-200/50 overflow-hidden">
          {/* Header */}
          <div className="p-6 pb-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className={`w-10 h-10 rounded-2xl flex items-center justify-center ${
                  type === 'danger' 
                    ? 'bg-gradient-to-br from-red-100 to-red-200 text-red-800' 
                    : 'bg-gradient-to-br from-gray-100 to-gray-200 text-gray-600'
                }`}>
                  {type === 'danger' ? (
                    <AlertTriangle className="w-5 h-5" />
                  ) : (
                    <Trash2 className="w-5 h-5" />
                  )}
                </div>
                <h3 className="text-lg font-bold text-gray-900">{title}</h3>
              </div>
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-all duration-200 hover:scale-105"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <p className="text-gray-600 leading-relaxed text-base">
              {message}
            </p>
          </div>

          {/* Actions */}
          <div className="px-6 pb-6 flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-2xl font-medium transition-all duration-200 hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-2"
            >
              {cancelText}
            </button>
            <button
              onClick={onConfirm}
              className={`flex-1 px-4 py-3 rounded-2xl font-medium transition-all duration-200 hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                type === 'danger'
                  ? 'bg-gradient-to-r from-red-800 to-red-900 hover:from-red-900 hover:to-red-800 text-white shadow-lg shadow-red-800/25 hover:shadow-red-800/40 focus:ring-red-800/30'
                  : 'bg-gradient-to-r from-gray-800 to-gray-900 hover:from-gray-900 hover:to-gray-800 text-white shadow-lg shadow-gray-800/25 hover:shadow-gray-800/40 focus:ring-gray-800/30'
              }`}
            >
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ConfirmationModal;
