import React, { useState } from 'react';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import HistorySidebar from './components/HistorySidebar';

function App() {
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (message) => {
    const newMessage = { text: message, sender: 'user', timestamp: new Date() };
    const updatedMessages = [...messages, newMessage];
    setMessages(updatedMessages);

    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: message }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const rawResponse = data.answer || 'Sorry, I couldn’t process your request.';

      const botResponse = {
        rawText: rawResponse,
        sender: 'bot',
        timestamp: new Date(),
      };

      // Update messages state with the bot response
      const finalMessages = [...updatedMessages, botResponse];
      setMessages(finalMessages);

      // Update conversations state only once per message cycle
      setConversations((prevConversations) => {
        const updatedConversations = [...prevConversations];
        if (selectedConversation === null) {
          // New conversation
          updatedConversations.push({
            id: prevConversations.length,
            messages: finalMessages,
          });
          setSelectedConversation(updatedConversations.length - 1);
        } else {
          // Update existing conversation
          updatedConversations[selectedConversation] = {
            id: selectedConversation,
            messages: finalMessages,
          };
        }
        return updatedConversations.slice(-5); // Keep only the last 5 conversations
      });
    } catch (error) {
      console.error('Error fetching API:', error);
      const errorResponse = {
        text: 'Oops, something went wrong. Please try again later.',
        sender: 'bot',
        timestamp: new Date(),
        isError: true,
      };
      const finalMessages = [...updatedMessages, errorResponse];
      setMessages(finalMessages);

      // Update conversations state
      setConversations((prevConversations) => {
        const updatedConversations = [...prevConversations];
        if (selectedConversation === null) {
          updatedConversations.push({
            id: prevConversations.length,
            messages: finalMessages,
          });
          setSelectedConversation(updatedConversations.length - 1);
        } else {
          updatedConversations[selectedConversation] = {
            id: selectedConversation,
            messages: finalMessages,
          };
        }
        return updatedConversations.slice(-5);
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadConversation = (index) => {
    setSelectedConversation(index);
    setMessages(conversations[index].messages);
  };

  const startNewConversation = () => {
    setSelectedConversation(null);
    setMessages([]);
  };

  return (
    <div className="flex min-h-screen w-full bg-gray-900 text-white">
      <HistorySidebar
        conversations={conversations}
        onSelectConversation={loadConversation}
        onNewConversation={startNewConversation}
      />
      <div className="flex-1 flex flex-col">
        <header className="p-4 bg-gray-800 border-b border-gray-700">
          <h1 className="text-xl font-semibold">University Advising Chatbot</h1>
        </header>
        <ChatWindow messages={messages} isLoading={isLoading} />
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}

export default App;