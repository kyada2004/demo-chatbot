import sqlite3
import json
from app.core.utils import db_connect

def add_feedback(response_id, user_gmail, rating, conversation_history):
    """Add feedback for a response."""
    try:
        conn = db_connect()
        cursor = conn.cursor()
        conversation_history_json = json.dumps(conversation_history)
        cursor.execute(
            "INSERT INTO feedback (response_id, user_gmail, rating, conversation_history) VALUES (?, ?, ?, ?)",
            (response_id, user_gmail, rating, conversation_history_json),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"[DB Save Error] {e}")
    finally:
        if conn:
            conn.close()