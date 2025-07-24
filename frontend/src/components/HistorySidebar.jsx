import React from 'react';
import { X, MessageCircle, Clock, Trash2 } from 'lucide-react';

function HistorySidebar({
  conversations,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  currentConversationId,
  NewChatIcon,
  isMobile = false,
  setIsOpen,
  isLoadingSessions = false,
}) {
  return (
    <div className="w-80 bg-gradient-to-b from-gray-50 to-white h-full p-4 flex flex-col border-r border-gray-100 shadow-xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-to-br from-red-800 to-red-900 rounded-xl flex items-center justify-center shadow-lg shadow-red-800/25">
            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M13,9H18.5L13,3.5V9M6,2H14L20,8V20A2,2 0 0,1 18,22H6C4.89,22 4,21.1 4,20V4C4,2.89 4.89,2 6,2M15,18V16H6V18H15M18,14V12H6V14H18Z"/>
            </svg>
          </div>
          <h2 className="text-xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent">History</h2>
        </div>
        {isMobile && (
          <button 
            className="p-2 text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-xl transition-all duration-200"
            onClick={() => setIsOpen(false)}
            aria-label="Close history menu"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
      <button
        onClick={onNewConversation}
        className="group flex items-center justify-center w-full mb-6 px-4 py-3.5 bg-gradient-to-r from-red-800 to-red-900 text-white rounded-2xl hover:from-red-900 hover:to-red-800 transition-all duration-200 font-semibold shadow-lg shadow-red-800/25 hover:shadow-red-800/40 hover:scale-[1.02] transform"
      >
        <NewChatIcon className="w-5 h-5 mr-2 group-hover:scale-110 transition-transform duration-200" />
        New Chat
      </button>
      <div className="flex-1 overflow-y-auto -mr-2 pr-2">
        {isLoadingSessions ? (
          <div className="space-y-4">
            <div className="text-center py-8">
              <div className="flex justify-center mb-3">
                <div className="w-8 h-8 animate-spin">
                  <svg
                    className="w-full h-full text-red-800"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                </div>
              </div>
              <p className="text-sm text-gray-600">Loading your conversations...</p>
            </div>
            {/* Skeleton placeholders */}
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-3 rounded-lg border border-transparent animate-pulse">
                <div className="flex items-start space-x-2">
                  <div className="w-4 h-4 mt-0.5 bg-gray-300 rounded"></div>
                  <div className="flex-1 min-w-0">
                    <div className="h-4 bg-gray-300 rounded mb-2"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <p className="text-gray-400 text-center text-sm mt-4 px-2">
            No past conversations.
          </p>
        ) : (
          <div className="space-y-3">
            {conversations.map((conv) => {
              const isServerConversation = conv.isFromServer;
              
              // Determine the display title
              let displayTitle;
              if (isServerConversation) {
                displayTitle = conv.summary || conv.title || 'University Chat';
              } else {
                // For local conversations, try to get a meaningful title
                const firstUserMessage = conv.messages?.find(m => m.sender === 'user')?.text;
                if (firstUserMessage && firstUserMessage.length > 10 && 
                    !['hi', 'hello', 'hey'].some(greeting => firstUserMessage.toLowerCase().includes(greeting))) {
                  displayTitle = firstUserMessage.length > 40 
                    ? firstUserMessage.substring(0, 37) + '...' 
                    : firstUserMessage;
                } else {
                  displayTitle = 'New Conversation';
                }
              }
              
              const timeAgo = isServerConversation && conv.lastMessage 
                ? new Date(conv.lastMessage).toLocaleDateString() 
                : null;
              
              return (
                <div
                  key={conv.id}
                  onClick={() => onSelectConversation(conv.id)}
                  className={`group relative p-4 rounded-2xl transition-all duration-300 cursor-pointer backdrop-blur-sm ${
                    currentConversationId === conv.id
                      ? 'bg-gradient-to-r from-red-50 to-red-100 text-red-800 border border-red-300 shadow-lg shadow-red-800/10 scale-[1.02] ring-2 ring-red-300'
                      : 'bg-white/60 hover:bg-white/80 hover:shadow-lg hover:shadow-gray-200/50 border border-gray-100/50 hover:scale-[1.01] hover:ring-1 hover:ring-gray-200'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className={`w-8 h-8 rounded-xl flex-shrink-0 flex items-center justify-center shadow-sm ${
                      currentConversationId === conv.id
                        ? 'bg-gradient-to-br from-red-800 to-red-900 text-white shadow-red-800/25'
                        : 'bg-gradient-to-br from-gray-100 to-gray-200 text-gray-600'
                    }`}>
                      <MessageCircle className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold truncate mb-1">
                        {displayTitle}
                      </p>
                      {timeAgo && (
                        <div className="flex items-center text-xs text-gray-500">
                          <Clock className="w-3 h-3 mr-1.5" />
                          {timeAgo}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteConversation(conv.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1.5 rounded-xl hover:bg-red-100 hover:text-red-800 transition-all duration-200 flex-shrink-0 hover:scale-110"
                      title="Delete conversation"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  {/* Subtle gradient border effect */}
                  <div className={`absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-200 ${
                    currentConversationId !== conv.id ? 'bg-gradient-to-r from-red-800/5 to-red-900/5' : ''
                  }`} />
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default HistorySidebar;
