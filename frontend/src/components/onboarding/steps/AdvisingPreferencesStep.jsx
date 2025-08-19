/**
 * AdvisingPreferencesStep Component
 * 
 * Allows students to set preferences for how they want to receive academic advising.
 */

import React, { useState } from 'react';
import { Settings, Bell, MessageCircle } from 'lucide-react';

const AdvisingPreferencesStep = ({ studentData, onUpdateData, onSaveProgress }) => {
  const [preferences, setPreferences] = useState({
    communication_style: 'balanced',
    reminder_frequency: 'weekly',
    focus_areas: [],
    ...studentData.advising_preferences
  });

  const handlePreferenceChange = async (key, value) => {
    const updated = { ...preferences, [key]: value };
    setPreferences(updated);
    const updatedData = { ...studentData, advising_preferences: updated };
    onUpdateData(updatedData);
    await onSaveProgress(updatedData);
  };

  const handleFocusAreaToggle = async (area) => {
    const currentAreas = preferences.focus_areas || [];
    const updated = currentAreas.includes(area)
      ? currentAreas.filter(a => a !== area)
      : [...currentAreas, area];
    
    handlePreferenceChange('focus_areas', updated);
  };

  const focusAreas = [
    'Course Planning',
    'Career Guidance',
    'Academic Performance',
    'Study Strategies',
    'Time Management',
    'Graduate School Prep'
  ];

  return (
    <div className="max-w-2xl mx-auto">
      <div className="space-y-8">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Advising Preferences</h3>
          <p className="text-gray-600">
            Customize how you'd like to receive academic guidance and support.
          </p>
        </div>

        {/* Communication Style */}
        <div>
          <div className="flex items-center space-x-2 mb-4">
            <MessageCircle className="w-5 h-5 text-red-600" />
            <h4 className="font-medium text-gray-900">Communication Style</h4>
          </div>
          
          <div className="space-y-3">
            {[
              { value: 'detailed', label: 'Detailed', description: 'Comprehensive explanations and context' },
              { value: 'balanced', label: 'Balanced', description: 'Clear information with key details' },
              { value: 'concise', label: 'Concise', description: 'Brief, direct responses' }
            ].map(style => (
              <div
                key={style.value}
                className={`p-3 border rounded-lg cursor-pointer transition-all ${
                  preferences.communication_style === style.value
                    ? 'border-red-500 bg-red-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handlePreferenceChange('communication_style', style.value)}
              >
                <div className="font-medium text-gray-900">{style.label}</div>
                <div className="text-sm text-gray-600">{style.description}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Focus Areas */}
        <div>
          <div className="flex items-center space-x-2 mb-4">
            <Settings className="w-5 h-5 text-red-600" />
            <h4 className="font-medium text-gray-900">Areas of Focus</h4>
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            {focusAreas.map(area => (
              <div
                key={area}
                className={`p-3 border rounded-lg cursor-pointer transition-all ${
                  preferences.focus_areas?.includes(area)
                    ? 'border-red-500 bg-red-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleFocusAreaToggle(area)}
              >
                <div className="text-sm font-medium text-gray-900">{area}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <Bell className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-blue-900 mb-1">
                Personalized Experience
              </h4>
              <p className="text-sm text-blue-700">
                These preferences help us tailor our guidance to your learning style and needs. 
                You can update them anytime in your profile settings.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvisingPreferencesStep;