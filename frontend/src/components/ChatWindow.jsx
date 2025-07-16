import React, { useEffect, useRef, useState } from 'react';
import { CornerDownRight } from 'lucide-react';

function ChatWindow({ messages, isLoading }) {
  const chatEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Simple auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const WelcomeScreen = () => (
    <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
      <div className="mb-4">
        <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center">
            <div className="w-16 h-16 bg-red-200 rounded-full flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-600"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="M16 8l-8 8"/><path d="m8 8 8 8"/></svg>
            </div>
        </div>
      </div>
      <h2 className="text-2xl font-semibold text-gray-800">
        Welcome to <span className="text-red-600">College</span>Advising Chat
      </h2>
      <p className="mt-2">Your AI-powered advisor. How can I help you today?</p>
    </div>
  );
  
  const renderStructuredResponse = (rawText) => {
    // Basic check for structured format
    if (!rawText.includes('**') || !rawText.includes('+')) {
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
    <div
      ref={chatContainerRef}
      className="flex-1 p-6 overflow-y-auto"
    >
      {messages.length === 0 && !isLoading ? (
        <WelcomeScreen />
      ) : (
        <div className="space-y-6">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex items-end gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-full flex-shrink-0 ${msg.sender === 'user' ? 'bg-red-500' : 'bg-gray-300'} flex items-center justify-center text-white font-bold`}>
                {msg.sender === 'user' ? 'U' : 'B'}
              </div>
              <div
                className={`max-w-xl p-4 rounded-2xl ${
                  msg.sender === 'user'
                    ? 'bg-red-500 text-white rounded-br-none'
                    : msg.isError
                    ? 'bg-red-100 text-red-800 border border-red-200 rounded-bl-none'
                    : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none'
                }`}
              >
                {msg.sender === 'bot' ? renderStructuredResponse(msg.rawText) : <p>{msg.text}</p>}
              </div>
            </div>
          ))}
        </div>
      )}
      {isLoading && (
        <div className="flex items-end gap-3 mt-6">
            <div className="w-8 h-8 rounded-full flex-shrink-0 bg-gray-300 flex items-center justify-center text-white font-bold">B</div>
            <div className="p-4 rounded-2xl bg-white border border-gray-200 rounded-bl-none">
                <div className="flex items-center justify-center space-x-1">
                    <span className="h-2 w-2 bg-red-500 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                    <span className="h-2 w-2 bg-red-500 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                    <span className="h-2 w-2 bg-red-500 rounded-full animate-bounce"></span>
                </div>
            </div>
        </div>
      )}
      <div ref={chatEndRef} />
    </div>
  );
}

export default ChatWindow;
