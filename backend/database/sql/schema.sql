-- =========================================================
-- ONBOARDING SYSTEM DATABASE SCHEMA FOR GANNON UNIVERSITY
-- =========================================================
-- This schema extends the existing conversation system with 
-- comprehensive student onboarding and course management
-- =========================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================================
-- CORE TABLES
-- =========================================================

-- Academic departments and programs
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,          -- e.g., 'GCIS', 'MATH', 'ENGL'
    name VARCHAR(200) NOT NULL,                -- e.g., 'Computer and Information Science'
    description TEXT,                          -- Department description
    college VARCHAR(100),                      -- e.g., 'Engineering and Business'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Course catalog
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,          -- e.g., 'GCIS 655'
    department_code VARCHAR(10) NOT NULL,      -- e.g., 'GCIS'  
    course_number VARCHAR(10) NOT NULL,        -- e.g., '655'
    title VARCHAR(300) NOT NULL,               -- e.g., 'Data Mining'
    description TEXT,                          -- Full course description
    credits INTEGER,                           -- Credit hours
    level VARCHAR(20) NOT NULL,               -- 'undergraduate' or 'graduate'
    prerequisites TEXT,                        -- Prerequisites as text
    is_active BOOLEAN DEFAULT true,
    source_catalog VARCHAR(100),               -- Source file reference
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (department_code) REFERENCES departments(code) ON UPDATE CASCADE
);

-- Student profiles (extends existing user system)
CREATE TABLE IF NOT EXISTS student_profiles (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) UNIQUE NOT NULL,   -- Links to existing auth system
    student_id VARCHAR(50),                     -- Optional university student ID
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    preferred_name VARCHAR(100),
    phone VARCHAR(20),
    emergency_contact_name VARCHAR(200),
    emergency_contact_phone VARCHAR(20),
    emergency_contact_relationship VARCHAR(100),
    
    -- Academic Information
    academic_level VARCHAR(30),                 -- 'undergraduate', 'graduate', 'doctoral'
    enrollment_status VARCHAR(30),              -- 'full-time', 'part-time', 'not-enrolled'
    expected_graduation TIMESTAMP,
    cumulative_gpa DECIMAL(3,2),               -- e.g., 3.85
    
    -- Program Information
    degree_program VARCHAR(150),                -- e.g., 'Master of Science in Data Science', 'Bachelor of Science in Computer Science'
    primary_major VARCHAR(100),
    secondary_major VARCHAR(100),
    minor_program VARCHAR(100),
    concentration VARCHAR(100),
    
    -- Demographics (optional)
    date_of_birth DATE,
    gender VARCHAR(30),
    ethnicity VARCHAR(100),
    citizenship_status VARCHAR(50),
    
    -- Status flags
    is_onboarding_complete BOOLEAN DEFAULT false,
    profile_completion_percentage INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Academic goals and interests
CREATE TABLE IF NOT EXISTS student_academic_goals (
    id SERIAL PRIMARY KEY,
    student_email VARCHAR(255) NOT NULL,
    goal_type VARCHAR(50) NOT NULL,            -- 'career', 'academic', 'skill', 'personal'
    goal_category VARCHAR(100),                -- e.g., 'Software Development', 'Research'
    goal_description TEXT NOT NULL,
    target_completion_date DATE,
    priority_level INTEGER DEFAULT 5,          -- 1-10 scale
    is_achieved BOOLEAN DEFAULT false,
    progress_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_email) REFERENCES student_profiles(user_email) ON DELETE CASCADE
);

-- Student course interests and selections
CREATE TABLE IF NOT EXISTS student_course_interests (
    id SERIAL PRIMARY KEY,
    student_email VARCHAR(255) NOT NULL,
    course_code VARCHAR(20) NOT NULL,
    interest_level VARCHAR(20) DEFAULT 'interested',  -- 'very_interested', 'interested', 'considering'
    planned_semester VARCHAR(20),               -- e.g., 'Fall 2024', 'Spring 2025'
    priority_order INTEGER,                     -- 1 = highest priority
    reason TEXT,                               -- Why interested in this course
    is_prerequisite_met BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_email) REFERENCES student_profiles(user_email) ON DELETE CASCADE,
    FOREIGN KEY (course_code) REFERENCES courses(code) ON UPDATE CASCADE,
    UNIQUE(student_email, course_code)
);

-- Academic history (previous courses taken)
CREATE TABLE IF NOT EXISTS student_academic_history (
    id SERIAL PRIMARY KEY,
    student_email VARCHAR(255) NOT NULL,
    course_code VARCHAR(20),
    course_title VARCHAR(300),
    institution VARCHAR(200) DEFAULT 'Gannon University',
    semester VARCHAR(20),                       -- e.g., 'Fall 2023'
    year INTEGER,
    grade VARCHAR(5),                          -- e.g., 'A', 'B+', 'C'
    grade_points DECIMAL(3,2),                 -- 4.0 scale
    credits_earned INTEGER,
    is_transfer_credit BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'completed',    -- 'completed', 'in_progress', 'withdrawn'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_email) REFERENCES student_profiles(user_email) ON DELETE CASCADE
);

-- =========================================================
-- ONBOARDING WORKFLOW TABLES
-- =========================================================

-- Onboarding steps and progress tracking
CREATE TABLE IF NOT EXISTS onboarding_steps (
    id SERIAL PRIMARY KEY,
    step_name VARCHAR(100) UNIQUE NOT NULL,    -- e.g., 'personal_info', 'academic_goals'
    display_name VARCHAR(200) NOT NULL,        -- e.g., 'Personal Information'
    description TEXT,
    step_order INTEGER NOT NULL,               -- Order in the onboarding flow
    is_required BOOLEAN DEFAULT true,
    estimated_time_minutes INTEGER DEFAULT 5,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track individual student progress through onboarding
CREATE TABLE IF NOT EXISTS student_onboarding_progress (
    id SERIAL PRIMARY KEY,
    student_email VARCHAR(255) NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'not_started',  -- 'not_started', 'in_progress', 'completed', 'skipped'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    data_json JSONB,                           -- Store form data/responses
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_email) REFERENCES student_profiles(user_email) ON DELETE CASCADE,
    FOREIGN KEY (step_name) REFERENCES onboarding_steps(step_name) ON UPDATE CASCADE,
    UNIQUE(student_email, step_name)
);

-- =========================================================
-- ADVISING AND RECOMMENDATIONS TABLES
-- =========================================================

-- AI-generated recommendations for students
CREATE TABLE IF NOT EXISTS student_recommendations (
    id SERIAL PRIMARY KEY,
    student_email VARCHAR(255) NOT NULL,
    recommendation_type VARCHAR(50) NOT NULL,  -- 'course', 'program', 'career', 'resource'
    title VARCHAR(300) NOT NULL,
    description TEXT NOT NULL,
    reasoning TEXT,                            -- AI explanation for recommendation
    confidence_score DECIMAL(3,2),            -- 0.0 to 1.0
    priority_level INTEGER DEFAULT 5,         -- 1-10 scale
    category VARCHAR(100),                     -- e.g., 'Academic Planning', 'Career Prep'
    
    -- Recommendation data
    recommended_course_code VARCHAR(20),       -- If course recommendation
    recommended_semester VARCHAR(20),
    action_url TEXT,                          -- Link to take action
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'active',      -- 'active', 'viewed', 'acted_on', 'dismissed'
    viewed_at TIMESTAMP,
    acted_on_at TIMESTAMP,
    dismissed_at TIMESTAMP,
    
    -- Metadata
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'ai_system',
    
    FOREIGN KEY (student_email) REFERENCES student_profiles(user_email) ON DELETE CASCADE,
    FOREIGN KEY (recommended_course_code) REFERENCES courses(code) ON UPDATE CASCADE
);

-- =========================================================
-- CONVERSATION ENHANCEMENT TABLES
-- =========================================================

-- Enhanced conversation context with student data
CREATE TABLE IF NOT EXISTS conversation_context (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    context_type VARCHAR(50) NOT NULL,         -- 'profile', 'goals', 'courses', 'history'
    context_data JSONB NOT NULL,              -- Relevant student data for this conversation
    relevance_score DECIMAL(3,2) DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Link to existing conversation system
    FOREIGN KEY (user_email) REFERENCES student_profiles(user_email) ON DELETE CASCADE
);

-- =========================================================
-- INDEXES FOR PERFORMANCE
-- =========================================================

-- Department indexes
CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code);
CREATE INDEX IF NOT EXISTS idx_departments_active ON departments(is_active);

-- Course indexes
CREATE INDEX IF NOT EXISTS idx_courses_code ON courses(code);
CREATE INDEX IF NOT EXISTS idx_courses_department ON courses(department_code);
CREATE INDEX IF NOT EXISTS idx_courses_level ON courses(level);
CREATE INDEX IF NOT EXISTS idx_courses_active ON courses(is_active);
CREATE INDEX IF NOT EXISTS idx_courses_search ON courses USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Student profile indexes
CREATE INDEX IF NOT EXISTS idx_student_profiles_email ON student_profiles(user_email);
CREATE INDEX IF NOT EXISTS idx_student_profiles_level ON student_profiles(academic_level);
CREATE INDEX IF NOT EXISTS idx_student_profiles_status ON student_profiles(enrollment_status);
CREATE INDEX IF NOT EXISTS idx_student_profiles_onboarding ON student_profiles(is_onboarding_complete);

-- Student goals indexes
CREATE INDEX IF NOT EXISTS idx_student_goals_email ON student_academic_goals(student_email);
CREATE INDEX IF NOT EXISTS idx_student_goals_type ON student_academic_goals(goal_type);
CREATE INDEX IF NOT EXISTS idx_student_goals_achieved ON student_academic_goals(is_achieved);

-- Course interests indexes
CREATE INDEX IF NOT EXISTS idx_course_interests_student ON student_course_interests(student_email);
CREATE INDEX IF NOT EXISTS idx_course_interests_course ON student_course_interests(course_code);
CREATE INDEX IF NOT EXISTS idx_course_interests_semester ON student_course_interests(planned_semester);

-- Academic history indexes
CREATE INDEX IF NOT EXISTS idx_academic_history_student ON student_academic_history(student_email);
CREATE INDEX IF NOT EXISTS idx_academic_history_course ON student_academic_history(course_code);
CREATE INDEX IF NOT EXISTS idx_academic_history_semester ON student_academic_history(semester, year);

-- Onboarding progress indexes
CREATE INDEX IF NOT EXISTS idx_onboarding_progress_student ON student_onboarding_progress(student_email);
CREATE INDEX IF NOT EXISTS idx_onboarding_progress_step ON student_onboarding_progress(step_name);
CREATE INDEX IF NOT EXISTS idx_onboarding_progress_status ON student_onboarding_progress(status);

-- Recommendations indexes  
CREATE INDEX IF NOT EXISTS idx_recommendations_student ON student_recommendations(student_email);
CREATE INDEX IF NOT EXISTS idx_recommendations_type ON student_recommendations(recommendation_type);
CREATE INDEX IF NOT EXISTS idx_recommendations_status ON student_recommendations(status);
CREATE INDEX IF NOT EXISTS idx_recommendations_generated ON student_recommendations(generated_at DESC);

-- Conversation context indexes
CREATE INDEX IF NOT EXISTS idx_conversation_context_session ON conversation_context(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_context_user ON conversation_context(user_email);
CREATE INDEX IF NOT EXISTS idx_conversation_context_type ON conversation_context(context_type);

-- =========================================================
-- SAMPLE DATA FOR ONBOARDING STEPS
-- =========================================================

INSERT INTO onboarding_steps (step_name, display_name, description, step_order, is_required, estimated_time_minutes) VALUES
('welcome', 'Welcome', 'Introduction to the advising system', 1, true, 2),
('personal_info', 'Personal Information', 'Basic personal and contact information', 2, true, 5),
('academic_background', 'Academic Background', 'Previous education and academic history', 3, true, 8),
('academic_goals', 'Academic Goals', 'Educational and career objectives', 4, true, 10),
('course_interests', 'Course Interests', 'Select courses of interest', 5, true, 15),
('program_selection', 'Program Selection', 'Choose major, minor, and concentration', 6, true, 10),
('advising_preferences', 'Advising Preferences', 'Set preferences for AI advising', 7, false, 5),
('completion', 'Complete Onboarding', 'Finalize profile and generate recommendations', 8, true, 3)
ON CONFLICT (step_name) DO NOTHING;

-- =========================================================
-- VIEWS FOR COMMON QUERIES
-- =========================================================

-- Student dashboard view - comprehensive student information
CREATE OR REPLACE VIEW student_dashboard AS
SELECT 
    sp.user_email,
    sp.first_name,
    sp.last_name,
    sp.preferred_name,
    sp.academic_level,
    sp.enrollment_status,
    sp.degree_program,
    sp.primary_major,
    sp.cumulative_gpa,
    sp.profile_completion_percentage,
    sp.is_onboarding_complete,
    
    -- Onboarding progress
    COALESCE(
        ROUND(
            (SELECT COUNT(*) FROM student_onboarding_progress sop 
             WHERE sop.student_email = sp.user_email AND sop.status = 'completed')::DECIMAL 
            / 
            (SELECT COUNT(*) FROM onboarding_steps WHERE is_required = true)::DECIMAL 
            * 100
        ), 0
    ) as onboarding_progress_percentage,
    
    -- Active recommendations count
    (SELECT COUNT(*) FROM student_recommendations sr 
     WHERE sr.student_email = sp.user_email AND sr.status = 'active') as active_recommendations_count,
     
    -- Course interests count
    (SELECT COUNT(*) FROM student_course_interests sci 
     WHERE sci.student_email = sp.user_email) as course_interests_count,
     
    sp.created_at,
    sp.updated_at
    
FROM student_profiles sp;

-- Course catalog view with department information
CREATE OR REPLACE VIEW course_catalog_view AS
SELECT 
    c.id,
    c.code,
    c.department_code,
    d.name as department_name,
    c.course_number,
    c.title,
    c.description,
    c.credits,
    c.level,
    c.prerequisites,
    c.is_active,
    
    -- Interest metrics
    (SELECT COUNT(*) FROM student_course_interests sci 
     WHERE sci.course_code = c.code) as student_interest_count,
     
    c.created_at,
    c.updated_at
    
FROM courses c
LEFT JOIN departments d ON c.department_code = d.code;

-- =========================================================
-- FUNCTIONS FOR COMMON OPERATIONS
-- =========================================================

-- Function to update profile completion percentage
CREATE OR REPLACE FUNCTION update_profile_completion(student_email_param VARCHAR)
RETURNS INTEGER AS $$
DECLARE
    completion_pct INTEGER;
BEGIN
    -- Calculate completion based on filled fields and onboarding progress
    WITH profile_fields AS (
        SELECT 
            sp.user_email,
            CASE WHEN sp.first_name IS NOT NULL AND LENGTH(TRIM(sp.first_name)) > 0 THEN 10 ELSE 0 END +
            CASE WHEN sp.last_name IS NOT NULL AND LENGTH(TRIM(sp.last_name)) > 0 THEN 10 ELSE 0 END +
            CASE WHEN sp.phone IS NOT NULL AND LENGTH(TRIM(sp.phone)) > 0 THEN 5 ELSE 0 END +
            CASE WHEN sp.academic_level IS NOT NULL THEN 10 ELSE 0 END +
            CASE WHEN sp.degree_program IS NOT NULL AND LENGTH(TRIM(sp.degree_program)) > 0 THEN 20 ELSE 0 END +
            CASE WHEN sp.primary_major IS NOT NULL AND LENGTH(TRIM(sp.primary_major)) > 0 THEN 5 ELSE 0 END +
            CASE WHEN sp.expected_graduation IS NOT NULL THEN 10 ELSE 0 END
            as profile_score
        FROM student_profiles sp
        WHERE sp.user_email = student_email_param
    ),
    onboarding_score AS (
        SELECT 
            COALESCE(
                ROUND(
                    (SELECT COUNT(*) FROM student_onboarding_progress sop 
                     WHERE sop.student_email = student_email_param AND sop.status = 'completed')::DECIMAL 
                    / 
                    (SELECT COUNT(*) FROM onboarding_steps WHERE is_required = true)::DECIMAL 
                    * 40  -- 40% weight for onboarding completion
                ), 0
            ) as onboarding_score
    )
    SELECT LEAST(100, pf.profile_score + os.onboarding_score)
    INTO completion_pct
    FROM profile_fields pf, onboarding_score os;
    
    -- Update the profile
    UPDATE student_profiles 
    SET 
        profile_completion_percentage = completion_pct,
        is_onboarding_complete = (completion_pct >= 90),
        updated_at = CURRENT_TIMESTAMP
    WHERE user_email = student_email_param;
    
    RETURN completion_pct;
END;
$$ LANGUAGE plpgsql;

-- =========================================================
-- TRIGGERS
-- =========================================================

-- Trigger to automatically update profile completion when related data changes
CREATE OR REPLACE FUNCTION trigger_update_profile_completion()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM update_profile_completion(
        CASE 
            WHEN TG_TABLE_NAME = 'student_profiles' THEN NEW.user_email
            WHEN TG_TABLE_NAME = 'student_onboarding_progress' THEN NEW.student_email
            ELSE NEW.student_email
        END
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER trigger_student_profiles_completion
    AFTER INSERT OR UPDATE ON student_profiles
    FOR EACH ROW EXECUTE FUNCTION trigger_update_profile_completion();

CREATE TRIGGER trigger_onboarding_progress_completion
    AFTER INSERT OR UPDATE ON student_onboarding_progress  
    FOR EACH ROW EXECUTE FUNCTION trigger_update_profile_completion();

-- =========================================================
-- COMMENTS FOR DOCUMENTATION
-- =========================================================

COMMENT ON TABLE departments IS 'Academic departments and organizational units';
COMMENT ON TABLE courses IS 'University course catalog with detailed information';
COMMENT ON TABLE student_profiles IS 'Comprehensive student profile information';
COMMENT ON TABLE student_academic_goals IS 'Student-defined academic and career goals';
COMMENT ON TABLE student_course_interests IS 'Courses students are interested in taking';
COMMENT ON TABLE student_academic_history IS 'Previous courses and academic record';
COMMENT ON TABLE onboarding_steps IS 'Defined steps in the onboarding workflow';
COMMENT ON TABLE student_onboarding_progress IS 'Individual student progress through onboarding';
COMMENT ON TABLE student_recommendations IS 'AI-generated recommendations for students';
COMMENT ON TABLE conversation_context IS 'Enhanced context for personalized conversations';

-- =========================================================
-- GRANT PERMISSIONS (adjust as needed for your environment)
-- =========================================================

-- Grant permissions to application user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_app_user;

COMMIT;