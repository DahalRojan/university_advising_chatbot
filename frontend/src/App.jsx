import React, { useEffect, useState } from "react";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import Login from "./pages/Login.jsx";
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import HistorySidebar from './components/HistorySidebar';
import UserProfile from './components/UserProfile';
import ErrorBoundary from './components/ErrorBoundary';
import { FullPageLoader } from './components/LoadingSpinner';
import { Plus, Trash2, Menu, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { CONFIG } from './config/constants';
import { v4 as uuidv4 } from 'uuid';

function ChatApp({ onLogout }) {
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false); // Mobile sidebar
  const [isDesktopSidebarOpen, setIsDesktopSidebarOpen] = useState(true); // Desktop sidebar
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
      const token = localStorage.getItem('jwt_token');
      const headers = {};
      
      // Add Authorization header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${CONFIG.API_BASE_URL}/user/sessions`, {
        method: 'GET',
        headers: headers,
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
      const token = localStorage.getItem('jwt_token');
      const headers = { 'Content-Type': 'application/json' };
      
      // Add Authorization header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${CONFIG.API_BASE_URL}/chat`, {
        method: 'POST',
        headers: headers,
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
      console.error('Error sending message:', error);
      
      // Provide user-friendly error messages based on error type
      let errorMessage = 'I apologize, but I encountered an issue. Please try again.';
      
      if (error.name === 'NetworkError' || error.message.includes('fetch')) {
        errorMessage = 'Unable to connect to the server. Please check your internet connection and try again.';
      } else if (error.message.includes('timeout')) {
        errorMessage = 'The request took too long to process. Please try again.';
      } else if (error.message.includes('500')) {
        errorMessage = 'The server is experiencing issues. Please try again in a moment.';
      } else if (error.message.includes('429')) {
        errorMessage = 'Too many requests. Please wait a moment before trying again.';
      }
      
      const errorResponse = {
        rawText: errorMessage,
        sender: 'bot',
        timestamp: new Date().toISOString(),
        isError: true,
      };
      
      const finalMessages = [...updatedMessages, errorResponse];
      setMessages(finalMessages);
      
      // Update conversations with error message
      if (conversationId) {
        setConversations(prev => prev.map(c => 
          c.id === conversationId ? { ...c, messages: finalMessages, lastMessage: new Date().toISOString() } : c
        ));
      }
    } finally {
      setIsLoading(false);
    }
  };

  const retryMessage = (messageIndex) => {
    if (messageIndex > 0) {
      const userMessage = messages[messageIndex - 1];
      if (userMessage && userMessage.sender === 'user') {
        // Remove the error message and retry
        setMessages(prev => prev.slice(0, messageIndex));
        handleSendMessage(userMessage.text);
      }
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
          const token = localStorage.getItem('jwt_token');
          const headers = {};
          
          // Add Authorization header if token exists
          if (token) {
            headers['Authorization'] = `Bearer ${token}`;
          }
          
          const response = await fetch(`${CONFIG.API_BASE_URL}/chat/${id}/history`, {
            method: 'GET',
            headers: headers,
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
    setScrollToBottom(true); // Reset to scroll to bottom for new conversations
    
    // Generate new session ID for the new conversation
    const newSessionId = uuidv4();
    setSessionId(newSessionId);
    localStorage.setItem('session_id', newSessionId);
  };

  const deleteConversation = async (conversationId) => {
    try {
      const token = localStorage.getItem('jwt_token');
      const headers = {};
      
      // Add Authorization header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${CONFIG.API_BASE_URL}/chat/${conversationId}`, {
        method: 'DELETE',
        headers: headers,
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
      {isDesktopSidebarOpen && (
        <div className="hidden md:flex md:flex-shrink-0 relative z-10 sidebar-transition">
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
      )}

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

      <div className="flex-1 flex flex-col h-full relative z-10 chat-expand">
        <header className="p-4 md:p-6 border-b border-gray-100 flex items-center justify-between z-20 bg-white/80 backdrop-blur-xl shadow-sm">
          <div className="flex items-center space-x-3">
            {/* Mobile menu button */}
            <button
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-all duration-200 md:hidden"
              onClick={() => setIsSidebarOpen(true)}
              aria-label="Open history menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            {/* Desktop sidebar toggle */}
            <button
              className="hidden md:flex p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-all duration-200"
              onClick={() => setIsDesktopSidebarOpen(!isDesktopSidebarOpen)}
              aria-label={isDesktopSidebarOpen ? "Hide sidebar" : "Show sidebar"}
              title={isDesktopSidebarOpen ? "Hide history sidebar" : "Show history sidebar"}
            >
              {isDesktopSidebarOpen ? (
                <PanelLeftClose className="w-5 h-5" />
              ) : (
                <PanelLeftOpen className="w-5 h-5" />
              )}
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
          <div className="flex-1 bg-gradient-to-b from-white/50 to-white/20 backdrop-blur-sm overflow-hidden">
            <ChatWindow 
              messages={messages} 
              isLoading={isLoading} 
              scrollToBottom={scrollToBottom}
              onRetryMessage={retryMessage}
            />
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

  const checkAuthStatus = async (retries = 3) => {
    try {
      const authUrl = `${CONFIG.API_BASE_URL}/auth/status`;
      const token = localStorage.getItem('jwt_token');
      
      console.log('🔍 Checking auth status at:', authUrl);
      console.log('🔑 Using JWT token:', token ? 'Present' : 'Missing');
      
      const headers = {
        'Cache-Control': 'no-cache'
      };
      
      // Add Authorization header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(authUrl, {
        method: "GET",
        headers: headers,
        timeout: 10000, // 10 second timeout
      });
      
      console.log('📡 Auth status response:', response.status, response.statusText);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Auth check result:', data);
      setIsAuthenticated(data.authenticated);
      
      // Store auth state in localStorage for faster loading
      localStorage.setItem('authState', JSON.stringify({
        authenticated: data.authenticated,
        timestamp: Date.now()
      }));
    } catch (error) {
      console.error('Auth check failed:', error);
      
      if (retries > 0 && error.name !== 'AbortError') {
        // Retry after delay
        setTimeout(() => checkAuthStatus(retries - 1), 1000);
      } else {
        setIsAuthenticated(false);
        localStorage.removeItem('authState');
      }
    }
  };

  const handleLogout = () => {
    // Clear JWT token and auth state
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('authState');
    setIsAuthenticated(false);
    console.log('🔑 JWT token cleared on logout');
    // Redirect to login page
    window.location.href = '/login';
  };

  useEffect(() => {
    // Check for auth success parameter and JWT token
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('auth') === 'success') {
      const token = urlParams.get('token');
      if (token) {
        // Store JWT token in localStorage
        localStorage.setItem('jwt_token', token);
        console.log('🔑 JWT token stored successfully');
      }
      // Remove the parameters from URL
      window.history.replaceState({}, document.title, window.location.pathname);
      setIsAuthenticated(true);
      return;
    }
    
    // Try to get cached auth state first (for faster loading)
    const cachedAuth = localStorage.getItem('authState');
    if (cachedAuth) {
      try {
        const authData = JSON.parse(cachedAuth);
        // Use cached state if less than 5 minutes old
        if (Date.now() - authData.timestamp < 300000) {
          setIsAuthenticated(authData.authenticated);
        }
      } catch (e) {
        localStorage.removeItem('authState');
      }
    }
    
    // Always verify with server
    checkAuthStatus();
  }, []);

  if (isAuthenticated === null) {
    return <FullPageLoader text="Checking authentication..." />;
  }

  return (
    <ErrorBoundary>
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
    </ErrorBoundary>
  );
}

export default App;
