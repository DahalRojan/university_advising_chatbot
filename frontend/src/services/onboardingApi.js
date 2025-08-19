/**
 * Onboarding API Service
 * 
 * Handles all API calls related to student onboarding, course selection,
 * and profile management.
 */

import { CONFIG } from '../config/constants';

class OnboardingApiService {
  constructor() {
    this.baseUrl = CONFIG.API_BASE_URL;
  }

  /**
   * Get authentication headers with JWT token
   */
  getAuthHeaders() {
    const token = localStorage.getItem('jwt_token');
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
  }

  /**
   * Handle API response and errors
   */
  async handleResponse(response) {
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error ${response.status}: ${errorText}`);
    }
    return response.json();
  }

  // =========================================================
  // DEPARTMENT AND COURSE ENDPOINTS
  // =========================================================

  /**
   * Get all active departments
   */
  async getDepartments() {
    try {
      const response = await fetch(`${this.baseUrl}/api/onboarding/departments`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });
      return this.handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch departments:', error);
      throw error;
    }
  }

  /**
   * Search courses with filters
   */
  async searchCourses(searchParams = {}) {
    try {
      // Build payload excluding null/undefined values
      const payload = {
        level: searchParams.level || 'undergraduate',
        limit: searchParams.limit || 100,
      };
      
      // Only include optional fields if they have values
      if (searchParams.department) {
        payload.department = searchParams.department;
      }
      if (searchParams.searchTerm) {
        payload.search_term = searchParams.searchTerm;
      }
      if (typeof searchParams.credits === 'number') {
        payload.credits = searchParams.credits;
      }
      if (typeof searchParams.hasPrerequisites === 'boolean') {
        payload.has_prerequisites = searchParams.hasPrerequisites;
      }

      const response = await fetch(`${this.baseUrl}/api/onboarding/courses/search`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(payload),
      });
      return this.handleResponse(response);
    } catch (error) {
      console.error('Failed to search courses:', error);
      throw error;
    }
  }

  /**
   * Get courses by department
   */
  async getCoursesByDepartment(departmentCode, level = 'undergraduate') {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/onboarding/courses/department/${departmentCode}?level=${level}`,
        {
          method: 'GET',
          headers: this.getAuthHeaders(),
        }
      );
      return this.handleResponse(response);
    } catch (error) {
      console.error(`Failed to fetch courses for department ${departmentCode}:`, error);
      throw error;
    }
  }

  /**
   * Get courses filtered by level (for course selection interfaces)
   */
  async getCourses(level = 'undergraduate', limit = 500) {
    try {
      // Use the search endpoint with level filter
      // Note: Backend has a maximum limit of 500
      return await this.searchCourses({
        level: level, // This will filter courses by academic level
        limit: limit
      });
    } catch (error) {
      console.error('Failed to fetch courses:', error);
      throw error;
    }
  }

  // =========================================================
  // ONBOARDING WORKFLOW ENDPOINTS
  // =========================================================

  /**
   * Get all onboarding steps
   */
  async getOnboardingSteps() {
    try {
      const response = await fetch(`${this.baseUrl}/api/onboarding/steps`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });
      return this.handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch onboarding steps:', error);
      throw error;
    }
  }

  /**
   * Get student's onboarding progress
   */
  async getOnboardingProgress() {
    try {
      const response = await fetch(`${this.baseUrl}/api/onboarding/progress`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });
      return this.handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch onboarding progress:', error);
      throw error;
    }
  }

  /**
   * Update onboarding progress
   */
  async updateOnboardingProgress(stepName, status, data = null) {
    try {
      const response = await fetch(`${this.baseUrl}/api/onboarding/progress`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          step_name: stepName,
          status: status,
          data: data,
        }),
      });
      return this.handleResponse(response);
    } catch (error) {
      console.error('Failed to update onboarding progress:', error);
      throw error;
    }
  }

  // =========================================================
  // STUDENT PROFILE ENDPOINTS
  // =========================================================

  /**
   * Get student profile and dashboard data
   */
  async getStudentProfile() {
    try {
      const response = await fetch(`${this.baseUrl}/api/onboarding/profile`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });
      return this.handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch student profile:', error);
      throw error;
    }
  }

  /**
   * Create or update student profile
   */
  async updateStudentProfile(profileData) {
    try {
      console.log('📝 Updating student profile with data:', profileData);
      
      // Clean the profile data - convert empty strings to null for optional fields
      const cleanedData = { ...profileData };
      
      // Date fields that should be null if empty
      const dateFields = ['expected_graduation', 'date_of_birth'];
      dateFields.forEach(field => {
        if (cleanedData[field] === '' || cleanedData[field] === undefined) {
          cleanedData[field] = null;
        }
      });
      
      // Numeric fields that should be null if empty
      const numericFields = ['cumulative_gpa'];
      numericFields.forEach(field => {
        if (cleanedData[field] === '' || cleanedData[field] === undefined) {
          cleanedData[field] = null;
        }
      });
      
      // String fields that should be null if empty (optional fields)
      const optionalStringFields = [
        'student_id', 'preferred_name', 'phone', 'emergency_contact_name',
        'emergency_contact_phone', 'emergency_contact_relationship',
        'secondary_major', 'minor_program', 'concentration',
        'gender', 'ethnicity', 'citizenship_status'
      ];
      optionalStringFields.forEach(field => {
        if (cleanedData[field] === '' || cleanedData[field] === undefined) {
          cleanedData[field] = null;
        }
      });
      
      console.log('🧹 Cleaned profile data:', cleanedData);
      
      const response = await fetch(`${this.baseUrl}/api/onboarding/profile`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(cleanedData),
      });
      
      console.log('🔄 Profile update response status:', response.status);
      const result = await this.handleResponse(response);
      console.log('✅ Profile update successful:', result);
      
      return result;
    } catch (error) {
      console.error('❌ Failed to update student profile:', error);
      throw error;
    }
  }

  // =========================================================
  // COURSE INTERESTS ENDPOINTS
  // =========================================================

  /**
   * Get student's course interests
   */
  async getCourseInterests() {
    try {
      const response = await fetch(`${this.baseUrl}/api/onboarding/course-interests`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });
      return this.handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch course interests:', error);
      throw error;
    }
  }

  /**
   * Add course to student's interest list
   */
  async addCourseInterest(courseCode, interestData = {}) {
    try {
      const response = await fetch(`${this.baseUrl}/api/onboarding/course-interests`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          course_code: courseCode,
          interest_level: interestData.interestLevel || 'interested',
          planned_semester: interestData.plannedSemester || null,
          priority_order: interestData.priorityOrder || null,
          reason: interestData.reason || null,
        }),
      });
      return this.handleResponse(response);
    } catch (error) {
      console.error('Failed to add course interest:', error);
      throw error;
    }
  }

  // =========================================================
  // ACADEMIC GOALS ENDPOINTS
  // =========================================================

  /**
   * Get student's academic goals
   */
  async getAcademicGoals() {
    try {
      const response = await fetch(`${this.baseUrl}/api/onboarding/academic-goals`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });
      return this.handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch academic goals:', error);
      throw error;
    }
  }

  /**
   * Get student's academic history (completed and enrolled courses)
   */
  async getAcademicHistory() {
    try {
      const response = await fetch(`${this.baseUrl}/api/onboarding/academic-history`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });
      return this.handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch academic history:', error);
      throw error;
    }
  }

  /**
   * Get student's field interests from onboarding
   */
  async getFieldInterests() {
    try {
      const response = await fetch(`${this.baseUrl}/api/onboarding/field-interests`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });
      return this.handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch field interests:', error);
      throw error;
    }
  }

  /**
   * Add academic goal for student
   */
  async addAcademicGoal(goalData) {
    try {
      const response = await fetch(`${this.baseUrl}/api/onboarding/academic-goals`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          goal_type: goalData.goalType,
          goal_category: goalData.goalCategory || null,
          goal_description: goalData.goalDescription,
          target_completion_date: goalData.targetCompletionDate || null,
          priority_level: goalData.priorityLevel || 5,
        }),
      });
      return this.handleResponse(response);
    } catch (error) {
      console.error('Failed to add academic goal:', error);
      throw error;
    }
  }

  // =========================================================
  // UTILITY METHODS
  // =========================================================

  /**
   * Check if user has completed onboarding using dedicated endpoint
   */
  async checkOnboardingStatus() {
    try {
      const response = await fetch(`${this.baseUrl}/api/onboarding/status`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to check onboarding status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to check onboarding status:', error);
      // If user doesn't exist or error occurs, assume onboarding not complete
      return {
        isComplete: false,
        completionPercentage: 0,
        profileCompletionPercentage: 0,
      };
    }
  }

  /**
   * Complete/skip onboarding without finishing all steps
   */
  async completeOnboarding() {
    try {
      const response = await fetch(`${this.baseUrl}/api/onboarding/complete`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to complete onboarding: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      throw error;
    }
  }

  /**
   * Get onboarding dashboard data
   */
  async getOnboardingDashboard() {
    try {
      const [profile, steps, progress] = await Promise.all([
        this.getStudentProfile(),
        this.getOnboardingSteps(),
        this.getOnboardingProgress(),
      ]);

      return {
        profile,
        steps,
        progress,
        isOnboardingComplete: profile?.is_onboarding_complete || false,
      };
    } catch (error) {
      console.error('Failed to fetch onboarding dashboard:', error);
      throw error;
    }
  }
}

// Create and export a singleton instance
export const onboardingApi = new OnboardingApiService();
export default onboardingApi;