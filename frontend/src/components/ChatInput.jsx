import React, { useState } from 'react';
import { Send } from 'lucide-react';

function ChatInput({ onSendMessage, isLoading }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="p-4 bg-white border-t border-gray-200">
      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me anything..."
          className="w-full p-4 pr-16 rounded-xl bg-gray-100 text-gray-800 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-red-500 transition-shadow"
          disabled={isLoading}
          autoFocus
        />
        <button
          type="submit"
          className={`absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-lg transition-colors ${
            isLoading ? 'bg-gray-300 cursor-not-allowed' : 'bg-red-500 text-white hover:bg-red-600'
          }`}
          disabled={isLoading}
          aria-label="Send message"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
}

export default ChatInput;
