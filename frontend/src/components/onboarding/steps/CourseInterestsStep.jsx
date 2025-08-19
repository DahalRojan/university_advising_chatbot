/**
 * CourseInterestsStep Component
 * 
 * Allows students to browse and select courses they're interested in during onboarding.
 */

import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Search, 
  Filter, 
  Plus, 
  X, 
  Star, 
  Clock,
  Users,
  ChevronDown,
  AlertCircle
} from 'lucide-react';
import LoadingSpinner from '../../ui/LoadingSpinner';
import onboardingApi from '../../../services/onboardingApi';

const CourseInterestsStep = ({ studentData, onUpdateData, onSaveProgress }) => {
  const [departments, setDepartments] = useState([]);
  const [courses, setCourses] = useState([]);
  const [selectedCourses, setSelectedCourses] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDepartment, setSelectedDepartment] = useState('');
  const [selectedLevel, setSelectedLevel] = useState(studentData?.academic_level || 'undergraduate');
  const [selectedCredits, setSelectedCredits] = useState('');
  const [hasPrerequisites, setHasPrerequisites] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    searchCourses();
  }, [searchTerm, selectedDepartment, selectedLevel, selectedCredits, hasPrerequisites]);

  // Update selected level when student data changes
  useEffect(() => {
    if (studentData?.academic_level && studentData.academic_level !== selectedLevel) {
      setSelectedLevel(studentData.academic_level);
    }
  }, [studentData?.academic_level]);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [departmentsData, courseInterests] = await Promise.all([
        onboardingApi.getDepartments(),
        onboardingApi.getCourseInterests(),
      ]);

      setDepartments(departmentsData);
      setSelectedCourses(courseInterests.course_interests || []);

      // Load initial courses
      const initialCourses = await onboardingApi.searchCourses({
        level: selectedLevel,
        limit: 50,
      });
      setCourses(initialCourses);
    } catch (error) {
      console.error('Failed to load course data:', error);
      setError('Failed to load course information. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const searchCourses = async () => {
    try {
      setIsSearching(true);
      setError(null);

      const searchParams = {
        level: selectedLevel,
        searchTerm: searchTerm.trim() || null,
        department: selectedDepartment || null,
        credits: selectedCredits ? parseInt(selectedCredits) : null,
        hasPrerequisites: hasPrerequisites,
        limit: 100,
      };

      const results = await onboardingApi.searchCourses(searchParams);
      setCourses(results);
    } catch (error) {
      console.error('Failed to search courses:', error);
      setError('Failed to search courses. Please try again.');
    } finally {
      setIsSearching(false);
    }
  };

  const addCourseInterest = async (course, interestLevel = 'interested') => {
    try {
      await onboardingApi.addCourseInterest(course.code, {
        interestLevel,
        reason: `Selected during onboarding`,
      });

      const newInterest = {
        course_code: course.code,
        title: course.title,
        credits: course.credits,
        department_code: course.department_code,
        department_name: course.department_name,
        interest_level: interestLevel,
        reason: 'Selected during onboarding',
      };

      setSelectedCourses(prev => {
        const filtered = prev.filter(c => c.course_code !== course.code);
        return [...filtered, newInterest];
      });

      // Auto-save progress
      await onSaveProgress({
        course_interests: [...selectedCourses, newInterest],
      });
    } catch (error) {
      console.error('Failed to add course interest:', error);
      setError('Failed to add course interest. Please try again.');
    }
  };

  const removeCourseInterest = async (courseCode) => {
    try {
      // Note: In a real implementation, you'd want a remove endpoint
      // For now, we'll just update the local state
      setSelectedCourses(prev => prev.filter(c => c.course_code !== courseCode));

      // Auto-save progress
      const updatedInterests = selectedCourses.filter(c => c.course_code !== courseCode);
      await onSaveProgress({
        course_interests: updatedInterests,
      });
    } catch (error) {
      console.error('Failed to remove course interest:', error);
      setError('Failed to remove course interest. Please try again.');
    }
  };

  const isSelected = (courseCode) => {
    return selectedCourses.some(c => c.course_code === courseCode);
  };

  const getInterestLevel = (courseCode) => {
    const interest = selectedCourses.find(c => c.course_code === courseCode);
    return interest?.interest_level || 'interested';
  };

  const updateInterestLevel = async (courseCode, newLevel) => {
    const course = courses.find(c => c.code === courseCode);
    if (course) {
      await addCourseInterest(course, newLevel);
    }
  };

  const getInterestLevelColor = (level) => {
    switch (level) {
      case 'very_interested':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'interested':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'considering':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getInterestLevelText = (level) => {
    switch (level) {
      case 'very_interested':
        return 'Very Interested';
      case 'interested':
        return 'Interested';
      case 'considering':
        return 'Considering';
      default:
        return 'Interested';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="md" text="Loading courses..." />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Search and Filters */}
      <div className="mb-6">
        <div className="flex flex-col lg:flex-row gap-4 mb-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search courses by name, code, or description..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
            />
            {isSearching && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
              </div>
            )}
          </div>

          {/* Filters Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Filter className="w-4 h-4" />
            <span>Filters</span>
            <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'transform rotate-180' : ''}`} />
          </button>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Academic Level
                </label>
                <select
                  value={selectedLevel}
                  onChange={(e) => setSelectedLevel(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                >
                  <option value="undergraduate">Undergraduate</option>
                  <option value="graduate">Graduate</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Department
                </label>
                <select
                  value={selectedDepartment}
                  onChange={(e) => setSelectedDepartment(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                >
                  <option value="">All Departments</option>
                  {departments.map(dept => (
                    <option key={dept.code} value={dept.code}>
                      {dept.code} - {dept.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Credit Hours
                </label>
                <select
                  value={selectedCredits}
                  onChange={(e) => setSelectedCredits(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                >
                  <option value="">Any Credits</option>
                  <option value="1">1 Credit</option>
                  <option value="2">2 Credits</option>
                  <option value="3">3 Credits</option>
                  <option value="4">4 Credits</option>
                  <option value="5">5 Credits</option>
                  <option value="6">6 Credits</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Prerequisites
                </label>
                <select
                  value={hasPrerequisites === null ? '' : hasPrerequisites.toString()}
                  onChange={(e) => {
                    const value = e.target.value;
                    setHasPrerequisites(value === '' ? null : value === 'true');
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                >
                  <option value="">Any</option>
                  <option value="false">No Prerequisites</option>
                  <option value="true">Has Prerequisites</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Selected Courses Summary */}
      {selectedCourses.length > 0 && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-medium text-green-900">
              Selected Courses ({selectedCourses.length})
            </h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedCourses.map(course => (
              <div
                key={course.course_code}
                className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-sm border ${getInterestLevelColor(course.interest_level)}`}
              >
                <span className="font-medium">{course.course_code}</span>
                <span>-</span>
                <span>{getInterestLevelText(course.interest_level)}</span>
                <button
                  onClick={() => removeCourseInterest(course.course_code)}
                  className="ml-1 hover:bg-red-100 rounded-full p-0.5 transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Course Results */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {courses.map(course => {
          const selected = isSelected(course.code);
          const interestLevel = getInterestLevel(course.code);
          
          return (
            <div
              key={course.code}
              className={`border rounded-lg p-4 transition-all duration-200 ${
                selected 
                  ? 'border-green-500 bg-green-50' 
                  : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <h3 className="font-semibold text-gray-900">{course.code}</h3>
                    {course.credits && (
                      <span className="inline-flex items-center space-x-1 text-xs text-gray-500">
                        <Clock className="w-3 h-3" />
                        <span>{course.credits} credits</span>
                      </span>
                    )}
                  </div>
                  <p className="text-sm font-medium text-gray-700 mb-2">{course.title}</p>
                  {course.department_name && (
                    <p className="text-xs text-gray-500 mb-2">
                      {course.department_code} - {course.department_name}
                    </p>
                  )}
                </div>
              </div>

              {course.description && (
                <p className="text-sm text-gray-600 mb-3 line-clamp-3">
                  {course.description}
                </p>
              )}

              {course.prerequisites && (
                <div className="mb-3">
                  <p className="text-xs font-medium text-gray-700 mb-1">Prerequisites:</p>
                  <p className="text-xs text-gray-600">{course.prerequisites}</p>
                </div>
              )}

              <div className="flex items-center justify-between">
                {selected ? (
                  <div className="flex items-center space-x-2">
                    <select
                      value={interestLevel}
                      onChange={(e) => updateInterestLevel(course.code, e.target.value)}
                      className="text-xs px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-red-500 focus:border-transparent"
                    >
                      <option value="considering">Considering</option>
                      <option value="interested">Interested</option>
                      <option value="very_interested">Very Interested</option>
                    </select>
                    <button
                      onClick={() => removeCourseInterest(course.code)}
                      className="text-red-600 hover:text-red-700 p-1"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => addCourseInterest(course)}
                    className="flex items-center space-x-2 px-3 py-1 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Add Interest</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {courses.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No courses found</h3>
          <p className="text-gray-600">
            Try adjusting your search terms or filters to find courses.
          </p>
        </div>
      )}

      {/* Info Box */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <BookOpen className="w-5 h-5 text-blue-600 mt-0.5" />
          </div>
          <div>
            <h4 className="text-sm font-medium text-blue-900 mb-1">
              Course Selection Tips
            </h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Select courses that align with your academic goals and interests</li>
              <li>• Consider prerequisites when planning your course sequence</li>
              <li>• You can adjust your interest level or remove courses at any time</li>
              <li>• This information helps us provide better academic recommendations</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourseInterestsStep;