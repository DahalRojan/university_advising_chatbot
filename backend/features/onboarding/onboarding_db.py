#!/usr/bin/env python3
"""
Onboarding Database Management Module

This module handles:
- Database schema creation and migration
- Course data ingestion from extracted JSON
- Student profile management
- Onboarding progress tracking

Author: Claude Code
Purpose: Support student onboarding system
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../configs/.env"))

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required. Please set up PostgreSQL connection.")

class OnboardingDatabaseManager:
    """Manages onboarding database operations"""
    
    def __init__(self):
        self.database_url = DATABASE_URL
        logger.info("Initialized OnboardingDatabaseManager")
    
    def get_connection(self):
        """Get PostgreSQL database connection"""
        try:
            conn = psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def setup_onboarding_schema(self):
        """Use the dedicated schema setup script"""
        
        try:
            # Import and run the schema setup
            import subprocess
            import sys
            
            # Run the setup script
            result = subprocess.run(
                [sys.executable, "-m", "src.setup_onboarding_schema"],
                cwd=os.path.dirname(os.path.dirname(__file__)),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("Onboarding schema setup completed successfully")
                return True
            else:
                logger.error(f"Schema setup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to setup onboarding schema: {e}")
            return False
    
    def ingest_course_data(self, courses_json_file: str = "data/extracted_courses.json"):
        """Ingest course data from the extracted JSON file"""
        
        json_path = os.path.join(os.path.dirname(__file__), "..", courses_json_file)
        
        if not os.path.exists(json_path):
            logger.error(f"Course data file not found: {json_path}")
            return False
        
        try:
            # Load course data
            with open(json_path, 'r', encoding='utf-8') as f:
                course_data = json.load(f)
            
            courses = course_data.get('courses', [])
            departments = set()
            
            logger.info(f"Loading {len(courses)} courses from {courses_json_file}")
            
            # Extract unique departments
            for course in courses:
                if course.get('department'):
                    departments.add(course['department'])
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    
                    # First, insert departments
                    logger.info(f"Inserting {len(departments)} departments...")
                    
                    for dept_code in departments:
                        try:
                            cur.execute("""
                                INSERT INTO departments (code, name, is_active, created_at)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (code) DO UPDATE SET
                                    name = EXCLUDED.name,
                                    is_active = EXCLUDED.is_active,
                                    updated_at = CURRENT_TIMESTAMP
                            """, (
                                dept_code,
                                f"{dept_code} Department",  # Generic name for now
                                True,
                                datetime.utcnow()
                            ))
                        except Exception as e:
                            logger.warning(f"Failed to insert department {dept_code}: {e}")
                    
                    conn.commit()
                    logger.info("Departments inserted successfully")
                    
                    # Insert courses
                    logger.info("Inserting courses...")
                    successful_inserts = 0
                    failed_inserts = 0
                    
                    for course in courses:
                        try:
                            # Validate required fields
                            if not course.get('code') or not course.get('department'):
                                logger.warning(f"Skipping invalid course: {course}")
                                failed_inserts += 1
                                continue
                            
                            # Determine proper title - use name if it's not just the course code
                            course_name = course.get('name', course.get('code'))
                            course_code = course.get('code')
                            
                            # If name is same as code, set title to None to indicate missing descriptive name
                            course_title = course_name if course_name != course_code else None
                            
                            cur.execute("""
                                INSERT INTO courses (
                                    code, department_code, course_number, title, 
                                    description, credits, level, prerequisites,
                                    source_catalog, is_active, created_at
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (code) DO UPDATE SET
                                    title = EXCLUDED.title,
                                    description = EXCLUDED.description,
                                    credits = EXCLUDED.credits,
                                    level = EXCLUDED.level,
                                    prerequisites = EXCLUDED.prerequisites,
                                    source_catalog = EXCLUDED.source_catalog,
                                    is_active = EXCLUDED.is_active,
                                    updated_at = CURRENT_TIMESTAMP
                            """, (
                                course.get('code'),
                                course.get('department'),
                                course.get('number', ''),
                                course_title,
                                course.get('description'),
                                course.get('credits'),
                                course.get('level', 'undergraduate'),
                                course.get('prerequisites'),
                                course.get('source_file'),
                                True,
                                datetime.utcnow()
                            ))
                            
                            successful_inserts += 1
                            
                        except Exception as e:
                            logger.warning(f"Failed to insert course {course.get('code', 'unknown')}: {e}")
                            failed_inserts += 1
                    
                    conn.commit()
                    
                    logger.info(f"Course ingestion completed:")
                    logger.info(f"  Successfully inserted: {successful_inserts} courses")
                    logger.info(f"  Failed insertions: {failed_inserts} courses")
                    logger.info(f"  Total processed: {len(courses)} courses")
                    
                    # Query final statistics
                    cur.execute("SELECT COUNT(*) FROM departments WHERE is_active = true")
                    dept_count = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM courses WHERE is_active = true")
                    course_count = cur.fetchone()[0]
                    
                    cur.execute("""
                        SELECT level, COUNT(*) 
                        FROM courses 
                        WHERE is_active = true 
                        GROUP BY level
                    """)
                    level_counts = dict(cur.fetchall())
                    
                    logger.info(f"Final database statistics:")
                    logger.info(f"  Active departments: {dept_count}")
                    logger.info(f"  Active courses: {course_count}")
                    for level, count in level_counts.items():
                        logger.info(f"  {level.title()} courses: {count}")
                    
                    return True
            
        except Exception as e:
            logger.error(f"Failed to ingest course data: {e}")
            return False
    
    def create_student_profile(self, user_email: str, profile_data: Dict[str, Any]) -> bool:
        """Create or update a student profile"""
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO student_profiles (
                            user_email, first_name, last_name, preferred_name,
                            phone, student_type, academic_level, enrollment_status, 
                            degree_program, primary_major, secondary_major, minor_program, concentration,
                            expected_graduation, is_active, created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_email) DO UPDATE SET
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            preferred_name = EXCLUDED.preferred_name,
                            phone = EXCLUDED.phone,
                            student_type = EXCLUDED.student_type,
                            academic_level = EXCLUDED.academic_level,
                            enrollment_status = EXCLUDED.enrollment_status,
                            degree_program = EXCLUDED.degree_program,
                            primary_major = EXCLUDED.primary_major,
                            secondary_major = EXCLUDED.secondary_major,
                            minor_program = EXCLUDED.minor_program,
                            concentration = EXCLUDED.concentration,
                            expected_graduation = EXCLUDED.expected_graduation,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        user_email,
                        profile_data.get('first_name'),
                        profile_data.get('last_name'),
                        profile_data.get('preferred_name'),
                        profile_data.get('phone'),
                        profile_data.get('student_type'),
                        profile_data.get('academic_level'),
                        profile_data.get('enrollment_status'),
                        profile_data.get('degree_program'),
                        profile_data.get('primary_major'),
                        profile_data.get('secondary_major'),
                        profile_data.get('minor_program'),
                        profile_data.get('concentration'),
                        profile_data.get('expected_graduation'),
                        True,
                        datetime.utcnow()
                    ))
                    
                    conn.commit()
                    
            logger.info(f"Student profile created/updated for {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create student profile for {user_email}: {e}")
            return False
    
    def update_onboarding_progress(self, user_email: str, step_name: str, 
                                 status: str, data: Optional[Dict] = None) -> bool:
        """Update student onboarding progress and trigger data transfer on completion"""
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Determine timestamps based on status
                    started_at = None
                    completed_at = None
                    
                    if status == 'in_progress':
                        started_at = datetime.utcnow()
                    elif status == 'completed':
                        completed_at = datetime.utcnow()
                    
                    # Update onboarding progress
                    cur.execute("""
                        INSERT INTO student_onboarding_progress (
                            student_email, step_name, status, started_at, 
                            completed_at, data_json, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (student_email, step_name) DO UPDATE SET
                            status = EXCLUDED.status,
                            started_at = COALESCE(student_onboarding_progress.started_at, EXCLUDED.started_at),
                            completed_at = EXCLUDED.completed_at,
                            data_json = EXCLUDED.data_json,
                            updated_at = EXCLUDED.updated_at
                    """, (
                        user_email,
                        step_name,
                        status,
                        started_at,
                        completed_at,
                        json.dumps(data) if data else None,
                        datetime.utcnow(),
                        datetime.utcnow()
                    ))
                    
                    # If step is completed, trigger data transfer
                    if status == 'completed':
                        self._transfer_step_data_to_profile(cur, user_email, step_name, data)
                        
                        # Check if all required steps are completed and transfer additional data
                        if self._check_onboarding_completion(cur, user_email):
                            self._complete_onboarding_process(cur, user_email)
                    
                    conn.commit()
                    
            logger.info(f"Onboarding progress updated for {user_email}: {step_name} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update onboarding progress for {user_email}: {e}")
            return False
    
    def _transfer_step_data_to_profile(self, cur, user_email: str, step_name: str, data: Optional[Dict] = None):
        """Transfer specific step data to appropriate tables"""
        
        if not data:
            return
            
        try:
            # Transfer based on step type
            if step_name == 'student_type':
                self._transfer_student_type_data(cur, user_email, data)
            elif step_name == 'academic_info':
                self._transfer_academic_info_data(cur, user_email, data)
            elif step_name in ['current_goals', 'prospective_goals', 'academic_goals']:
                self._transfer_goals_data(cur, user_email, data)
            elif step_name == 'course_interests':
                self._transfer_course_interests_data(cur, user_email, data)
            elif step_name == 'current_courses':
                self._transfer_course_history_data(cur, user_email, data)
            elif step_name == 'field_interests':
                self._transfer_field_interests_data(cur, user_email, data)
                
        except Exception as e:
            logger.error(f"Failed to transfer step data for {step_name}: {e}")
    
    def _transfer_student_type_data(self, cur, user_email: str, data: Dict):
        """Transfer student type data to profile"""
        
        student_type = data.get('student_type')
        if student_type:
            cur.execute("""
                UPDATE student_profiles 
                SET student_type = %s, updated_at = %s
                WHERE user_email = %s
            """, (student_type, datetime.utcnow(), user_email))
    
    def _transfer_academic_info_data(self, cur, user_email: str, data: Dict):
        """Transfer academic information to profile"""
        
        updates = []
        values = []
        
        # Map data fields to database columns
        field_mapping = {
            'academic_level': 'academic_level',
            'enrollment_status': 'enrollment_status', 
            'student_id': 'student_id',
            'primary_major': 'primary_major',
            'degree_program': 'degree_program',
            'expected_graduation': 'expected_graduation'
        }
        
        for data_key, db_column in field_mapping.items():
            if data_key in data and data[data_key]:
                if data_key == 'expected_graduation' and data[data_key] != '':
                    try:
                        # Handle date conversion
                        date_value = datetime.fromisoformat(data[data_key].replace('Z', '+00:00'))
                        updates.append(f"{db_column} = %s")
                        values.append(date_value)
                    except:
                        continue
                elif data_key == 'student_id' and data[data_key] != '':
                    updates.append(f"{db_column} = %s")
                    values.append(data[data_key])
                elif data[data_key] != '':
                    updates.append(f"{db_column} = %s")
                    values.append(data[data_key])
        
        if updates:
            updates.append("updated_at = %s")
            values.append(datetime.utcnow())
            values.append(user_email)
            
            query = f"UPDATE student_profiles SET {', '.join(updates)} WHERE user_email = %s"
            cur.execute(query, values)
    
    def _transfer_goals_data(self, cur, user_email: str, data: Dict):
        """Transfer goals data to academic goals table"""
        
        goals = data.get('goals', [])
        if not goals:
            return
            
        for goal in goals:
            cur.execute("""
                INSERT INTO student_academic_goals (
                    student_email, goal_type, goal_category, goal_description,
                    target_completion_date, priority_level, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                user_email,
                goal.get('goal_type', 'academic'),
                goal.get('goal_category'),
                goal.get('goal_description', ''),
                goal.get('target_completion_date'),
                goal.get('priority_level', 5),
                datetime.utcnow(),
                datetime.utcnow()
            ))
    
    def _transfer_course_interests_data(self, cur, user_email: str, data: Dict):
        """Transfer course interests to course interests table"""
        
        course_interests = data.get('course_interests', [])
        if not course_interests:
            return
            
        for interest in course_interests:
            cur.execute("""
                INSERT INTO student_course_interests (
                    student_email, course_code, interest_level, planned_semester,
                    priority_order, reason, notes, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (student_email, course_code) DO UPDATE SET
                    interest_level = EXCLUDED.interest_level,
                    planned_semester = EXCLUDED.planned_semester,
                    priority_order = EXCLUDED.priority_order,
                    reason = EXCLUDED.reason,
                    notes = EXCLUDED.notes,
                    updated_at = EXCLUDED.updated_at
            """, (
                user_email,
                interest.get('course_code'),
                interest.get('interest_level', 'interested'),
                interest.get('planned_semester'),
                interest.get('priority_order'),
                interest.get('reason'),
                interest.get('notes'),
                datetime.utcnow(),
                datetime.utcnow()
            ))
    
    def _transfer_course_history_data(self, cur, user_email: str, data: Dict):
        """Transfer course history to academic history table"""
        
        # Transfer completed courses
        completed_courses = data.get('completed_courses', [])
        for course in completed_courses:
            cur.execute("""
                INSERT INTO student_academic_history (
                    student_email, course_code, course_title, institution,
                    semester, year, grade, credits_earned, status, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                user_email,
                course.get('code'),
                course.get('title'),
                'Gannon University',
                course.get('semester'),
                course.get('year'),
                course.get('grade'),
                course.get('credits'),
                'completed',
                datetime.utcnow()
            ))
        
        # Transfer enrolled courses
        enrolled_courses = data.get('enrolled_courses', [])
        for course in enrolled_courses:
            cur.execute("""
                INSERT INTO student_academic_history (
                    student_email, course_code, course_title, institution,
                    semester, year, credits_earned, status, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                user_email,
                course.get('code'),
                course.get('title'),
                'Gannon University',
                course.get('semester'),
                course.get('year'),
                course.get('credits'),
                'enrolled',
                datetime.utcnow()
            ))
    
    def _transfer_field_interests_data(self, cur, user_email: str, data: Dict):
        """Transfer field interests as academic goals"""
        
        field_interests = data.get('field_interests', [])
        career_interests = data.get('career_interests', [])
        
        # Convert field interests to academic goals
        for field in field_interests:
            cur.execute("""
                INSERT INTO student_academic_goals (
                    student_email, goal_type, goal_category, goal_description,
                    priority_level, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                user_email,
                'academic',
                'field_interest',
                f'Explore and develop expertise in {field}',
                5,
                datetime.utcnow(),
                datetime.utcnow()
            ))
        
        # Convert career interests to career goals
        for career in career_interests:
            if career:  # Skip empty strings
                cur.execute("""
                    INSERT INTO student_academic_goals (
                        student_email, goal_type, goal_category, goal_description,
                        priority_level, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    user_email,
                    'career',
                    'career_interest',
                    f'Pursue career opportunities in {career}',
                    5,
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
    
    def _check_onboarding_completion(self, cur, user_email: str) -> bool:
        """Check if all required onboarding steps are completed"""
        
        cur.execute("""
            SELECT COUNT(*) as completed_count
            FROM student_onboarding_progress sop
            JOIN onboarding_steps os ON sop.step_name = os.step_name
            WHERE sop.student_email = %s 
                AND sop.status = 'completed'
                AND os.is_required = true
                AND os.is_active = true
        """, (user_email,))
        
        completed_count = cur.fetchone()['completed_count']
        
        cur.execute("""
            SELECT COUNT(*) as required_count
            FROM onboarding_steps
            WHERE is_required = true AND is_active = true
        """, ())
        
        required_count = cur.fetchone()['required_count']
        
        return completed_count >= required_count
    
    def _complete_onboarding_process(self, cur, user_email: str):
        """Complete the onboarding process and update profile"""
        
        # Mark onboarding as complete
        cur.execute("""
            UPDATE student_profiles 
            SET is_onboarding_complete = true, updated_at = %s
            WHERE user_email = %s
        """, (datetime.utcnow(), user_email))
        
        # Update profile completion percentage
        self._update_profile_completion_percentage(cur, user_email)
        
        logger.info(f"Onboarding completed for {user_email}")
    
    def _update_profile_completion_percentage(self, cur, user_email: str):
        """Calculate and update profile completion percentage"""
        
        cur.execute("""
            UPDATE student_profiles sp
            SET profile_completion_percentage = (
                SELECT ROUND(
                    (CASE WHEN sp.first_name IS NOT NULL THEN 10 ELSE 0 END +
                     CASE WHEN sp.last_name IS NOT NULL THEN 10 ELSE 0 END +
                     CASE WHEN sp.student_type IS NOT NULL THEN 15 ELSE 0 END +
                     CASE WHEN sp.academic_level IS NOT NULL THEN 10 ELSE 0 END +
                     CASE WHEN sp.enrollment_status IS NOT NULL THEN 10 ELSE 0 END +
                     CASE WHEN sp.degree_program IS NOT NULL THEN 20 ELSE 0 END +
                     CASE WHEN sp.primary_major IS NOT NULL THEN 10 ELSE 0 END +
                     CASE WHEN sp.expected_graduation IS NOT NULL THEN 10 ELSE 0 END +
                     CASE WHEN sp.phone IS NOT NULL THEN 5 ELSE 0 END +
                     CASE WHEN sp.preferred_name IS NOT NULL THEN 5 ELSE 0 END)::numeric
                )
            ),
            updated_at = %s
            WHERE user_email = %s
        """, (datetime.utcnow(), user_email))
    
    def get_student_dashboard_data(self, user_email: str) -> Optional[Dict]:
        """Get comprehensive dashboard data for a student"""
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get student dashboard view
                    cur.execute("""
                        SELECT * FROM student_dashboard WHERE user_email = %s
                    """, (user_email,))
                    
                    dashboard_data = cur.fetchone()
                    
                    if not dashboard_data:
                        return None
                    
                    # Convert to dict for JSON serialization
                    result = dict(dashboard_data)
                    
                    # Convert datetime objects to ISO strings
                    for key, value in result.items():
                        if isinstance(value, datetime):
                            result[key] = value.isoformat()
                    
                    return result
                    
        except Exception as e:
            logger.error(f"Failed to get dashboard data for {user_email}: {e}")
            return None
    
    def update_student_profile_names(self, user_email: str, first_name: str, last_name: str) -> bool:
        """Update first_name and last_name in student_profiles table"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE student_profiles 
                        SET first_name = %s,
                            last_name = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_email = %s
                    """, (first_name, last_name, user_email))
                    
                    affected_rows = cur.rowcount
                    conn.commit()
                    
                    logger.info(f"Updated {affected_rows} student profile names for {user_email}")
                    return affected_rows > 0
                    
        except Exception as e:
            logger.error(f"Failed to update student profile names for {user_email}: {e}")
            return False
    
    def get_courses_by_level(self, level: str = 'undergraduate', 
                           department: Optional[str] = None,
                           search_term: Optional[str] = None,
                           credits: Optional[int] = None,
                           has_prerequisites: Optional[bool] = None,
                           limit: int = 500) -> List[Dict]:
        """Get courses filtered by level, department, search term, credits, and prerequisites"""
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    
                    # Build dynamic query with comprehensive filtering
                    where_conditions = ["c.is_active = true", "c.level = %s"]
                    params = [level]
                    
                    if department:
                        where_conditions.append("c.department_code = %s")
                        params.append(department)
                    
                    if search_term:
                        # Enhanced search across multiple fields
                        where_conditions.append("""
                            (c.title ILIKE %s OR c.code ILIKE %s OR c.description ILIKE %s 
                             OR c.department_name ILIKE %s)
                        """)
                        search_pattern = f"%{search_term}%"
                        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
                    
                    if credits is not None:
                        where_conditions.append("c.credits = %s")
                        params.append(credits)
                    
                    if has_prerequisites is not None:
                        if has_prerequisites:
                            where_conditions.append("c.prerequisites IS NOT NULL AND LENGTH(c.prerequisites) > 0")
                        else:
                            where_conditions.append("(c.prerequisites IS NULL OR LENGTH(c.prerequisites) = 0)")
                    
                    query = f"""
                        SELECT c.code, 
                               c.title,
                               c.credits, 
                               c.department_code,
                               c.department_name,
                               c.description, 
                               c.prerequisites,
                               c.level,
                               c.course_number
                        FROM courses c
                        WHERE {' AND '.join(where_conditions)}
                        ORDER BY c.department_code, c.course_number
                        LIMIT %s
                    """
                    
                    params.append(limit)
                    cur.execute(query, params)
                    courses = [dict(row) for row in cur.fetchall()]
                    
                    # Clean up any null titles
                    for course in courses:
                        if not course.get('title'):
                            course['title'] = course['code']
                    
                    return courses
                    
        except Exception as e:
            logger.error(f"Failed to get courses: {e}")
            return []
    
    def get_departments(self) -> List[Dict]:
        """Get all active departments"""
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT d.code, d.name, COUNT(c.id) as course_count
                        FROM departments d
                        LEFT JOIN courses c ON d.code = c.department_code AND c.is_active = true
                        WHERE d.is_active = true
                        GROUP BY d.code, d.name
                        ORDER BY d.code
                    """)
                    
                    return [dict(row) for row in cur.fetchall()]
                    
        except Exception as e:
            logger.error(f"Failed to get departments: {e}")
            return []

def main():
    """Main function to set up the onboarding database"""
    
    print("Setting up Gannon University Onboarding Database")
    print("=" * 60)
    
    try:
        # Initialize database manager
        db_manager = OnboardingDatabaseManager()
        
        # Step 1: Setup schema
        print("\n1. Setting up database schema...")
        if db_manager.setup_onboarding_schema():
            print("   Schema setup completed successfully")
        else:
            print("   Schema setup failed")
            return False
        
        # Step 2: Ingest course data
        print("\n2. Ingesting course data...")
        if db_manager.ingest_course_data():
            print("   Course data ingestion completed successfully")
        else:
            print("   Course data ingestion failed")
            return False
        
        # Step 3: Verify setup
        print("\n3. Verifying setup...")
        departments = db_manager.get_departments()
        courses = db_manager.get_courses_by_level('undergraduate')
        
        print(f"   Departments loaded: {len(departments)}")
        print(f"   Undergraduate courses: {len(courses)}")
        
        if departments and courses:
            print("\nOnboarding database setup completed successfully!")
            print(f"Ready to support student onboarding for {len(courses)} courses across {len(departments)} departments")
            return True
        else:
            print("\nSetup verification failed - no data found")
            return False
    
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        print(f"\nDatabase setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)