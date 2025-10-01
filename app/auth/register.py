import customtkinter as ctk
from tkinter import messagebox
import re
import os
from app.core.utils import db_connect


def show_register_window(parent=None, on_success=None, icon_path=None):
    # ⬇️ Import here instead of top-level
    from app.auth.login import show_login_window

    register_frame = ctk.CTkToplevel(parent)
    register_frame.title("Register")
    register_frame.geometry("400x520")
    register_frame.resizable(False, False)

    if icon_path and os.path.exists(icon_path):
        register_frame.iconbitmap(icon_path)

    # Center
    register_frame.update_idletasks()
    w, h = 400, 520
    x = (register_frame.winfo_screenwidth() // 2) - (w // 2)
    y = (register_frame.winfo_screenheight() // 2) - (h // 2)
    register_frame.geometry(f"{w}x{h}+{x}+{y}")

    # Modal
    register_frame.transient(parent)
    register_frame.grab_set()

    # ---------------- UI Fields ----------------
    ctk.CTkLabel(register_frame, text="First Name:").pack(pady=(20, 5))
    first_name_entry = ctk.CTkEntry(register_frame, width=280)
    first_name_entry.pack()
    first_error = ctk.CTkLabel(register_frame, text="", text_color="red")
    first_error.pack()

    ctk.CTkLabel(register_frame, text="Last Name:").pack(pady=(10, 5))
    last_name_entry = ctk.CTkEntry(register_frame, width=280)
    last_name_entry.pack()
    last_error = ctk.CTkLabel(register_frame, text="", text_color="red")
    last_error.pack()

    ctk.CTkLabel(register_frame, text="Gmail:").pack(pady=(10, 5))
    gmail_entry = ctk.CTkEntry(register_frame, width=280)
    gmail_entry.pack()
    gmail_error = ctk.CTkLabel(register_frame, text="", text_color="red")
    gmail_error.pack()

    ctk.CTkLabel(register_frame, text="Password:").pack(pady=(10, 5))
    password_entry = ctk.CTkEntry(register_frame, show="*", width=280)
    password_entry.pack()
    password_error = ctk.CTkLabel(register_frame, text="", text_color="red")
    password_error.pack()

    # ---------------- Validation ----------------
    def is_valid_gmail(email):
        return re.match(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", email)

    def is_strong_password(password):
        return (
            len(password) >= 8
            and re.search(r"[A-Z]", password)
            and re.search(r"[a-z]", password)
            and re.search(r"\d", password)
            and re.search(r"[@$!%*?&]", password)
        )

    def register_action():
        first_error.configure(text="")
        last_error.configure(text="")
        gmail_error.configure(text="")
        password_error.configure(text="")

        first = first_name_entry.get().strip()
        last = last_name_entry.get().strip()
        gmail = gmail_entry.get().strip()
        pwd = password_entry.get().strip()

        has_error = False
        if not first:
            first_error.configure(text="First name required")
            has_error = True
        if not last:
            last_error.configure(text="Last name required")
            has_error = True
        if not gmail or not is_valid_gmail(gmail):
            gmail_error.configure(text="Enter a valid Gmail ID")
            has_error = True
        if not pwd or not is_strong_password(pwd):
            password_error.configure(
                text="Password must be 8+ chars, 1 upper, 1 lower, 1 number, 1 special"
            )
            has_error = True

        if has_error:
            return

        try:
            conn = db_connect()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (first_name, last_name, gmail, password) VALUES (?, ?, ?, ?)",
                (first, last, gmail, pwd),
            )
            conn.commit()
            messagebox.showinfo("Success", "Registration successful!")

            register_frame.destroy()
            if on_success:
                on_success(first, last, gmail)

        except Exception as e:
            if "UNIQUE constraint" in str(e):
                gmail_error.configure(text="Gmail already exists")
            else:
                messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    # Buttons
    ctk.CTkButton(register_frame, text="Register", width=120, command=register_action).pack(pady=20)

    # 🔹 Switch to Login
    ctk.CTkButton(
        register_frame,
        text="Already have an account? Login",
        fg_color="transparent",
        text_color="blue",
        command=lambda: (register_frame.destroy(), show_login_window(parent, on_success, icon_path))
    ).pack(pady=(0, 10))

    parent.wait_window(register_frame)
