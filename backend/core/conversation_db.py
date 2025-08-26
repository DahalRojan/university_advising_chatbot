"""
PostgreSQL-only database module for conversation storage
Clean, production-ready implementation
"""
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../configs/.env"))

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required. Please set up Cloud SQL PostgreSQL.")

print("[OK] Using PostgreSQL for conversations")

def get_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"[ERROR] Failed to connect to PostgreSQL: {e}")
        print("[INFO] Make sure your database instance is running and DATABASE_URL is correct")
        raise

def create_table():
    """Create conversation and session_summaries tables"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Create conversations table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS conversation (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    user_email VARCHAR(255) NOT NULL,
                    sender VARCHAR(50) NOT NULL,
                    text TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create session_summaries table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS session_summaries (
                    session_id VARCHAR(255) PRIMARY KEY,
                    user_email VARCHAR(255) NOT NULL,
                    summary TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cur.execute('''
                CREATE INDEX IF NOT EXISTS idx_conversation_session_user 
                ON conversation(session_id, user_email)
            ''')
            
            cur.execute('''
                CREATE INDEX IF NOT EXISTS idx_conversation_user_timestamp 
                ON conversation(user_email, timestamp DESC)
            ''')
            
            cur.execute('''
                CREATE INDEX IF NOT EXISTS idx_session_summaries_user 
                ON session_summaries(user_email)
            ''')
            
            conn.commit()
            print("[OK] PostgreSQL tables and indexes created successfully")

def add_message(session_id, user_email, sender, text):
    """Add a message to the conversation"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO conversation (session_id, user_email, sender, text, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            ''', (session_id, user_email, sender, text, datetime.utcnow()))
            conn.commit()

def get_history(session_id, user_email=None, limit=20):
    """Get conversation history for a session"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if user_email:
                cur.execute('''
                    SELECT sender, text FROM conversation 
                    WHERE session_id = %s AND user_email = %s 
                    ORDER BY timestamp ASC 
                    LIMIT %s
                ''', (session_id, user_email, limit))
            else:
                cur.execute('''
                    SELECT sender, text FROM conversation 
                    WHERE session_id = %s 
                    ORDER BY timestamp ASC 
                    LIMIT %s
                ''', (session_id, limit))
            
            return [{"sender": row["sender"], "text": row["text"]} for row in cur.fetchall()]

def get_user_sessions(user_email, limit=10):
    """Get recent session IDs for a user with summaries"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT DISTINCT c.session_id, 
                       MAX(c.timestamp) as last_message, 
                       s.summary
                FROM conversation c
                LEFT JOIN session_summaries s ON c.session_id = s.session_id
                WHERE c.user_email = %s 
                GROUP BY c.session_id, s.summary
                ORDER BY last_message DESC 
                LIMIT %s
            ''', (user_email, limit))
            
            return [{
                "session_id": row["session_id"], 
                "last_message": row["last_message"].isoformat() if row["last_message"] else None,
                "summary": row["summary"]
            } for row in cur.fetchall()]

def update_session_summary(session_id, user_email, summary):
    """Update or create a session summary"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO session_summaries (session_id, user_email, summary, last_updated)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (session_id) 
                DO UPDATE SET 
                    summary = EXCLUDED.summary,
                    last_updated = EXCLUDED.last_updated
            ''', (session_id, user_email, summary, datetime.utcnow()))
            conn.commit()

def get_session_summary(session_id):
    """Get the summary for a specific session"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT summary FROM session_summaries 
                WHERE session_id = %s
            ''', (session_id,))
            result = cur.fetchone()
            return result["summary"] if result else None

def delete_conversation(session_id, user_email):
    """Delete a conversation and its summary for a specific user"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Delete conversation messages
            cur.execute('''
                DELETE FROM conversation 
                WHERE session_id = %s AND user_email = %s
            ''', (session_id, user_email))
            
            # Delete session summary
            cur.execute('''
                DELETE FROM session_summaries 
                WHERE session_id = %s AND user_email = %s
            ''', (session_id, user_email))
            
            changes = cur.rowcount
            conn.commit()
            return changes > 0

if __name__ == "__main__":
    # Test the database connection and setup
    try:
        print("🔍 Testing PostgreSQL connection...")
        create_table()
        print("🎉 PostgreSQL database setup completed successfully!")
        
        # Test basic operations
        test_session = "test-session-123"
        test_email = "test@example.com"
        
        add_message(test_session, test_email, "user", "Hello, this is a test message!")
        add_message(test_session, test_email, "assistant", "Hello! I received your test message.")
        
        history = get_history(test_session, test_email)
        print(f"[OK] Test conversation created with {len(history)} messages")
        
        sessions = get_user_sessions(test_email)
        print(f"[OK] Found {len(sessions)} sessions for test user")
        
    except Exception as e:
        print(f"[ERROR] Database setup failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure Cloud SQL instance is running")
        print("2. Check DATABASE_URL format: postgresql://user:pass@host:port/dbname")
        print("3. Verify network connectivity to Cloud SQL")
        print("4. Check if psycopg2-binary is installed: pip install psycopg2-binary")