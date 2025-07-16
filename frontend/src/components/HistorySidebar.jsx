import React from 'react';

function HistorySidebar({
  conversations,
  onSelectConversation,
  onNewConversation,
  onClearHistory,
  currentConversationId,
  NewChatIcon,
  ClearHistoryIcon,
}) {
  return (
    <div className="w-80 bg-white p-4 flex flex-col border-r border-gray-200">
      <button
        onClick={onNewConversation}
        className="flex items-center justify-center w-full mb-4 px-4 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors font-semibold"
      >
        <NewChatIcon className="w-5 h-5 mr-2" />
        New Chat
      </button>
      <div className="flex-1 overflow-y-auto -mr-2 pr-2">
        <h2 className="text-sm font-semibold text-gray-500 mb-2 px-2">History</h2>
        {conversations.length === 0 ? (
          <p className="text-gray-400 text-center text-sm mt-4 px-2">
            No past conversations.
          </p>
        ) : (
          <div className="space-y-1">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                className={`p-2.5 rounded-lg cursor-pointer transition-colors ${
                  currentConversationId === conv.id
                    ? 'bg-red-100 text-red-700'
                    : 'hover:bg-gray-100'
                }`}
              >
                <p className="text-sm font-medium truncate">
                  {conv.messages[0]?.text || 'New Conversation'}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
      <button
        onClick={onClearHistory}
        className="flex items-center justify-center w-full mt-4 px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 hover:text-gray-800 transition-colors"
      >
        <ClearHistoryIcon className="w-4 h-4 mr-2" />
        Clear History
      </button>
    </div>
  );
}

export default HistorySidebar;
