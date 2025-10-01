import sqlite3
import json
from app.core.utils import db_connect

def create_tables():
    """Create the necessary tables for chat history."""
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_gmail TEXT NOT NULL,
                session_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS last_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_gmail TEXT NOT NULL,
                query TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(f"[DB Error] {e}")
    finally:
        if conn:
            conn.close()

def create_session(user_gmail, session_id):
    """Create a new session for a user."""
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (user_gmail, session_id) VALUES (?, ?)",
            (user_gmail, session_id),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"[DB Error] {e}")
    finally:
        if conn:
            conn.close()

def get_last_session_id(user_gmail):
    """Get the last session ID for a user."""
    session_id = None
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM sessions WHERE user_gmail = ? ORDER BY created_at DESC LIMIT 1",
            (user_gmail,),
        )
        result = cursor.fetchone()
        if result:
            session_id = result[0]
    except sqlite3.Error as e:
        print(f"[DB Error] {e}")
    finally:
        if conn:
            conn.close()
    return session_id

def add_message(session_id, role, content):
    """Add a message to the chat history."""
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"[DB Error] {e}")
    finally:
        if conn:
            conn.close()

def get_chat_history(session_id):
    """Get the chat history for a session."""
    messages = []
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        )
        messages = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"[DB Error] {e}")
    finally:
        if conn:
            conn.close()
    return messages

def add_last_query(user_gmail, query):
    """Add a query to the last_queries table."""
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO last_queries (user_gmail, query) VALUES (?, ?)",
            (user_gmail, query),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"[DB Error] {e}")
    finally:
        if conn:
            conn.close()

def get_last_queries(user_gmail, limit=5):
    """Get the last few queries for a user."""
    queries = []
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT query FROM last_queries WHERE user_gmail = ? ORDER BY created_at DESC LIMIT ?",
            (user_gmail, limit),
        )
        queries = [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"[DB Error] {e}")
    finally:
        if conn:
            conn.close()
    return queries
