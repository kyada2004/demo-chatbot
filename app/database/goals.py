import sqlite3
from app.core.utils import db_connect

def add_goal(user_gmail, goal_description):
    """Adds a new goal for a user."""
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO goals (user_gmail, goal_description) VALUES (?, ?)",
            (user_gmail, goal_description),
        )
        conn.commit()
        return "Goal added successfully!"
    except sqlite3.Error as e:
        return f"Error adding goal: {e}"
    finally:
        if conn:
            conn.close()

def get_active_goals(user_gmail):
    """Retrieves all active goals for a user."""
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, goal_description, status FROM goals WHERE user_gmail = ? AND status = 'active'",
            (user_gmail,),
        )
        return cursor.fetchall()
    except sqlite3.Error as e:
        return f"Error retrieving goals: {e}"
    finally:
        if conn:
            conn.close()

def update_goal_status(goal_id, status):
    """Updates the status of a goal."""
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE goals SET status = ? WHERE id = ?",
            (status, goal_id),
        )
        conn.commit()
        return "Goal status updated successfully!"
    except sqlite3.Error as e:
        return f"Error updating goal status: {e}"
    finally:
        if conn:
            conn.close()