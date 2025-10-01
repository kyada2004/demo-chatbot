import customtkinter as ctk
from tkinter import messagebox
from app.core.utils import db_connect
import re
import os


def show_login_window(parent=None, on_success=None, icon_path=None):
    # ⬇️ Import here instead of top-level
    from app.auth.register import show_register_window

    login_frame = ctk.CTkToplevel(parent)
    login_frame.title("Login")
    login_frame.geometry("400x320")
    login_frame.resizable(False, False)

    if icon_path and os.path.exists(icon_path):
        login_frame.iconbitmap(icon_path)

    # Center
    login_frame.update_idletasks()
    w, h = 400, 320
    x = (login_frame.winfo_screenwidth() // 2) - (w // 2)
    y = (login_frame.winfo_screenheight() // 2) - (h // 2)
    login_frame.geometry(f"{w}x{h}+{x}+{y}")

    # Modal
    login_frame.transient(parent)
    login_frame.grab_set()

    # ---------------- UI ----------------
    ctk.CTkLabel(login_frame, text="Gmail:").pack(pady=(20, 5))
    gmail_entry = ctk.CTkEntry(login_frame, width=280)
    gmail_entry.pack()
    gmail_error = ctk.CTkLabel(login_frame, text="", text_color="red")
    gmail_error.pack()

    ctk.CTkLabel(login_frame, text="Password:").pack(pady=(10, 5))
    password_entry = ctk.CTkEntry(login_frame, show="*", width=280)
    password_entry.pack()
    password_error = ctk.CTkLabel(login_frame, text="", text_color="red")
    password_error.pack()

    def is_valid_gmail(email):
        return re.match(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", email)

    def login_action():
        gmail_error.configure(text="")
        password_error.configure(text="")

        gmail = gmail_entry.get().strip()
        password = password_entry.get().strip()

        has_error = False
        if not gmail or not is_valid_gmail(gmail):
            gmail_error.configure(text="Enter a valid Gmail ID")
            has_error = True
        if not password:
            password_error.configure(text="Password required")
            has_error = True

        if has_error:
            return

        try:
            conn = db_connect()
            cur = conn.cursor()
            cur.execute(
                "SELECT first_name, last_name FROM users WHERE gmail=? AND password=?",
                (gmail, password),
            )
            row = cur.fetchone()

            if row:
                login_frame.destroy()
                if on_success:
                    on_success(row[0], row[1], gmail)
            else:
                password_error.configure(text="Invalid Gmail or Password")

        except Exception as e:
            messagebox.showerror("Error", f"Database error:\n{e}")
        finally:
            conn.close()

    # Buttons
    ctk.CTkButton(login_frame, text="Login", width=120, command=login_action).pack(pady=20)

    # 🔹 Switch to Register
    ctk.CTkButton(
        login_frame,
        text="Don’t have an account? Register",
        fg_color="transparent",
        text_color="blue",
        command=lambda: (login_frame.destroy(), show_register_window(parent, on_success, icon_path))
    ).pack(pady=(0, 10))

    parent.wait_window(login_frame)
