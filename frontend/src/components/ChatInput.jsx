import React, { useState, memo, useCallback } from 'react';
import { Send } from 'lucide-react';

function ChatInput({ onSendMessage, isLoading }) {
  const [input, setInput] = useState('');

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
    }
  }, [input, isLoading, onSendMessage]);

  const handleSuggestionClick = useCallback((suggestion) => {
    setInput(suggestion);
  }, []);

  return (
    <div className="p-4 md:p-6">
      <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
        <div className="relative group">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything about your academic journey..."
            className="w-full p-4 md:p-5 pr-14 md:pr-16 rounded-3xl bg-white/90 backdrop-blur-md text-gray-800 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-red-800/50 focus:border-red-800 transition-all duration-200 shadow-lg shadow-gray-200/50 placeholder-gray-500 group-hover:shadow-xl group-hover:shadow-gray-200/60"
            disabled={isLoading}
            autoFocus
            aria-label="Message input"
            aria-describedby="message-help"
          />
          <button
            type="submit"
            className={`absolute right-2 md:right-3 top-1/2 -translate-y-1/2 p-2.5 md:p-3 rounded-2xl transition-all duration-200 shadow-lg ${
              isLoading || !input.trim()
                ? 'bg-gray-300 cursor-not-allowed text-gray-500 shadow-gray-300/50'
                : 'bg-gradient-to-r from-red-800 to-red-900 text-white hover:from-red-900 hover:to-red-800 shadow-red-800/25 hover:shadow-red-800/40 hover:scale-105 active:scale-95'
            }`}
            disabled={isLoading || !input.trim()}
            aria-label="Send message"
          >
            <Send className={`w-4 h-4 md:w-5 md:h-5 transition-transform duration-200 ${
              !isLoading && input.trim() ? 'group-hover:translate-x-0.5' : ''
            }`} />
          </button>
        </div>
        
        {/* Suggestion pills */}
        {!input && !isLoading && (
          <div className="flex flex-wrap gap-2 mt-4 justify-center">
            <button
              type="button"
              onClick={() => handleSuggestionClick("What courses do I need for my major?")}
              className="px-4 py-2 bg-white/60 hover:bg-white/80 backdrop-blur-sm border border-gray-200 rounded-full text-sm text-gray-600 hover:text-gray-800 transition-all duration-200 hover:shadow-md hover:scale-105"
            >
              Course Requirements
            </button>
            <button
              type="button"
              onClick={() => handleSuggestionClick("How do I plan my schedule?")}
              className="px-4 py-2 bg-white/60 hover:bg-white/80 backdrop-blur-sm border border-gray-200 rounded-full text-sm text-gray-600 hover:text-gray-800 transition-all duration-200 hover:shadow-md hover:scale-105"
            >
              Schedule Planning
            </button>
            <button
              type="button"
              onClick={() => handleSuggestionClick("What are the graduation requirements?")}
              className="px-4 py-2 bg-white/60 hover:bg-white/80 backdrop-blur-sm border border-gray-200 rounded-full text-sm text-gray-600 hover:text-gray-800 transition-all duration-200 hover:shadow-md hover:scale-105"
            >
              Graduation Info
            </button>
          </div>
        )}
      </form>
    </div>
  );
}

export default memo(ChatInput);
