import React, { useEffect, useState } from "react";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import HistorySidebar from './components/HistorySidebar';
import UserProfile from './components/UserProfile';
import { FullPageLoader } from './components/LoadingSpinner';
import { Plus, Trash2, Menu } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';

function ChatApp({ onLogout }) {
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [scrollToBottom, setScrollToBottom] = useState(true);

  const [sessionId, setSessionId] = useState(() => {
    const saved = localStorage.getItem('session_id');
    if (saved) return saved;
    const newId = uuidv4();
    localStorage.setItem('session_id', newId);
    return newId;
  });

  // Load conversations from server and localStorage on initial render
  useEffect(() => {
    loadChatSessions();
  }, []);

  const loadChatSessions = async () => {
    setIsLoadingSessions(true);
    try {
      // First, try to load from server
      const response = await fetch('http://localhost:8000/user/sessions', {
        method: 'GET',
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        const serverSessions = data.sessions.map(session => ({
          id: session.session_id,
          title: session.summary || `Chat ${new Date(session.last_message).toLocaleDateString()}`,
          lastMessage: session.last_message,
          messages: [], // Will be loaded when selected
          isFromServer: true,
          summary: session.summary
        }));
        setConversations(serverSessions);
      } else {
        // Fallback to localStorage if server fails
        const storedConversations = localStorage.getItem('chatConversations');
        if (storedConversations) {
          setConversations(JSON.parse(storedConversations));
        }
      }
    } catch (error) {
      console.error("Failed to load chat sessions:", error);
      // Fallback to localStorage
      try {
        const storedConversations = localStorage.getItem('chatConversations');
        if (storedConversations) {
          setConversations(JSON.parse(storedConversations));
        }
      } catch (localError) {
        console.error("Failed to parse conversations from localStorage", localError);
      }
    } finally {
      setIsLoadingSessions(false);
    }
  };

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
    setScrollToBottom(true); // Enable scrolling to bottom for new messages

    let conversationId = currentConversationId;
    let updatedMessages;

    if (conversationId === null) {
      conversationId = `conv_${Date.now()}`;
      updatedMessages = [newMessage];
      setConversations(prev => [{ id: conversationId, messages: updatedMessages }, ...prev]);
    } else {
      const conversation = conversations.find(c => c.id === conversationId);
      updatedMessages = [...(conversation?.messages || []), newMessage];
      setConversations(prev => prev.map(c => c.id === conversationId ? { ...c, messages: updatedMessages } : c));
    }

    setMessages(updatedMessages);
    setCurrentConversationId(conversationId);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          session_id: sessionId,
          message: messageText
        }),
      });

      if (!response.ok) throw new Error(`API Error: ${response.statusText}`);

      const data = await response.json();
      const botResponse = {
        rawText: data.answer || 'Sorry, I had trouble understanding that.',
        sender: 'bot',
        timestamp: new Date().toISOString(),
        confidence: data.confidence,
        suggested_questions: data.suggested_questions || []
      };
      
      // Update session_id if returned
      if (data.session_id) {
        setSessionId(data.session_id);
        localStorage.setItem('session_id', data.session_id);
      }

      const finalMessages = [...updatedMessages, botResponse];
      setMessages(finalMessages);
      
      // Update conversations list - either update existing or create new server-synced conversation
      if (conversationId === null) {
        // This is a new conversation, add it to the list as a server-synced conversation
        // Generate a meaningful title from the user's first message
        let conversationTitle = `Chat ${new Date().toLocaleDateString()}`;
        if (messageText.length > 10 && !['hi', 'hello', 'hey'].some(greeting => messageText.toLowerCase().includes(greeting))) {
          conversationTitle = messageText.length > 40 ? messageText.substring(0, 37) + '...' : messageText;
        }
        
        const newConversation = {
          id: data.session_id,
          title: conversationTitle,
          lastMessage: new Date().toISOString(),
          messages: finalMessages,
          isFromServer: true,
          summary: conversationTitle !== `Chat ${new Date().toLocaleDateString()}` ? conversationTitle : null
        };
        setConversations(prev => [newConversation, ...prev]);
        setCurrentConversationId(data.session_id);
      } else {
        // Update existing conversation
        setConversations(prev => prev.map(c => 
          c.id === conversationId ? { ...c, messages: finalMessages, lastMessage: new Date().toISOString() } : c
        ));
      }

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
      
      // Update conversations with error message too
      if (conversationId) {
        setConversations(prev => prev.map(c => 
          c.id === conversationId ? { ...c, messages: finalMessages, lastMessage: new Date().toISOString() } : c
        ));
      }
    } finally {
      setIsLoading(false);
    }
  };

  const selectConversation = async (id) => {
    const conversation = conversations.find(c => c.id === id);
    
    if (conversation) {
      setCurrentConversationId(id);
      setIsSidebarOpen(false); // Close sidebar on selection
      setScrollToBottom(false); // Don't scroll to bottom when selecting from history
      
      // If it's a server conversation and messages aren't loaded, fetch them
      if (conversation.isFromServer && (!conversation.messages || conversation.messages.length === 0)) {
        setIsLoading(true);
        try {
          const response = await fetch(`http://localhost:8000/chat/${id}/history`, {
            method: 'GET',
            credentials: 'include',
          });
          
          if (response.ok) {
            const data = await response.json();
            
            const formattedMessages = data.history.map(msg => ({
              text: msg.text,
              sender: msg.sender === 'user' ? 'user' : 'bot',
              rawText: msg.text,
              timestamp: new Date().toISOString(),
            }));
            
            setMessages(formattedMessages);
            
            // Update the conversation in state with loaded messages
            setConversations(prev => prev.map(c => 
              c.id === id ? { ...c, messages: formattedMessages } : c
            ));
          } else {
            console.error('Failed to load chat history, status:', response.status);
            setMessages([]);
          }
        } catch (error) {
          console.error('Error loading chat history:', error);
          setMessages([]);
        } finally {
          setIsLoading(false);
        }
      } else {
        // For local conversations or already loaded conversations
        setMessages(conversation.messages || []);
      }
      
      // Update session ID to match the selected conversation
      setSessionId(id);
      localStorage.setItem('session_id', id);
    }
  };

  const startNewConversation = () => {
    setCurrentConversationId(null);
    setMessages([]);
    setIsSidebarOpen(false); // Close sidebar on new chat
    
    // Generate new session ID for the new conversation
    const newSessionId = uuidv4();
    setSessionId(newSessionId);
    localStorage.setItem('session_id', newSessionId);
  };

  const deleteConversation = async (conversationId) => {
    try {
      const response = await fetch(`http://localhost:8000/chat/${conversationId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      
      if (response.ok) {
        // Remove from local state
        setConversations(prev => prev.filter(c => c.id !== conversationId));
        
        // If this was the current conversation, clear the chat window
        if (currentConversationId === conversationId) {
          setCurrentConversationId(null);
          setMessages([]);
          // Generate new session ID for a fresh start
          const newSessionId = uuidv4();
          setSessionId(newSessionId);
          localStorage.setItem('session_id', newSessionId);
        }
      } else {
        console.error('Failed to delete conversation');
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  return (
    <div className="h-screen w-full bg-gradient-to-br from-gray-50 via-white to-gray-100 font-sans flex overflow-hidden relative">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-red-800/4 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-red-900/4 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-60 h-60 bg-red-800/3 rounded-full blur-3xl"></div>
      </div>

      {/* Sidebar for Desktop */}
      <div className="hidden md:flex md:flex-shrink-0 relative z-10">
        <HistorySidebar
          conversations={conversations}
          onSelectConversation={selectConversation}
          onNewConversation={startNewConversation}
          onDeleteConversation={deleteConversation}
          currentConversationId={currentConversationId}
          NewChatIcon={Plus}
          setIsOpen={setIsSidebarOpen}
          isLoadingSessions={isLoadingSessions}
        />
      </div>

      {/* Mobile Sidebar (off-canvas) */}
      <div
        className={`fixed inset-0 z-40 transform transition-transform duration-300 ease-in-out md:hidden ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
      >
        <HistorySidebar
          conversations={conversations}
          onSelectConversation={selectConversation}
          onNewConversation={startNewConversation}
          onDeleteConversation={deleteConversation}
          currentConversationId={currentConversationId}
          NewChatIcon={Plus}
          isMobile={true}
          setIsOpen={setIsSidebarOpen}
          isLoadingSessions={isLoadingSessions}
        />
      </div>

      {/* Overlay for mobile */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={() => setIsSidebarOpen(false)}
        ></div>
      )}

      <div className="flex-1 flex flex-col h-full relative z-10">
        <header className="p-4 md:p-6 border-b border-gray-100 flex items-center justify-between z-20 bg-white/80 backdrop-blur-xl shadow-sm">
          <div className="flex items-center space-x-3">
            <button
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-all duration-200 md:hidden"
              onClick={() => setIsSidebarOpen(true)}
              aria-label="Open history menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center space-x-3">
              <img
                src="https://upload.wikimedia.org/wikipedia/commons/4/49/Gannon_university_logo.png"
                alt="Gannon University Logo"
                className="w-8 h-8 md:w-10 md:h-10 shadow-lg"
              />
              <h1 className="text-xl md:text-2xl font-bold">
                <span className="bg-gradient-to-r from-red-800 to-red-700 bg-clip-text text-transparent">
                  Advisor
                </span>
              </h1>
            </div>
          </div>
          <div className="flex-shrink-0">
            <UserProfile onLogout={onLogout} />
          </div>
        </header>
        <main className="flex-1 flex flex-col overflow-hidden bg-white/20 backdrop-blur-sm">
          <div className="flex-1 bg-gradient-to-b from-white/50 to-white/20 backdrop-blur-sm">
            <ChatWindow messages={messages} isLoading={isLoading} scrollToBottom={scrollToBottom} />
          </div>
          <div className="bg-white/80 backdrop-blur-xl border-t border-gray-100">
            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
          </div>
        </main>
      </div>
    </div>
  );
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(null);

  const checkAuthStatus = () => {
    fetch("http://localhost:8000/auth/status", {
      method: "GET",
      credentials: "include", // Important: send cookies!
    })
      .then((res) => res.json())
      .then((data) => setIsAuthenticated(data.authenticated))
      .catch(() => setIsAuthenticated(false));
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    // Redirect to login page
    window.location.href = '/login';
  };

  useEffect(() => {
    // Check for auth success parameter
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('auth') === 'success') {
      // Remove the parameter from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    
    // Check authentication status
    checkAuthStatus();
  }, []);

  if (isAuthenticated === null) {
    return <FullPageLoader text="Checking authentication..." />;
  }

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            isAuthenticated ? <ChatApp onLogout={handleLogout} /> : <Navigate to="/login" replace />
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
