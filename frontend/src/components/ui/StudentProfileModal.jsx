import React, { useState, useEffect } from 'react';
import { 
  X, 
  Edit3, 
  Save, 
  Loader, 
  User, 
  GraduationCap, 
  Target, 
  BookOpen, 
  Heart,
  AlertCircle,
  Clock,
  Check
} from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';
import onboardingApi from '../../services/onboardingApi';

const StudentProfileModal = ({ onClose }) => {
  const [profile, setProfile] = useState(null);
  const [academicGoals, setAcademicGoals] = useState([]);
  const [courseInterests, setCourseInterests] = useState([]);
  const [academicHistory, setAcademicHistory] = useState([]);
  const [fieldInterests, setFieldInterests] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editedProfile, setEditedProfile] = useState({});
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadAllProfileData();
  }, []);

  useEffect(() => {
    if (profile) {
      setEditedProfile({ ...profile });
    }
  }, [profile]);

  const loadAllProfileData = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      console.log('📊 Loading complete profile data...');
      
      // Load profile data first, then additional data
      const profileData = await onboardingApi.getStudentProfile();
      console.log('📊 Raw profile data:', profileData);
      
      // Load additional data in parallel, with error handling
      const [goalsData, interestsData, historyData, fieldInterestsData] = await Promise.allSettled([
        onboardingApi.getAcademicGoals().then(data => data.academic_goals || []).catch(err => {
          console.warn('Academic goals failed:', err);
          return [];
        }),
        onboardingApi.getCourseInterests().catch(err => {
          console.warn('Course interests failed:', err);
          return [];
        }),
        onboardingApi.getAcademicHistory().then(data => {
          console.log('📚 Raw academic history response:', data);
          return data.academic_history || [];
        }).catch(err => {
          console.error('❌ Academic history failed:', err);
          return [];
        }),
        onboardingApi.getFieldInterests().then(data => data.field_interests || []).catch(err => {
          console.warn('Field interests failed:', err);
          return [];
        })
      ]);
      
      // Extract values from Promise.allSettled results
      const resolvedGoals = goalsData.status === 'fulfilled' ? goalsData.value : [];
      const resolvedInterests = interestsData.status === 'fulfilled' ? interestsData.value : [];
      const resolvedHistory = historyData.status === 'fulfilled' ? historyData.value : [];
      const resolvedFieldInterests = fieldInterestsData.status === 'fulfilled' ? fieldInterestsData.value : [];
      
      console.log('📊 Profile data loaded:', profileData);
      console.log('📊 Profile first_name:', profileData?.first_name);
      console.log('📊 Profile last_name:', profileData?.last_name);
      console.log('📊 Profile expected_graduation:', profileData?.expected_graduation);
      console.log('🎯 Academic goals loaded:', resolvedGoals);
      console.log('💝 Course interests loaded:', resolvedInterests);
      console.log('📚 Academic history loaded:', resolvedHistory);
      console.log('📚 Academic history length:', resolvedHistory?.length);
      console.log('📚 Academic history sample:', resolvedHistory?.[0]);
      console.log('🌟 Field interests loaded:', resolvedFieldInterests);
      
      setProfile(profileData || {});
      setAcademicGoals(resolvedGoals || []);
      setCourseInterests(resolvedInterests || []);
      setAcademicHistory(resolvedHistory || []);
      setFieldInterests(resolvedFieldInterests || []);
      
    } catch (error) {
      console.error('❌ Failed to load profile data:', error);
      setError('Failed to load profile information. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const updateField = (fieldName, value) => {
    setEditedProfile(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Not specified';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch (error) {
      return 'Invalid date';
    }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setError('');
      
      console.log('💾 Saving profile changes...', editedProfile);
      
      const result = await onboardingApi.updateStudentProfile(editedProfile);
      console.log('💾 Save result:', result);
      
      // Update local profile state
      setProfile(editedProfile);
      setIsEditing(false);
      
    } catch (error) {
      console.error('❌ Error saving profile:', error);
      setError('Failed to save profile. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditedProfile({ ...profile });
    setIsEditing(false);
    setError('');
  };

  const getCompletionPercentage = () => {
    if (!profile) return 0;
    
    // Use the database completion percentage if available
    if (profile.profile_completion_percentage !== undefined && profile.profile_completion_percentage !== null) {
      console.log('📊 Using database completion percentage:', profile.profile_completion_percentage);
      return Math.round(profile.profile_completion_percentage);
    }
    
    // Fallback: Calculate based on available fields
    const onboardingFields = [
      'first_name',
      'last_name', 
      'student_type',
      'academic_level',
      'enrollment_status',
      'primary_major'
    ];
    
    const completedFields = onboardingFields.filter(field => 
      profile[field] && profile[field] !== ''
    );
    
    const percentage = Math.round((completedFields.length / onboardingFields.length) * 100);
    console.log('📊 Calculated completion percentage:', percentage);
    return percentage;
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4">
          <div className="flex flex-col items-center space-y-4">
            <LoadingSpinner size="lg" text="Getting your onboarding information..." />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-red-800 to-red-900 text-white p-6 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-white bg-opacity-20 rounded-xl flex items-center justify-center">
                <User className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-2xl font-bold">Student Profile</h2>
                <p className="text-red-100">
                  {profile?.first_name && profile?.last_name 
                    ? `${profile.first_name} ${profile.last_name}` 
                    : profile?.user_email || 'Your Onboarding Information'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              {!isEditing && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 bg-white bg-opacity-20 rounded-lg hover:bg-opacity-30 
                           transition-all duration-200 flex items-center space-x-2"
                >
                  <Edit3 className="w-4 h-4" />
                  <span>Edit</span>
                </button>
              )}
              <button
                onClick={onClose}
                className="w-8 h-8 bg-white bg-opacity-20 rounded-lg hover:bg-opacity-30 
                         transition-all duration-200 flex items-center justify-center"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Profile completion progress */}
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-red-100">Onboarding Progress</span>
              <span className="text-white font-semibold">
                {getCompletionPercentage()}% Complete
              </span>
            </div>
            <div className="w-full bg-red-900 bg-opacity-50 rounded-full h-2">
              <div 
                className="bg-white h-2 rounded-full transition-all duration-700"
                style={{ width: `${getCompletionPercentage()}%` }}
              />
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
              <p className="text-red-700">{error}</p>
            </div>
          )}

          <div className="space-y-6">
            {/* 1. Student Type Section */}
            <div className="bg-gray-50 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <GraduationCap className="w-5 h-5 mr-2 text-red-600" />
                Student Status
              </h3>
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Student Type
                  </label>
                  {isEditing ? (
                    <select
                      value={editedProfile.student_type || ''}
                      onChange={(e) => updateField('student_type', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    >
                      <option value="">Select student type</option>
                      <option value="current_gannon">Current Gannon Student</option>
                      <option value="prospective">Prospective Student</option>
                    </select>
                  ) : (
                    <p className="text-gray-900 py-2">
                      {profile?.student_type === 'current_gannon' ? 'Current Gannon Student' : 
                       profile?.student_type === 'prospective' ? 'Prospective Student' : 
                       'Not specified'}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* 2. Personal Information Section */}
            <div className="bg-gray-50 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <User className="w-5 h-5 mr-2 text-red-600" />
                Personal Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    First Name
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={editedProfile.first_name || ''}
                      onChange={(e) => updateField('first_name', e.target.value)}
                      placeholder="Enter your first name"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    />
                  ) : (
                    <div className="py-2">
                      {profile?.first_name ? (
                        <p className="text-gray-900">{profile.first_name}</p>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <p className="text-orange-600 font-medium">Not provided</p>
                          <button
                            onClick={() => setIsEditing(true)}
                            className="text-sm bg-orange-100 text-orange-700 px-2 py-1 rounded hover:bg-orange-200 transition-colors"
                          >
                            Add Now
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Last Name
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={editedProfile.last_name || ''}
                      onChange={(e) => updateField('last_name', e.target.value)}
                      placeholder="Enter your last name"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    />
                  ) : (
                    <div className="py-2">
                      {profile?.last_name ? (
                        <p className="text-gray-900">{profile.last_name}</p>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <p className="text-orange-600 font-medium">Not provided</p>
                          <button
                            onClick={() => setIsEditing(true)}
                            className="text-sm bg-orange-100 text-orange-700 px-2 py-1 rounded hover:bg-orange-200 transition-colors"
                          >
                            Add Now
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Expected Graduation
                  </label>
                  {isEditing ? (
                    <input
                      type="date"
                      value={editedProfile.expected_graduation ? new Date(editedProfile.expected_graduation).toISOString().split('T')[0] : ''}
                      onChange={(e) => updateField('expected_graduation', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    />
                  ) : (
                    <p className="text-gray-900 py-2">{formatDate(profile?.expected_graduation) || 'Not specified'}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Preferred Name
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={editedProfile.preferred_name || ''}
                      onChange={(e) => updateField('preferred_name', e.target.value)}
                      placeholder="Enter preferred name (optional)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    />
                  ) : (
                    <div className="py-2">
                      {profile?.preferred_name ? (
                        <p className="text-gray-900">{profile.preferred_name}</p>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <p className="text-red-600 font-medium">Not provided</p>
                          <button
                            onClick={() => setIsEditing(true)}
                            className="text-sm bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200 transition-colors"
                          >
                            Add Now
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Student ID
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={editedProfile.student_id || ''}
                      onChange={(e) => updateField('student_id', e.target.value)}
                      placeholder="Enter student ID (optional)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    />
                  ) : (
                    <div className="py-2">
                      {profile?.student_id ? (
                        <p className="text-gray-900">{profile.student_id}</p>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <p className="text-red-600 font-medium">Not provided</p>
                          <button
                            onClick={() => setIsEditing(true)}
                            className="text-sm bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200 transition-colors"
                          >
                            Add Now
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address
                  </label>
                  <p className="text-gray-600 py-2 text-sm">{profile?.user_email || 'Not available'}</p>
                </div>
              </div>
            </div>

            {/* 3. Academic Information Section */}
            <div className="bg-gray-50 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <BookOpen className="w-5 h-5 mr-2 text-red-600" />
                Academic Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Academic Level
                  </label>
                  {isEditing ? (
                    <select
                      value={editedProfile.academic_level || ''}
                      onChange={(e) => updateField('academic_level', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    >
                      <option value="">Select level</option>
                      <option value="undergraduate">Undergraduate</option>
                      <option value="graduate">Graduate</option>
                      <option value="doctoral">Doctoral</option>
                    </select>
                  ) : (
                    <p className="text-gray-900 py-2 capitalize">{profile?.academic_level || 'Not specified'}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Enrollment Status
                  </label>
                  {isEditing ? (
                    <select
                      value={editedProfile.enrollment_status || ''}
                      onChange={(e) => updateField('enrollment_status', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    >
                      <option value="">Select status</option>
                      <option value="full-time">Full-time</option>
                      <option value="part-time">Part-time</option>
                      <option value="not-enrolled">Not enrolled</option>
                    </select>
                  ) : (
                    <p className="text-gray-900 py-2">{profile?.enrollment_status?.replace('-', ' ') || 'Not specified'}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Primary Major
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={editedProfile.primary_major || ''}
                      onChange={(e) => updateField('primary_major', e.target.value)}
                      placeholder="Enter your major"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    />
                  ) : (
                    <p className="text-gray-900 py-2">{profile?.primary_major || 'Not specified'}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Expected Graduation
                  </label>
                  {isEditing ? (
                    <input
                      type="date"
                      value={editedProfile.expected_graduation || ''}
                      onChange={(e) => updateField('expected_graduation', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    />
                  ) : (
                    <p className="text-gray-900 py-2">
                      {profile?.expected_graduation ? formatDate(profile.expected_graduation) : 'Not specified'}
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Current GPA
                  </label>
                  {isEditing ? (
                    <input
                      type="number"
                      min="0"
                      max="4.0"
                      step="0.01"
                      value={editedProfile.cumulative_gpa || ''}
                      onChange={(e) => updateField('cumulative_gpa', e.target.value)}
                      placeholder="e.g., 3.75"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    />
                  ) : (
                    <div className="py-2">
                      {profile?.cumulative_gpa ? (
                        <p className="text-gray-900">{profile.cumulative_gpa}/4.0</p>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <p className="text-red-600 font-medium">Not provided</p>
                          <button
                            onClick={() => setIsEditing(true)}
                            className="text-sm bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200 transition-colors"
                          >
                            Add Now
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Secondary Major
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={editedProfile.secondary_major || ''}
                      onChange={(e) => updateField('secondary_major', e.target.value)}
                      placeholder="Enter secondary major (optional)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    />
                  ) : (
                    <div className="py-2">
                      {profile?.secondary_major ? (
                        <p className="text-gray-900">{profile.secondary_major}</p>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <p className="text-red-600 font-medium">Not provided</p>
                          <button
                            onClick={() => setIsEditing(true)}
                            className="text-sm bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200 transition-colors"
                          >
                            Add Now
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Minor Program
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={editedProfile.minor_program || ''}
                      onChange={(e) => updateField('minor_program', e.target.value)}
                      placeholder="Enter minor program (optional)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    />
                  ) : (
                    <div className="py-2">
                      {profile?.minor_program ? (
                        <p className="text-gray-900">{profile.minor_program}</p>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <p className="text-red-600 font-medium">Not provided</p>
                          <button
                            onClick={() => setIsEditing(true)}
                            className="text-sm bg-red-100 text-red-800 px-2 py-1 rounded hover:bg-red-200 transition-colors"
                          >
                            Add Now
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 4. Academic History Section - Current Students Only */}
            {profile?.student_type === 'current_gannon' && (
              <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <BookOpen className="w-5 h-5 mr-2 text-red-600" />
                  Academic History ({academicHistory.length} courses)
                </h3>
                
                {academicHistory.length > 0 ? (
                  <div className="space-y-4">
                    {/* Completed Courses */}
                    {academicHistory.filter(course => course.status === 'completed').length > 0 && (
                      <div>
                        <h4 className="text-md font-medium text-gray-800 mb-3 flex items-center">
                          <Check className="w-4 h-4 mr-2 text-green-600" />
                          Completed Courses ({academicHistory.filter(course => course.status === 'completed').length})
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {academicHistory
                            .filter(course => course.status === 'completed')
                            .map((course, index) => (
                              <div key={index} className="bg-white rounded-lg p-4 border border-gray-200">
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <p className="font-semibold text-gray-900">{course.course_code}</p>
                                    {course.course_title && course.course_title !== course.course_code && (
                                      <p className="text-sm text-gray-600 mt-1">{course.course_title}</p>
                                    )}
                                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                                      <span>{course.semester} {course.year}</span>
                                      {course.credits_earned && (
                                        <span>• {course.credits_earned} credits</span>
                                      )}
                                      {course.institution && course.institution !== 'Gannon University' && (
                                        <span>• {course.institution}</span>
                                      )}
                                    </div>
                                  </div>
                                  <div className="ml-4">
                                    {course.grade && (
                                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                        ['A', 'A+', 'A-'].includes(course.grade) ? 'bg-green-100 text-green-700' :
                                        ['B+', 'B', 'B-'].includes(course.grade) ? 'bg-blue-100 text-blue-700' :
                                        ['C+', 'C', 'C-'].includes(course.grade) ? 'bg-yellow-100 text-yellow-700' :
                                        'bg-gray-100 text-gray-700'
                                      }`}>
                                        {course.grade}
                                      </span>
                                    )}
                                    {course.is_transfer_credit && (
                                      <div className="mt-1">
                                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                                          Transfer
                                        </span>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* Enrolled Courses */}
                    {academicHistory.filter(course => course.status === 'enrolled').length > 0 && (
                      <div>
                        <h4 className="text-md font-medium text-gray-800 mb-3 flex items-center">
                          <Clock className="w-4 h-4 mr-2 text-blue-600" />
                          Currently Enrolled ({academicHistory.filter(course => course.status === 'enrolled').length})
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {academicHistory
                            .filter(course => course.status === 'enrolled')
                            .map((course, index) => (
                              <div key={index} className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <p className="font-semibold text-gray-900">{course.course_code}</p>
                                    {course.course_title && course.course_title !== course.course_code && (
                                      <p className="text-sm text-gray-600 mt-1">{course.course_title}</p>
                                    )}
                                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                                      <span>{course.semester} {course.year}</span>
                                      {course.credits_earned && (
                                        <span>• {course.credits_earned} credits</span>
                                      )}
                                    </div>
                                  </div>
                                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                                    In Progress
                                  </span>
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <BookOpen className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>No academic history found</p>
                    <p className="text-sm">Complete courses will appear here</p>
                  </div>
                )}
              </div>
            )}

            {/* 5. Field Interests Section - Prospective Students Only */}
            {profile?.student_type === 'prospective' && fieldInterests.length > 0 && (
              <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Target className="w-5 h-5 mr-2 text-red-600" />
                  Academic & Career Interests ({fieldInterests.length})
                </h3>
                <div className="flex flex-wrap gap-2">
                  {fieldInterests.map((interest, index) => (
                    <span 
                      key={index}
                      className="px-3 py-2 bg-blue-100 text-blue-800 text-sm font-medium rounded-full"
                    >
                      {interest}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 6. Academic Goals Section */}
            {academicGoals.length > 0 && (
              <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Target className="w-5 h-5 mr-2 text-red-600" />
                  Academic Goals ({academicGoals.length})
                </h3>
                <div className="space-y-3">
                  {academicGoals.map((goal, index) => (
                    <div key={index} className="bg-white rounded-lg p-4 border border-gray-200">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              goal.goal_type === 'academic' ? 'bg-blue-100 text-blue-700' :
                              goal.goal_type === 'career' ? 'bg-green-100 text-green-700' :
                              goal.goal_type === 'skill' ? 'bg-purple-100 text-purple-700' :
                              goal.goal_type === 'personal' ? 'bg-pink-100 text-pink-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {goal.goal_type || 'general'}
                            </span>
                            {goal.goal_category && (
                              <span className="text-sm text-gray-500">• {goal.goal_category}</span>
                            )}
                          </div>
                          <p className="text-gray-900 font-medium">{goal.goal_description || 'No description provided'}</p>
                          {goal.target_completion_date && (
                            <p className="text-sm text-gray-500 mt-1">
                              Target: {formatDate(goal.target_completion_date)}
                            </p>
                          )}
                        </div>
                        <div className="flex items-center space-x-1">
                          {Array.from({ length: 5 }, (_, i) => (
                            <div
                              key={i}
                              className={`w-2 h-2 rounded-full ${
                                i < (goal.priority_level || 1) / 2 ? 'bg-yellow-400' : 'bg-gray-200'
                              }`}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 7. Course Interests Section */}
            {courseInterests.length > 0 && (
              <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Heart className="w-5 h-5 mr-2 text-red-600" />
                  Course Interests ({courseInterests.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {courseInterests.map((interest, index) => (
                    <div key={index} className="bg-white rounded-lg p-4 border border-gray-200">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="font-semibold text-gray-900">{interest.course_code || 'Unknown Course'}</p>
                          {interest.title && (
                            <p className="text-sm text-gray-600 mt-1">{interest.title}</p>
                          )}
                          {interest.department_name && (
                            <p className="text-xs text-gray-500 mt-1">{interest.department_name}</p>
                          )}
                          {interest.planned_semester && (
                            <p className="text-xs text-blue-600 mt-1">
                              Planned: {interest.planned_semester}
                            </p>
                          )}
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          interest.interest_level === 'very_interested' ? 'bg-green-100 text-green-700' :
                          interest.interest_level === 'interested' ? 'bg-blue-100 text-blue-700' :
                          interest.interest_level === 'somewhat_interested' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {interest.interest_level?.replace('_', ' ') || 'unknown'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Academic Progress & Activity section removed as requested */}

            {/* 8. Account Information */}
            <div className="bg-gray-50 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Clock className="w-5 h-5 mr-2 text-red-600" />
                Account Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <p className="text-sm text-gray-600 mb-1">Account Created</p>
                  <p className="text-sm font-medium text-gray-900">
                    {profile?.created_at ? formatDate(profile.created_at) : 'Unknown'}
                  </p>
                </div>
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <p className="text-sm text-gray-600 mb-1">Last Updated</p>
                  <p className="text-sm font-medium text-gray-900">
                    {profile?.updated_at ? formatDate(profile.updated_at) : 'Unknown'}
                  </p>
                </div>
              </div>
            </div>

            {/* Empty state messages */}
            {academicGoals.length === 0 && (
              <div className="bg-blue-50 rounded-xl p-6 border border-blue-200">
                <div className="flex items-center space-x-3">
                  <Target className="w-5 h-5 text-blue-600" />
                  <div>
                    <h4 className="text-sm font-medium text-blue-800">No Academic Goals Set</h4>
                    <p className="text-sm text-blue-600">Complete the onboarding process to set your academic goals.</p>
                  </div>
                </div>
              </div>
            )}

            {profile?.student_type === 'prospective' && fieldInterests.length === 0 && (
              <div className="bg-green-50 rounded-xl p-6 border border-green-200">
                <div className="flex items-center space-x-3">
                  <Target className="w-5 h-5 text-green-600" />
                  <div>
                    <h4 className="text-sm font-medium text-green-800">No Field Interests Recorded</h4>
                    <p className="text-sm text-green-600">Complete the onboarding process to explore academic and career interests.</p>
                  </div>
                </div>
              </div>
            )}

            {profile?.student_type === 'current_gannon' && academicHistory.length === 0 && (
              <div className="bg-yellow-50 rounded-xl p-6 border border-yellow-200">
                <div className="flex items-center space-x-3">
                  <BookOpen className="w-5 h-5 text-yellow-600" />
                  <div>
                    <h4 className="text-sm font-medium text-yellow-800">No Academic History Found</h4>
                    <p className="text-sm text-yellow-600">Complete the onboarding process to record your completed and enrolled courses.</p>
                  </div>
                </div>
              </div>
            )}

            {courseInterests.length === 0 && (
              <div className="bg-purple-50 rounded-xl p-6 border border-purple-200">
                <div className="flex items-center space-x-3">
                  <Heart className="w-5 h-5 text-purple-600" />
                  <div>
                    <h4 className="text-sm font-medium text-purple-800">No Course Interests Added</h4>
                    <p className="text-sm text-purple-600">Complete the onboarding process to explore course interests.</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        {isEditing && (
          <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end space-x-3 flex-shrink-0">
            <button
              onClick={handleCancel}
              disabled={isSaving}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg 
                       hover:bg-gray-50 focus:ring-2 focus:ring-red-500 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-4 py-2 bg-red-800 text-white rounded-lg hover:bg-red-900 
                       focus:ring-2 focus:ring-red-700 disabled:opacity-50 flex items-center space-x-2"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>Save Changes</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentProfileModal;
