-- =========================================================
-- CHATBOT_LOCAL DATABASE ADMINISTRATION VIEWS & CLEANUP
-- =========================================================
-- This script creates comprehensive views and cleanup procedures
-- for managing all chatbot data via pgAdmin
-- =========================================================

-- =========================================================
-- COMPREHENSIVE DATA VIEWS FOR ADMINISTRATION
-- =========================================================

-- 1. Complete Student Overview
CREATE OR REPLACE VIEW admin_student_overview AS
SELECT 
    sp.user_email,
    sp.first_name,
    sp.last_name,
    sp.preferred_name,
    sp.student_type,
    sp.academic_level,
    sp.enrollment_status,
    sp.degree_program,
    sp.primary_major,
    sp.secondary_major,
    sp.minor_program,
    sp.concentration,
    sp.cumulative_gpa,
    sp.expected_graduation,
    sp.phone,
    sp.profile_completion_percentage,
    sp.is_onboarding_complete,
    sp.is_active,
    sp.created_at,
    sp.updated_at,
    
    -- Onboarding Progress Summary
    (SELECT COUNT(*) FROM student_onboarding_progress sop 
     WHERE sop.student_email = sp.user_email) as total_onboarding_steps,
    (SELECT COUNT(*) FROM student_onboarding_progress sop 
     WHERE sop.student_email = sp.user_email AND sop.status = 'completed') as completed_steps,
    
    -- Goals and Interests Count
    (SELECT COUNT(*) FROM student_academic_goals sag 
     WHERE sag.student_email = sp.user_email) as academic_goals_count,
    (SELECT COUNT(*) FROM student_course_interests sci 
     WHERE sci.student_email = sp.user_email) as course_interests_count,
    
    -- Academic History Count
    (SELECT COUNT(*) FROM student_academic_history sah 
     WHERE sah.student_email = sp.user_email) as academic_history_count,
    
    -- Conversation Activity
    (SELECT COUNT(*) FROM conversation c 
     WHERE c.user_email = sp.user_email) as total_conversations,
    (SELECT MAX(c.timestamp) FROM conversation c 
     WHERE c.user_email = sp.user_email) as last_conversation_date
     
FROM student_profiles sp
ORDER BY sp.created_at DESC;

-- 2. Detailed Onboarding Progress View
CREATE OR REPLACE VIEW admin_onboarding_progress AS
SELECT 
    sop.student_email,
    sp.first_name,
    sp.last_name,
    sop.step_name,
    os.display_name as step_display_name,
    os.description as step_description,
    sop.status,
    sop.started_at,
    sop.completed_at,
    sop.data_json,
    os.step_order,
    os.is_required,
    os.estimated_time_minutes,
    sop.created_at,
    sop.updated_at
FROM student_onboarding_progress sop
JOIN student_profiles sp ON sop.student_email = sp.user_email
LEFT JOIN onboarding_steps os ON sop.step_name = os.step_name
ORDER BY sop.student_email, os.step_order;

-- 3. Academic Goals and Interests View
CREATE OR REPLACE VIEW admin_student_goals_interests AS
SELECT 
    sp.user_email,
    sp.first_name,
    sp.last_name,
    sp.degree_program,
    
    -- Academic Goals
    sag.goal_type,
    sag.goal_category,
    sag.goal_description,
    sag.target_completion_date,
    sag.priority_level,
    sag.is_achieved,
    sag.progress_notes,
    
    -- Course Interests
    (SELECT COUNT(*) FROM student_course_interests sci 
     WHERE sci.student_email = sp.user_email) as total_course_interests,
    
    sag.created_at as goal_created_at,
    sag.updated_at as goal_updated_at
    
FROM student_profiles sp
LEFT JOIN student_academic_goals sag ON sp.user_email = sag.student_email
ORDER BY sp.user_email, sag.priority_level DESC, sag.created_at;

-- 4. Course Interests Detail View  
CREATE OR REPLACE VIEW admin_course_interests AS
SELECT 
    sp.user_email,
    sp.first_name,
    sp.last_name,
    sp.degree_program,
    sci.course_code,
    c.title as course_title,
    c.description as course_description,
    c.credits,
    c.level,
    c.department_code,
    sci.interest_level,
    sci.planned_semester,
    sci.priority_order,
    sci.reason,
    sci.notes,
    sci.created_at,
    sci.updated_at
FROM student_profiles sp
JOIN student_course_interests sci ON sp.user_email = sci.student_email
LEFT JOIN courses c ON sci.course_code = c.code
ORDER BY sp.user_email, sci.priority_order, sci.created_at;

-- 5. Academic History View
CREATE OR REPLACE VIEW admin_academic_history AS
SELECT 
    sp.user_email,
    sp.first_name,
    sp.last_name,
    sp.degree_program,
    sah.course_code,
    sah.course_title,
    sah.institution,
    sah.semester,
    sah.year,
    sah.grade,
    sah.credits_earned,
    sah.status,
    sah.transfer_credit,
    sah.notes,
    sah.created_at
FROM student_profiles sp
JOIN student_academic_history sah ON sp.user_email = sah.student_email
ORDER BY sp.user_email, sah.year DESC, sah.semester;

-- 6. Conversation Activity View
CREATE OR REPLACE VIEW admin_conversation_activity AS
SELECT 
    c.user_email,
    sp.first_name,
    sp.last_name,
    sp.degree_program,
    c.session_id,
    c.message,
    c.response,
    c.timestamp,
    
    -- Session Summary Info
    ss.total_messages,
    ss.session_start_time,
    ss.session_end_time,
    ss.summary_text,
    
    -- Count conversations per user
    (SELECT COUNT(*) FROM conversation c2 
     WHERE c2.user_email = c.user_email) as total_user_conversations
     
FROM conversation c
LEFT JOIN student_profiles sp ON c.user_email = sp.user_email
LEFT JOIN session_summaries ss ON c.session_id = ss.session_id
ORDER BY c.timestamp DESC;

-- 7. System Usage Statistics View
CREATE OR REPLACE VIEW admin_system_stats AS
SELECT 
    'Total Students' as metric,
    COUNT(*)::text as value,
    'active student profiles' as description
FROM student_profiles WHERE is_active = true

UNION ALL

SELECT 
    'Completed Onboarding' as metric,
    COUNT(*)::text as value,
    'students finished onboarding' as description
FROM student_profiles WHERE is_onboarding_complete = true

UNION ALL

SELECT 
    'Total Conversations' as metric,
    COUNT(*)::text as value,
    'chat messages exchanged' as description
FROM conversation

UNION ALL

SELECT 
    'Active Course Interests' as metric,
    COUNT(*)::text as value,
    'course interests registered' as description
FROM student_course_interests

UNION ALL

SELECT 
    'Academic Goals Set' as metric,
    COUNT(*)::text as value,
    'student goals defined' as description
FROM student_academic_goals

UNION ALL

SELECT 
    'Academic Records' as metric,
    COUNT(*)::text as value,
    'course history entries' as description
FROM student_academic_history

UNION ALL

SELECT 
    'Available Courses' as metric,
    COUNT(*)::text as value,
    'courses in catalog' as description
FROM courses WHERE is_active = true

UNION ALL

SELECT 
    'Active Departments' as metric,
    COUNT(*)::text as value,
    'academic departments' as description
FROM departments WHERE is_active = true;

-- =========================================================
-- DATA CLEANUP PROCEDURES
-- =========================================================

-- Function to safely delete a student and all related data
CREATE OR REPLACE FUNCTION delete_student_data(student_email_param VARCHAR)
RETURNS TABLE(deleted_table VARCHAR, deleted_count INTEGER) AS $$
BEGIN
    -- Delete in proper order to respect foreign key constraints
    
    -- 1. Delete conversation data
    DELETE FROM conversation WHERE user_email = student_email_param;
    RETURN QUERY SELECT 'conversation'::VARCHAR, ROW_COUNT;
    
    -- 2. Delete session summaries for this user's sessions
    DELETE FROM session_summaries 
    WHERE session_id IN (
        SELECT DISTINCT session_id FROM conversation WHERE user_email = student_email_param
    );
    RETURN QUERY SELECT 'session_summaries'::VARCHAR, ROW_COUNT;
    
    -- 3. Delete student recommendations
    DELETE FROM student_recommendations WHERE student_email = student_email_param;
    RETURN QUERY SELECT 'student_recommendations'::VARCHAR, ROW_COUNT;
    
    -- 4. Delete academic history
    DELETE FROM student_academic_history WHERE student_email = student_email_param;
    RETURN QUERY SELECT 'student_academic_history'::VARCHAR, ROW_COUNT;
    
    -- 5. Delete course interests
    DELETE FROM student_course_interests WHERE student_email = student_email_param;
    RETURN QUERY SELECT 'student_course_interests'::VARCHAR, ROW_COUNT;
    
    -- 6. Delete academic goals
    DELETE FROM student_academic_goals WHERE student_email = student_email_param;
    RETURN QUERY SELECT 'student_academic_goals'::VARCHAR, ROW_COUNT;
    
    -- 7. Delete onboarding progress
    DELETE FROM student_onboarding_progress WHERE student_email = student_email_param;
    RETURN QUERY SELECT 'student_onboarding_progress'::VARCHAR, ROW_COUNT;
    
    -- 8. Finally delete the profile
    DELETE FROM student_profiles WHERE user_email = student_email_param;
    RETURN QUERY SELECT 'student_profiles'::VARCHAR, ROW_COUNT;
    
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup test/demo data
CREATE OR REPLACE FUNCTION cleanup_test_data()
RETURNS TABLE(action VARCHAR, count INTEGER) AS $$
BEGIN
    -- Delete students with test emails
    RETURN QUERY 
    SELECT 'test_students_deleted'::VARCHAR, COUNT(*)::INTEGER 
    FROM student_profiles 
    WHERE user_email LIKE '%test%' OR user_email LIKE '%demo%' OR user_email LIKE '%example%';
    
    DELETE FROM student_profiles 
    WHERE user_email LIKE '%test%' OR user_email LIKE '%demo%' OR user_email LIKE '%example%';
    
    -- Delete orphaned conversation data
    DELETE FROM conversation 
    WHERE user_email NOT IN (SELECT user_email FROM student_profiles);
    RETURN QUERY SELECT 'orphaned_conversations_deleted'::VARCHAR, ROW_COUNT;
    
    -- Delete orphaned session summaries
    DELETE FROM session_summaries 
    WHERE session_id NOT IN (SELECT DISTINCT session_id FROM conversation WHERE session_id IS NOT NULL);
    RETURN QUERY SELECT 'orphaned_sessions_deleted'::VARCHAR, ROW_COUNT;
    
END;
$$ LANGUAGE plpgsql;

-- Function to get table sizes for monitoring
CREATE OR REPLACE FUNCTION get_table_sizes()
RETURNS TABLE(table_name VARCHAR, row_count BIGINT, size_pretty VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'student_profiles'::VARCHAR,
        (SELECT COUNT(*) FROM student_profiles),
        pg_size_pretty(pg_total_relation_size('student_profiles'))
    UNION ALL
    SELECT 
        'conversation'::VARCHAR,
        (SELECT COUNT(*) FROM conversation),
        pg_size_pretty(pg_total_relation_size('conversation'))
    UNION ALL
    SELECT 
        'student_onboarding_progress'::VARCHAR,
        (SELECT COUNT(*) FROM student_onboarding_progress),
        pg_size_pretty(pg_total_relation_size('student_onboarding_progress'))
    UNION ALL
    SELECT 
        'student_academic_goals'::VARCHAR,
        (SELECT COUNT(*) FROM student_academic_goals),
        pg_size_pretty(pg_total_relation_size('student_academic_goals'))
    UNION ALL
    SELECT 
        'student_course_interests'::VARCHAR,
        (SELECT COUNT(*) FROM student_course_interests),
        pg_size_pretty(pg_total_relation_size('student_course_interests'))
    UNION ALL
    SELECT 
        'student_academic_history'::VARCHAR,
        (SELECT COUNT(*) FROM student_academic_history),
        pg_size_pretty(pg_total_relation_size('student_academic_history'))
    UNION ALL
    SELECT 
        'courses'::VARCHAR,
        (SELECT COUNT(*) FROM courses),
        pg_size_pretty(pg_total_relation_size('courses'))
    UNION ALL
    SELECT 
        'departments'::VARCHAR,
        (SELECT COUNT(*) FROM departments),
        pg_size_pretty(pg_total_relation_size('departments'));
END;
$$ LANGUAGE plpgsql;

-- =========================================================
-- QUICK ACCESS QUERIES FOR PGADMIN
-- =========================================================

-- Comment: Copy and paste these queries in pgAdmin for quick access

/*
-- VIEW ALL STUDENTS WITH SUMMARY
SELECT * FROM admin_student_overview;

-- VIEW ONBOARDING PROGRESS
SELECT * FROM admin_onboarding_progress WHERE student_email = 'your-email@domain.com';

-- VIEW SYSTEM STATISTICS
SELECT * FROM admin_system_stats;

-- VIEW TABLE SIZES
SELECT * FROM get_table_sizes();

-- DELETE SPECIFIC STUDENT (BE CAREFUL!)
SELECT * FROM delete_student_data('student-email@domain.com');

-- CLEANUP TEST DATA
SELECT * FROM cleanup_test_data();

-- VIEW CONVERSATION ACTIVITY
SELECT * FROM admin_conversation_activity 
WHERE user_email = 'your-email@domain.com' 
ORDER BY timestamp DESC;

-- VIEW COURSE INTERESTS
SELECT * FROM admin_course_interests 
WHERE user_email = 'your-email@domain.com';

-- VIEW ACADEMIC GOALS
SELECT * FROM admin_student_goals_interests 
WHERE user_email = 'your-email@domain.com';

-- BULK DELETE ALL DATA (NUCLEAR OPTION - BE VERY CAREFUL!)
-- TRUNCATE TABLE conversation CASCADE;
-- TRUNCATE TABLE session_summaries CASCADE;
-- TRUNCATE TABLE student_recommendations CASCADE;
-- TRUNCATE TABLE student_academic_history CASCADE;
-- TRUNCATE TABLE student_course_interests CASCADE;
-- TRUNCATE TABLE student_academic_goals CASCADE;
-- TRUNCATE TABLE student_onboarding_progress CASCADE;
-- TRUNCATE TABLE student_profiles CASCADE;
*/

-- =========================================================
-- EXAMPLE USAGE COMMANDS FOR PGADMIN
-- =========================================================

-- To run this script:
-- 1. Open pgAdmin
-- 2. Connect to your chatbot_local database  
-- 3. Open SQL Query Tool
-- 4. Paste and execute this entire script
-- 5. Use the quick access queries above for daily administration

COMMENT ON VIEW admin_student_overview IS 'Comprehensive view of all students with activity summary';
COMMENT ON VIEW admin_onboarding_progress IS 'Detailed onboarding progress for all students';
COMMENT ON VIEW admin_conversation_activity IS 'All conversation activity with user context';
COMMENT ON VIEW admin_system_stats IS 'System-wide usage statistics';
COMMENT ON FUNCTION delete_student_data(VARCHAR) IS 'Safely delete a student and all related data';
COMMENT ON FUNCTION cleanup_test_data() IS 'Remove test and demo data from system';
COMMENT ON FUNCTION get_table_sizes() IS 'Monitor database table sizes and row counts';

-- Grant permissions for admin users
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_admin_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_admin_user;