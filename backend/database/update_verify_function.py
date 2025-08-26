#!/usr/bin/env python3
"""
Update verify_user_email function to handle already-verified users correctly
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from features.auth.password_auth import PasswordAuthManager

def update_verify_function():
    """Update the verify_user_email function"""
    
    # Get database connection
    auth_manager = PasswordAuthManager()
    
    function_sql = """
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
    """
    
    try:
        with auth_manager.get_connection() as conn:
            with conn.cursor() as cur:
                print("Updating verify_user_email function...")
                cur.execute(function_sql)
                conn.commit()
                print("Function updated successfully!")
                
    except Exception as e:
        print(f"Error updating function: {e}")
        return False
    
    return True

if __name__ == "__main__":
    update_verify_function()