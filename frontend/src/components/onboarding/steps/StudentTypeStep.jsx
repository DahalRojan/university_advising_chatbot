/**
 * StudentTypeStep Component
 * 
 * Allows users to select whether they are a current Gannon student or prospective student.
 * This determines which onboarding flow they will follow.
 */

import React, { useState, useEffect } from 'react';
import { GraduationCap, Users, School, Target, AlertCircle } from 'lucide-react';
import LoadingSpinner from '../../ui/LoadingSpinner';

const StudentTypeStep = ({ studentData, onUpdateData, onSaveProgress }) => {
  const [selectedType, setSelectedType] = useState(studentData?.student_type || '');
  const [errors, setErrors] = useState({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    // Auto-save when student type is selected
    if (selectedType) {
      handleAutoSave();
    }
  }, [selectedType]);

  const handleAutoSave = async () => {
    try {
      setIsSaving(true);
      const formData = { student_type: selectedType };
      await onSaveProgress(formData);
      onUpdateData(formData);
    } catch (error) {
      console.error('Failed to auto-save:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleTypeSelection = (type) => {
    setSelectedType(type);
    
    // Clear any existing errors
    if (errors.student_type) {
      setErrors(prev => ({
        ...prev,
        student_type: null
      }));
    }
  };

  const validateSelection = () => {
    const newErrors = {};

    if (!selectedType) {
      newErrors.student_type = 'Please select your student status to continue';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const studentTypes = [
    {
      id: 'current_gannon',
      title: 'Current Gannon Student',
      description: 'I am currently enrolled at Gannon University',
      details: [
        'Access to course history and transcript',
        'Personalized degree planning',
        'Course recommendations based on completed coursework',
        'Academic progress tracking'
      ],
      icon: School,
      gradient: 'from-red-800 to-red-700'
    },
    {
      id: 'prospective',
      title: 'Prospective Student',
      description: 'I am interested in attending Gannon University',
      details: [
        'Explore academic programs and majors',
        'Discover courses in your areas of interest',
        'Learn about admission requirements',
        'Get guidance on program selection'
      ],
      icon: Target,
      gradient: 'from-red-800 to-red-700'
    }
  ];

  return (
    <div className="max-w-4xl mx-auto">
      <div className="space-y-8">
        {/* Welcome Message */}
        <div className="text-center bg-gradient-to-r from-red-800 to-red-900 text-white rounded-lg p-6">
          <div className="flex items-center justify-center mb-4">
            <GraduationCap className="w-8 h-8 mr-3" />
            <h2 className="text-2xl font-bold">Welcome to Gannon University Advisor!</h2>
          </div>
          <p className="text-red-100 text-lg">
            Let's personalize your experience based on your current status with Gannon University.
          </p>
        </div>

        {/* Student Type Selection */}
        <div>
          <div className="flex items-center space-x-2 mb-6">
            <Users className="w-6 h-6 text-red-800" />
            <h3 className="text-xl font-semibold text-gray-900">What describes you best?</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {studentTypes.map((type) => {
              const IconComponent = type.icon;
              const isSelected = selectedType === type.id;
              
              return (
                <div
                  key={type.id}
                  className={`relative p-6 border-2 rounded-xl cursor-pointer transition-all duration-300 transform hover:scale-105 ${
                    isSelected
                      ? 'border-red-800 bg-red-50 shadow-lg ring-4 ring-red-800 ring-opacity-20'
                      : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'
                  }`}
                  onClick={() => handleTypeSelection(type.id)}
                >
                  {/* Selection indicator */}
                  {isSelected && (
                    <div className="absolute top-4 right-4 w-6 h-6 bg-red-800 rounded-full flex items-center justify-center">
                      <div className="w-3 h-3 bg-white rounded-full"></div>
                    </div>
                  )}
                  
                  <div className="space-y-4">
                    {/* Header */}
                    <div className="flex items-center space-x-3">
                      <div className={`p-3 rounded-lg bg-gradient-to-r ${type.gradient}`}>
                        <IconComponent className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h4 className="text-lg font-semibold text-gray-900">{type.title}</h4>
                        <p className="text-sm text-gray-600">{type.description}</p>
                      </div>
                    </div>
                    
                    {/* Benefits */}
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-gray-700 mb-2">What you'll get:</p>
                      <ul className="space-y-1">
                        {type.details.map((detail, index) => (
                          <li key={index} className="flex items-start space-x-2 text-sm text-gray-600">
                            <div className="w-1.5 h-1.5 bg-red-800 rounded-full mt-2 flex-shrink-0"></div>
                            <span>{detail}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          
          {errors.student_type && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm flex items-center space-x-2">
                <AlertCircle className="w-4 h-4" />
                <span>{errors.student_type}</span>
              </p>
            </div>
          )}
        </div>

        {/* Auto-save indicator */}
        {isSaving && (
          <div className="flex items-center justify-center py-2">
            <LoadingSpinner size="sm" text="Saving your selection..." />
          </div>
        )}

        {/* Next Steps Preview */}
        {selectedType && (
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-6 border border-gray-200">
            <h4 className="text-lg font-semibold text-gray-900 mb-3">Next Steps</h4>
            <div className="text-sm text-gray-700">
              {selectedType === 'current_gannon' ? (
                <div className="space-y-2">
                  <p className="font-medium">As a current Gannon student, we'll help you:</p>
                  <ul className="list-disc list-inside space-y-1 ml-4">
                    <li>Review your academic progress and completed courses</li>
                    <li>Identify courses you're currently enrolled in</li>
                    <li>Set academic and career goals</li>
                    <li>Discover additional courses that align with your interests</li>
                  </ul>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="font-medium">As a prospective student, we'll help you:</p>
                  <ul className="list-disc list-inside space-y-1 ml-4">
                    <li>Explore academic fields and potential majors</li>
                    <li>Discover programs that match your interests</li>
                    <li>Learn about course offerings and requirements</li>
                    <li>Plan your educational journey at Gannon</li>
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentTypeStep;