/**
 * CurrentCoursesStep Component
 * 
 * Allows current Gannon students to input their completed and currently enrolled courses.
 * This helps provide personalized degree planning and course recommendations.
 */

import React, { useState, useEffect } from 'react';
import { BookOpen, CheckCircle, Clock, Plus, X, Search, AlertCircle } from 'lucide-react';
import LoadingSpinner from '../../ui/LoadingSpinner';
import onboardingApi from '../../../services/onboardingApi';

const CurrentCoursesStep = ({ studentData, onUpdateData, onSaveProgress }) => {
  const [completedCourses, setCompletedCourses] = useState(studentData?.completed_courses || []);
  const [enrolledCourses, setEnrolledCourses] = useState(studentData?.enrolled_courses || []);
  const [availableCourses, setAvailableCourses] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState({});

  // Load available courses when component mounts or academic level changes
  useEffect(() => {
    loadCourses();
  }, [studentData?.academic_level]);

  // Auto-save when courses change
  useEffect(() => {
    const timer = setTimeout(() => {
      if (completedCourses.length > 0 || enrolledCourses.length > 0) {
        handleAutoSave();
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [completedCourses, enrolledCourses]);

  const loadCourses = async () => {
    try {
      setIsLoading(true);
      // Get courses filtered by student's academic level
      const level = studentData?.academic_level || 'undergraduate';
      const courses = await onboardingApi.getCourses(level, 500);
      setAvailableCourses(courses);
    } catch (error) {
      console.error('Failed to load courses:', error);
      setErrors({ courses: 'Failed to load course list' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAutoSave = async () => {
    try {
      setIsSaving(true);
      const formData = {
        completed_courses: completedCourses,
        enrolled_courses: enrolledCourses
      };
      await onSaveProgress(formData);
      onUpdateData(formData);
    } catch (error) {
      console.error('Failed to auto-save:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const addCompletedCourse = (course) => {
    if (!completedCourses.find(c => c.code === course.code) && 
        !enrolledCourses.find(c => c.code === course.code)) {
      const currentYear = new Date().getFullYear();
      const defaultSemester = `Fall ${currentYear - 1}`; // Most likely last completed semester
      
      setCompletedCourses(prev => [...prev, {
        ...course,
        semester: defaultSemester,
        grade: 'A',
        year: currentYear - 1
      }]);
    }
  };

  const addEnrolledCourse = (course) => {
    if (!enrolledCourses.find(c => c.code === course.code) && 
        !completedCourses.find(c => c.code === course.code)) {
      const currentYear = new Date().getFullYear();
      const currentMonth = new Date().getMonth() + 1; // 1-12
      
      // Determine current semester based on month
      let defaultSemester;
      if (currentMonth >= 1 && currentMonth <= 5) {
        defaultSemester = `Spring ${currentYear}`;
      } else if (currentMonth >= 6 && currentMonth <= 8) {
        defaultSemester = `Summer ${currentYear}`;
      } else {
        defaultSemester = `Fall ${currentYear}`;
      }
      
      setEnrolledCourses(prev => [...prev, {
        ...course,
        semester: defaultSemester,
        year: currentYear
      }]);
    }
  };

  const removeCompletedCourse = (courseCode) => {
    setCompletedCourses(prev => prev.filter(c => c.code !== courseCode));
  };

  const removeEnrolledCourse = (courseCode) => {
    setEnrolledCourses(prev => prev.filter(c => c.code !== courseCode));
  };

  const updateCourseDetails = (courseCode, field, value, isCompleted = true) => {
    if (isCompleted) {
      setCompletedCourses(prev => prev.map(c => 
        c.code === courseCode ? { ...c, [field]: value } : c
      ));
    } else {
      setEnrolledCourses(prev => prev.map(c => 
        c.code === courseCode ? { ...c, [field]: value } : c
      ));
    }
  };

  const filteredCourses = availableCourses.filter(course => {
    const search = searchTerm.toLowerCase();
    return (
      course.code.toLowerCase().includes(search) ||
      course.title.toLowerCase().includes(search) ||
      course.department_code.toLowerCase().includes(search) ||
      `${course.code} ${course.title}`.toLowerCase().includes(search)
    );
  }).slice(0, 15); // Show more results for better UX

  const getCurrentSemesterOptions = () => {
    const currentYear = new Date().getFullYear();
    const options = [];
    
    // Generate current and past 3 years of semesters
    for (let year = currentYear; year >= currentYear - 3; year--) {
      options.push(`Fall ${year}`);
      options.push(`Spring ${year}`);
      options.push(`Summer ${year}`);
    }
    
    return options;
  };
  
  const currentSemesterOptions = getCurrentSemesterOptions();

  const gradeOptions = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F', 'W', 'I'];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="md" text="Loading courses..." />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex items-center justify-center mb-4">
            <BookOpen className="w-8 h-8 text-red-800 mr-3" />
            <h2 className="text-2xl font-bold text-gray-900">Your Course History</h2>
          </div>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Help us understand your academic journey by sharing your completed and currently enrolled courses. 
            This information will help us provide better degree planning and course recommendations.
          </p>
        </div>

        {/* Course Search */}
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Search and Add Courses</h3>
          
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search courses... (e.g., 'CIS 180', 'Data Structures', 'Biology')"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-800 focus:border-transparent"
            />
          </div>

          {searchTerm && (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {filteredCourses.map(course => (
                <div key={course.code} className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      <div className="font-semibold text-red-800 bg-red-50 px-2 py-1 rounded text-sm">
                        {course.code}
                      </div>
                      <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {course.credits} credits
                      </div>
                    </div>
                    <div className="font-medium text-gray-900 mt-1 truncate pr-4">{course.title}</div>
                    <div className="text-xs text-gray-500 mt-1">{course.department_code}</div>
                  </div>
                  <div className="flex space-x-2 flex-shrink-0">
                    <button
                      onClick={() => addCompletedCourse(course)}
                      className="flex items-center space-x-1 px-3 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition-colors"
                      title="Mark as completed"
                    >
                      <CheckCircle className="w-4 h-4" />
                      <span className="hidden sm:inline">Completed</span>
                    </button>
                    <button
                      onClick={() => addEnrolledCourse(course)}
                      className="flex items-center space-x-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                      title="Mark as enrolled"
                    >
                      <Clock className="w-4 h-4" />
                      <span className="hidden sm:inline">Enrolled</span>
                    </button>
                  </div>
                </div>
              ))}
              {filteredCourses.length === 0 && searchTerm && (
                <div className="text-center py-4 text-gray-500">
                  No courses found matching "{searchTerm}"
                </div>
              )}
            </div>
          )}
        </div>

        {/* Completed Courses */}
        <div>
          <div className="flex items-center space-x-2 mb-4">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <h3 className="text-lg font-semibold text-gray-900">
              Completed Courses ({completedCourses.length})
            </h3>
          </div>
          
          {completedCourses.length === 0 ? (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <p className="text-gray-500">No completed courses added yet. Search above to add courses.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {completedCourses.map(course => (
                <div key={course.code} className="flex items-center space-x-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{course.code}</div>
                    <div className="text-sm text-gray-600">{course.title}</div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <select
                      value={course.semester}
                      onChange={(e) => updateCourseDetails(course.code, 'semester', e.target.value, true)}
                      className="px-2 py-1 border border-gray-300 rounded text-sm"
                    >
                      {currentSemesterOptions.map(semester => (
                        <option key={semester} value={semester}>{semester}</option>
                      ))}
                    </select>
                    <select
                      value={course.grade}
                      onChange={(e) => updateCourseDetails(course.code, 'grade', e.target.value, true)}
                      className="px-2 py-1 border border-gray-300 rounded text-sm"
                    >
                      {gradeOptions.map(grade => (
                        <option key={grade} value={grade}>{grade}</option>
                      ))}
                    </select>
                    <button
                      onClick={() => removeCompletedCourse(course.code)}
                      className="p-1 text-red-600 hover:text-red-800 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Currently Enrolled Courses */}
        <div>
          <div className="flex items-center space-x-2 mb-4">
            <Clock className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">
              Currently Enrolled Courses ({enrolledCourses.length})
            </h3>
          </div>
          
          {enrolledCourses.length === 0 ? (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <p className="text-gray-500">No enrolled courses added yet. Search above to add courses.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {enrolledCourses.map(course => (
                <div key={course.code} className="flex items-center space-x-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{course.code}</div>
                    <div className="text-sm text-gray-600">{course.title}</div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <select
                      value={course.semester}
                      onChange={(e) => updateCourseDetails(course.code, 'semester', e.target.value, false)}
                      className="px-2 py-1 border border-gray-300 rounded text-sm"
                    >
                      {currentSemesterOptions.slice(0, 3).map(semester => (
                        <option key={semester} value={semester}>{semester}</option>
                      ))}
                    </select>
                    <button
                      onClick={() => removeEnrolledCourse(course.code)}
                      className="p-1 text-red-600 hover:text-red-800 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Auto-save indicator */}
        {isSaving && (
          <div className="flex items-center justify-center py-2">
            <LoadingSpinner size="sm" text="Saving courses..." />
          </div>
        )}

        {/* Summary */}
        {(completedCourses.length > 0 || enrolledCourses.length > 0) && (
          <div className="bg-gray-50 rounded-lg p-6">
            <h4 className="font-semibold text-gray-900 mb-2">Course Summary</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-green-600">{completedCourses.length}</div>
                <div className="text-sm text-gray-600">Completed</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-600">{enrolledCourses.length}</div>
                <div className="text-sm text-gray-600">Enrolled</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-800">
                  {completedCourses.reduce((sum, c) => sum + (c.credits || 0), 0)}
                </div>
                <div className="text-sm text-gray-600">Credits Earned</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-purple-600">
                  {enrolledCourses.reduce((sum, c) => sum + (c.credits || 0), 0)}
                </div>
                <div className="text-sm text-gray-600">Credits in Progress</div>
              </div>
            </div>
          </div>
        )}

        {errors.courses && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm flex items-center space-x-2">
              <AlertCircle className="w-4 h-4" />
              <span>{errors.courses}</span>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CurrentCoursesStep;