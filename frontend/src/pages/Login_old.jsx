import React from "react";
import { CheckCircle, MessageCircle, Calendar, GraduationCap, BookOpen, Users } from 'lucide-react';

import { CONFIG } from '../config/constants';

const Login = () => {
  const handleLogin = () => {
    const loginUrl = `${CONFIG.API_BASE_URL}/login`;
    console.log('🚀 Attempting redirect to backend login URL:', loginUrl);
    console.log('CONFIG.API_BASE_URL:', CONFIG.API_BASE_URL);
    console.log('Environment:', import.meta.env.MODE);
    console.log('VITE_API_URL:', import.meta.env.VITE_API_URL);
    
    // Force full page navigation by directly setting window.location
    console.log('🔄 Executing window.location redirect...');
    window.location.href = loginUrl;
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
    <>
      {/* Mobile Layout */}
      <div className="lg:hidden bg-gradient-to-br from-gray-50 via-white to-gray-100 min-h-screen">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-red-800/4 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-red-900/4 rounded-full blur-3xl"></div>
        </div>
        
        <div className="relative z-10 p-6 space-y-8">
          {/* Mobile Header - Compact */}
          <div className="text-center pt-8">
            <div className="flex items-center justify-center space-x-3 mb-6">
              <img
                src="https://upload.wikimedia.org/wikipedia/commons/4/49/Gannon_university_logo.png"
                alt="Gannon University Logo"
                className="w-10 h-10 shadow-lg"
              />
              <div>
                <h1 className="text-xl font-bold">
                  <span className="bg-gradient-to-r from-red-800 to-red-700 bg-clip-text text-transparent">
                    Advisor
                  </span>
                </h1>
                <p className="text-gray-600 text-sm">AI-Powered Academic Guidance</p>
              </div>
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
              Your Personal Academic Assistant
            </h2>
            <p className="text-gray-600 mb-6">
              Navigate your academic journey with confidence.
            </p>
            <div className="flex justify-center mb-8">
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm font-medium border border-red-100">Course Planning</span>
                <span className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm font-medium border border-red-100">24/7 Support</span>
                <span className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm font-medium border border-red-100">Degree Tracking</span>
              </div>
            </div>
          </div>

          {/* Mobile Login Section */}
          <div className="pb-12">
            <div className="bg-white/90 backdrop-blur-xl border border-gray-100/50 rounded-3xl shadow-2xl shadow-gray-200/20 p-6">
              {/* Login Header */}
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-gradient-to-br from-red-800 to-red-900 rounded-3xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-red-800/25 transform rotate-3">
                  <Users className="w-8 h-8 text-white transform -rotate-3" />
                </div>
                <h2 className="text-xl font-bold text-gray-800 mb-2">
                  Welcome
                </h2>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Sign in with your university Microsoft account
                </p>
              </div>

              {/* Login Button */}
              <button
                onClick={handleLogin}
                className="group w-full flex items-center justify-center py-4 px-6 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-lg font-semibold rounded-2xl shadow-xl shadow-blue-600/30 hover:shadow-blue-600/50 transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-blue-500/30 hover:scale-105 transform active:scale-95 mb-4"
              >
                <svg className="w-6 h-6 mr-3 group-hover:scale-110 transition-transform duration-200" viewBox="0 0 24 24" fill="none">
                  <rect fill="#F35325" x="1" y="1" width="10" height="10" />
                  <rect fill="#81BC06" x="13" y="1" width="10" height="10" />
                  <rect fill="#05A6F0" x="1" y="13" width="10" height="10" />
                  <rect fill="#FFBA08" x="13" y="13" width="10" height="10" />
                </svg>
                Continue with Microsoft
              </button>

              {/* Security Notice */}
              <div className="p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-2xl border border-green-100 mb-4">
                <div className="flex items-center space-x-2 text-green-800">
                  <div className="w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
                    <CheckCircle className="w-2.5 h-2.5 text-white" />
                  </div>
                  <span className="font-medium text-sm">Secure authentication powered by Microsoft</span>
                </div>
              </div>

              {/* Footer */}
              <div className="text-center space-y-2">
                <p className="text-xs text-gray-500">
                  By signing in, you agree to our terms of service and privacy policy
                </p>
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-1.5 h-1.5 bg-red-800 rounded-full"></div>
                  <p className="text-xs text-gray-400">
                    Powered by Gannon University • Academic Year 2024-2025
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Desktop Layout */}
      <div className="hidden lg:block bg-gradient-to-br from-gray-50 via-white to-gray-100 relative min-h-screen">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-red-800/4 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-red-900/4 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10 min-h-screen flex">
          {/* Left Section - Information */}
          <div className="flex-1 flex items-center justify-center p-12 bg-gradient-to-br from-white/60 to-white/20 backdrop-blur-sm">
            <div className="w-full max-w-xl">
            {/* Header */}
            <div className="flex items-center space-x-4 mb-8">
              <img
                src="https://upload.wikimedia.org/wikipedia/commons/4/49/Gannon_university_logo.png"
                alt="Gannon University Logo"
                className="w-12 h-12 shadow-lg"
              />
              <div>
                <h1 className="text-2xl lg:text-3xl font-bold">
                  <span className="bg-gradient-to-r from-red-800 to-red-700 bg-clip-text text-transparent">
                    Advisor
                  </span>
                </h1>
                <p className="text-gray-600 text-sm lg:text-base">AI-Powered Academic Guidance</p>
              </div>
            </div>

            {/* Main Description */}
            <div className="mb-8">
              <h2 className="text-3xl lg:text-4xl font-bold text-gray-800 mb-4 leading-tight">
                Your Personal Academic Assistant
              </h2>
              <p className="text-gray-600 text-lg lg:text-xl leading-relaxed mb-6">
                Navigate your academic journey with confidence. Get personalized guidance, 
                course planning, and degree tracking to succeed at every step.
              </p>
              
              {/* Benefits */}
              <div className="space-y-3">
                <div className="flex items-center space-x-3 text-gray-700">
                  <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <CheckCircle className="w-3 h-3 text-white" />
                  </div>
                  <span className="text-base lg:text-lg">Instant access to academic information</span>
                </div>
                <div className="flex items-center space-x-3 text-gray-700">
                  <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <CheckCircle className="w-3 h-3 text-white" />
                  </div>
                  <span className="text-base lg:text-lg">Personalized course recommendations</span>
                </div>
                <div className="flex items-center space-x-3 text-gray-700">
                  <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <CheckCircle className="w-3 h-3 text-white" />
                  </div>
                  <span className="text-base lg:text-lg">Track graduation requirements</span>
                </div>
              </div>
            </div>

            {/* Features Grid - Hidden on mobile to save space */}
            <div className="hidden lg:grid grid-cols-2 gap-3 lg:gap-4 mb-8">
              {features.map((feature, index) => (
                <div key={index} className="group p-4 bg-white/70 backdrop-blur-sm rounded-xl border border-gray-100/50 hover:bg-white/90 hover:shadow-lg transition-all duration-200">
                  <div className="text-center">
                    <div className="w-10 h-10 bg-gradient-to-br from-red-800 to-red-900 rounded-lg flex items-center justify-center text-white shadow-lg shadow-red-800/25 mx-auto mb-2 group-hover:scale-110 transition-transform duration-200">
                      {feature.icon}
                    </div>
                    <h3 className="font-semibold text-gray-800 mb-1 text-xs lg:text-sm">{feature.title}</h3>
                    <p className="text-xs text-gray-600">{feature.description}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Mobile-friendly feature list */}
            <div className="lg:hidden mb-6">
              <div className="flex flex-wrap gap-2 justify-center">
                <span className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm font-medium border border-red-100">Course Planning</span>
                <span className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm font-medium border border-red-100">24/7 Support</span>
                <span className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm font-medium border border-red-100">Degree Tracking</span>
              </div>
            </div>

            {/* Stats - Hidden on mobile to save space */}
            <div className="hidden lg:flex items-center justify-around bg-white/50 backdrop-blur-sm rounded-xl p-4 border border-gray-100/50">
              <div className="text-center">
                <div className="text-2xl lg:text-3xl font-bold text-gray-800">24/7</div>
                <div className="text-xs lg:text-sm text-gray-600">Available</div>
              </div>
              <div className="w-px h-8 bg-gray-300"></div>
              <div className="text-center">
                <div className="text-2xl lg:text-3xl font-bold text-gray-800">1000+</div>
                <div className="text-xs lg:text-sm text-gray-600">Students</div>
              </div>
              <div className="w-px h-8 bg-gray-300"></div>
              <div className="text-center">
                <div className="text-2xl lg:text-3xl font-bold text-gray-800">100%</div>
                <div className="text-xs lg:text-sm text-gray-600">Secure</div>
              </div>
            </div>
          </div>
        </div>

          {/* Right Section - Login */}
          <div className="flex-1 flex items-center justify-center p-12">
            <div className="w-full max-w-md">
              <div className="bg-white/90 backdrop-blur-xl border border-gray-100/50 rounded-3xl shadow-2xl shadow-gray-200/20 p-10">
                {/* Login Header */}
                <div className="text-center mb-8">
                  <div className="w-20 h-20 bg-gradient-to-br from-red-800 to-red-900 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-red-800/25 transform rotate-3">
                    <Users className="w-10 h-10 text-white transform -rotate-3" />
                  </div>
                  <h2 className="text-3xl font-bold text-gray-800 mb-3">
                    Welcome
                  </h2>
                  <p className="text-gray-600 text-lg leading-relaxed">
                    Sign in with your university Microsoft account to access your personalized academic advisor
                  </p>
                </div>

                {/* Login Button */}
                <button
                  onClick={handleLogin}
                  className="group w-full flex items-center justify-center py-5 px-8 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white text-xl font-semibold rounded-2xl shadow-xl shadow-blue-600/30 hover:shadow-blue-600/50 transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-blue-500/30 hover:scale-105 transform active:scale-95"
                >
                  <svg className="w-7 h-7 mr-4 group-hover:scale-110 transition-transform duration-200" viewBox="0 0 24 24" fill="none">
                    <rect fill="#F35325" x="1" y="1" width="10" height="10" />
                    <rect fill="#81BC06" x="13" y="1" width="10" height="10" />
                    <rect fill="#05A6F0" x="1" y="13" width="10" height="10" />
                    <rect fill="#FFBA08" x="13" y="13" width="10" height="10" />
                  </svg>
                  Continue with Microsoft
                </button>

                {/* Security Notice */}
                <div className="mt-8 p-5 bg-gradient-to-r from-green-50 to-emerald-50 rounded-2xl border border-green-100">
                  <div className="flex items-center space-x-3 text-green-800">
                    <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                      <CheckCircle className="w-4 h-4 text-white" />
                    </div>
                    <span className="font-medium text-base">Secure authentication powered by Microsoft</span>
                  </div>
                </div>

                {/* Footer */}
                <div className="mt-10 text-center space-y-3">
                  <p className="text-sm text-gray-500">
                    By signing in, you agree to our terms of service and privacy policy
                  </p>
                  <div className="flex items-center justify-center space-x-2">
                    <div className="w-2 h-2 bg-red-800 rounded-full"></div>
                    <p className="text-xs text-gray-400">
                      Powered by Gannon University • Academic Year 2024-2025
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Login;
