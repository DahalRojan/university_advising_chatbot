/**
 * Email Verification Page
 * 
 * Handles email verification when users click verification links from emails.
 * Extracts token from URL parameters and calls verification endpoint.
 */

import React, { useEffect, useState } from 'react';
import { CheckCircle, AlertCircle, Loader, Mail, ArrowLeft } from 'lucide-react';
import { CONFIG } from '../config/constants';

const VerifyEmail = () => {
  const [status, setStatus] = useState('verifying'); // 'verifying', 'success', 'error'
  const [message, setMessage] = useState('');
  const [isResending, setIsResending] = useState(false);

  useEffect(() => {
    const verifyEmail = async () => {
      // Extract token from URL parameters
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get('token');

      if (!token) {
        console.error('🚫 No verification token found in URL');
        setStatus('error');
        setMessage('Invalid verification link. Please check your email and try again.');
        return;
      }

      console.log('🔍 Starting email verification with token:', token.substring(0, 10) + '...');

      try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/auth/verify-email`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token })
        });

        const data = await response.json();
        console.log('📡 Verification API response:', { status: response.status, success: data.success, message: data.message });

        if (response.ok && data.success) {
          console.log('✅ Email verification successful!');
          setStatus('success');
          setMessage(data.message || 'Email verified successfully!');
          
          // Show success message briefly then redirect to login with success indicator
          setTimeout(() => {
            console.log('🔄 Redirecting to login page with verified=true parameter');
            window.location.href = '/login?verified=true';
          }, 2000); // Reduced to 2 seconds for better UX
        } else {
          console.error('❌ Email verification failed:', { status: response.status, data });
          setStatus('error');
          setMessage(data.message || 'Verification failed. The link may be expired or invalid.');
        }
      } catch (error) {
        console.error('Email verification error:', error);
        setStatus('error');
        setMessage('Network error. Please check your connection and try again.');
      }
    };

    verifyEmail();
  }, []);

  const handleResendVerification = async () => {
    const email = prompt('Please enter your email address to resend verification:');
    if (!email) return;

    setIsResending(true);
    try {
      const response = await fetch(`${CONFIG.API_BASE_URL}/auth/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      const data = await response.json();
      
      if (data.success) {
        alert('Verification email sent! Please check your inbox.');
      } else {
        alert(data.message || 'Failed to resend verification email.');
      }
    } catch (error) {
      alert('Failed to resend verification email. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

  const goToLogin = () => {
    window.location.href = '/login?verified=true';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 flex items-center justify-center p-4">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-red-800/4 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-red-900/4 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 w-full max-w-md">
        <div className="bg-white/90 backdrop-blur-xl border border-gray-100/50 rounded-3xl shadow-2xl shadow-gray-200/20 p-8">
          
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center space-x-3 mb-6">
              <img
                src="https://upload.wikimedia.org/wikipedia/commons/4/49/Gannon_university_logo.png"
                alt="Gannon University"
                className="w-10 h-10"
              />
              <h1 className="text-xl font-bold">
                <span className="bg-gradient-to-r from-red-800 to-red-700 bg-clip-text text-transparent">
                  Advisor
                </span>
              </h1>
            </div>
          </div>

          {/* Status Content */}
          <div className="text-center">
            {status === 'verifying' && (
              <div>
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Loader className="w-8 h-8 text-blue-600 animate-spin" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Verifying Your Email
                </h2>
                <p className="text-gray-600 mb-6">
                  Please wait while we verify your email address...
                </p>
              </div>
            )}

            {status === 'success' && (
              <div>
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-green-600" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Email Verified Successfully!
                </h2>
                <p className="text-gray-600 mb-6">
                  {message}
                </p>
                <p className="text-sm text-gray-500 mb-6">
                  Redirecting to login page in 2 seconds...
                </p>
                <button
                  onClick={goToLogin}
                  className="w-full bg-gradient-to-r from-red-800 to-red-700 text-white py-3 px-4 rounded-lg hover:from-red-900 hover:to-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-all duration-200 font-medium"
                >
                  Go to Login
                </button>
              </div>
            )}

            {status === 'error' && (
              <div>
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <AlertCircle className="w-8 h-8 text-red-600" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Verification Failed
                </h2>
                <p className="text-gray-600 mb-6">
                  {message}
                </p>
                
                <div className="space-y-3">
                  <button
                    onClick={handleResendVerification}
                    disabled={isResending}
                    className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-3 px-4 rounded-lg hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium"
                  >
                    {isResending ? (
                      <div className="flex items-center justify-center space-x-2">
                        <Loader className="w-4 h-4 animate-spin" />
                        <span>Resending...</span>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center space-x-2">
                        <Mail className="w-4 h-4" />
                        <span>Resend Verification Email</span>
                      </div>
                    )}
                  </button>
                  
                  <button
                    onClick={goToLogin}
                    className="w-full bg-gray-100 text-gray-700 py-3 px-4 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-all duration-200 font-medium"
                  >
                    <div className="flex items-center justify-center space-x-2">
                      <ArrowLeft className="w-4 h-4" />
                      <span>Back to Login</span>
                    </div>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8">
          <p className="text-xs text-gray-500">
            Need help? Contact support at support@gannon.edu
          </p>
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;