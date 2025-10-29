import React, { useState, memo, useCallback, useEffect } from 'react';
import { Send, Sparkles, ChevronDown, BookOpen, Clock } from 'lucide-react';

function ChatInput({ onSendMessage, isLoading, messages = [] }) {
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [queryMode, setQueryMode] = useState('catalog_info'); // 'catalog_info' or 'current_sections'
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Handle typing indicator
  useEffect(() => {
    if (input.length > 0) {
      setIsTyping(true);
    } else {
      setIsTyping(false);
    }
  }, [input]);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input, queryMode);  // Pass query mode to parent
      setInput('');
      setIsTyping(false);
    }
  }, [input, isLoading, onSendMessage, queryMode]);

  const handleSuggestionClick = useCallback((suggestion) => {
    setInput(suggestion);
    setIsTyping(true);
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isDropdownOpen && !event.target.closest('.dropdown-container')) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  return (
    <div className="p-4 md:p-6 bg-white/90 backdrop-blur-xl border-t border-gray-100/50">
      <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
        {/* Query Mode Dropdown */}
        <div className="relative mb-3 dropdown-container">
          <button
            type="button"
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center space-x-2 px-4 py-2.5 bg-white border-2 border-gray-200/60 rounded-2xl hover:border-gray-300/70 transition-all duration-200 shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-red-800/20 focus:border-red-800/40"
            aria-label="Select query mode"
          >
            {queryMode === 'current_sections' ? (
              <>
                <Clock className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-gray-700">Current Term Sections</span>
                <span className="text-xs text-gray-500 ml-1">(Live Data)</span>
              </>
            ) : (
              <>
                <BookOpen className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-gray-700">Course Catalog</span>
                <span className="text-xs text-gray-500 ml-1">(General Info)</span>
              </>
            )}
            <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* Dropdown Menu */}
          {isDropdownOpen && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-2xl shadow-xl z-50 overflow-hidden">
              <button
                type="button"
                onClick={() => {
                  setQueryMode('current_sections');
                  setIsDropdownOpen(false);
                }}
                className={`w-full flex items-center space-x-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors duration-200 ${
                  queryMode === 'current_sections' ? 'bg-green-50 border-l-4 border-green-500' : ''
                }`}
              >
                <Clock className="w-5 h-5 text-green-600" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">Current Term Sections</div>
                  <div className="text-xs text-gray-500">Real-time course availability, enrollment, faculty, meeting times</div>
                </div>
              </button>
              <button
                type="button"
                onClick={() => {
                  setQueryMode('catalog_info');
                  setIsDropdownOpen(false);
                }}
                className={`w-full flex items-center space-x-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors duration-200 ${
                  queryMode === 'catalog_info' ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                }`}
              >
                <BookOpen className="w-5 h-5 text-blue-600" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">Course Catalog</div>
                  <div className="text-xs text-gray-500">Course descriptions, prerequisites, degree requirements</div>
                </div>
              </button>
            </div>
          )}
        </div>

        <div className="relative group">
          <div className={`absolute inset-0 bg-gradient-to-r from-red-800/5 to-red-900/5 rounded-3xl blur-xl transition-opacity duration-300 ${isTyping ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}></div>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything about your academic journey at Gannon..."
            maxLength={1000}
            className={`relative w-full p-4 md:p-5 pr-14 md:pr-16 rounded-3xl bg-white text-gray-800 focus:outline-none transition-all duration-200 shadow-lg placeholder-gray-400 text-base md:text-lg font-medium ${
              isTyping 
                ? 'border-2 border-red-800/40 ring-2 ring-red-800/20 shadow-xl shadow-red-100/50' 
                : 'border-2 border-gray-200/60 hover:border-gray-300/70 shadow-gray-100/80 hover:shadow-xl hover:shadow-gray-200/60 focus:ring-2 focus:ring-red-800/30 focus:border-red-800/60'
            }`}
            disabled={isLoading}
            autoFocus
            aria-label="Message input"
            aria-describedby="message-help"
          />
          <button
            type="submit"
            className={`absolute right-2 md:right-3 top-1/2 -translate-y-1/2 p-2.5 md:p-3 rounded-2xl transition-all duration-200 shadow-lg hover:shadow-xl ${
              isLoading || !input.trim()
                ? 'bg-gray-300 cursor-not-allowed text-gray-500 shadow-gray-200/50'
                : 'bg-gradient-to-r from-red-800 to-red-900 text-white hover:from-red-900 hover:to-red-800 shadow-red-800/30 hover:shadow-red-800/50 hover:scale-105 active:scale-95 focus:ring-2 focus:ring-red-800/30 focus:outline-none'
            }`}
            disabled={isLoading || !input.trim()}
            aria-label="Send message"
          >
            {isLoading ? (
              <div className="w-4 h-4 md:w-5 md:h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <Send className={`w-4 h-4 md:w-5 md:h-5 transition-transform duration-200 ${
                input.trim() ? 'group-hover:translate-x-0.5' : ''
              }`} />
            )}
          </button>
        </div>
        
        {/* Suggestion pills - only show in completely new chat */}
        {!input && !isLoading && messages.length === 0 && (
          <div className="flex flex-wrap gap-2 md:gap-3 mt-4 md:mt-6 justify-center">
            <button
              type="button"
              onClick={() => handleSuggestionClick("What courses do I need for my major?")}
              className="px-4 md:px-5 py-2.5 md:py-3 bg-white/80 hover:bg-white border border-gray-200/60 hover:border-red-800/30 rounded-full text-sm md:text-base text-gray-600 hover:text-red-800 transition-all duration-200 hover:shadow-lg hover:shadow-gray-200/50 hover:scale-105 focus:ring-2 focus:ring-red-800/20 focus:outline-none backdrop-blur-sm"
            >
              📚 Course Requirements
            </button>
            <button
              type="button"
              onClick={() => handleSuggestionClick("How do I plan my schedule for next semester?")}
              className="px-4 md:px-5 py-2.5 md:py-3 bg-white/80 hover:bg-white border border-gray-200/60 hover:border-red-800/30 rounded-full text-sm md:text-base text-gray-600 hover:text-red-800 transition-all duration-200 hover:shadow-lg hover:shadow-gray-200/50 hover:scale-105 focus:ring-2 focus:ring-red-800/20 focus:outline-none backdrop-blur-sm"
            >
              📅 Schedule Planning
            </button>
            <button
              type="button"
              onClick={() => handleSuggestionClick("What are the graduation requirements for my program?")}
              className="px-4 md:px-5 py-2.5 md:py-3 bg-white/80 hover:bg-white border border-gray-200/60 hover:border-red-800/30 rounded-full text-sm md:text-base text-gray-600 hover:text-red-800 transition-all duration-200 hover:shadow-lg hover:shadow-gray-200/50 hover:scale-105 focus:ring-2 focus:ring-red-800/20 focus:outline-none backdrop-blur-sm"
            >
              🎓 Graduation Info
            </button>
            <button
              type="button"
              onClick={() => handleSuggestionClick("How do I apply for financial aid?")}
              className="px-4 md:px-5 py-2.5 md:py-3 bg-white/80 hover:bg-white border border-gray-200/60 hover:border-red-800/30 rounded-full text-sm md:text-base text-gray-600 hover:text-red-800 transition-all duration-200 hover:shadow-lg hover:shadow-gray-200/50 hover:scale-105 focus:ring-2 focus:ring-red-800/20 focus:outline-none backdrop-blur-sm"
            >
              💰 Financial Aid
            </button>
          </div>
        )}
        
        {/* Character count and help text */}
        <div className="flex justify-between items-center mt-3">
          <p id="message-help" className="text-xs md:text-sm text-gray-500 opacity-70">
            Ask about courses, schedules, requirements, campus life, and more...
          </p>
          {input.length > 100 && (
            <span className={`text-xs font-medium ${
              input.length > 500 ? 'text-red-500' : 'text-gray-400'
            }`}>
              {input.length}/1000
            </span>
          )}
        </div>
      </form>
    </div>
  );
}

export default memo(ChatInput);
