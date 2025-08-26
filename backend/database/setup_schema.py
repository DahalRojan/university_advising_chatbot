#!/usr/bin/env python3
"""
Simple onboarding schema setup script

This creates the essential tables for the onboarding system step by step.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../config/.env"))

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def setup_onboarding_tables():
    """Set up the core onboarding tables"""
    
    print("Setting up onboarding database tables...")
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            
            # 1. Departments table
            print("Creating departments table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS departments (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(10) UNIQUE NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    college VARCHAR(100),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. Courses table (updated with comprehensive fields)
            print("Creating courses table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(20) UNIQUE NOT NULL,
                    department_code VARCHAR(10) NOT NULL,
                    department_name VARCHAR(200),
                    course_number INTEGER NOT NULL,
                    title VARCHAR(300),
                    description TEXT,
                    credits INTEGER,
                    level VARCHAR(20) NOT NULL, -- 'graduate' or 'undergraduate'
                    prerequisites TEXT,
                    is_active BOOLEAN DEFAULT true,
                    source_catalog VARCHAR(100) DEFAULT 'comprehensive_pdf',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Indexes for better search performance
                    CONSTRAINT courses_code_unique UNIQUE(code),
                    CONSTRAINT courses_level_check CHECK (level IN ('graduate', 'undergraduate'))
                )
            """)
            
            # Create indexes for better performance
            cur.execute("CREATE INDEX IF NOT EXISTS idx_courses_department_code ON courses(department_code)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_courses_level ON courses(level)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_courses_credits ON courses(credits)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_courses_title ON courses USING gin(to_tsvector('english', title))")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_courses_description ON courses USING gin(to_tsvector('english', description))")
            
            # 3. Student profiles table
            print("Creating student_profiles table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS student_profiles (
                    id SERIAL PRIMARY KEY,
                    user_email VARCHAR(255) UNIQUE NOT NULL,
                    student_id VARCHAR(50),
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    preferred_name VARCHAR(100),
                    phone VARCHAR(20),
                    emergency_contact_name VARCHAR(200),
                    emergency_contact_phone VARCHAR(20),
                    emergency_contact_relationship VARCHAR(100),
                    
                    student_type VARCHAR(30), -- 'current_gannon' or 'prospective'
                    academic_level VARCHAR(30),
                    enrollment_status VARCHAR(30),
                    expected_graduation TIMESTAMP,
                    cumulative_gpa DECIMAL(3,2),
                    
                    primary_major VARCHAR(100),
                    secondary_major VARCHAR(100),
                    minor_program VARCHAR(100),
                    concentration VARCHAR(100),
                    
                    date_of_birth DATE,
                    gender VARCHAR(30),
                    ethnicity VARCHAR(100),
                    citizenship_status VARCHAR(50),
                    
                    is_onboarding_complete BOOLEAN DEFAULT false,
                    profile_completion_percentage INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT true,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 4. Academic goals table
            print("Creating student_academic_goals table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS student_academic_goals (
                    id SERIAL PRIMARY KEY,
                    student_email VARCHAR(255) NOT NULL,
                    goal_type VARCHAR(50) NOT NULL,
                    goal_category VARCHAR(100),
                    goal_description TEXT NOT NULL,
                    target_completion_date DATE,
                    priority_level INTEGER DEFAULT 5,
                    is_achieved BOOLEAN DEFAULT false,
                    progress_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 5. Course interests table
            print("Creating student_course_interests table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS student_course_interests (
                    id SERIAL PRIMARY KEY,
                    student_email VARCHAR(255) NOT NULL,
                    course_code VARCHAR(20) NOT NULL,
                    interest_level VARCHAR(20) DEFAULT 'interested',
                    planned_semester VARCHAR(20),
                    priority_order INTEGER,
                    reason TEXT,
                    is_prerequisite_met BOOLEAN DEFAULT false,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 6. Academic history table
            print("Creating student_academic_history table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS student_academic_history (
                    id SERIAL PRIMARY KEY,
                    student_email VARCHAR(255) NOT NULL,
                    course_code VARCHAR(20),
                    course_title VARCHAR(300),
                    institution VARCHAR(200) DEFAULT 'Gannon University',
                    semester VARCHAR(20),
                    year INTEGER,
                    grade VARCHAR(5),
                    grade_points DECIMAL(3,2),
                    credits_earned INTEGER,
                    is_transfer_credit BOOLEAN DEFAULT false,
                    status VARCHAR(20) DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 7. Onboarding steps table
            print("Creating onboarding_steps table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS onboarding_steps (
                    id SERIAL PRIMARY KEY,
                    step_name VARCHAR(100) UNIQUE NOT NULL,
                    display_name VARCHAR(200) NOT NULL,
                    description TEXT,
                    step_order INTEGER NOT NULL,
                    is_required BOOLEAN DEFAULT true,
                    estimated_time_minutes INTEGER DEFAULT 5,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 8. Student onboarding progress table
            print("Creating student_onboarding_progress table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS student_onboarding_progress (
                    id SERIAL PRIMARY KEY,
                    student_email VARCHAR(255) NOT NULL,
                    step_name VARCHAR(100) NOT NULL,
                    status VARCHAR(20) DEFAULT 'not_started',
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    data_json JSONB,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 9. Student recommendations table
            print("Creating student_recommendations table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS student_recommendations (
                    id SERIAL PRIMARY KEY,
                    student_email VARCHAR(255) NOT NULL,
                    recommendation_type VARCHAR(50) NOT NULL,
                    title VARCHAR(300) NOT NULL,
                    description TEXT NOT NULL,
                    reasoning TEXT,
                    confidence_score DECIMAL(3,2),
                    priority_level INTEGER DEFAULT 5,
                    category VARCHAR(100),
                    
                    recommended_course_code VARCHAR(20),
                    recommended_semester VARCHAR(20),
                    action_url TEXT,
                    
                    status VARCHAR(20) DEFAULT 'active',
                    viewed_at TIMESTAMP,
                    acted_on_at TIMESTAMP,
                    dismissed_at TIMESTAMP,
                    
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    created_by VARCHAR(100) DEFAULT 'ai_system'
                )
            """)
            
            # 10. Create indexes
            print("Creating indexes...")
            
            # Departments indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_departments_active ON departments(is_active)")
            
            # Courses indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_courses_code ON courses(code)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_courses_department ON courses(department_code)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_courses_level ON courses(level)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_courses_active ON courses(is_active)")
            
            # Student profiles indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_student_profiles_email ON student_profiles(user_email)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_student_profiles_level ON student_profiles(academic_level)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_student_profiles_onboarding ON student_profiles(is_onboarding_complete)")
            
            # Other important indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_student_goals_email ON student_academic_goals(student_email)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_course_interests_student ON student_course_interests(student_email)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_course_interests_course ON student_course_interests(course_code)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_onboarding_progress_student ON student_onboarding_progress(student_email)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_student ON student_recommendations(student_email)")
            
            # 11. Insert sample onboarding steps
            print("Inserting onboarding steps...")
            onboarding_steps = [
                # Universal steps
                ('student_type', 'Student Type', 'Are you a current Gannon student or prospective student?', 1, True, 2),
                ('academic_info', 'Academic Information', 'Your academic level and enrollment status', 2, True, 3),
                
                # Current Gannon student steps
                ('current_courses', 'Course History', 'Your completed and currently enrolled courses', 3, False, 8),
                ('current_goals', 'Academic Goals', 'Your educational and career objectives', 4, False, 5),
                ('course_interests', 'Course Interests', 'Additional courses you are interested in', 5, False, 6),
                
                # Prospective student steps  
                ('field_interests', 'Fields of Interest', 'Academic areas and potential majors you are considering', 3, False, 8),
                ('prospective_goals', 'Educational Goals', 'Your educational and career aspirations', 4, False, 5),
                ('program_exploration', 'Program Exploration', 'Explore programs and courses that match your interests', 5, False, 8),
                
                # Completion
                ('completion', 'Get Started', 'Welcome to your personalized academic advisor', 6, True, 2)
            ]
            
            for step_name, display_name, description, step_order, is_required, estimated_time in onboarding_steps:
                cur.execute("""
                    INSERT INTO onboarding_steps (step_name, display_name, description, step_order, is_required, estimated_time_minutes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (step_name) DO NOTHING
                """, (step_name, display_name, description, step_order, is_required, estimated_time))
            
            conn.commit()
            print("All tables and indexes created successfully!")
            
            # Print table counts
            tables = [
                'departments', 'courses', 'student_profiles', 'student_academic_goals',
                'student_course_interests', 'student_academic_history', 'onboarding_steps',
                'student_onboarding_progress', 'student_recommendations'
            ]
            
            print("\nTable status:")
            for table in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    print(f"  {table}: {count} records")
                except Exception as e:
                    print(f"  {table}: Error - {e}")

if __name__ == "__main__":
    try:
        setup_onboarding_tables()
        print("\nOnboarding database schema setup completed successfully!")
    except Exception as e:
        print(f"\nSchema setup failed: {e}")
        exit(1)