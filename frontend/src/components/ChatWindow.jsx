import React, { useEffect, useRef, memo } from 'react';
import { CornerDownRight, RefreshCw, AlertCircle } from 'lucide-react';
import { ChatLoader } from './LoadingSpinner';

function ChatWindow({ messages, isLoading, scrollToBottom = true, onRetryMessage }) {
  const chatEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  useEffect(() => {
    if (scrollToBottom && chatEndRef.current) {
      // For new messages, scroll to bottom
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    } else if (!scrollToBottom && chatContainerRef.current && messages.length > 0) {
      // For history conversations, start at the top but allow full scrolling
      setTimeout(() => {
        if (chatContainerRef.current) {
          chatContainerRef.current.scrollTop = 0;
        }
      }, 50);
    }
  }, [messages, isLoading, scrollToBottom]);

  const WelcomeScreen = () => (
    <div className="flex flex-col items-center justify-center h-full text-center p-6">
      <div className="mb-8">
        <div className="relative">
          <div className="w-24 h-24 md:w-32 md:h-32 bg-gradient-to-br from-red-800 to-red-900 rounded-3xl flex items-center justify-center shadow-lg shadow-red-800/25 transform rotate-3">
            <div className="w-18 h-18 md:w-24 md:h-24 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center transform -rotate-3">
              <div className="w-12 h-12 md:w-16 md:h-16 bg-white rounded-xl flex items-center justify-center shadow-inner">
                <svg className="w-6 h-6 md:w-8 md:h-8 text-red-800" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 1H5C3.89 1 3 1.89 3 3V21C3 22.11 3.89 23 5 23H11V21H5V3H13V9H21ZM14 10V12H12V14H14V16H16V14H18V12H16V10H14Z"/>
                </svg>
              </div>
            </div>
          </div>
          <div className="absolute -top-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-2 border-white shadow-lg animate-pulse"></div>
        </div>
      </div>
      <div className="max-w-md mx-auto">
        <h2 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent mb-4">
          Welcome to <span className="bg-gradient-to-r from-red-600 to-red-500 bg-clip-text text-transparent">University</span> Advising
        </h2>
        <div className="space-y-3">
          <p className="text-gray-600 text-base md:text-lg">Your AI-powered academic advisor is ready to help</p>
          <div className="flex flex-wrap gap-2 justify-center mt-6">
            <span className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm font-medium border border-red-100">Course Planning</span>
            <span className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm font-medium border border-red-100">Degree Requirements</span>
            <span className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm font-medium border border-red-100">Academic Support</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderStructuredResponse = (rawText) => {
    if (!rawText || (!rawText.includes('**') || !rawText.includes('+'))) {
      return <p className="whitespace-pre-wrap">{rawText}</p>;
    }

    try {
      const [intro, ...courseSections] = rawText.split('\n\n');
      const sections = courseSections.join('\n\n').split('**').filter(Boolean);

      return (
        <div>
          {intro && <p className="mb-4 whitespace-pre-wrap">{intro}</p>}
          {sections.map((section, idx) => {
            const [title, ...content] = section.split(':');
            const courses = content.join(':').split('+').map(c => c.trim()).filter(Boolean);
            return (
              <div key={idx} className="mb-3 last:mb-0">
                {title && <h3 className="font-semibold text-gray-800 mb-2">{title.trim()}</h3>}
                <ul className="space-y-1">
                  {courses.map((course, courseIdx) => (
                    <li key={courseIdx} className="flex items-start">
                      <CornerDownRight className="w-4 h-4 mr-2 mt-1 text-red-500 flex-shrink-0" />
                      <span>{course}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      );
    } catch (error) {
      console.error("Error parsing structured response:", error);
      return <p className="whitespace-pre-wrap">{rawText}</p>;
    }
  };


  return (
    <div className="flex-1 flex flex-col h-full">
      <div 
        ref={chatContainerRef} 
        className="flex-1 p-4 md:p-6 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-400 hover:scrollbar-thumb-gray-500 scrollbar-track-gray-100 scroll-smooth"
        style={{ height: '100%', minHeight: '0' }}
        role="log"
        aria-live="polite"
        aria-label="Chat conversation"
      >
        {messages.length === 0 && !isLoading ? (
          <WelcomeScreen />
        ) : (
          <div className="space-y-8">
            {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex items-end gap-3 md:gap-4 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-10 h-10 rounded-2xl flex-shrink-0 flex items-center justify-center text-white font-semibold text-sm shadow-lg ${
                msg.sender === 'user' 
                  ? 'bg-gradient-to-br from-red-500 to-red-600 shadow-red-500/25' 
                  : 'bg-gradient-to-br from-gray-600 to-gray-700 shadow-gray-600/25'
              }`}>
                {msg.sender === 'user' ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 1H5C3.89 1 3 1.89 3 3V21C3 22.11 3.89 23 5 23H11V21H5V3H13V9H21ZM14 10V12H12V14H14V16H16V14H18V12H16V10H14Z"/>
                  </svg>
                )}
              </div>
              <div
                className={`max-w-[80%] md:max-w-xl p-4 md:p-5 rounded-3xl shadow-lg backdrop-blur-sm ${
                  msg.sender === 'user'
                    ? 'bg-gradient-to-br from-red-500 to-red-600 text-white rounded-br-lg shadow-red-500/20'
                    : msg.isError
                      ? 'bg-gradient-to-br from-red-50 to-red-100 text-red-800 border border-red-200 rounded-bl-lg shadow-red-200/50'
                      : 'bg-white/80 backdrop-blur-md border border-gray-100 text-gray-800 rounded-bl-lg shadow-gray-200/50'
                }`}
              >
                <div className="relative">
                  {msg.sender === 'bot' ? renderStructuredResponse(msg.rawText) : <p className="text-sm md:text-base leading-relaxed">{msg.text}</p>}
                  {msg.isError && onRetryMessage && (
                    <div className="mt-3 pt-3 border-t border-red-200">
                      <button
                        onClick={() => onRetryMessage(index)}
                        className="flex items-center text-xs text-red-700 hover:text-red-800 font-medium transition-colors duration-200"
                      >
                        <RefreshCw className="w-3 h-3 mr-1" />
                        Try Again
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          </div>
        )}
        {isLoading && (
          <div className="flex items-end gap-3 md:gap-4 mt-8">
            <div className="w-10 h-10 rounded-2xl flex-shrink-0 bg-gradient-to-br from-gray-600 to-gray-700 shadow-lg shadow-gray-600/25 flex items-center justify-center text-white font-semibold text-sm">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 1H5C3.89 1 3 1.89 3 3V21C3 22.11 3.89 23 5 23H11V21H5V3H13V9H21ZM14 10V12H12V14H14V16H16V14H18V12H16V10H14Z"/>
              </svg>
            </div>
            <div className="p-4 md:p-5 rounded-3xl rounded-bl-lg bg-white/80 backdrop-blur-md border border-gray-100 shadow-lg shadow-gray-200/50">
              <ChatLoader />
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>
    </div>
  );
}

export default memo(ChatWindow);
