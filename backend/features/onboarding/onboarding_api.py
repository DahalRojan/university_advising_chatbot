#!/usr/bin/env python3
"""
Onboarding API Endpoints

This module provides FastAPI endpoints for the student onboarding system,
including course selection, profile management, and progress tracking.

Author: Claude Code
Purpose: Support student onboarding REST API
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from fastapi import HTTPException, Depends
from pydantic import BaseModel, Field, EmailStr
from .onboarding_db import OnboardingDatabaseManager
import logging

logger = logging.getLogger(__name__)

# =========================================================
# PYDANTIC MODELS FOR REQUEST/RESPONSE
# =========================================================

class CourseSearchRequest(BaseModel):
    level: str = Field(default="undergraduate", description="Course level: undergraduate or graduate")
    department: Optional[str] = Field(default=None, description="Department code filter")
    search_term: Optional[str] = Field(default=None, description="Search term for course title/description")
    credits: Optional[int] = Field(default=None, description="Filter by credit hours")
    has_prerequisites: Optional[bool] = Field(default=None, description="Filter by prerequisite presence")
    limit: Optional[int] = Field(default=100, ge=1, le=500, description="Maximum number of results")

class CourseResponse(BaseModel):
    code: str
    title: str
    credits: Optional[int]
    department_code: str
    department_name: str
    description: Optional[str]
    prerequisites: Optional[str]
    level: str
    course_number: int

class DepartmentResponse(BaseModel):
    code: str
    name: str
    course_count: int

class StudentProfileRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    
    student_type: Optional[str] = None  # 'current_gannon' or 'prospective'
    academic_level: Optional[str] = None
    enrollment_status: Optional[str] = None
    expected_graduation: Optional[datetime] = None
    
    primary_major: Optional[str] = None
    secondary_major: Optional[str] = None
    minor_program: Optional[str] = None
    concentration: Optional[str] = None
    
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    ethnicity: Optional[str] = None
    citizenship_status: Optional[str] = None

class StudentProfileResponse(BaseModel):
    user_email: str
    first_name: Optional[str]
    last_name: Optional[str]
    preferred_name: Optional[str]
    expected_graduation: Optional[datetime]
    student_type: Optional[str]
    academic_level: Optional[str]
    enrollment_status: Optional[str]
    primary_major: Optional[str]
    cumulative_gpa: Optional[float]
    profile_completion_percentage: int
    is_onboarding_complete: bool
    onboarding_progress_percentage: float
    active_recommendations_count: int
    course_interests_count: int
    created_at: datetime
    updated_at: datetime

class AcademicGoalRequest(BaseModel):
    goal_type: str = Field(description="Type: career, academic, skill, personal")
    goal_category: Optional[str] = None
    goal_description: str
    target_completion_date: Optional[datetime] = None
    priority_level: int = Field(default=5, ge=1, le=10)

class CourseInterestRequest(BaseModel):
    course_code: str
    interest_level: str = Field(default="interested", description="very_interested, interested, considering")
    planned_semester: Optional[str] = None
    priority_order: Optional[int] = None
    reason: Optional[str] = None

class OnboardingProgressRequest(BaseModel):
    step_name: str
    status: str = Field(description="not_started, in_progress, completed, skipped")
    data: Optional[Dict[str, Any]] = None

class OnboardingStepResponse(BaseModel):
    step_name: str
    display_name: str
    description: Optional[str]
    step_order: int
    is_required: bool
    estimated_time_minutes: int
    is_active: bool

class OnboardingProgressResponse(BaseModel):
    step_name: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    data_json: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

# =========================================================
# API ENDPOINT FUNCTIONS
# =========================================================

class OnboardingAPI:
    """Handles all onboarding-related API endpoints"""
    
    def __init__(self):
        self.db_manager = OnboardingDatabaseManager()
    
    # Course-related endpoints
    def get_departments(self) -> List[DepartmentResponse]:
        """Get all active departments"""
        try:
            departments = self.db_manager.get_departments()
            return [DepartmentResponse(**dept) for dept in departments]
        except Exception as e:
            logger.error(f"Failed to get departments: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve departments")
    
    def search_courses(self, search_request: CourseSearchRequest) -> List[CourseResponse]:
        """Search courses with comprehensive filters"""
        try:
            courses = self.db_manager.get_courses_by_level(
                level=search_request.level,
                department=search_request.department,
                search_term=search_request.search_term,
                credits=search_request.credits,
                has_prerequisites=search_request.has_prerequisites,
                limit=search_request.limit or 100
            )
            
            return [CourseResponse(**course) for course in courses]
        except Exception as e:
            logger.error(f"Failed to search courses: {e}")
            raise HTTPException(status_code=500, detail="Failed to search courses")
    
    def get_courses_by_department(self, department_code: str, level: str = "undergraduate") -> List[CourseResponse]:
        """Get all courses for a specific department"""
        try:
            courses = self.db_manager.get_courses_by_level(
                level=level,
                department=department_code
            )
            return [CourseResponse(**course) for course in courses]
        except Exception as e:
            logger.error(f"Failed to get courses for department {department_code}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve courses for {department_code}")
    
    # Student profile endpoints
    def create_or_update_student_profile(self, user_email: str, profile_data: StudentProfileRequest) -> bool:
        """Create or update a student profile"""
        try:
            # Convert Pydantic model to dict, excluding None values
            profile_dict = profile_data.dict(exclude_none=True)
            
            success = self.db_manager.create_student_profile(user_email, profile_dict)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to create/update profile")
            
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create/update profile for {user_email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to create/update student profile")
    
    def get_student_dashboard(self, user_email: str, user_data: Optional[dict] = None) -> Optional[StudentProfileResponse]:
        """Get comprehensive student dashboard data"""
        try:
            dashboard_data = self.db_manager.get_student_dashboard_data(user_email)
            
            if not dashboard_data:
                return None
            
            # Auto-populate missing first_name and last_name from Microsoft login if available
            if user_data and user_data.get('name') and (not dashboard_data.get('first_name') or not dashboard_data.get('last_name')):
                self._auto_populate_name_from_microsoft(user_email, user_data.get('name'), dashboard_data)
            
            return StudentProfileResponse(**dashboard_data)
        except Exception as e:
            logger.error(f"Failed to get dashboard for {user_email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve student dashboard")
    
    def _auto_populate_name_from_microsoft(self, user_email: str, display_name: str, dashboard_data: dict):
        """Auto-populate first_name and last_name from Microsoft display name"""
        try:
            # Split the display name into first and last name
            name_parts = display_name.strip().split()
            
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])  # Everything after first name
                
                logger.info(f"Auto-populating name for {user_email}: '{first_name}' '{last_name}' from Microsoft display name: '{display_name}'")
                
                # Update the database
                success = self.db_manager.update_student_profile_names(user_email, first_name, last_name)
                
                if success:
                    # Update the dashboard_data dict so it's reflected in the response
                    dashboard_data['first_name'] = first_name
                    dashboard_data['last_name'] = last_name
                    logger.info(f"Successfully auto-populated names for {user_email}")
                else:
                    logger.warning(f"Failed to update names in database for {user_email}")
            else:
                logger.info(f"Display name '{display_name}' for {user_email} doesn't contain enough parts to split into first/last name")
                
        except Exception as e:
            logger.error(f"Failed to auto-populate names for {user_email}: {e}")
    
    # Onboarding progress endpoints
    def update_onboarding_progress(self, user_email: str, progress_data: OnboardingProgressRequest) -> bool:
        """Update student onboarding progress"""
        try:
            success = self.db_manager.update_onboarding_progress(
                user_email=user_email,
                step_name=progress_data.step_name,
                status=progress_data.status,
                data=progress_data.data
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update onboarding progress")
            
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update onboarding progress for {user_email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update onboarding progress")
    
    def get_onboarding_steps(self) -> List[OnboardingStepResponse]:
        """Get all onboarding steps"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT step_name, display_name, description, step_order,
                               is_required, estimated_time_minutes, is_active
                        FROM onboarding_steps
                        WHERE is_active = true
                        ORDER BY step_order
                    """)
                    
                    steps = [dict(row) for row in cur.fetchall()]
                    return [OnboardingStepResponse(**step) for step in steps]
        except Exception as e:
            logger.error(f"Failed to get onboarding steps: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve onboarding steps")
    
    def get_student_onboarding_progress(self, user_email: str) -> List[OnboardingProgressResponse]:
        """Get student's onboarding progress"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT sop.step_name, sop.status, sop.started_at, sop.completed_at,
                               sop.data_json, sop.created_at, sop.updated_at
                        FROM student_onboarding_progress sop
                        JOIN onboarding_steps os ON sop.step_name = os.step_name
                        WHERE sop.student_email = %s
                        ORDER BY os.step_order
                    """, (user_email,))
                    
                    progress_records = []
                    for row in cur.fetchall():
                        record = dict(row)
                        # Convert datetime objects to ISO strings for JSON serialization
                        for key, value in record.items():
                            if isinstance(value, datetime):
                                record[key] = value
                        progress_records.append(OnboardingProgressResponse(**record))
                    
                    return progress_records
        except Exception as e:
            logger.error(f"Failed to get onboarding progress for {user_email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve onboarding progress")
    
    # Course interest endpoints
    def add_course_interest(self, user_email: str, interest_data: CourseInterestRequest) -> bool:
        """Add a course to student's interest list"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO student_course_interests (
                            student_email, course_code, interest_level, planned_semester,
                            priority_order, reason, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (student_email, course_code) DO UPDATE SET
                            interest_level = EXCLUDED.interest_level,
                            planned_semester = EXCLUDED.planned_semester,
                            priority_order = EXCLUDED.priority_order,
                            reason = EXCLUDED.reason,
                            updated_at = EXCLUDED.updated_at
                    """, (
                        user_email,
                        interest_data.course_code,
                        interest_data.interest_level,
                        interest_data.planned_semester,
                        interest_data.priority_order,
                        interest_data.reason,
                        datetime.utcnow(),
                        datetime.utcnow()
                    ))
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Failed to add course interest for {user_email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to add course interest")
    
    def get_student_course_interests(self, user_email: str) -> List[Dict]:
        """Get student's course interests"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT sci.course_code, sci.interest_level, sci.planned_semester,
                               sci.priority_order, sci.reason, c.title, c.credits,
                               c.department_code, d.name as department_name
                        FROM student_course_interests sci
                        LEFT JOIN courses c ON sci.course_code = c.code
                        LEFT JOIN departments d ON c.department_code = d.code
                        WHERE sci.student_email = %s
                        ORDER BY sci.priority_order NULLS LAST, sci.course_code
                    """, (user_email,))
                    
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get course interests for {user_email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve course interests")
    
    # Academic goals endpoints
    def add_academic_goal(self, user_email: str, goal_data: AcademicGoalRequest) -> bool:
        """Add an academic goal for the student"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO student_academic_goals (
                            student_email, goal_type, goal_category, goal_description,
                            target_completion_date, priority_level, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_email,
                        goal_data.goal_type,
                        goal_data.goal_category,
                        goal_data.goal_description,
                        goal_data.target_completion_date,
                        goal_data.priority_level,
                        datetime.utcnow(),
                        datetime.utcnow()
                    ))
                    
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Failed to add academic goal for {user_email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to add academic goal")
    
    def get_student_academic_goals(self, user_email: str) -> List[Dict]:
        """Get student's academic goals"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT goal_type, goal_category, goal_description,
                               target_completion_date, priority_level, is_achieved,
                               progress_notes, created_at, updated_at
                        FROM student_academic_goals
                        WHERE student_email = %s
                        ORDER BY priority_level DESC, created_at ASC
                    """, (user_email,))
                    
                    goals = []
                    for row in cur.fetchall():
                        goal = dict(row)
                        # Convert datetime objects for JSON serialization
                        for key, value in goal.items():
                            if isinstance(value, datetime):
                                goal[key] = value.isoformat()
                        goals.append(goal)
                    
                    return goals
        except Exception as e:
            logger.error(f"Failed to get academic goals for {user_email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve academic goals")

    def get_student_academic_history(self, user_email: str) -> List[Dict]:
        """Get student's academic history (completed and enrolled courses)"""
        try:
            print(f"🔍 [DEBUG] Getting academic history for user: {user_email}")
            print(f"🔍 [DEBUG] Database URL: {self.db_manager.database_url}")
            
            with self.db_manager.get_connection() as conn:
                print(f"🔍 [DEBUG] Connected to database successfully")
                with conn.cursor() as cur:
                    # First test a simple query
                    cur.execute("SELECT current_database(), current_user")
                    db_info = cur.fetchone()
                    print(f"🔍 [DEBUG] Database info: {dict(db_info)}")
                    
                    # Test if the table exists
                    cur.execute("""
                        SELECT COUNT(*) as total_records 
                        FROM student_academic_history
                    """)
                    total_count = cur.fetchone()
                    print(f"🔍 [DEBUG] Total records in student_academic_history: {dict(total_count)}")
                    
                    # Now run the actual query
                    cur.execute("""
                        SELECT course_code, course_title, institution, semester, year,
                               grade, grade_points, credits_earned, status, is_transfer_credit,
                               created_at
                        FROM student_academic_history
                        WHERE student_email = %s
                        ORDER BY year DESC, semester DESC, course_code
                    """, (user_email,))
                    
                    rows = cur.fetchall()
                    print(f"🔍 [DEBUG] Query returned {len(rows)} rows for {user_email}")
                    
                    history = []
                    for row in rows:
                        record = dict(row)
                        print(f"🔍 [DEBUG] Processing row: {record}")
                        # Convert datetime objects for JSON serialization
                        for key, value in record.items():
                            if isinstance(value, datetime):
                                record[key] = value.isoformat()
                        history.append(record)
                    
                    print(f"🔍 [DEBUG] Final history list: {len(history)} courses")
                    return history
        except Exception as e:
            logger.error(f"Failed to get academic history for {user_email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve academic history")

    def get_student_field_interests(self, user_email: str) -> List[str]:
        """Get student's field interests from onboarding data"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get field interests from onboarding progress data
                    cur.execute("""
                        SELECT data_json
                        FROM student_onboarding_progress
                        WHERE student_email = %s AND step_name = 'field_interests' AND data_json IS NOT NULL
                    """, (user_email,))
                    
                    result = cur.fetchone()
                    if result and result['data_json']:
                        field_interests = result['data_json'].get('field_interests', [])
                        career_interests = result['data_json'].get('career_interests', [])
                        
                        # Combine and filter out empty strings
                        all_interests = []
                        if isinstance(field_interests, list):
                            all_interests.extend([interest for interest in field_interests if interest])
                        if isinstance(career_interests, list):
                            all_interests.extend([interest for interest in career_interests if interest])
                        
                        return all_interests
                    
                    return []
        except Exception as e:
            logger.error(f"Failed to get field interests for {user_email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve field interests")

# =========================================================
# DEPENDENCY FUNCTIONS
# =========================================================

def get_onboarding_api() -> OnboardingAPI:
    """Dependency function to get OnboardingAPI instance"""
    return OnboardingAPI()

# =========================================================
# UTILITY FUNCTIONS
# =========================================================

def validate_user_email(user_email: str) -> str:
    """Validate and return user email"""
    if not user_email or "@" not in user_email:
        raise HTTPException(status_code=400, detail="Valid email address is required")
    return user_email.lower().strip()

def validate_course_code(course_code: str) -> str:
    """Validate course code format"""
    if not course_code or len(course_code.strip()) < 3:
        raise HTTPException(status_code=400, detail="Valid course code is required")
    return course_code.upper().strip()