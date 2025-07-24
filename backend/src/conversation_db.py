import sqlite3
from datetime import datetime
import os

DB_PATH = "./vector_db/conversations.sqlite"

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_table():
    with get_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS conversation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_email TEXT,
                sender TEXT,
                text TEXT,
                timestamp TEXT
            )
        ''')
        # Add user_email column if it doesn't exist (for existing databases)
        try:
            conn.execute('ALTER TABLE conversation ADD COLUMN user_email TEXT')
        except:
            pass  # Column already exists
            
        # Create session summaries table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS session_summaries (
                session_id TEXT PRIMARY KEY,
                user_email TEXT,
                summary TEXT,
                last_updated TEXT
            )
        ''')

def add_message(session_id, user_email, sender, text):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO conversation (session_id, user_email, sender, text, timestamp) VALUES (?, ?, ?, ?, ?)",
            (session_id, user_email, sender, text, datetime.utcnow().isoformat())
        )

def get_history(session_id, user_email=None, limit=20):
    with get_connection() as conn:
        if user_email:
            cur = conn.execute(
                "SELECT sender, text FROM conversation WHERE session_id = ? AND user_email = ? ORDER BY id ASC LIMIT ?",
                (session_id, user_email, limit)
            )
        else:
            cur = conn.execute(
                "SELECT sender, text FROM conversation WHERE session_id = ? ORDER BY id ASC LIMIT ?",
                (session_id, limit)
            )
        return [{"sender": row[0], "text": row[1]} for row in cur.fetchall()]

def get_user_sessions(user_email, limit=10):
    """Get recent session IDs for a user with summaries"""
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT DISTINCT c.session_id, MAX(c.timestamp) as last_message, s.summary
            FROM conversation c
            LEFT JOIN session_summaries s ON c.session_id = s.session_id
            WHERE c.user_email = ? 
            GROUP BY c.session_id 
            ORDER BY last_message DESC 
            LIMIT ?
        """, (user_email, limit))
        return [{"session_id": row[0], "last_message": row[1], "summary": row[2]} for row in cur.fetchall()]

def update_session_summary(session_id, user_email, summary):
    """Update or create a session summary"""
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO session_summaries (session_id, user_email, summary, last_updated)
            VALUES (?, ?, ?, ?)
        """, (session_id, user_email, summary, datetime.utcnow().isoformat()))

def get_session_summary(session_id):
    """Get the summary for a specific session"""
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT summary FROM session_summaries WHERE session_id = ?",
            (session_id,)
        )
        result = cur.fetchone()
        return result[0] if result else None

def delete_conversation(session_id, user_email):
    """Delete a conversation and its summary for a specific user"""
    with get_connection() as conn:
        # Delete conversation messages
        conn.execute(
            "DELETE FROM conversation WHERE session_id = ? AND user_email = ?",
            (session_id, user_email)
        )
        # Delete session summary
        conn.execute(
            "DELETE FROM session_summaries WHERE session_id = ? AND user_email = ?",
            (session_id, user_email)
        )
        return conn.total_changes > 0
