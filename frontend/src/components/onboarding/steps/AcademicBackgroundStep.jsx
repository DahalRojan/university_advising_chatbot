/**
 * AcademicBackgroundStep Component
 * 
 * Collects information about the student's academic background and history.
 */

import React, { useState, useEffect } from 'react';
import { GraduationCap, Calendar, Award } from 'lucide-react';
import LoadingSpinner from '../../ui/LoadingSpinner';

const AcademicBackgroundStep = ({ studentData, onUpdateData, onSaveProgress }) => {
  const [formData, setFormData] = useState({
    academic_level: '',
    enrollment_status: '',
    expected_graduation: '',
    primary_major: '',
    secondary_major: '',
    minor_program: '',
    concentration: '',
    cumulative_gpa: '',
    ...studentData
  });

  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      handleAutoSave();
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
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="space-y-8">
        {/* Academic Level */}
        <div>
          <div className="flex items-center space-x-2 mb-4">
            <GraduationCap className="w-5 h-5 text-red-600" />
            <h3 className="text-lg font-semibold text-gray-900">Academic Information</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Academic Level
              </label>
              <select
                value={formData.academic_level}
                onChange={(e) => handleInputChange('academic_level', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              >
                <option value="">Select level</option>
                <option value="undergraduate">Undergraduate</option>
                <option value="graduate">Graduate</option>
                <option value="doctoral">Doctoral</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Enrollment Status
              </label>
              <select
                value={formData.enrollment_status}
                onChange={(e) => handleInputChange('enrollment_status', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              >
                <option value="">Select status</option>
                <option value="full-time">Full-time</option>
                <option value="part-time">Part-time</option>
                <option value="not-enrolled">Not Enrolled</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expected Graduation
              </label>
              <input
                type="date"
                value={formData.expected_graduation}
                onChange={(e) => handleInputChange('expected_graduation', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Current GPA <span className="text-gray-500">(optional)</span>
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="4.0"
                value={formData.cumulative_gpa}
                onChange={(e) => handleInputChange('cumulative_gpa', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder="3.5"
              />
            </div>
          </div>
        </div>

        {/* Program Information */}
        <div>
          <div className="flex items-center space-x-2 mb-4">
            <Award className="w-5 h-5 text-red-600" />
            <h3 className="text-lg font-semibold text-gray-900">Program Information</h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Primary Major
              </label>
              <input
                type="text"
                value={formData.primary_major}
                onChange={(e) => handleInputChange('primary_major', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder="e.g., Computer Science, Business Administration"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Secondary Major <span className="text-gray-500">(optional)</span>
              </label>
              <input
                type="text"
                value={formData.secondary_major}
                onChange={(e) => handleInputChange('secondary_major', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder="Double major or second degree"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Minor <span className="text-gray-500">(optional)</span>
                </label>
                <input
                  type="text"
                  value={formData.minor_program}
                  onChange={(e) => handleInputChange('minor_program', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  placeholder="e.g., Mathematics, Psychology"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Concentration <span className="text-gray-500">(optional)</span>
                </label>
                <input
                  type="text"
                  value={formData.concentration}
                  onChange={(e) => handleInputChange('concentration', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  placeholder="Area of specialization"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Auto-save indicator */}
        {isSaving && (
          <div className="flex items-center justify-center py-2">
            <LoadingSpinner size="sm" text="Saving..." />
          </div>
        )}

        {/* Info box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <Calendar className="w-5 h-5 text-blue-600 mt-0.5" />
            </div>
            <div>
              <h4 className="text-sm font-medium text-blue-900 mb-1">
                Academic Planning
              </h4>
              <p className="text-sm text-blue-700">
                This information helps us provide personalized course recommendations and 
                academic planning advice tailored to your program requirements.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AcademicBackgroundStep;