import React, { useEffect, useState } from "react";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import Login from "./pages/Login.jsx";
import VerifyEmail from "./pages/VerifyEmail.jsx";
import ChatWindow from './components/chat/ChatWindow';
import ChatInput from './components/chat/ChatInput';
import HistorySidebar from './components/chat/HistorySidebar';
import UserProfile from './components/ui/UserProfile';
import ErrorBoundary from './components/ui/ErrorBoundary';
import LoadingSpinner, { FullPageLoader } from './components/ui/LoadingSpinner';
import ConfirmationModal from './components/ui/ConfirmationModal';
import OnboardingWizard from './components/onboarding/OnboardingWizard';
import { Plus, Trash2, Menu, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { CONFIG } from './config/constants';
import { v4 as uuidv4 } from 'uuid';
import onboardingApi from './services/onboardingApi';

function ChatApp({ onLogout }) {
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false); // Mobile sidebar
  const [isDesktopSidebarOpen, setIsDesktopSidebarOpen] = useState(true); // Desktop sidebar
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [scrollToBottom, setScrollToBottom] = useState(true);

  // Delete confirmation modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState(null);

  // Onboarding state
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [isCheckingOnboarding, setIsCheckingOnboarding] = useState(true);
  const [onboardingStatus, setOnboardingStatus] = useState(null);

  const [sessionId, setSessionId] = useState(() => {
    const saved = localStorage.getItem('session_id');
    if (saved) return saved;
    const newId = uuidv4();
    localStorage.setItem('session_id', newId);
    return newId;
  });

  // Load conversations from server and localStorage on initial render
  useEffect(() => {
    checkOnboardingStatus();
    loadChatSessions();
  }, []);

  const checkOnboardingStatus = async () => {
    try {
      setIsCheckingOnboarding(true);
      const status = await onboardingApi.checkOnboardingStatus();
      
      console.log('🔍 Onboarding status check results:', {
        isComplete: status?.isComplete,
        completionPercentage: status?.completionPercentage,
        profileCompletionPercentage: status?.profileCompletionPercentage,
        fullStatus: status
      });
      
      setOnboardingStatus(status);
      
      // Only show onboarding if explicitly NOT complete
      if (status && status.isComplete === true) {
        console.log('✅ Onboarding is complete - skipping to chat');
        setShowOnboarding(false);
      } else if (status && (status.completionPercentage >= 100 || status.profileCompletionPercentage >= 100)) {
        console.log('🔧 Profile shows 100% complete but not marked as finished - marking complete');
        // If profile is 100% but not marked complete, mark it complete
        try {
          console.log('📝 Calling completeOnboarding API...');
          await onboardingApi.completeOnboarding();
          console.log('✅ Successfully marked onboarding as complete');
          setShowOnboarding(false);
          setOnboardingStatus(prev => ({ ...prev, isComplete: true }));
        } catch (error) {
          console.error('❌ Failed to auto-complete onboarding:', error);
          setShowOnboarding(true);
        }
      } else {
        console.log('❌ Onboarding not complete - showing wizard', {
          isComplete: status?.isComplete,
          completionPercentage: status?.completionPercentage,
          profileCompletionPercentage: status?.profileCompletionPercentage
        });
        setShowOnboarding(true);
      }
    } catch (error) {
      console.error('❌ Failed to check onboarding status:', error);
      // If there's an error, assume onboarding is needed for new users
      setShowOnboarding(true);
    } finally {
      setIsCheckingOnboarding(false);
    }
  };

  const handleOnboardingComplete = async () => {
    console.log('🎉 Onboarding completed! Updating status...');
    setShowOnboarding(false);
    setOnboardingStatus(prev => ({ ...prev, isComplete: true }));
    
    // Reload onboarding status to ensure it's properly synced
    try {
      console.log('🔄 Refreshing onboarding status after completion...');
      await checkOnboardingStatus();
    } catch (error) {
      console.error('❌ Failed to refresh onboarding status:', error);
    }
    
    // Optionally reload chat sessions or profile data
    loadChatSessions();
  };

  const handleCloseOnboarding = () => {
    // Don't allow closing onboarding if it's not complete - mandatory for all users
    if (onboardingStatus?.isComplete) {
      setShowOnboarding(false);
    }
  };

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

  const handleDeleteRequest = (conversationId) => {
    console.log('🗑️ Delete request for conversation:', conversationId);
    setConversationToDelete(conversationId);
    setDeleteModalOpen(true);
  };

  const handleConfirmDelete = () => {
    if (conversationToDelete) {
      console.log('✅ Confirmed deletion, proceeding with delete');
      deleteConversation(conversationToDelete);
      setDeleteModalOpen(false);
      setConversationToDelete(null);
    }
  };

  const handleCancelDelete = () => {
    console.log('❌ Cancelled deletion');
    setDeleteModalOpen(false);
    setConversationToDelete(null);
  };

  const deleteConversation = async (conversationId) => {
    console.log('🗑️ Attempting to delete conversation:', conversationId);
    
    try {
      const token = localStorage.getItem('jwt_token');
      const headers = {
        'Content-Type': 'application/json'
      };
      
      // Add Authorization header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      console.log('🔗 Delete API call to:', `${CONFIG.API_BASE_URL}/chat/${conversationId}`);
      
      const response = await fetch(`${CONFIG.API_BASE_URL}/chat/${conversationId}`, {
        method: 'DELETE',
        headers: headers,
      });
      
      console.log('📡 Delete response status:', response.status, response.statusText);
      
      if (response.ok) {
        console.log('✅ Successfully deleted conversation from server');
        // Remove from local state
        setConversations(prev => {
          const filtered = prev.filter(c => c.id !== conversationId);
          console.log('📝 Updated conversations list:', filtered.length, 'conversations remaining');
          return filtered;
        });
        
        // If this was the current conversation, clear the chat window
        if (currentConversationId === conversationId) {
          console.log('🔄 Clearing current conversation from chat window');
          setCurrentConversationId(null);
          setMessages([]);
          // Generate new session ID for a fresh start
          const newSessionId = uuidv4();
          setSessionId(newSessionId);
          localStorage.setItem('session_id', newSessionId);
        }
      } else {
        console.error('❌ Failed to delete conversation. Status:', response.status);
        const errorText = await response.text();
        console.error('Error details:', errorText);
        
        // For local conversations or when server fails, still remove from local state
        if (response.status === 404 || response.status >= 500) {
          console.log('🔄 Removing from local state anyway (server error or not found)');
          setConversations(prev => prev.filter(c => c.id !== conversationId));
          
          if (currentConversationId === conversationId) {
            setCurrentConversationId(null);
            setMessages([]);
            const newSessionId = uuidv4();
            setSessionId(newSessionId);
            localStorage.setItem('session_id', newSessionId);
          }
        }
      }
    } catch (error) {
      console.error('❌ Error deleting conversation:', error);
      
      // If network error, still try to remove from local state for local conversations
      const conversation = conversations.find(c => c.id === conversationId);
      if (conversation && !conversation.isFromServer) {
        console.log('🔄 Removing local conversation from state');
        setConversations(prev => prev.filter(c => c.id !== conversationId));
        
        if (currentConversationId === conversationId) {
          setCurrentConversationId(null);
          setMessages([]);
          const newSessionId = uuidv4();
          setSessionId(newSessionId);
          localStorage.setItem('session_id', newSessionId);
        }
      }
    }
  };

  // Show loading while checking onboarding status
  if (isCheckingOnboarding) {
    return (
      <div className="h-screen w-full bg-gradient-to-br from-gray-50 via-white to-gray-100 font-sans flex items-center justify-center">
        <LoadingSpinner size="md" text="Loading your profile..." />
      </div>
    );
  }

  // If onboarding is required and not complete, show only onboarding
  if (showOnboarding && onboardingStatus && !onboardingStatus.isComplete) {
    return (
      <div className="h-screen w-full bg-gradient-to-br from-gray-50 via-white to-gray-100 font-sans flex overflow-hidden relative">
        <OnboardingWizard 
          onComplete={handleOnboardingComplete}
          onClose={null} // Don't allow closing until complete
        />
      </div>
    );
  }

  return (
    <div className="chat-app-container h-screen w-full bg-gradient-to-br from-gray-50 via-white to-gray-100 font-sans flex relative">
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
            onDeleteConversation={handleDeleteRequest}
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
          onDeleteConversation={handleDeleteRequest}
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
          <div className="flex-shrink-0">
            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} messages={messages} />
          </div>
        </main>
      </div>
      
      {/* Confirmation Modal */}
      <ConfirmationModal
        isOpen={deleteModalOpen}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        title="Delete Conversation"
        message="Are you sure you want to delete this conversation? This action cannot be undone and all messages will be permanently removed."
        type="danger"
        confirmText="Yes, Delete"
        cancelText="No, Keep"
      />

    </div>
  );
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(null);

  const checkAuthStatus = async (retries = 1) => {
    try {
      const authUrl = `${CONFIG.API_BASE_URL}/auth/status`;
      const token = localStorage.getItem('jwt_token');
      
      console.log('🔍 Checking auth status at:', authUrl);
      console.log('🔑 Using JWT token:', token ? 'Present' : 'Missing');
      
      // If no token, skip server check and set to false immediately
      if (!token) {
        console.log('⚡ No JWT token found, setting authenticated to false');
        setIsAuthenticated(false);
        localStorage.removeItem('authState');
        return;
      }
      
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Cache-Control': 'no-cache'
      };
      
      // Create abort controller for faster timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout
      
      const response = await fetch(authUrl, {
        method: "GET",
        headers: headers,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
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
        // Only retry once, with shorter delay
        setTimeout(() => checkAuthStatus(retries - 1), 500);
      } else {
        // If auth check fails, assume not authenticated
        console.log('🔒 Auth check failed, assuming not authenticated');
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
        
        // Store auth state in localStorage immediately
        localStorage.setItem('authState', JSON.stringify({
          authenticated: true,
          timestamp: Date.now()
        }));
      }
      // Remove the parameters from URL
      window.history.replaceState({}, document.title, window.location.pathname);
      setIsAuthenticated(true);
      return; // Don't call checkAuthStatus after successful auth
    }
    
    // Try to get cached auth state first (for faster loading)
    const cachedAuth = localStorage.getItem('authState');
    const token = localStorage.getItem('jwt_token');
    
    if (cachedAuth && token) {
      try {
        const authData = JSON.parse(cachedAuth);
        // Use cached state if less than 2 minutes old for faster UX
        if (Date.now() - authData.timestamp < 120000) {
          console.log('⚡ Using cached auth state:', authData.authenticated);
          setIsAuthenticated(authData.authenticated);
          // Still verify in background but don't block UI
          setTimeout(() => checkAuthStatus(), 100);
          return;
        }
      } catch (e) {
        localStorage.removeItem('authState');
      }
    }
    
    // If no token at all, immediately set to false
    if (!token) {
      console.log('⚡ No JWT token, immediately setting to false');
      setIsAuthenticated(false);
      return;
    }
    
    // Only verify with server if no recent cached auth or successful redirect
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
          <Route path="/verify-email" element={<VerifyEmail />} />
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
