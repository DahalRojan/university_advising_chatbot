#!/usr/bin/env python3
"""
Simple Database Connection Test
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
    """Test database connection with simple output"""
    
    print("DATABASE CONNECTION TEST")
    print("=" * 40)
    
    print(f"DATABASE_URL: {DATABASE_URL}")
    
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL is not set!")
        return False
    
    print("Attempting connection...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        print("SUCCESS: Connection established!")
        
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version_result = cur.fetchone()
            print(f"PostgreSQL Version: {version_result}")
            
            # Test existing tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables_result = cur.fetchall()
            print(f"Query returned {len(tables_result)} tables")
            
            # Try to extract table names safely
            tables = []
            for row in tables_result:
                if isinstance(row, dict):
                    tables.append(row.get('table_name', str(row)))
                elif isinstance(row, (list, tuple)):
                    tables.append(row[0])
                else:
                    tables.append(str(row))
            
            print(f"Existing tables: {len(tables)}")
            for table in tables:
                print(f"  - {table}")
        
        conn.close()
        print("Connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Print detailed error info
        if hasattr(e, 'pgcode'):
            print(f"PostgreSQL error code: {e.pgcode}")
        if hasattr(e, 'pgerror'):
            print(f"PostgreSQL error: {e.pgerror}")
        
        print("\nTROUBLESHOoting:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify database 'chatbot_local' exists")
        print("3. Check username/password are correct")
        print("4. Try: psql -h localhost -p 5432 -U postgres -d chatbot_local")
        
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        print("\nDatabase is ready for authentication setup!")
    else:
        print("\nPlease fix database connection before continuing.")
    sys.exit(0 if success else 1)