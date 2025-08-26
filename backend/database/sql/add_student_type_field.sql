-- Migration: Add student_type field to student_profiles table and update view
-- Date: 2025-08-19
-- Purpose: Fix missing student_type field causing student profile modal display issues

-- Add student_type column to student_profiles table
ALTER TABLE student_profiles 
ADD COLUMN IF NOT EXISTS student_type VARCHAR(20) DEFAULT 'current_gannon';

-- Add index for the new column
CREATE INDEX IF NOT EXISTS idx_student_profiles_student_type ON student_profiles(student_type);

-- Add comment for the new column
COMMENT ON COLUMN student_profiles.student_type IS 'Type of student: current_gannon, prospective, or transfer';

-- Drop and recreate the student_dashboard view to include student_type
DROP VIEW IF EXISTS student_dashboard;
CREATE VIEW student_dashboard AS
SELECT 
    sp.user_email,
    sp.first_name,
    sp.last_name,
    sp.preferred_name,
    sp.student_type,
    sp.academic_level,
    sp.enrollment_status,
    sp.primary_major,
    sp.cumulative_gpa,
    sp.expected_graduation,
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

-- Set existing students to 'current_gannon' type if they have enrollment_status
UPDATE student_profiles 
SET student_type = CASE 
    WHEN enrollment_status IN ('full-time', 'part-time') THEN 'current_gannon'
    WHEN enrollment_status = 'not-enrolled' THEN 'prospective'
    ELSE 'current_gannon'
END
WHERE student_type IS NULL OR student_type = '';

COMMIT;