import sqlite3
from app.core.utils import db_connect

def set_user_preference(user_gmail, key, value):
    """Set a preference for a user."""
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO user_preferences (user_gmail, preference_key, preference_value) VALUES (?, ?, ?)",
            (user_gmail, key, value),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"[DB Error] {e}")
    finally:
        if conn:
            conn.close()

def get_user_preference(user_gmail, key):
    """Get a preference for a user."""
    preference = None
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT preference_value FROM user_preferences WHERE user_gmail = ? AND preference_key = ?",
            (user_gmail, key),
        )
        result = cursor.fetchone()
        if result:
            preference = result[0]
    except sqlite3.Error as e:
        print(f"[DB Error] {e}")
    finally:
        if conn:
            conn.close()
    return preference
