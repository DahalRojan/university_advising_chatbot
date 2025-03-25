import React, { useEffect, useRef, useState } from 'react';

function ChatWindow({ messages, isLoading }) {
  const chatEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const [displayedMessages, setDisplayedMessages] = useState([]);
  const [isUserScrolling, setIsUserScrolling] = useState(false);

  // Parse raw response into structured format
  const parseResponse = (rawResponse) => {
    if (rawResponse.includes('**') && rawResponse.includes('+')) {
      try {
        const [intro, ...courseSections] = rawResponse.split('\n\n');
        const structured = {
          intro: intro || 'Here’s the list of courses for your curriculum! I’ve organized them by semester for clarity.',
          sections: [],
        };

        const sections = courseSections.join('\n\n').split('**').filter(Boolean);
        sections.forEach((section) => {
          const [title, ...content] = section.split(':');
          const courses = content.join(':').split('+').map((course) => course.trim()).filter(Boolean);

          if (title && courses.length > 0) {
            structured.sections.push({
              title: title.trim(),
              courses,
            });
          }
        });

        return structured.sections.length > 0
          ? structured
          : { intro: rawResponse, sections: [] };
      } catch (error) {
        console.error('Error parsing response:', error);
        return { intro: rawResponse, sections: [] };
      }
    } else {
      return { intro: rawResponse, sections: [] };
    }
  };

  // Detect if the user is scrolling
  useEffect(() => {
    const handleScroll = () => {
      const container = chatContainerRef.current;
      if (container) {
        const isAtBottom =
          container.scrollHeight - container.scrollTop <= container.clientHeight + 1;
        setIsUserScrolling(!isAtBottom);
      }
    };

    const container = chatContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
    }

    return () => {
      if (container) {
        container.removeEventListener('scroll', handleScroll);
      }
    };
  }, []);

  // Handle typing animation for all messages
  useEffect(() => {
    if (messages.length === 0) {
      setDisplayedMessages([]);
      return;
    }

    // Initialize displayed messages for all messages
    const newDisplayedMessages = messages.map((msg, index) => {
      const existingMessage = displayedMessages[index];
      if (existingMessage && !existingMessage.isTyping) {
        return existingMessage;
      }

      if (msg.sender === 'user') {
        return {
          ...msg,
          displayedText: msg.text || '',
          displayedStructuredText: null,
          isTyping: false,
        };
      }

      const structuredText = parseResponse(msg.rawText);
      const { intro, sections } = structuredText;

      const introSentences = intro
        .split(/(?<=[.!?])\s+/)
        .filter(Boolean)
        .map((sentence) => sentence.trim());

      return {
        ...msg,
        displayedText: '',
        displayedStructuredText: { intro: '', sections: [] },
        isTyping: true,
        introSentences,
        sections,
        currentSentenceIndex: 0,
        currentSentenceText: '',
        charIndex: 0,
        displayedSentences: [],
        currentSectionIndex: -1,
        currentSectionText: '',
        sectionCharIndex: 0,
        displayedSections: [],
      };
    });

    setDisplayedMessages(newDisplayedMessages);

    // Find the first message that needs animation
    const messageToAnimate = newDisplayedMessages.find((msg) => msg.isTyping);
    if (!messageToAnimate) return;

    const messageIndex = newDisplayedMessages.indexOf(messageToAnimate);

    const typingInterval = setInterval(() => {
      setDisplayedMessages((prev) => {
        const updated = [...prev];
        const msg = updated[messageIndex];

        // Step 1: Type the intro sentences
        if (msg.currentSectionIndex === -1) {
          if (msg.currentSentenceIndex < msg.introSentences.length) {
            const currentSentence = msg.introSentences[msg.currentSentenceIndex];
            if (msg.charIndex < currentSentence.length) {
              msg.currentSentenceText += currentSentence[msg.charIndex];
              msg.displayedSentences[msg.currentSentenceIndex] = msg.currentSentenceText;

              msg.displayedStructuredText = {
                intro: msg.displayedSentences.join(' '),
                sections: [],
              };
              msg.charIndex++;
            } else {
              msg.currentSentenceIndex++;
              msg.charIndex = 0;
              msg.currentSentenceText = '';
              msg.displayedSentences[msg.currentSentenceIndex] = '';
              setTimeout(() => {}, 200);
            }
          } else {
            msg.currentSectionIndex = msg.sections.length > 0 ? 0 : Infinity;
            msg.charIndex = 0;
          }
        }
        // Step 2: Type each section (if any)
        else if (msg.currentSectionIndex < msg.sections.length) {
          const currentSection = msg.sections[msg.currentSectionIndex];
          const sectionText = `${currentSection.title}\n${currentSection.courses.join('\n')}`;

          if (msg.sectionCharIndex === 0) {
            msg.displayedSections = [...msg.displayedSections, { title: currentSection.title, courses: [] }];
          }

          if (msg.sectionCharIndex < sectionText.length) {
            msg.currentSectionText += sectionText[msg.sectionCharIndex];
            const displayedCourses = currentSection.courses.filter((course) =>
              msg.currentSectionText.includes(course)
            );
            msg.displayedSections[msg.currentSectionIndex] = {
              title: currentSection.title,
              courses: displayedCourses,
            };

            msg.displayedStructuredText = {
              intro: msg.introSentences.join(' '),
              sections: msg.displayedSections,
            };
            msg.sectionCharIndex++;
          } else {
            msg.currentSectionIndex++;
            msg.sectionCharIndex = 0;
            msg.currentSectionText = '';
            setTimeout(() => {}, 200);
          }
        } else {
          clearInterval(typingInterval);
          msg.isTyping = false;
          msg.displayedStructuredText = {
            intro: msg.introSentences.join(' '),
            sections: msg.sections,
          };
        }

        return updated;
      });
    }, 10); // Typing speed (10ms per character)

    return () => clearInterval(typingInterval);
  }, [messages]);

  // Scroll to bottom only if the user is not scrolling
  useEffect(() => {
    if (!isUserScrolling) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [displayedMessages, isUserScrolling]);

  return (
    <div
      ref={chatContainerRef}
      className="flex-1 p-6 overflow-y-auto bg-gray-800"
      style={{ maxHeight: 'calc(100vh - 120px)' }} // Adjust height to fit within viewport
    >
      {displayedMessages.length === 0 ? (
        <div className="text-center text-gray-200 mt-20">
          <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 text-transparent bg-clip-text">
            Welcome to Student Advising
          </h2>
          <p className="mt-2">Ask me anything about your university journey!</p>
        </div>
      ) : (
        displayedMessages.map((msg, index) => (
          <div
            key={index}
            className={`mb-4 flex ${
              msg.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-2xl p-4 rounded-lg ${
                msg.sender === 'user'
                  ? 'bg-blue-600'
                  : msg.isError
                  ? 'bg-red-600'
                  : 'bg-gray-700'
              }`}
            >
              {msg.displayedStructuredText ? (
                <div>
                  {msg.displayedStructuredText.intro && (
                    <p className="text-gray-200 mb-4 whitespace-pre-wrap">
                      {msg.displayedStructuredText.intro}
                    </p>
                  )}
                  {msg.displayedStructuredText.sections.map((section, idx) => (
                    <div key={idx} className="mb-4">
                      {section.title && (
                        <h3 className="text-lg font-bold text-gray-100 mb-2">
                          {section.title}
                        </h3>
                      )}
                      <ul className="list-disc list-inside space-y-1">
                        {section.courses.map((course, courseIdx) => (
                          course && (
                            <li key={courseIdx} className="text-gray-200">
                              {course}
                            </li>
                          )
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-200">{msg.displayedText || msg.text}</p>
              )}
              <p className="text-xs text-gray-400 mt-2">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))
      )}
      {isLoading && (
        <div className="text-center text-gray-400">
          <p>
            Typing
            <span className="animate-pulse inline-block">.</span>
            <span className="animate-pulse inline-block animation-delay-200">.</span>
            <span className="animate-pulse inline-block animation-delay-400">.</span>
          </p>
        </div>
      )}
      <div ref={chatEndRef} />
    </div>
  );
}

export default ChatWindow;