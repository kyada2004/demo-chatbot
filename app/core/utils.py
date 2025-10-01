import asyncio
import edge_tts
import sqlite3
import tkinter.messagebox as mbox
import os
from playsound import playsound

# Constants for DB location
DB_DIR = "app/database"
DB_FILE = os.path.join(DB_DIR, "app.db")

# Ensure the database folder exists
os.makedirs(DB_DIR, exist_ok=True)


async def amain(text, voice="en-US-AriaNeural") -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("speech.mp3")

def say(text):
    """Text-to-speech function."""
    try:
        asyncio.run(amain(text))
        playsound("speech.mp3")
        os.remove("speech.mp3")
    except Exception as e:
        print(f"[TTS Error] {e}")


def db_connect():
    """Connect to SQLite with WAL and threading support."""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")  # Better concurrency
        return conn
    except sqlite3.Error as err:
        show_error("Database Error", str(err))
        return None


def init_db():
    """Initialize the users and responses tables."""
    conn = db_connect()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # Create users table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                gmail TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            );
        """
        )

        # Create responses table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_gmail TEXT NOT NULL,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_gmail TEXT NOT NULL,
                reminder_message TEXT NOT NULL,
                reminder_time DATETIME NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )

        # Add session_id column to responses table if it doesn't exist (for backward compatibility)
        cursor.execute("PRAGMA table_info(responses)")
        columns = [info[1] for info in cursor.fetchall()]
        if "session_id" not in columns:
            cursor.execute(
                "ALTER TABLE responses ADD COLUMN session_id TEXT NOT NULL DEFAULT 'default'"
            )

        # Create user_preferences table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_gmail TEXT NOT NULL,
                preference_key TEXT NOT NULL,
                preference_value TEXT NOT NULL,
                UNIQUE(user_gmail, preference_key)
            );
            """
        )

        # Create feedback table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id INTEGER NOT NULL,
                user_gmail TEXT NOT NULL,
                rating INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (response_id) REFERENCES responses (id)
            );
            """
        )

        # Add conversation_history column to feedback table if it doesn't exist
        cursor.execute("PRAGMA table_info(feedback)")
        columns = [info[1] for info in cursor.fetchall()]
        if "conversation_history" not in columns:
            cursor.execute(
                "ALTER TABLE feedback ADD COLUMN conversation_history TEXT"
            )

        # Create goals table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_gmail TEXT NOT NULL,
                goal_description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_gmail) REFERENCES users (gmail)
            );
            """
        )

        conn.commit()
    except sqlite3.Error as err:
        show_error("DB Init Error", str(err))
    finally:
        conn.close()


def show_error(title, message):
    """Show error popup."""
    try:
        mbox.showerror(title, message)
    except Exception:
        print(f"[ERROR] {title}: {message}")


def show_info(title, message):
    """Show info popup."""
    try:
        mbox.showinfo(title, message)
    except Exception:
        print(f"[INFO] {title}: {message}")
