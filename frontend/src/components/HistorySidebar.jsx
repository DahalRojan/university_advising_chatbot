import React from 'react';

function HistorySidebar({ conversations, onSelectConversation, onNewConversation }) {
  return (
    <div className="w-64 bg-gray-800 p-4 flex flex-col border-r border-gray-700">
    <button
        onClick={onNewConversation}
        className="mb-4 px-4 py-2 bg-blue-600 rounded hover:bg-blue-700"
    >
        New Conversation
    </button>
    <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
        <p className="text-gray-400 text-center mt-10">
            No conversations yet. Start one!
        </p>
        ) : (
        conversations.map((conv, index) => (
            <div
            key={conv.id}
            onClick={() => onSelectConversation(index)}
            className="p-2 mb-2 bg-gray-700 rounded cursor-pointer hover:bg-gray-600"
            >
            <p className="text-sm truncate">
                {conv.messages[0]?.text || 'Empty Conversation'}
            </p>
            <p className="text-xs text-gray-400">
                {new Date(conv.messages[0]?.timestamp).toLocaleTimeString()}
            </p>
            </div>
        ))
        )}
    </div>
    </div>
  );
}

export default HistorySidebar;