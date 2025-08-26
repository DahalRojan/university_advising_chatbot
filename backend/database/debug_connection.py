#!/usr/bin/env python3
"""
Debug Database Connection

This script helps debug database connection issues for the authentication setup.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../config/.env"))

DATABASE_URL = os.getenv("DATABASE_URL")

def test_connection():
    """Test database connection with detailed error reporting"""
    
    print("🔍 DEBUGGING DATABASE CONNECTION")
    print("=" * 50)
    
    # Check if DATABASE_URL is loaded
    print(f"📝 Environment check:")
    print(f"   DATABASE_URL: {DATABASE_URL}")
    print(f"   DATABASE_URL type: {type(DATABASE_URL)}")
    print(f"   DATABASE_URL length: {len(DATABASE_URL) if DATABASE_URL else 0}")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL is not set!")
        return False
    
    print(f"\n🔌 Attempting connection...")
    
    # Test basic connection
    try:
        print("   📡 Connecting with psycopg2...")
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        
        print("   ✅ Connection successful!")
        
        # Test a simple query
        with conn.cursor() as cur:
            print("   🔍 Testing query...")
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            print(f"   📊 PostgreSQL Version: {version}")
            
            # Check if uuid extension is available
            cur.execute("SELECT COUNT(*) FROM pg_extension WHERE extname = 'uuid-ossp'")
            uuid_ext = cur.fetchone()[0]
            print(f"   🔧 UUID extension installed: {'Yes' if uuid_ext > 0 else 'No'}")
            
            # Check existing tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
            print(f"   📋 Existing tables ({len(tables)}): {', '.join(tables[:10])}")
            if len(tables) > 10:
                print(f"       ... and {len(tables) - 10} more")
        
        conn.close()
        print("   🔒 Connection closed successfully")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"   ❌ Operational Error: {e}")
        print(f"   📝 Error code: {e.pgcode}")
        print(f"   📝 Error details: {e.pgerror}")
        
        # Common issues and solutions
        print(f"\n🔧 COMMON SOLUTIONS:")
        print(f"   1. Check if PostgreSQL is running: `pg_ctl status`")
        print(f"   2. Check if database exists: `psql -l`")
        print(f"   3. Check connection: `psql {DATABASE_URL}`")
        print(f"   4. Check password: Make sure password in DATABASE_URL is correct")
        
        return False
        
    except psycopg2.Error as e:
        print(f"   ❌ PostgreSQL Error: {e}")
        print(f"   📝 Error class: {type(e).__name__}")
        return False
        
    except Exception as e:
        print(f"   ❌ Unexpected Error: {e}")
        print(f"   📝 Error type: {type(e).__name__}")
        return False

def test_manual_connection():
    """Test connection with individual components"""
    print(f"\n🧪 TESTING MANUAL CONNECTION")
    print("=" * 50)
    
    # Parse DATABASE_URL manually
    if DATABASE_URL.startswith('postgresql://'):
        import urllib.parse as urlparse
        url = urlparse.urlparse(DATABASE_URL)
        
        print(f"📝 Connection details:")
        print(f"   Host: {url.hostname}")
        print(f"   Port: {url.port}")
        print(f"   Database: {url.path[1:] if url.path else 'postgres'}")  # Remove leading /
        print(f"   Username: {url.username}")
        print(f"   Password: {'*' * len(url.password) if url.password else 'None'}")
        
        try:
            # Connect with individual parameters
            conn = psycopg2.connect(
                host=url.hostname,
                port=url.port or 5432,
                database=url.path[1:] if url.path else 'postgres',
                user=url.username,
                password=url.password,
                cursor_factory=RealDictCursor
            )
            
            print("   ✅ Manual connection successful!")
            conn.close()
            return True
            
        except Exception as e:
            print(f"   ❌ Manual connection failed: {e}")
            return False

def main():
    """Main debug function"""
    
    print("DATABASE CONNECTION DEBUGGER")
    print("=" * 60)
    
    # Test environment loading
    if not test_connection():
        # Try manual connection if first method fails
        if not test_manual_connection():
            print(f"\n❌ Both connection methods failed")
            print(f"\n🔧 TROUBLESHOOTING STEPS:")
            print(f"1. Verify PostgreSQL is running:")
            print(f"   - Windows: Check Services or run `pg_ctl status`")
            print(f"   - Check process: `tasklist | findstr postgres`")
            
            print(f"\n2. Test direct connection:")
            print(f"   psql -h localhost -p 5432 -U postgres -d chatbot_local")
            
            print(f"\n3. Check database exists:")
            print(f"   psql -h localhost -p 5432 -U postgres -l")
            
            print(f"\n4. Create database if needed:")
            print(f"   createdb -h localhost -p 5432 -U postgres chatbot_local")
            
            return
    
    print(f"\n✅ DATABASE CONNECTION IS WORKING!")
    print(f"The authentication setup should work now.")

if __name__ == "__main__":
    main()