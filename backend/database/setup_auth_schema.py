#!/usr/bin/env python3
"""
Database Schema Setup for Authentication System

This script sets up the new authentication tables for username/password login
alongside the existing Microsoft OAuth system.

Run this script to add the new authentication features to your database.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../config/.env"))

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def setup_auth_schema():
    """Set up authentication schema by running the SQL script"""
    
    print("🔧 Setting up authentication schema...")
    print("This will add username/password authentication alongside Microsoft OAuth")
    
    # Read the auth schema SQL file
    sql_file_path = Path(__file__).parent / "sql" / "auth_schema_update.sql"
    
    if not sql_file_path.exists():
        print(f"❌ Error: SQL file not found at {sql_file_path}")
        return False
    
    try:
        with open(sql_file_path, 'r') as file:
            sql_content = file.read()
        
        print("📖 Loaded SQL schema script")
        
        # Execute the SQL script
        with get_connection() as conn:
            with conn.cursor() as cur:
                print("🗄️ Executing database schema updates...")
                
                # Execute the entire script
                cur.execute(sql_content)
                
                print("✅ Database schema updated successfully!")
                
                # Check if migration function worked
                cur.execute("SELECT migrate_oauth_users();")
                migration_result = cur.fetchone()
                if isinstance(migration_result, dict):
                    migrated_count = list(migration_result.values())[0]
                else:
                    migrated_count = migration_result[0] if migration_result else 0
                
                if migrated_count > 0:
                    print(f"📊 Migrated {migrated_count} existing OAuth users to new schema")
                else:
                    print("📊 No existing OAuth users found to migrate")
                
                # Show table status
                auth_tables = ['users', 'email_verification_logs', 'login_attempts']
                print("\n📋 New authentication tables created:")
                
                for table in auth_tables:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        count_result = cur.fetchone()
                        if isinstance(count_result, dict):
                            count = list(count_result.values())[0]
                        else:
                            count = count_result[0] if count_result else 0
                        print(f"  ✓ {table}: {count} records")
                    except Exception as e:
                        print(f"  ⚠️ {table}: Error - {e}")
                
                print("\n🎉 Authentication system setup completed!")
                print("\n📝 Summary of changes:")
                print("  • Added 'users' table for unified authentication")
                print("  • Added 'email_verification_logs' table for email tracking")
                print("  • Added 'login_attempts' table for security monitoring")
                print("  • Added authentication functions for registration and verification")
                print("  • Created security views for monitoring")
                print("  • Migrated existing OAuth users to new schema")
                
                conn.commit()
                
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_schema():
    """Verify that the authentication schema is properly set up"""
    
    print("\n🔍 Verifying authentication schema...")
    
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
                    if isinstance(exists_result, dict):
                        exists = list(exists_result.values())[0]
                    else:
                        exists = exists_result[0] if exists_result else False
                    
                    if exists:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        count_result = cur.fetchone()
                        if isinstance(count_result, dict):
                            count = list(count_result.values())[0]
                        else:
                            count = count_result[0] if count_result else 0
                        print(f"  ✅ {table}: {count} records - {description}")
                    else:
                        print(f"  ❌ {table}: Missing - {description}")
                        all_good = False
                
                # Check if student_profiles has user_id column
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'student_profiles' AND column_name = 'user_id'
                """)
                
                if cur.fetchone():
                    print("  ✅ student_profiles.user_id column exists")
                else:
                    print("  ❌ student_profiles.user_id column missing")
                    all_good = False
                
                # Check key functions
                functions_to_check = [
                    'create_user_with_verification',
                    'verify_user_email',
                    'log_login_attempt',
                    'migrate_oauth_users'
                ]
                
                print("\n🔧 Checking authentication functions:")
                for func in functions_to_check:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM pg_proc p
                            JOIN pg_namespace n ON p.pronamespace = n.oid
                            WHERE p.proname = %s AND n.nspname = 'public'
                        )
                    """, (func,))
                    
                    exists_result = cur.fetchone()
                    if isinstance(exists_result, dict):
                        exists = list(exists_result.values())[0]
                    else:
                        exists = exists_result[0] if exists_result else False
                    status = "✅" if exists else "❌"
                    print(f"  {status} {func}")
                    if not exists:
                        all_good = False
                
                if all_good:
                    print("\n🎉 Authentication schema verification completed successfully!")
                    print("✅ All required tables, columns, and functions are present")
                    return True
                else:
                    print("\n⚠️ Schema verification found issues")
                    print("❌ Some required components are missing")
                    return False
                    
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def main():
    """Main setup function"""
    
    print("=" * 60)
    print("🚀 GANNON UNIVERSITY ADVISOR - AUTHENTICATION SETUP")
    print("=" * 60)
    
    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL not found in environment variables")
        print("Please make sure your .env file is configured properly")
        return
    
    print(f"📡 Connecting to database...")
    print(f"   Database: {DATABASE_URL.split('/')[-1] if '/' in DATABASE_URL else 'Unknown'}")
    
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
                print(f"   PostgreSQL Version: {db_version.split()[1] if 'PostgreSQL' in db_version else db_version[:50]}")
        
        print("✅ Database connection successful\n")
        
        # Run schema setup
        success = setup_auth_schema()
        
        if success:
            # Verify the setup
            verify_schema()
            
            print("\n" + "=" * 60)
            print("🎉 AUTHENTICATION SYSTEM SETUP COMPLETE!")
            print("=" * 60)
            print("\n📋 What was added:")
            print("✅ Username/password authentication")
            print("✅ Email verification system")
            print("✅ Security monitoring and logging")
            print("✅ Integration with existing OAuth system")
            
            print("\n📝 Next steps:")
            print("1. Configure SMTP settings in your .env file for email verification")
            print("2. Test registration and login with the new system")
            print("3. Both Microsoft OAuth and username/password will work together")
            
            print("\n🔧 SMTP Configuration needed:")
            print("Add these lines to your backend/config/.env file:")
            print("SMTP_USERNAME=your_email@gmail.com")
            print("SMTP_PASSWORD=your_app_password")
            
        else:
            print("\n❌ Schema setup failed. Please check the error messages above.")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Please check your DATABASE_URL and ensure PostgreSQL is running")

if __name__ == "__main__":
    main()