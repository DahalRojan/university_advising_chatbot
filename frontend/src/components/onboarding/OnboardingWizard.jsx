/**
 * OnboardingWizard Component
 * 
 * A multi-step wizard that guides new students through the onboarding process,
 * including profile setup, academic goals, and course selection.
 */

import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  ArrowRight, 
  CheckCircle, 
  Circle,
  User,
  GraduationCap,
  Target,
  BookOpen,
  Settings,
  Clock,
  X
} from 'lucide-react';
import LoadingSpinner from '../ui/LoadingSpinner';
import onboardingApi from '../../services/onboardingApi';
import StudentTypeStep from './steps/StudentTypeStep';
import PersonalInfoStep from './steps/PersonalInfoStep';
import AcademicBackgroundStep from './steps/AcademicBackgroundStep';
import ProgramSelectionStep from './steps/ProgramSelectionStep';
import CurrentCoursesStep from './steps/CurrentCoursesStep';
import FieldInterestsStep from './steps/FieldInterestsStep';
import AcademicGoalsStep from './steps/AcademicGoalsStep';
import CourseInterestsStep from './steps/CourseInterestsStep';
import AdvisingPreferencesStep from './steps/AdvisingPreferencesStep';
import CompletionStep from './steps/CompletionStep';

const OnboardingWizard = ({ onComplete, onClose }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [steps, setSteps] = useState([]);
  const [progress, setProgress] = useState([]);
  const [studentData, setStudentData] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);

  // Step icons mapping - streamlined for essential steps only
  const stepIcons = {
    'student_type': User,
    'academic_info': GraduationCap,
    'current_courses': BookOpen,
    'current_goals': Target,
    'field_interests': BookOpen,
    'prospective_goals': Target,
    'completion': CheckCircle,
  };

  // Step components mapping - streamlined for essential steps only
  const stepComponents = {
    'student_type': StudentTypeStep,
    'academic_info': PersonalInfoStep,
    'current_courses': CurrentCoursesStep,
    'current_goals': AcademicGoalsStep,
    'field_interests': FieldInterestsStep,
    'prospective_goals': AcademicGoalsStep,
    'completion': CompletionStep,
  };

  useEffect(() => {
    loadOnboardingData();
  }, []);

  const loadOnboardingData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [stepsData, progressData, profileData] = await Promise.all([
        onboardingApi.getOnboardingSteps(),
        onboardingApi.getOnboardingProgress(),
        onboardingApi.getStudentProfile(),
      ]);

      setSteps(stepsData);
      setProgress(progressData);
      setStudentData(profileData || {});

      // Find the current step based on progress
      const currentStepIndex = findCurrentStep(stepsData, progressData);
      setCurrentStep(currentStepIndex);
    } catch (error) {
      console.error('Failed to load onboarding data:', error);
      setError('Failed to load onboarding information. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getWorkingSteps = (stepsData, studentType) => {
    // Streamlined onboarding flow - only essential steps for academic advising
    const baseSteps = ['student_type', 'academic_info'];
    let typeSpecificSteps = [];
    const completionSteps = ['completion'];
    
    if (studentType === 'current_gannon') {
      // For current students: focus on current courses and goals
      typeSpecificSteps = ['current_courses', 'current_goals'];
    } else if (studentType === 'prospective') {
      // For prospective students: focus on field interests and goals
      typeSpecificSteps = ['field_interests', 'prospective_goals'];
    } else {
      // If student type not selected yet, show minimal set
      typeSpecificSteps = ['current_courses', 'field_interests'];
    }
    
    const relevantStepNames = [...baseSteps, ...typeSpecificSteps, ...completionSteps];
    
    return stepsData.filter(step => relevantStepNames.includes(step.step_name))
                   .sort((a, b) => {
                     const aIndex = relevantStepNames.indexOf(a.step_name);
                     const bIndex = relevantStepNames.indexOf(b.step_name);
                     return aIndex - bIndex;
                   });
  };

  const findCurrentStep = (stepsData, progressData) => {
    const studentType = studentData?.student_type;
    const workingSteps = getWorkingSteps(stepsData, studentType);
    
    for (let i = 0; i < workingSteps.length; i++) {
      const step = workingSteps[i];
      const stepProgress = progressData.find(p => p.step_name === step.step_name);
      
      if (!stepProgress || stepProgress.status !== 'completed') {
        return i;
      }
    }
    
    // If all steps are completed, go to the last step
    return Math.max(0, workingSteps.length - 1);
  };

  const getCurrentStepData = () => {
    const studentType = studentData?.student_type;
    const workingSteps = getWorkingSteps(steps, studentType);
    return workingSteps[currentStep] || null;
  };

  const getStepProgress = (stepName) => {
    return progress.find(p => p.step_name === stepName);
  };

  const updateStepData = (stepData) => {
    setStudentData(prev => ({
      ...prev,
      ...stepData,
    }));
  };

  const saveStepProgress = async (stepName, status, data = null) => {
    try {
      await onboardingApi.updateOnboardingProgress(stepName, status, data);
      
      // Update local progress state
      setProgress(prev => {
        const existing = prev.find(p => p.step_name === stepName);
        if (existing) {
          return prev.map(p => 
            p.step_name === stepName 
              ? { ...p, status, data_json: data }
              : p
          );
        } else {
          return [...prev, { step_name: stepName, status, data_json: data }];
        }
      });
    } catch (error) {
      console.error('Failed to save step progress:', error);
      throw error;
    }
  };

  const handleNext = async () => {
    const currentStepData = getCurrentStepData();
    if (!currentStepData) return;

    try {
      setIsSaving(true);
      setError(null);

      // Mark current step as completed
      await saveStepProgress(currentStepData.step_name, 'completed', studentData);

      // Move to next step
      const studentType = studentData?.student_type;
      const workingSteps = getWorkingSteps(steps, studentType);
      if (currentStep < workingSteps.length - 1) {
        const nextStep = currentStep + 1;
        setCurrentStep(nextStep);
        
        // Mark next step as in progress
        const nextStepData = workingSteps[nextStep];
        if (nextStepData) {
          await saveStepProgress(nextStepData.step_name, 'in_progress');
        }
      } else {
        // Last step completed - finish onboarding
        await completeOnboarding();
      }
    } catch (error) {
      console.error('Failed to proceed to next step:', error);
      setError('Failed to save progress. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkipOnboarding = async () => {
    try {
      console.log('⏭️ User is skipping onboarding...');
      setIsSaving(true);
      setError(null);
      
      // Mark onboarding as complete without going through all steps
      console.log('🏃‍♀️ Marking onboarding as complete via skip...');
      await onboardingApi.completeOnboarding();
      console.log('✅ Onboarding successfully skipped and marked complete');
      
      if (onComplete) {
        console.log('🎉 Calling onComplete callback after skip');
        onComplete();
      }
    } catch (error) {
      console.error('❌ Failed to skip onboarding:', error);
      setError('Failed to skip setup. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const completeOnboarding = async () => {
    try {
      console.log('🎯 Starting onboarding completion process...');
      console.log('📊 Student data to save:', studentData);
      
      // Update profile with all collected data
      console.log('📝 Updating student profile...');
      await onboardingApi.updateStudentProfile({
        ...studentData
      });
      console.log('✅ Student profile updated successfully');
      
      // Mark the final completion step as completed
      console.log('✅ Marking completion step as completed...');
      await saveStepProgress('completion', 'completed', studentData);
      console.log('✅ Completion step marked as completed');

      // Explicitly mark onboarding as complete
      console.log('🏁 Explicitly marking onboarding as complete...');
      await onboardingApi.completeOnboarding();
      console.log('✅ Onboarding marked as complete via API');

      if (onComplete) {
        console.log('🎉 Calling onComplete callback');
        onComplete();
      }
    } catch (error) {
      console.error('❌ Failed to complete onboarding:', error);
      setError('Failed to complete onboarding. Please try again.');
    }
  };

  const calculateProgress = () => {
    const studentType = studentData?.student_type;
    const workingSteps = getWorkingSteps(steps, studentType);
    if (workingSteps.length === 0) return 0;
    
    const completedSteps = progress.filter(p => 
      p.status === 'completed' && workingSteps.some(ws => ws.step_name === p.step_name)
    ).length;
    
    return Math.round((completedSteps / workingSteps.length) * 100);
  };

  const isStepCompleted = (stepName) => {
    const stepProgress = getStepProgress(stepName);
    return stepProgress?.status === 'completed';
  };

  const canProceed = () => {
    const currentStepData = getCurrentStepData();
    if (!currentStepData) return false;
    
    // Validate based on step requirements
    switch (currentStepData.step_name) {
      case 'student_type':
        return studentData?.student_type;
      
      case 'academic_info':
        return studentData?.academic_level && studentData?.enrollment_status;
      
      case 'current_courses':
        // Optional for current students - can proceed even without adding courses
        return true;
      
      case 'field_interests':
        // Prospective students should select at least one field
        return studentData?.field_interests && studentData.field_interests.length > 0;
      
      case 'current_goals':
      case 'prospective_goals':
        // Goals are important but can be skipped
        return true;
      
      
      case 'completion':
        return true;
      
      default:
        return true;
    }
  };

  const getCurrentStepRequirementMessage = () => {
    const currentStepData = getCurrentStepData();
    if (!currentStepData) return '';
    
    switch (currentStepData.step_name) {
      case 'student_type':
        return 'Please select whether you are a current Gannon student or prospective student';
      
      case 'academic_info':
        if (!studentData?.academic_level) return 'Please select your academic level';
        if (!studentData?.enrollment_status) return 'Please select your enrollment status';
        return '';
      
      case 'field_interests':
        return 'Please select at least one academic field that interests you';
      
      default:
        return '';
    }
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-gray-50 via-white to-gray-100 flex items-center justify-center z-50 font-sans">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-red-800/4 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-red-900/4 rounded-full blur-3xl"></div>
        </div>
        <div className="bg-white/80 backdrop-blur-xl border border-white/20 shadow-2xl rounded-2xl p-8 max-w-md w-full mx-4 relative">
          <div className="flex flex-col items-center space-y-4">
            <LoadingSpinner size="lg" text="Loading your personalized onboarding experience..." />
          </div>
        </div>
      </div>
    );
  }

  const studentType = studentData?.student_type;
  const workingSteps = getWorkingSteps(steps, studentType);
  const currentStepData = getCurrentStepData();
  const totalSteps = workingSteps.length;
  const progressPercentage = calculateProgress();

  if (!currentStepData) {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-gray-50 via-white to-gray-100 flex items-center justify-center z-50 font-sans">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-red-800/4 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-red-900/4 rounded-full blur-3xl"></div>
        </div>
        <div className="bg-white/80 backdrop-blur-xl border border-white/20 shadow-2xl rounded-2xl p-8 max-w-md w-full mx-4 relative">
          <div className="text-center">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <X className="w-6 h-6 text-red-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Setup Unavailable</h3>
            <p className="text-gray-600 mb-6">Unable to load onboarding steps. Please try again later.</p>
            <button
              onClick={onClose}
              className="px-6 py-3 bg-gradient-to-r from-gray-600 to-gray-700 text-white rounded-xl hover:from-gray-700 hover:to-gray-800 transition-all font-medium shadow-lg"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  const StepComponent = stepComponents[currentStepData.step_name];

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-gray-50 via-white to-gray-100 flex items-center justify-center z-50 p-4 font-sans">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-red-800/4 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-red-900/4 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-60 h-60 bg-red-800/3 rounded-full blur-3xl"></div>
      </div>
      
      <div className="bg-white/80 backdrop-blur-xl border border-white/20 shadow-2xl rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col relative">
        {/* Header with glassy effect */}
        <div className="border-b border-gray-100/50 p-6 bg-white/40 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <div className="p-2 bg-white/80 rounded-xl shadow-sm">
                <img
                  src="https://upload.wikimedia.org/wikipedia/commons/4/49/Gannon_university_logo.png"
                  alt="Gannon University Logo"
                  className="w-8 h-8"
                />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-red-800 to-red-700 bg-clip-text text-transparent">
                  Academic Advisor Setup
                </h1>
                <p className="text-sm text-gray-600">Complete your profile to get personalized guidance</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleSkipOnboarding}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-white/50 rounded-lg transition-all duration-200 backdrop-blur-sm font-medium"
                title="Skip setup and go to chat"
              >
                Skip Setup
              </button>
              {onClose && (
                <button
                  onClick={onClose}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-white/50 rounded-xl transition-all duration-200 backdrop-blur-sm"
                  title="Close"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>

          {/* Progress Bar with glassy design */}
          <div className="mb-8">
            <div className="flex items-center justify-between text-sm mb-3">
              <span className="text-gray-700 font-medium">Setup Progress</span>
              <span className="font-bold text-red-800 bg-red-50/80 px-3 py-1 rounded-full">
                {progressPercentage}% Complete
              </span>
            </div>
            <div className="relative">
              <div className="w-full bg-gray-100/70 backdrop-blur-sm rounded-full h-3 shadow-inner">
                <div 
                  className="bg-gradient-to-r from-red-800 via-red-700 to-red-600 h-3 rounded-full transition-all duration-700 ease-out shadow-sm relative overflow-hidden"
                  style={{ width: `${progressPercentage}%` }}
                >
                  <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between text-xs text-gray-500 mt-2">
              <span>Step {currentStep + 1} of {totalSteps}</span>
              <span className="flex items-center space-x-1">
                <Clock className="w-3 h-3" />
                <span>~{currentStepData?.estimated_time_minutes || 0} min</span>
              </span>
            </div>
          </div>

          {/* Steps Navigation with glassy design */}
          <div className="flex items-center justify-between px-2">
            {workingSteps.map((step, index) => {
              const IconComponent = stepIcons[step.step_name] || Circle;
              const isActive = index === currentStep;
              const isCompleted = isStepCompleted(step.step_name);
              
              return (
                <div
                  key={step.step_name}
                  className={`flex items-center ${index < workingSteps.length - 1 ? 'flex-1' : ''}`}
                >
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center backdrop-blur-sm transition-all duration-300 shadow-sm ${
                        isCompleted
                          ? 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-green-200'
                          : isActive
                          ? 'bg-gradient-to-r from-red-800 to-red-700 text-white shadow-red-200 ring-2 ring-red-200'
                          : 'bg-white/60 text-gray-500 border border-gray-200/50'
                      }`}
                    >
                      {isCompleted ? (
                        <CheckCircle className="w-5 h-5" />
                      ) : (
                        <IconComponent className="w-5 h-5" />
                      )}
                    </div>
                    <span className={`text-xs mt-2 text-center max-w-20 leading-tight font-medium ${
                      isActive 
                        ? 'text-red-800' 
                        : isCompleted 
                        ? 'text-green-700' 
                        : 'text-gray-500'
                    }`}>
                      {step.display_name}
                    </span>
                  </div>
                  {index < workingSteps.length - 1 && (
                    <div className="flex-1 flex items-center px-3">
                      <div className={`w-full h-1 rounded-full transition-all duration-500 ${
                        isCompleted 
                          ? 'bg-gradient-to-r from-green-400 to-green-500 shadow-sm' 
                          : 'bg-gray-200/70'
                      }`}></div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content with glassy background */}
        <div className="flex-1 overflow-y-auto p-6 bg-gradient-to-b from-white/20 to-white/40 backdrop-blur-sm">
          <div className="max-w-2xl mx-auto">
            <div className="mb-8">
              <div className="mb-4">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  {currentStepData.display_name}
                </h2>
                {currentStepData.description && (
                  <p className="text-gray-600 leading-relaxed">
                    {currentStepData.description}
                  </p>
                )}
              </div>
            </div>

            {error && (
              <div className="mb-6 p-4 bg-red-50/80 backdrop-blur-sm border border-red-200/50 rounded-xl shadow-sm">
                <p className="text-red-700 font-medium">{error}</p>
              </div>
            )}

            {/* Step Component */}
            <div className="bg-white/60 backdrop-blur-sm rounded-xl border border-white/30 shadow-sm p-6">
              {StepComponent ? (
                <StepComponent
                  studentData={studentData}
                  onUpdateData={updateStepData}
                  onSaveProgress={(data) => saveStepProgress(currentStepData.step_name, 'in_progress', data)}
                />
              ) : (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Settings className="w-8 h-8 text-gray-400" />
                  </div>
                  <p className="text-gray-500 font-medium">This step is not yet implemented.</p>
                  <p className="text-sm text-gray-400 mt-1">Coming soon...</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer with glassy design */}
        <div className="border-t border-gray-100/50 p-6 bg-white/40 backdrop-blur-sm">
          <div className="flex items-center justify-between max-w-2xl mx-auto">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className={`flex items-center space-x-2 px-5 py-3 rounded-xl border backdrop-blur-sm transition-all font-medium ${
                currentStep === 0
                  ? 'text-gray-400 border-gray-200/50 bg-gray-50/50 cursor-not-allowed'
                  : 'text-gray-700 border-gray-300/50 bg-white/60 hover:bg-white/80 hover:border-gray-400/50 hover:shadow-sm'
              }`}
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>

            <div className="text-center px-4">
              <div className="text-sm font-semibold text-gray-800">
                {currentStepData?.display_name}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Step {currentStep + 1} of {totalSteps}
              </div>
            </div>

            <button
              onClick={handleNext}
              disabled={!canProceed() || isSaving}
              className={`flex items-center space-x-2 px-6 py-3 rounded-xl font-semibold transition-all backdrop-blur-sm ${
                canProceed() && !isSaving
                  ? 'bg-gradient-to-r from-red-800 to-red-700 text-white hover:from-red-900 hover:to-red-800 shadow-lg hover:shadow-xl transform hover:scale-[1.02]'
                  : 'bg-gray-200/60 text-gray-400 cursor-not-allowed border border-gray-200/50'
              }`}
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Saving...</span>
                </>
              ) : currentStep === totalSteps - 1 ? (
                <>
                  <span>Complete Setup</span>
                  <CheckCircle className="w-4 h-4" />
                </>
              ) : (
                <>
                  <span>Continue</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
          
          {!canProceed() && !isSaving && (
            <div className="mt-4 text-center max-w-2xl mx-auto">
              <div className="bg-amber-50/80 backdrop-blur-sm border border-amber-200/50 rounded-xl px-4 py-3 inline-block shadow-sm">
                <p className="text-sm text-amber-700 font-medium">
                  {getCurrentStepRequirementMessage()}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OnboardingWizard;