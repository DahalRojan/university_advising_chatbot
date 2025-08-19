/**
 * AcademicGoalsStep Component
 * 
 * Allows students to input their academic interests, career goals, and other interests.
 */

import React, { useState, useEffect } from 'react';
import { Target, Plus, X, BookOpen, Briefcase, Heart } from 'lucide-react';
import LoadingSpinner from '../../ui/LoadingSpinner';
import onboardingApi from '../../../services/onboardingApi';

const AcademicGoalsStep = ({ studentData, onUpdateData, onSaveProgress }) => {
  const [formData, setFormData] = useState({
    academic_interests: studentData?.academic_interests || [],
    career_goals: studentData?.career_goals || [],
    other_interests: studentData?.other_interests || []
  });
  const [isSaving, setIsSaving] = useState(false);

  // Auto-save when form data changes
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

  const addEntry = (category, value) => {
    if (value.trim()) {
      setFormData(prev => ({
        ...prev,
        [category]: [...prev[category], value.trim()]
      }));
    }
  };

  const removeEntry = (category, index) => {
    setFormData(prev => ({
      ...prev,
      [category]: prev[category].filter((_, i) => i !== index)
    }));
  };

  const InterestSection = ({ title, icon: Icon, category, placeholder, color }) => {
    const [newEntry, setNewEntry] = useState('');

    const handleAdd = () => {
      addEntry(category, newEntry);
      setNewEntry('');
    };

    const handleKeyPress = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleAdd();
      }
    };

    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${color.bg}`}>
            <Icon className={`w-5 h-5 ${color.text}`} />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>

        {/* Add new entry */}
        <div className="flex space-x-2">
          <input
            type="text"
            value={newEntry}
            onChange={(e) => setNewEntry(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
          />
          <button
            onClick={handleAdd}
            disabled={!newEntry.trim()}
            className={`px-4 py-2 ${color.button} text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1`}
          >
            <Plus className="w-4 h-4" />
            <span>Add</span>
          </button>
        </div>

        {/* Existing entries */}
        <div className="space-y-2">
          {formData[category].map((item, index) => (
            <div key={index} className={`flex items-center justify-between p-3 ${color.bg} border ${color.border} rounded-lg`}>
              <span className="text-gray-900">{item}</span>
              <button
                onClick={() => removeEntry(category, index)}
                className="p-1 text-red-600 hover:text-red-800 transition-colors"
                title="Remove"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
          {formData[category].length === 0 && (
            <div className="text-center py-4 text-gray-500">
              No {title.toLowerCase()} added yet
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex items-center justify-center mb-4">
            <Target className="w-8 h-8 text-red-800 mr-3" />
            <h2 className="text-2xl font-bold text-gray-900">Your Interests & Goals</h2>
          </div>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Tell us about your academic interests, career aspirations, and other passions. 
            This helps us provide personalized recommendations and guidance.
          </p>
        </div>

        {/* Academic Interests Section */}
        <InterestSection
          title="Academic Interests"
          icon={BookOpen}
          category="academic_interests"
          placeholder="e.g., Data Science, Machine Learning, Web Development"
          color={{
            bg: 'bg-blue-50',
            text: 'text-blue-600',
            button: 'bg-blue-600',
            border: 'border-blue-200'
          }}
        />

        {/* Career Goals Section */}
        <InterestSection
          title="Future Career Goals"
          icon={Briefcase}
          category="career_goals"
          placeholder="e.g., Software Engineer, Data Analyst, Product Manager"
          color={{
            bg: 'bg-green-50',
            text: 'text-green-600',
            button: 'bg-green-600',
            border: 'border-green-200'
          }}
        />

        {/* Other Interests Section */}
        <InterestSection
          title="Other Interests"
          icon={Heart}
          category="other_interests"
          placeholder="e.g., Music, Sports, Volunteering, Travel"
          color={{
            bg: 'bg-purple-50',
            text: 'text-purple-600',
            button: 'bg-purple-600',
            border: 'border-purple-200'
          }}
        />

        {/* Auto-save indicator */}
        {isSaving && (
          <div className="flex items-center justify-center py-2">
            <LoadingSpinner size="sm" text="Saving your interests..." />
          </div>
        )}

        {/* Summary */}
        {(formData.academic_interests.length > 0 || formData.career_goals.length > 0 || formData.other_interests.length > 0) && (
          <div className="bg-gray-50 rounded-lg p-6">
            <h4 className="font-semibold text-gray-900 mb-3">Summary</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-blue-600">{formData.academic_interests.length}</div>
                <div className="text-sm text-gray-600">Academic Interests</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{formData.career_goals.length}</div>
                <div className="text-sm text-gray-600">Career Goals</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-purple-600">{formData.other_interests.length}</div>
                <div className="text-sm text-gray-600">Other Interests</div>
              </div>
            </div>
          </div>
        )}

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <Target className="w-5 h-5 text-blue-600 mt-0.5" />
            </div>
            <div>
              <h4 className="text-sm font-medium text-blue-900 mb-1">
                Why This Matters
              </h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Helps us recommend relevant courses and programs</li>
                <li>• Guides personalized academic and career advice</li>
                <li>• Connects you with similar-minded students and opportunities</li>
                <li>• You can always update these as your interests evolve</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AcademicGoalsStep;