/**
 * PersonalInfoStep Component
 * 
 * Collects essential academic information from the student during onboarding.
 * Basic personal info is obtained from Microsoft login.
 */

import React, { useState, useEffect } from 'react';
import { GraduationCap, Calendar, User, AlertCircle, Target } from 'lucide-react';
import LoadingSpinner from '../../ui/LoadingSpinner';

const PersonalInfoStep = ({ studentData, onUpdateData, onSaveProgress }) => {
  const [formData, setFormData] = useState({
    academic_level: '',
    enrollment_status: '',
    student_id: '',
    expected_graduation: '',
    primary_major: '',
    ...studentData
  });

  const [errors, setErrors] = useState({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    // Auto-save when form data changes (debounced)
    const timer = setTimeout(() => {
      if (validateForm()) {
        handleAutoSave();
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [formData]);

  const handleAutoSave = async () => {
    try {
      setIsSaving(true);
      await onSaveProgress(formData);
      onUpdateData(formData);
    } catch (error) {
      console.error('Failed to auto-save:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: null
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.academic_level?.trim()) {
      newErrors.academic_level = 'Academic level is required for personalized guidance';
    }

    if (!formData.enrollment_status?.trim()) {
      newErrors.enrollment_status = 'Enrollment status helps us provide relevant advice';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Get current year for graduation date suggestions
  const currentYear = new Date().getFullYear();
  const graduationYears = Array.from({length: 8}, (_, i) => currentYear + i);

  return (
    <div className="max-w-2xl mx-auto">
      <div className="space-y-8">
        {/* Welcome Message */}
        <div className="text-center bg-gradient-to-r from-red-800 to-red-900 text-white rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-2">
            {formData.student_type === 'current_gannon' 
              ? 'Tell Us About Your Academic Status' 
              : 'Let\'s Plan Your Academic Journey!'}
          </h2>
          <p className="text-red-100">
            {formData.student_type === 'current_gannon'
              ? 'Help us understand your current academic standing so we can provide better guidance.'
              : 'Share your academic goals so we can recommend the best programs for you.'}
          </p>
        </div>

        {/* Academic Level */}
        <div>
          <div className="flex items-center space-x-2 mb-4">
            <GraduationCap className="w-5 h-5 text-red-800" />
            <h3 className="text-lg font-semibold text-gray-900">Academic Information</h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                What is your academic level? *
              </label>
              <div className="space-y-2">
                {[
                  { value: 'undergraduate', label: 'Undergraduate', description: 'Working towards a Bachelor\'s degree' },
                  { value: 'graduate', label: 'Graduate', description: 'Working towards a Master\'s degree' },
                  { value: 'doctoral', label: 'Doctoral', description: 'Working towards a PhD or professional doctorate' }
                ].map(level => (
                  <div
                    key={level.value}
                    className={`p-3 border rounded-lg cursor-pointer transition-all ${
                      formData.academic_level === level.value
                        ? 'border-red-800 bg-red-50 ring-2 ring-red-800'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleInputChange('academic_level', level.value)}
                  >
                    <div className="font-medium text-gray-900">{level.label}</div>
                    <div className="text-sm text-gray-600">{level.description}</div>
                  </div>
                ))}
              </div>
              {errors.academic_level && (
                <p className="text-red-600 text-sm mt-2 flex items-center space-x-1">
                  <AlertCircle className="w-4 h-4" />
                  <span>{errors.academic_level}</span>
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                What is your enrollment status? *
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[
                  { value: 'full-time', label: 'Full-Time Student', description: '12+ credits per semester' },
                  { value: 'part-time', label: 'Part-Time Student', description: 'Less than 12 credits per semester' }
                ].map(status => (
                  <div
                    key={status.value}
                    className={`p-3 border rounded-lg cursor-pointer transition-all ${
                      formData.enrollment_status === status.value
                        ? 'border-red-800 bg-red-50 ring-2 ring-red-800'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleInputChange('enrollment_status', status.value)}
                  >
                    <div className="font-medium text-gray-900">{status.label}</div>
                    <div className="text-sm text-gray-600">{status.description}</div>
                  </div>
                ))}
              </div>
              {errors.enrollment_status && (
                <p className="text-red-600 text-sm mt-2 flex items-center space-x-1">
                  <AlertCircle className="w-4 h-4" />
                  <span>{errors.enrollment_status}</span>
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Essential Academic Information */}
        {formData.student_type === 'current_gannon' && (
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Calendar className="w-5 h-5 text-red-800" />
              <h3 className="text-lg font-semibold text-gray-900">Academic Details</h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Expected Graduation Year
                </label>
                <select
                  value={formData.expected_graduation}
                  onChange={(e) => handleInputChange('expected_graduation', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-800 focus:border-transparent"
                >
                  <option value="">Select graduation year</option>
                  {graduationYears.map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Current Major
                </label>
                <input
                  type="text"
                  value={formData.primary_major}
                  onChange={(e) => handleInputChange('primary_major', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-800 focus:border-transparent"
                  placeholder="e.g., Computer Science, Business Administration"
                />
              </div>
            </div>
          </div>
        )}

        {/* Prospective Student Information */}
        {formData.student_type === 'prospective' && (
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Calendar className="w-5 h-5 text-red-800" />
              <h3 className="text-lg font-semibold text-gray-900">Academic Interests</h3>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Intended Major or Area of Interest
              </label>
              <input
                type="text"
                value={formData.primary_major}
                onChange={(e) => handleInputChange('primary_major', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-800 focus:border-transparent"
                placeholder="e.g., Computer Science, Business, Undecided"
              />
              <p className="text-gray-500 text-xs mt-1">
                Don't worry if you're undecided - we'll help you explore your options!
              </p>
            </div>
          </div>
        )}

        {/* Auto-save indicator */}
        {isSaving && (
          <div className="flex items-center justify-center py-2">
            <LoadingSpinner size="sm" text="Saving..." />
          </div>
        )}

        {/* Progress Info */}
        <div className="bg-gradient-to-r from-red-50 to-red-100 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <Target className="w-5 h-5 text-red-800 mt-0.5" />
            </div>
            <div>
              <h4 className="text-sm font-medium text-red-900 mb-1">
                {formData.student_type === 'current_gannon' 
                  ? 'Personalized Academic Support' 
                  : 'Discover Your Perfect Program'}
              </h4>
              <p className="text-sm text-red-700">
                {formData.student_type === 'current_gannon'
                  ? 'We\'ll use this information to provide tailored course recommendations and degree planning based on your current progress.'
                  : 'Based on your interests, we\'ll recommend programs and courses that align with your career goals at Gannon University.'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PersonalInfoStep;