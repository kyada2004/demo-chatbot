import sqlite3
from app.core.utils import db_connect

def add_task(user_gmail, task_description, due_date=None):
    """Adds a new task for a user."""
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (user_gmail, task_description, due_date) VALUES (?, ?, ?)",
            (user_gmail, task_description, due_date),
        )
        conn.commit()
        return "Task added successfully!"
    except sqlite3.Error as e:
        return f"Error adding task: {e}"
    finally:
        if conn:
            conn.close()

def get_pending_tasks(user_gmail):
    """Retrieves all pending tasks for a user."""
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, task_description, due_date FROM tasks WHERE user_gmail = ? AND status = 'pending'",
            (user_gmail,),
        )
        return cursor.fetchall()
    except sqlite3.Error as e:
        return f"Error retrieving tasks: {e}"
    finally:
        if conn:
            conn.close()

def update_task_status(task_id, status):
    """Updates the status of a task."""
    try:
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (status, task_id),
        )
        conn.commit()
        return "Task status updated successfully!"
    except sqlite3.Error as e:
        return f"Error updating task status: {e}"
    finally:
        if conn:
            conn.close()
