import React, { useState, useEffect } from 'react';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import HistorySidebar from './components/HistorySidebar';
import { Plus, Trash2 } from 'lucide-react';

function App() {
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Load conversations from localStorage on initial render
  useEffect(() => {
    try {
      const storedConversations = localStorage.getItem('chatConversations');
      if (storedConversations) {
        setConversations(JSON.parse(storedConversations));
      }
    } catch (error) {
      console.error("Failed to parse conversations from localStorage", error);
    }
  }, []);

  // Save conversations to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem('chatConversations', JSON.stringify(conversations));
    } catch (error) {
      console.error("Failed to save conversations to localStorage", error);
    }
  }, [conversations]);

  const handleSendMessage = async (messageText) => {
    const newMessage = { text: messageText, sender: 'user', timestamp: new Date().toISOString() };
    
    setIsLoading(true);

    let conversationId = currentConversationId;
    let updatedMessages;

    if (conversationId === null) {
      // Start a new conversation
      conversationId = `conv_${Date.now()}`;
      updatedMessages = [newMessage];
      setConversations(prev => [...prev, { id: conversationId, messages: updatedMessages }]);
    } else {
      // Add to the existing conversation
      const conversation = conversations.find(c => c.id === conversationId);
      updatedMessages = [...conversation.messages, newMessage];
      setConversations(prev => prev.map(c => c.id === conversationId ? { ...c, messages: updatedMessages } : c));
    }
    
    setMessages(updatedMessages);
    setCurrentConversationId(conversationId);

    try {
      // Replace with your actual API endpoint
      const response = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: messageText }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      const data = await response.json();
      const botResponse = {
        rawText: data.answer || 'Sorry, I had trouble understanding that.',
        sender: 'bot',
        timestamp: new Date().toISOString(),
      };
      
      const finalMessages = [...updatedMessages, botResponse];
      setMessages(finalMessages);
      setConversations(prev => prev.map(c => c.id === conversationId ? { ...c, messages: finalMessages } : c));

    } catch (error) {
      console.error('Error fetching API:', error);
      const errorResponse = {
        rawText: 'Oops! Something went wrong. Please check the console or try again.',
        sender: 'bot',
        timestamp: new Date().toISOString(),
        isError: true,
      };
      const finalMessages = [...updatedMessages, errorResponse];
      setMessages(finalMessages);
      setConversations(prev => prev.map(c => c.id === conversationId ? { ...c, messages: finalMessages } : c));
    } finally {
      setIsLoading(false);
    }
  };

  const selectConversation = (id) => {
    const conversation = conversations.find(c => c.id === id);
    if (conversation) {
      setCurrentConversationId(id);
      setMessages(conversation.messages);
    }
  };

  const startNewConversation = () => {
    setCurrentConversationId(null);
    setMessages([]);
  };

  const clearHistory = () => {
    setConversations([]);
    startNewConversation();
  };

  return (
    <div className="flex h-screen w-full bg-white text-gray-800 font-sans">
      <HistorySidebar
        conversations={conversations}
        onSelectConversation={selectConversation}
        onNewConversation={startNewConversation}
        onClearHistory={clearHistory}
        currentConversationId={currentConversationId}
        NewChatIcon={Plus}
        ClearHistoryIcon={Trash2}
      />
      <div className="flex-1 flex flex-col bg-gray-50">
        <header className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">
            <span className="text-red-600">College</span>Advising Chat
          </h1>
        </header>
        <ChatWindow messages={messages} isLoading={isLoading} />
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}

export default App;
