import sqlite3
import json
from datetime import datetime

def get_user_gmail():
    try:
        with open("session.json", "r") as f:
            session_data = json.load(f)
            return session_data.get("gmail")
    except FileNotFoundError:
        return None

def set_reminder(message, time_str):
    user_gmail = get_user_gmail()
    if not user_gmail:
        return "User not logged in."

    try:
        reminder_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return "Invalid time format. Please use YYYY-MM-DD HH:MM:SS."

    conn = sqlite3.connect("app/database/app.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reminders (user_gmail, reminder_message, reminder_time) VALUES (?, ?, ?)",
        (user_gmail, message, reminder_time),
    )
    conn.commit()
    conn.close()
    return "Reminder set successfully."

def show_reminders():
    user_gmail = get_user_gmail()
    if not user_gmail:
        return "User not logged in."

    conn = sqlite3.connect("app/database/app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, reminder_message, reminder_time FROM reminders WHERE user_gmail = ?", (user_gmail,))
    reminders = cursor.fetchall()
    conn.close()

    if not reminders:
        return "No reminders found."

    return reminders

def delete_reminder(reminder_id):
    user_gmail = get_user_gmail()
    if not user_gmail:
        return "User not logged in."

    conn = sqlite3.connect("app/database/app.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders WHERE id = ? AND user_gmail = ?", (reminder_id, user_gmail))
    conn.commit()
    conn.close()

    if cursor.rowcount > 0:
        return "Reminder deleted successfully."
    else:
        return "Reminder not found or you don't have permission to delete it."