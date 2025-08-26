import React, { useState, useEffect } from "react";
import { 
  CheckCircle, 
  MessageCircle, 
  Calendar, 
  GraduationCap, 
  BookOpen, 
  Users,
  User,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  Loader,
  UserPlus,
  RefreshCw,
  Mail
} from 'lucide-react';
import { CONFIG } from '../config/constants';
import RegisterModal from '../components/auth/RegisterModal';

const Login = () => {
  // State for username/password login
  const [loginData, setLoginData] = useState({
    identifier: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [verificationError, setVerificationError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [isResendingEmail, setIsResendingEmail] = useState(false);
  const [verificationSuccess, setVerificationSuccess] = useState(false);

  // Handle dynamic viewport height for mobile
  useEffect(() => {
    const setVH = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
    };

    setVH();
    window.addEventListener('resize', setVH);
    window.addEventListener('orientationchange', setVH);

    return () => {
      window.removeEventListener('resize', setVH);
      window.removeEventListener('orientationchange', setVH);
    };
  }, []);

  // Check for verification success parameter
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('verified') === 'true') {
      setVerificationSuccess(true);
      // Remove the parameter from URL
      window.history.replaceState({}, document.title, window.location.pathname);
      // Auto-hide success message after 8 seconds
      setTimeout(() => {
        setVerificationSuccess(false);
      }, 8000);
    }
  }, []);

  // Microsoft OAuth login handler
  const handleMicrosoftLogin = () => {
    const loginUrl = `${CONFIG.API_BASE_URL}/login`;
    console.log('🚀 Attempting redirect to backend login URL:', loginUrl);
    window.location.href = loginUrl;
  };

  // Username/password login handler
  const handlePasswordLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setLoginError('');
    setVerificationError(null);

    try {
      const response = await fetch(`${CONFIG.API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginData)
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Store JWT token
        localStorage.setItem('jwt_token', data.token);
        
        // Store auth state
        localStorage.setItem('authState', JSON.stringify({
          authenticated: true,
          timestamp: Date.now()
        }));

        // Redirect to main app
        window.location.href = '/';
      } else {
        // Check if this is an email verification error
        if (response.status === 403 && typeof data.detail === 'object' && data.detail.error_type === 'email_not_verified') {
          setVerificationError(data.detail);
        } else {
          const errorMessage = typeof data.detail === 'string' ? data.detail : 
                              (typeof data.detail === 'object' ? data.detail.message : 
                               'Login failed. Please check your credentials.');
          setLoginError(errorMessage);
        }
      }
    } catch (error) {
      console.error('Login error:', error);
      setLoginError('Network error. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setLoginData(prev => ({ ...prev, [name]: value }));
    // Clear error when user types
    if (loginError) setLoginError('');
    if (verificationError) setVerificationError(null);
  };

  const handleResendVerification = async () => {
    setIsResendingEmail(true);
    
    try {
      const response = await fetch(`${CONFIG.API_BASE_URL}/auth/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: verificationError.email })
      });

      const data = await response.json();
      
      if (response.ok && data.success) {
        setVerificationError({
          ...verificationError,
          message: 'Verification email sent! Please check your inbox.',
          sent: true
        });
      } else {
        setLoginError(data.detail || 'Failed to resend verification email.');
        setVerificationError(null);
      }
    } catch (error) {
      console.error('Resend verification error:', error);
      setLoginError('Network error. Please try again.');
      setVerificationError(null);
    } finally {
      setIsResendingEmail(false);
    }
  };

  const features = [
    {
      icon: <MessageCircle className="w-6 h-6" />,
      title: "24/7 Academic Support",
      description: "Get instant answers to your academic questions anytime, anywhere"
    },
    {
      icon: <Calendar className="w-6 h-6" />,
      title: "Smart Schedule Planning",
      description: "Plan your courses and optimize your academic timeline"
    },
    {
      icon: <GraduationCap className="w-6 h-6" />,
      title: "Degree Progress Tracking",
      description: "Monitor your progress toward graduation requirements"
    },
    {
      icon: <BookOpen className="w-6 h-6" />,
      title: "Course Recommendations",
      description: "Get personalized course suggestions based on your major"
    }
  ];

  return (
    <div className="login-page">
      {/* Mobile Layout */}
      <div className="lg:hidden bg-gradient-to-br from-gray-50 via-white to-gray-100 min-h-screen-safe overflow-y-auto">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-red-800/4 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-red-900/4 rounded-full blur-3xl"></div>
        </div>
        
        <div className="relative z-10 min-h-screen-safe">
          <div className="container mx-auto px-4 py-6 min-h-screen-safe flex flex-col">
            {/* Mobile Header */}
            <div className="text-center py-4 flex-shrink-0">
              <div className="flex items-center justify-center space-x-3 mb-4">
                <img
                  src="https://upload.wikimedia.org/wikipedia/commons/4/49/Gannon_university_logo.png"
                  alt="Gannon University Logo"
                  className="w-8 h-8 shadow-lg"
                />
                <div>
                  <h1 className="text-lg font-bold">
                    <span className="bg-gradient-to-r from-red-800 to-red-700 bg-clip-text text-transparent">
                      Advisor
                    </span>
                  </h1>
                  <p className="text-gray-600 text-xs">AI-Powered Academic Guidance</p>
                </div>
              </div>
            </div>

            {/* Mobile Login Section - Centered */}
            <div className="flex-1 flex items-center justify-center py-4">
              <div className="w-full max-w-sm">
                <div className="bg-white/90 backdrop-blur-xl border border-gray-100/50 rounded-3xl shadow-2xl shadow-gray-200/20 p-5">
              {/* Login Header */}
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-gradient-to-br from-red-800 to-red-900 rounded-3xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-red-800/25">
                  <Users className="w-8 h-8 text-white" />
                </div>
                <h2 className="text-xl font-bold text-gray-800 mb-2">
                  Welcome Back
                </h2>
                <p className="text-gray-600 text-sm">
                  Sign in to your account
                </p>
              </div>

              {/* Email Verification Success Message */}
              {verificationSuccess && (
                <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-xl">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                    <div>
                      <p className="text-green-800 font-medium text-sm">
                        Email verified successfully!
                      </p>
                      <p className="text-green-700 text-xs mt-1">
                        You can now log in to your account.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Username/Password Login Form */}
              <form onSubmit={handlePasswordLogin} className="space-y-3 mb-4">
                {loginError && (
                  <div className="bg-red-50 border border-red-200 rounded-md p-3 flex items-start space-x-2">
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                    <span className="text-red-700 text-sm">{loginError}</span>
                  </div>
                )}
                
                {verificationError && (
                  <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                    <div className="flex items-start space-x-2">
                      <Mail className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-blue-700 text-sm mb-2">{verificationError.message}</p>
                        {verificationError.email && (
                          <p className="text-blue-600 text-xs mb-3">
                            Email: <span className="font-medium">{verificationError.email}</span>
                          </p>
                        )}
                        {!verificationError.sent && verificationError.can_resend && (
                          <button
                            type="button"
                            onClick={handleResendVerification}
                            disabled={isResendingEmail}
                            className="flex items-center text-xs text-blue-700 hover:text-blue-800 font-medium transition-colors disabled:opacity-50"
                          >
                            {isResendingEmail ? (
                              <>
                                <Loader className="w-3 h-3 mr-1 animate-spin" />
                                Sending...
                              </>
                            ) : (
                              <>
                                <RefreshCw className="w-3 h-3 mr-1" />
                                Resend verification email
                              </>
                            )}
                          </button>
                        )}
                        {verificationError.sent && (
                          <div className="flex items-center text-xs text-green-700">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Email sent successfully!
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    name="identifier"
                    value={loginData.identifier}
                    onChange={handleInputChange}
                    placeholder="Username or email"
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                    required
                  />
                </div>

                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    value={loginData.password}
                    onChange={handleInputChange}
                    placeholder="Password"
                    className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-gradient-to-r from-red-800 to-red-700 text-white py-3 px-4 rounded-lg hover:from-red-900 hover:to-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center space-x-2">
                      <Loader className="w-4 h-4 animate-spin" />
                      <span>Signing in...</span>
                    </div>
                  ) : (
                    'Sign In'
                  )}
                </button>
              </form>

              {/* Separator */}
              <div className="flex items-center my-4">
                <div className="flex-1 border-t border-gray-200"></div>
                <span className="px-3 text-gray-500 text-sm">or</span>
                <div className="flex-1 border-t border-gray-200"></div>
              </div>

              {/* Microsoft Login Button */}
              <button
                onClick={handleMicrosoftLogin}
                className="w-full flex items-center justify-center py-3 px-6 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-base font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-blue-500/30 mb-4"
              >
                <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24" fill="none">
                  <rect fill="#F35325" x="1" y="1" width="10" height="10" />
                  <rect fill="#81BC06" x="13" y="1" width="10" height="10" />
                  <rect fill="#05A6F0" x="1" y="13" width="10" height="10" />
                  <rect fill="#FFBA08" x="13" y="13" width="10" height="10" />
                </svg>
                Continue with Microsoft
              </button>

              {/* Register Link */}
              <div className="text-center">
                <p className="text-gray-600 text-sm mb-3">
                  Don't have an account?
                </p>
                <button
                  onClick={() => setShowRegisterModal(true)}
                  className="inline-flex items-center space-x-2 text-red-600 hover:text-red-700 font-medium text-sm transition-colors"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>Create Account</span>
                </button>
              </div>
                </div>
              </div>
            </div>
            
            {/* Bottom padding for mobile safe area */}
            <div className="flex-shrink-0 pb-safe"></div>
          </div>
        </div>
      </div>

      {/* Desktop Layout */}
      <div className="hidden lg:block bg-gradient-to-br from-gray-50 via-white to-gray-100 relative h-screen-safe overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-red-800/4 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-red-900/4 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10 h-full flex items-center w-full max-w-none mx-0 px-16 lg:px-20 py-4 lg:py-8">
          {/* Left Section - Information */}
          <div className="w-1/2 flex items-center justify-center p-8 lg:p-12 bg-gradient-to-br from-white/60 to-white/20 backdrop-blur-sm rounded-l-2xl">
            <div className="w-full max-w-xl">
              {/* Header */}
              <div className="flex items-center space-x-3 mb-6">
                <img
                  src="https://upload.wikimedia.org/wikipedia/commons/4/49/Gannon_university_logo.png"
                  alt="Gannon University Logo"
                  className="w-10 h-10 shadow-lg"
                />
                <div>
                  <h1 className="text-xl lg:text-2xl font-bold">
                    <span className="bg-gradient-to-r from-red-800 to-red-700 bg-clip-text text-transparent">
                      Advisor
                    </span>
                  </h1>
                  <p className="text-gray-600 text-xs lg:text-sm">AI-Powered Academic Guidance</p>
                </div>
              </div>

              {/* Main Description */}
              <div className="mb-6">
                <h2 className="text-2xl lg:text-3xl font-bold text-gray-800 mb-3 leading-tight">
                  Your Personal Academic Assistant
                </h2>
                <p className="text-gray-600 text-base lg:text-lg leading-relaxed mb-4">
                  Navigate your academic journey with confidence. Get personalized guidance, 
                  course planning, and degree tracking to succeed at every step.
                </p>
                
                {/* Benefits */}
                <div className="space-y-2">
                  <div className="flex items-center space-x-3 text-gray-700">
                    <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                      <CheckCircle className="w-3 h-3 text-white" />
                    </div>
                    <span className="text-sm lg:text-base">Instant access to academic information</span>
                  </div>
                  <div className="flex items-center space-x-3 text-gray-700">
                    <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                      <CheckCircle className="w-3 h-3 text-white" />
                    </div>
                    <span className="text-sm lg:text-base">Personalized course recommendations</span>
                  </div>
                  <div className="flex items-center space-x-3 text-gray-700">
                    <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                      <CheckCircle className="w-3 h-3 text-white" />
                    </div>
                    <span className="text-sm lg:text-base">Track graduation requirements</span>
                  </div>
                </div>
              </div>

              {/* Features Grid */}
              <div className="hidden lg:grid grid-cols-2 gap-2 lg:gap-3 mb-4">
                {features.map((feature, index) => (
                  <div key={index} className="group p-3 bg-white/70 backdrop-blur-sm rounded-lg border border-gray-100/50 hover:bg-white/90 hover:shadow-lg transition-all duration-200">
                    <div className="text-center">
                      <div className="w-8 h-8 bg-gradient-to-br from-red-800 to-red-900 rounded-lg flex items-center justify-center text-white shadow-lg shadow-red-800/25 mx-auto mb-1 group-hover:scale-110 transition-transform duration-200">
                        {feature.icon}
                      </div>
                      <h3 className="font-semibold text-gray-800 mb-0.5 text-xs">{feature.title}</h3>
                      <p className="text-xs text-gray-600">{feature.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Section - Login */}
          <div className="w-1/2 flex items-center justify-center p-8 lg:p-12 bg-white/5 rounded-r-2xl">
            <div className="w-full max-w-md">
              <div className="bg-white/90 backdrop-blur-xl border border-gray-100/50 rounded-2xl shadow-2xl shadow-gray-200/20 p-6 lg:p-8">
                {/* Login Header */}
                <div className="text-center mb-6">
                  <div className="w-16 h-16 bg-gradient-to-br from-red-800 to-red-900 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-red-800/25">
                    <Users className="w-8 h-8 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-800 mb-2">
                    Welcome Back
                  </h2>
                  <p className="text-gray-600 text-base leading-relaxed">
                    Sign in to access your personalized academic advisor
                  </p>
                </div>

                {/* Email Verification Success Message */}
                {verificationSuccess && (
                  <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
                      <div>
                        <p className="text-green-800 font-semibold">
                          Email verified successfully!
                        </p>
                        <p className="text-green-700 text-sm mt-1">
                          You can now log in to your account.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Username/Password Login Form */}
                <form onSubmit={handlePasswordLogin} className="space-y-4 mb-6">
                  {loginError && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-3 flex items-start space-x-3">
                      <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                      <span className="text-red-700 text-sm">{loginError}</span>
                    </div>
                  )}
                  
                  {verificationError && (
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                      <div className="flex items-start space-x-3">
                        <Mail className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <p className="text-blue-700 text-sm mb-3">{verificationError.message}</p>
                          {verificationError.email && (
                            <p className="text-blue-600 text-xs mb-3">
                              Email: <span className="font-medium">{verificationError.email}</span>
                            </p>
                          )}
                          {!verificationError.sent && verificationError.can_resend && (
                            <button
                              type="button"
                              onClick={handleResendVerification}
                              disabled={isResendingEmail}
                              className="flex items-center text-sm text-blue-700 hover:text-blue-800 font-medium transition-colors disabled:opacity-50"
                            >
                              {isResendingEmail ? (
                                <>
                                  <Loader className="w-4 h-4 mr-2 animate-spin" />
                                  Sending...
                                </>
                              ) : (
                                <>
                                  <RefreshCw className="w-4 h-4 mr-2" />
                                  Resend verification email
                                </>
                              )}
                            </button>
                          )}
                          {verificationError.sent && (
                            <div className="flex items-center text-sm text-green-700">
                              <CheckCircle className="w-4 h-4 mr-2" />
                              Email sent successfully!
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-6 h-6" />
                    <input
                      type="text"
                      name="identifier"
                      value={loginData.identifier}
                      onChange={handleInputChange}
                      placeholder="Username or email"
                      className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      required
                    />
                  </div>

                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-6 h-6" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      name="password"
                      value={loginData.password}
                      onChange={handleInputChange}
                      placeholder="Password"
                      className="w-full pl-12 pr-14 py-3 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showPassword ? <EyeOff className="w-6 h-6" /> : <Eye className="w-6 h-6" />}
                    </button>
                  </div>

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-gradient-to-r from-red-800 to-red-700 text-white py-3 px-4 rounded-lg text-base font-semibold hover:from-red-900 hover:to-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
                  >
                    {isLoading ? (
                      <div className="flex items-center justify-center space-x-2">
                        <Loader className="w-5 h-5 animate-spin" />
                        <span>Signing in...</span>
                      </div>
                    ) : (
                      'Sign In'
                    )}
                  </button>
                </form>

                {/* Separator */}
                <div className="flex items-center mb-4">
                  <div className="flex-1 border-t border-gray-300"></div>
                  <span className="px-4 text-gray-500 text-base font-medium">or</span>
                  <div className="flex-1 border-t border-gray-300"></div>
                </div>

                {/* Microsoft Login Button */}
                <button
                  onClick={handleMicrosoftLogin}
                  className="w-full flex items-center justify-center py-3 px-6 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-base font-semibold rounded-lg shadow-xl shadow-blue-600/30 hover:shadow-blue-600/50 transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-blue-500/30 mb-6"
                >
                  <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="none">
                    <rect fill="#F35325" x="1" y="1" width="10" height="10" />
                    <rect fill="#81BC06" x="13" y="1" width="10" height="10" />
                    <rect fill="#05A6F0" x="1" y="13" width="10" height="10" />
                    <rect fill="#FFBA08" x="13" y="13" width="10" height="10" />
                  </svg>
                  Continue with Microsoft
                </button>

                {/* Register Link */}
                <div className="text-center">
                  <p className="text-gray-600 text-base mb-3">
                    Don't have an account?
                  </p>
                  <button
                    onClick={() => setShowRegisterModal(true)}
                    className="inline-flex items-center space-x-2 text-red-600 hover:text-red-700 font-semibold text-base transition-colors"
                  >
                    <UserPlus className="w-4 h-4" />
                    <span>Create Account</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Register Modal */}
      <RegisterModal
        isOpen={showRegisterModal}
        onClose={() => setShowRegisterModal(false)}
        onSuccess={() => {
          setShowRegisterModal(false);
          // Optionally show success message or auto-fill login form
        }}
      />
    </div>
  );
};

export default Login;