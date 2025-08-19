/**
 * FieldInterestsStep Component
 * 
 * Allows prospective students to explore and select academic fields and potential majors.
 * This helps provide personalized program recommendations and course exploration.
 */

import React, { useState, useEffect } from 'react';
import { Lightbulb, Star, Search, BookOpen, Target, Users, Briefcase, Heart } from 'lucide-react';
import LoadingSpinner from '../../ui/LoadingSpinner';

const FieldInterestsStep = ({ studentData, onUpdateData, onSaveProgress }) => {
  const [selectedFields, setSelectedFields] = useState(studentData?.field_interests || []);
  const [careerInterests, setCareerInterests] = useState(studentData?.career_interests || []);
  const [searchTerm, setSearchTerm] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Auto-save when selections change
  useEffect(() => {
    const timer = setTimeout(() => {
      if (selectedFields.length > 0 || careerInterests.length > 0) {
        handleAutoSave();
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [selectedFields, careerInterests]);

  const handleAutoSave = async () => {
    try {
      setIsSaving(true);
      const formData = {
        field_interests: selectedFields,
        career_interests: careerInterests
      };
      await onSaveProgress(formData);
      onUpdateData(formData);
    } catch (error) {
      console.error('Failed to auto-save:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const academicFields = [
    {
      id: 'business',
      name: 'Business & Management',
      description: 'Leadership, entrepreneurship, finance, marketing',
      icon: Briefcase,
      color: 'bg-blue-600',
      programs: ['Business Administration', 'Marketing', 'Finance', 'Management', 'Accounting']
    },
    {
      id: 'engineering',
      name: 'Engineering & Technology',
      description: 'Problem-solving, innovation, technical design',
      icon: Target,
      color: 'bg-green-600',
      programs: ['Computer Engineering', 'Mechanical Engineering', 'Electrical Engineering', 'Software Engineering']
    },
    {
      id: 'health',
      name: 'Health & Medical Sciences',
      description: 'Healthcare, medicine, nursing, therapy',
      icon: Heart,
      color: 'bg-red-600',
      programs: ['Nursing', 'Physical Therapy', 'Occupational Therapy', 'Health Sciences', 'Pre-Med']
    },
    {
      id: 'science',
      name: 'Natural Sciences',
      description: 'Research, discovery, laboratory work, analysis',
      icon: Search,
      color: 'bg-purple-600',
      programs: ['Biology', 'Chemistry', 'Physics', 'Environmental Science', 'Mathematics']
    },
    {
      id: 'liberal_arts',
      name: 'Liberal Arts & Humanities',
      description: 'Communication, critical thinking, cultural studies',
      icon: BookOpen,
      color: 'bg-orange-600',
      programs: ['English', 'History', 'Philosophy', 'Communications', 'Foreign Languages']
    },
    {
      id: 'social_sciences',
      name: 'Social Sciences',
      description: 'Human behavior, society, psychology, education',
      icon: Users,
      color: 'bg-indigo-600',
      programs: ['Psychology', 'Social Work', 'Education', 'Criminal Justice', 'Political Science']
    },
    {
      id: 'arts',
      name: 'Creative Arts & Design',
      description: 'Creativity, visual arts, performance, media',
      icon: Star,
      color: 'bg-pink-600',
      programs: ['Graphic Design', 'Theatre', 'Music', 'Digital Media', 'Fine Arts']
    },
    {
      id: 'computer_science',
      name: 'Computer Science & IT',
      description: 'Programming, software development, cybersecurity',
      icon: Lightbulb,
      color: 'bg-teal-600',
      programs: ['Computer Science', 'Information Systems', 'Cybersecurity', 'Data Science', 'Web Development']
    }
  ];

  const careerAreas = [
    'Healthcare & Medicine',
    'Technology & Engineering', 
    'Business & Finance',
    'Education & Training',
    'Research & Science',
    'Creative & Media',
    'Social Services',
    'Entrepreneurship'
  ];

  const toggleFieldSelection = (fieldId) => {
    setSelectedFields(prev => {
      if (prev.includes(fieldId)) {
        return prev.filter(id => id !== fieldId);
      } else {
        return [...prev, fieldId];
      }
    });
  };

  const toggleCareerInterest = (career) => {
    setCareerInterests(prev => {
      if (prev.includes(career)) {
        return prev.filter(c => c !== career);
      } else {
        return [...prev, career];
      }
    });
  };

  const filteredFields = academicFields.filter(field =>
    field.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    field.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    field.programs.some(program => program.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="max-w-5xl mx-auto">
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex items-center justify-center mb-4">
            <Lightbulb className="w-8 h-8 text-red-800 mr-3" />
            <h2 className="text-2xl font-bold text-gray-900">What Interests You?</h2>
          </div>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Select the academic areas that interest you most. We'll use this to recommend the perfect programs at Gannon University.
          </p>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search academic fields or programs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-800 focus:border-transparent"
          />
        </div>

        {/* Academic Fields */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Academic Fields 
            {selectedFields.length > 0 && (
              <span className="text-sm font-normal text-red-600 ml-2">
                ({selectedFields.length} selected)
              </span>
            )}
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Select 1-3 fields that interest you most. You can always change these later.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredFields.map(field => {
              const IconComponent = field.icon;
              const isSelected = selectedFields.includes(field.id);
              
              return (
                <div
                  key={field.id}
                  className={`p-6 border-2 rounded-xl cursor-pointer transition-all duration-300 transform hover:scale-105 ${
                    isSelected
                      ? 'border-red-800 bg-red-50 shadow-lg'
                      : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'
                  }`}
                  onClick={() => toggleFieldSelection(field.id)}
                >
                  <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${field.color}`}>
                        <IconComponent className="w-5 h-5 text-white" />
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900">{field.name}</h4>
                        {isSelected && (
                          <div className="w-4 h-4 bg-red-800 rounded-full mt-1"></div>
                        )}
                      </div>
                    </div>
                    
                    <p className="text-sm text-gray-600">{field.description}</p>
                    
                    <div className="space-y-1">
                      <p className="text-xs font-medium text-gray-700">Sample Programs:</p>
                      <div className="flex flex-wrap gap-1">
                        {field.programs.slice(0, 3).map(program => (
                          <span key={program} className="px-2 py-1 bg-gray-100 text-xs text-gray-600 rounded">
                            {program}
                          </span>
                        ))}
                        {field.programs.length > 3 && (
                          <span className="px-2 py-1 bg-gray-100 text-xs text-gray-600 rounded">
                            +{field.programs.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Career Interests */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Career Goals 
            {careerInterests.length > 0 && (
              <span className="text-sm font-normal text-red-600 ml-2">
                ({careerInterests.length} selected)
              </span>
            )}
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            What type of career do you see yourself in? Select any that appeal to you.
          </p>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {careerAreas.map(career => {
              const isSelected = careerInterests.includes(career);
              
              return (
                <button
                  key={career}
                  onClick={() => toggleCareerInterest(career)}
                  className={`p-3 text-sm border-2 rounded-lg text-left transition-all duration-200 ${
                    isSelected
                      ? 'border-red-800 bg-red-50 text-red-800 font-medium'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {career}
                </button>
              );
            })}
          </div>
        </div>

        {/* Auto-save indicator */}
        {isSaving && (
          <div className="flex items-center justify-center py-2">
            <LoadingSpinner size="sm" text="Saving your interests..." />
          </div>
        )}

        {/* Summary */}
        {(selectedFields.length > 0 || careerInterests.length > 0) && (
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-6 border border-gray-200">
            <h4 className="text-lg font-semibold text-gray-900 mb-4">Your Interest Profile</h4>
            
            <div className="space-y-4">
              {selectedFields.length > 0 && (
                <div>
                  <p className="font-medium text-gray-700 mb-2">Academic Fields:</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedFields.map(fieldId => {
                      const field = academicFields.find(f => f.id === fieldId);
                      return (
                        <span key={fieldId} className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm">
                          {field?.name}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}
              
              {careerInterests.length > 0 && (
                <div>
                  <p className="font-medium text-gray-700 mb-2">Career Interests:</p>
                  <div className="flex flex-wrap gap-2">
                    {careerInterests.map(career => (
                      <span key={career} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                        {career}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="mt-4 p-4 bg-white rounded-lg border border-gray-200">
              <p className="text-sm text-gray-600">
                <strong>Next:</strong> We'll use these interests to recommend specific programs and courses 
                that align with your goals and help you explore what Gannon University has to offer.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FieldInterestsStep;