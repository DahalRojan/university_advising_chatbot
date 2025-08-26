-- =========================================================
-- AUTHENTICATION SYSTEM UPGRADE
-- Adding username/password auth alongside Microsoft OAuth
-- =========================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table for unified authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE,                    -- For username/password login (nullable for OAuth users)
    email VARCHAR(255) UNIQUE NOT NULL,             -- Primary identifier (from OAuth or registration)
    password_hash VARCHAR(255),                     -- For username/password login (nullable for OAuth users) 
    
    -- Authentication method tracking
    auth_method VARCHAR(20) NOT NULL DEFAULT 'password', -- 'password', 'oauth', 'both'
    oauth_provider VARCHAR(50),                     -- 'microsoft', 'google', etc.
    oauth_id VARCHAR(255),                          -- External OAuth user ID (oid from Microsoft)
    
    -- Verification and security
    email_verified BOOLEAN DEFAULT false,
    email_verification_token VARCHAR(255),
    email_verification_expires TIMESTAMP,
    password_reset_token VARCHAR(255), 
    password_reset_expires TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    
    -- Profile information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(200),                      -- Full name for display
    
    -- Status and metadata
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_oauth_id ON users(oauth_id);
CREATE INDEX IF NOT EXISTS idx_users_auth_method ON users(auth_method);
CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(email_verified);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- Create email verification tokens table for tracking
CREATE TABLE IF NOT EXISTS email_verification_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    email VARCHAR(255) NOT NULL,
    verification_token VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create login attempts table for security
CREATE TABLE IF NOT EXISTS login_attempts (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR(255) NOT NULL,              -- username or email
    ip_address INET NOT NULL,
    success BOOLEAN NOT NULL,
    auth_method VARCHAR(20) NOT NULL,              -- 'password', 'oauth'
    failure_reason VARCHAR(100),                   -- 'invalid_credentials', 'account_locked', etc.
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT
);

-- Create index for security monitoring
CREATE INDEX IF NOT EXISTS idx_login_attempts_identifier ON login_attempts(identifier);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON login_attempts(attempted_at DESC);

-- =========================================================
-- UPDATE EXISTING STUDENT_PROFILES TABLE
-- =========================================================

-- Add reference to users table (for gradual migration)
ALTER TABLE student_profiles 
ADD COLUMN IF NOT EXISTS user_id UUID,
ADD COLUMN IF NOT EXISTS auth_source VARCHAR(20) DEFAULT 'oauth';

-- Create foreign key relationship
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_student_profiles_user_id'
    ) THEN
        ALTER TABLE student_profiles 
        ADD CONSTRAINT fk_student_profiles_user_id 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Create index for the new relationship
CREATE INDEX IF NOT EXISTS idx_student_profiles_user_id ON student_profiles(user_id);

-- =========================================================
-- MIGRATION FUNCTION FOR EXISTING OAUTH USERS
-- =========================================================

CREATE OR REPLACE FUNCTION migrate_oauth_users()
RETURNS INTEGER AS $$
DECLARE
    migrated_count INTEGER := 0;
    profile_record RECORD;
    new_user_id UUID;
BEGIN
    -- Migrate existing OAuth users to new users table
    FOR profile_record IN 
        SELECT DISTINCT user_email, first_name, last_name, created_at
        FROM student_profiles 
        WHERE user_id IS NULL
    LOOP
        -- Insert into users table
        INSERT INTO users (
            email, 
            auth_method, 
            oauth_provider, 
            email_verified,
            first_name, 
            last_name,
            display_name,
            is_active,
            created_at
        ) VALUES (
            profile_record.user_email,
            'oauth',
            'microsoft',
            true,  -- OAuth users are already verified
            profile_record.first_name,
            profile_record.last_name,
            COALESCE(profile_record.first_name || ' ' || profile_record.last_name, 'OAuth User'),
            true,
            profile_record.created_at
        ) 
        ON CONFLICT (email) DO NOTHING
        RETURNING id INTO new_user_id;
        
        -- Update student_profiles with user_id reference
        IF new_user_id IS NOT NULL THEN
            UPDATE student_profiles 
            SET user_id = new_user_id, auth_source = 'oauth'
            WHERE user_email = profile_record.user_email AND user_id IS NULL;
            
            migrated_count := migrated_count + 1;
        END IF;
    END LOOP;
    
    RETURN migrated_count;
END;
$$ LANGUAGE plpgsql;

-- =========================================================
-- FUNCTIONS FOR AUTHENTICATION
-- =========================================================

-- Function to create a new user with email verification
CREATE OR REPLACE FUNCTION create_user_with_verification(
    p_username VARCHAR(50),
    p_email VARCHAR(255),
    p_password_hash VARCHAR(255),
    p_first_name VARCHAR(100),
    p_last_name VARCHAR(100),
    p_verification_token VARCHAR(255)
)
RETURNS UUID AS $$
DECLARE
    new_user_id UUID;
BEGIN
    -- Insert new user
    INSERT INTO users (
        username,
        email,
        password_hash,
        auth_method,
        email_verified,
        email_verification_token,
        email_verification_expires,
        first_name,
        last_name,
        display_name
    ) VALUES (
        p_username,
        p_email,
        p_password_hash,
        'password',
        false,
        p_verification_token,
        NOW() + INTERVAL '24 hours',
        p_first_name,
        p_last_name,
        p_first_name || ' ' || p_last_name
    ) RETURNING id INTO new_user_id;
    
    -- Create corresponding student profile
    INSERT INTO student_profiles (
        user_email,
        user_id,
        first_name,
        last_name,
        auth_source
    ) VALUES (
        p_email,
        new_user_id,
        p_first_name,
        p_last_name,
        'password'
    );
    
    RETURN new_user_id;
END;
$$ LANGUAGE plpgsql;

-- Function to verify email
CREATE OR REPLACE FUNCTION verify_user_email(
    p_verification_token VARCHAR(255)
)
RETURNS BOOLEAN AS $$
DECLARE
    user_found INTEGER := 0;
    user_record RECORD;
BEGIN
    -- Check if user exists with this token
    SELECT id, email, email_verified, email_verification_expires
    INTO user_record
    FROM users 
    WHERE email_verification_token = p_verification_token;
    
    -- If no user found with this token, return false
    IF user_record.id IS NULL THEN
        RETURN false;
    END IF;
    
    -- If already verified, return true (allow multiple clicks)
    IF user_record.email_verified = true THEN
        RETURN true;
    END IF;
    
    -- If token expired, return false
    IF user_record.email_verification_expires <= NOW() THEN
        RETURN false;
    END IF;
    
    -- Token is valid and user not yet verified - update user
    UPDATE users 
    SET 
        email_verified = true,
        email_verification_token = NULL,
        email_verification_expires = NULL,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = user_record.id;
    
    -- Log successful verification
    UPDATE email_verification_logs
    SET verified_at = CURRENT_TIMESTAMP
    WHERE verification_token = p_verification_token;
    
    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- Function to handle login attempts
CREATE OR REPLACE FUNCTION log_login_attempt(
    p_identifier VARCHAR(255),
    p_ip_address INET,
    p_success BOOLEAN,
    p_auth_method VARCHAR(20),
    p_failure_reason VARCHAR(100) DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO login_attempts (
        identifier,
        ip_address,
        success,
        auth_method,
        failure_reason,
        user_agent
    ) VALUES (
        p_identifier,
        p_ip_address,
        p_success,
        p_auth_method,
        p_failure_reason,
        p_user_agent
    );
    
    -- Update failed login attempts on user record
    IF NOT p_success THEN
        UPDATE users 
        SET 
            failed_login_attempts = failed_login_attempts + 1,
            locked_until = CASE 
                WHEN failed_login_attempts + 1 >= 5 THEN NOW() + INTERVAL '15 minutes'
                ELSE locked_until 
            END
        WHERE email = p_identifier OR username = p_identifier;
    ELSE
        -- Reset failed attempts on successful login
        UPDATE users 
        SET 
            failed_login_attempts = 0,
            locked_until = NULL,
            last_login = CURRENT_TIMESTAMP
        WHERE email = p_identifier OR username = p_identifier;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =========================================================
-- VIEWS FOR AUTHENTICATION
-- =========================================================

-- Unified user view combining auth and profile data
CREATE OR REPLACE VIEW user_profiles_view AS
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    u.auth_method,
    u.oauth_provider,
    u.email_verified,
    u.is_active,
    u.last_login,
    u.first_name as auth_first_name,
    u.last_name as auth_last_name,
    u.display_name,
    
    -- Student profile data
    sp.first_name as profile_first_name,
    sp.last_name as profile_last_name,
    sp.preferred_name,
    sp.academic_level,
    sp.enrollment_status,
    sp.degree_program,
    sp.primary_major,
    sp.is_onboarding_complete,
    sp.profile_completion_percentage,
    
    u.created_at as user_created_at,
    sp.created_at as profile_created_at,
    u.updated_at as user_updated_at,
    sp.updated_at as profile_updated_at

FROM users u
LEFT JOIN student_profiles sp ON u.id = sp.user_id;

-- =========================================================
-- SECURITY VIEWS
-- =========================================================

-- View for monitoring suspicious activity
CREATE OR REPLACE VIEW security_monitor_view AS
SELECT 
    la.identifier,
    la.ip_address,
    COUNT(*) as attempt_count,
    COUNT(*) FILTER (WHERE NOT success) as failed_attempts,
    MAX(attempted_at) as last_attempt,
    array_agg(DISTINCT failure_reason) FILTER (WHERE failure_reason IS NOT NULL) as failure_reasons,
    array_agg(DISTINCT auth_method) as auth_methods_tried
FROM login_attempts la
WHERE attempted_at > NOW() - INTERVAL '24 hours'
GROUP BY identifier, ip_address
HAVING COUNT(*) FILTER (WHERE NOT success) > 3
ORDER BY failed_attempts DESC, last_attempt DESC;

-- =========================================================
-- COMMENTS AND DOCUMENTATION
-- =========================================================

COMMENT ON TABLE users IS 'Unified authentication table supporting both OAuth and username/password login';
COMMENT ON TABLE email_verification_logs IS 'Tracks email verification tokens and attempts';
COMMENT ON TABLE login_attempts IS 'Security log of all login attempts for monitoring';
COMMENT ON VIEW user_profiles_view IS 'Combined view of authentication and profile data';
COMMENT ON VIEW security_monitor_view IS 'Security monitoring view for suspicious login activity';

-- =========================================================
-- FINAL MIGRATION
-- =========================================================

-- Run the migration for existing users
SELECT migrate_oauth_users();

COMMIT;