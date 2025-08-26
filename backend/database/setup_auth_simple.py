#!/usr/bin/env python3
"""
Database Schema Setup for Authentication System - Simple Version

This script sets up the new authentication tables for username/password login
alongside the existing Microsoft OAuth system.
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

def safe_fetchone_value(cursor_result):
    """Safely extract value from cursor result (handles RealDictRow)"""
    if isinstance(cursor_result, dict):
        return list(cursor_result.values())[0]
    elif cursor_result:
        return cursor_result[0]
    else:
        return None

def setup_auth_schema():
    """Set up authentication schema by running the SQL script"""
    
    print("Setting up authentication schema...")
    print("This will add username/password authentication alongside Microsoft OAuth")
    
    # Read the auth schema SQL file
    sql_file_path = os.path.join(os.path.dirname(__file__), "sql", "auth_schema_update.sql")
    
    if not os.path.exists(sql_file_path):
        print(f"ERROR: SQL file not found at {sql_file_path}")
        return False
    
    try:
        with open(sql_file_path, 'r') as file:
            sql_content = file.read()
        
        print("Loaded SQL schema script")
        
        # Execute the SQL script
        with get_connection() as conn:
            with conn.cursor() as cur:
                print("Executing database schema updates...")
                
                # Execute the entire script
                cur.execute(sql_content)
                
                print("SUCCESS: Database schema updated!")
                
                # Check if migration function worked
                cur.execute("SELECT migrate_oauth_users();")
                migration_result = cur.fetchone()
                migrated_count = safe_fetchone_value(migration_result) or 0
                
                if migrated_count > 0:
                    print(f"Migrated {migrated_count} existing OAuth users to new schema")
                else:
                    print("No existing OAuth users found to migrate")
                
                # Show table status
                auth_tables = ['users', 'email_verification_logs', 'login_attempts']
                print("\nNew authentication tables created:")
                
                for table in auth_tables:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        count_result = cur.fetchone()
                        count = safe_fetchone_value(count_result) or 0
                        print(f"  - {table}: {count} records")
                    except Exception as e:
                        print(f"  - {table}: Error - {e}")
                
                print("\nAuthentication system setup completed!")
                print("\nSummary of changes:")
                print("  * Added 'users' table for unified authentication")
                print("  * Added 'email_verification_logs' table for email tracking")
                print("  * Added 'login_attempts' table for security monitoring")
                print("  * Added authentication functions for registration and verification")
                print("  * Created security views for monitoring")
                print("  * Migrated existing OAuth users to new schema")
                
                conn.commit()
                
        return True
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def verify_schema():
    """Verify that the authentication schema is properly set up"""
    
    print("\nVerifying authentication schema...")
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Check if key tables exist
                tables_to_check = {
                    'users': 'Main authentication table',
                    'email_verification_logs': 'Email verification tracking',
                    'login_attempts': 'Security monitoring',
                    'student_profiles': 'User profiles (should have user_id column)'
                }
                
                all_good = True
                
                for table, description in tables_to_check.items():
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = %s
                        )
                    """, (table,))
                    
                    exists_result = cur.fetchone()
                    exists = safe_fetchone_value(exists_result) or False
                    
                    if exists:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        count_result = cur.fetchone()
                        count = safe_fetchone_value(count_result) or 0
                        print(f"  [OK] {table}: {count} records - {description}")
                    else:
                        print(f"  [ERROR] {table}: Missing - {description}")
                        all_good = False
                
                # Check if student_profiles has user_id column
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'student_profiles' AND column_name = 'user_id'
                """)
                
                if cur.fetchone():
                    print("  [OK] student_profiles.user_id column exists")
                else:
                    print("  [ERROR] student_profiles.user_id column missing")
                    all_good = False
                
                # Check key functions
                functions_to_check = [
                    'create_user_with_verification',
                    'verify_user_email',
                    'log_login_attempt',
                    'migrate_oauth_users'
                ]
                
                print("\nChecking authentication functions:")
                for func in functions_to_check:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM pg_proc p
                            JOIN pg_namespace n ON p.pronamespace = n.oid
                            WHERE p.proname = %s AND n.nspname = 'public'
                        )
                    """, (func,))
                    
                    exists_result = cur.fetchone()
                    exists = safe_fetchone_value(exists_result) or False
                    status = "[OK]" if exists else "[ERROR]"
                    print(f"  {status} {func}")
                    if not exists:
                        all_good = False
                
                if all_good:
                    print("\nAuthentication schema verification completed successfully!")
                    print("All required tables, columns, and functions are present")
                    return True
                else:
                    print("\nSchema verification found issues")
                    print("Some required components are missing")
                    return False
                    
    except Exception as e:
        print(f"Verification error: {e}")
        return False

def main():
    """Main setup function"""
    
    print("=" * 60)
    print("GANNON UNIVERSITY ADVISOR - AUTHENTICATION SETUP")
    print("=" * 60)
    
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found in environment variables")
        print("Please make sure your .env file is configured properly")
        return
    
    print(f"Connecting to database...")
    database_name = DATABASE_URL.split('/')[-1] if '/' in DATABASE_URL else 'Unknown'
    print(f"   Database: {database_name}")
    
    try:
        # Test database connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                db_version_result = cur.fetchone()
                # Handle RealDictRow properly
                if isinstance(db_version_result, dict):
                    db_version = db_version_result.get('version', str(db_version_result))
                else:
                    db_version = str(db_version_result)
                version_parts = db_version.split()
                if len(version_parts) >= 2:
                    print(f"   PostgreSQL Version: {version_parts[1]}")
                else:
                    print(f"   PostgreSQL Version: {db_version[:50]}")
        
        print("Database connection successful\n")
        
        # Run schema setup
        success = setup_auth_schema()
        
        if success:
            # Verify the setup
            verify_schema()
            
            print("\n" + "=" * 60)
            print("AUTHENTICATION SYSTEM SETUP COMPLETE!")
            print("=" * 60)
            print("\nWhat was added:")
            print("* Username/password authentication")
            print("* Email verification system")
            print("* Security monitoring and logging")
            print("* Integration with existing OAuth system")
            
            print("\nNext steps:")
            print("1. Configure SMTP settings in your .env file for email verification")
            print("2. Test registration and login with the new system")
            print("3. Both Microsoft OAuth and username/password will work together")
            
            print("\nSMTP Configuration needed:")
            print("Add these lines to your backend/config/.env file:")
            print("SMTP_USERNAME=your_email@gmail.com")
            print("SMTP_PASSWORD=your_app_password")
            
        else:
            print("\nSchema setup failed. Please check the error messages above.")
        
    except Exception as e:
        print(f"Connection error: {e}")
        print("Please check your DATABASE_URL and ensure PostgreSQL is running")

if __name__ == "__main__":
    main()