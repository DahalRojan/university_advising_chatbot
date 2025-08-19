/**
 * CompletionStep Component
 * 
 * Final step that congratulates the student and shows next steps.
 */

import React from 'react';
import { CheckCircle, Star, ArrowRight, MessageCircle } from 'lucide-react';

const CompletionStep = ({ studentData, onUpdateData, onSaveProgress }) => {
  return (
    <div className="max-w-2xl mx-auto text-center">
      <div className="space-y-8">
        {/* Success Icon */}
        <div className="flex justify-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
            <CheckCircle className="w-12 h-12 text-green-600" />
          </div>
        </div>

        {/* Congratulations */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Congratulations! 🎉
          </h2>
          <p className="text-lg text-gray-600 mb-6">
            You've successfully completed your onboarding. We're excited to help you 
            on your academic journey at Gannon University!
          </p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 my-8">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-600 mb-1">
              {(studentData.completed_courses?.length || 0) + (studentData.enrolled_courses?.length || 0)}
            </div>
            <div className="text-sm text-blue-700">Courses Added</div>
          </div>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-600 mb-1">
              {(studentData.academic_interests?.length || 0) + 
               (studentData.career_goals?.length || 0) + 
               (studentData.other_interests?.length || 0)}
            </div>
            <div className="text-sm text-green-700">Interests & Goals</div>
          </div>
          
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-red-600 mb-1">
              {studentData.completed_courses?.length || 0}
            </div>
            <div className="text-sm text-red-700">Completed Courses</div>
          </div>
          
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-purple-600 mb-1">100%</div>
            <div className="text-sm text-purple-700">Profile Complete</div>
          </div>
        </div>

        {/* Next Steps */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-left">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
            What's Next?
          </h3>
          
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 bg-red-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">1</span>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Start Chatting</h4>
                <p className="text-sm text-gray-600">
                  Ask questions about courses, requirements, or academic planning
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 bg-red-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">2</span>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Explore Recommendations</h4>
                <p className="text-sm text-gray-600">
                  Get personalized course and academic pathway suggestions
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 bg-red-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">3</span>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Plan Your Schedule</h4>
                <p className="text-sm text-gray-600">
                  Use our guidance to plan your semester and degree progression
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Tips */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <Star className="w-5 h-5 text-blue-600 mt-0.5" />
            </div>
            <div className="text-left">
              <h4 className="text-sm font-medium text-blue-900 mb-1">
                Pro Tips for Success
              </h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Ask specific questions for more detailed responses</li>
                <li>• Mention course codes (like "GCIS 655") for targeted advice</li>
                <li>• Update your profile as your goals and interests evolve</li>
                <li>• Use the chat history to track your academic planning journey</li>
              </ul>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="bg-gradient-to-r from-red-600 to-red-700 rounded-lg p-6 text-white">
          <h3 className="text-lg font-semibold mb-2">Ready to Start?</h3>
          <p className="mb-4">
            Your personalized academic advisor is ready to help you succeed.
          </p>
          <div className="flex items-center justify-center space-x-2 text-red-100">
            <MessageCircle className="w-5 h-5" />
            <span className="font-medium">Try asking: "What courses should I take next semester?"</span>
            <ArrowRight className="w-4 h-4" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompletionStep;