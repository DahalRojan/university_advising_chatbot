// Production configuration constants
export const CONFIG = {
  // API Configuration
  API_BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  API_TIMEOUT: 30000, // 30 seconds
  
  // Chat Configuration  
  MAX_MESSAGE_LENGTH: 2000,
  MAX_MESSAGES_PER_SESSION: 100,
  TYPING_DELAY: 1000, // Simulated typing delay
  
  // University Branding
  UNIVERSITY: {
    name: 'Gannon University',
    logo: 'https://upload.wikimedia.org/wikipedia/commons/4/49/Gannon_university_logo.png',
    colors: {
      primary: '#8B1538', // Gannon red
      secondary: '#FFFFFF',
      accent: '#F3F4F6'
    }
  },
  
  // Feature Flags
  FEATURES: {
    voiceInput: false,
    darkMode: false,
    exportChat: true,
    analytics: import.meta.env.MODE === 'production'
  },
  
  // Error Messages
  ERRORS: {
    network: 'Unable to connect to the server. Please check your internet connection.',
    timeout: 'The request took too long. Please try again.',
    server: 'Server error occurred. Please try again later.',
    rateLimit: 'Too many requests. Please wait before trying again.',
    generic: 'Something went wrong. Please try again.'
  },
  
  // Accessibility
  ACCESSIBILITY: {
    announceMessages: true,
    keyboardNavigation: true,
    highContrast: false,
    reducedMotion: false
  }
};

// Environment-specific overrides
if (import.meta.env.MODE === 'production') {
  CONFIG.API_BASE_URL = import.meta.env.VITE_API_URL || window.location.origin;
}

export default CONFIG;