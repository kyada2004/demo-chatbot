# app/core/main.py
import pvporcupine
import struct
import asyncio
import customtkinter as ctk
from tkinter import scrolledtext, messagebox, filedialog, Toplevel, Label
import tkinter as tk
import speech_recognition as sr
import datetime
import threading
import webbrowser
import queue
import re
import os
import json
import requests
import time

from PIL import Image, ImageTk
import io
from app.database.chat_history import create_tables, add_message, get_chat_history
from app.database.goals import get_active_goals
from app.features.rag import RAG
from app.auth.login import show_login_window
from app.auth.register import show_register_window
from app.core.utils import say, db_connect, init_db
from app.features.greetme import greetMe
from app.features.calendar import show_reminders
from app.features.weather import handle_weather_query
from app.features.ai import get_ai_response
from app.features.image_generate import generate_image
from langdetect import detect
from deep_translator import GoogleTranslator
import edge_tts

import tempfile
from app.core.agent import AIAgent
from app.database.feedback import add_feedback
from app.core.input_handler import process_input
import html  # required for escaping sanitized text
import textwrap

speech_queue = queue.Queue()
SESSION_FILE = "session.json"


def speech_worker():
    while True:
        text = speech_queue.get()
        if text is None:
            break
        try:
            say(text)
        except Exception as e:
            print(f"[Speech Worker Error] {e}")


threading.Thread(target=speech_worker, daemon=True).start()



class ChatApplication(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("Light")
        self.title("Jenny AI Chatbot")
        self.geometry("900x650")
        self.minsize(800, 600)

        self.icon_path = os.path.join("app", "static", "ai.ico")
        self.current_user = None
        self.session_id = None
        self.dropdown_menu = None
        self.history_sidebar = None
        self.guest_question_count = 0
        self.max_guest_questions = 10
        self.image_generation_count = 0
        self.image_limit_logged_in = 5
        self.message_history = []
        self.request_tracker = {}
        self.start_time = None

        self.rag = RAG()
        self.agent = AIAgent(self, self.rag)
        self.response_queue = queue.Queue()

        self.setup_ui()
        init_db()
        create_tables()
        self.auto_login()
        greetMe()
        self._check_response_queue()
        # self.start_wake_word_listener()

    def start_wake_word_listener(self):
        threading.Thread(target=self.listen_for_wake_word, daemon=True).start()

    def listen_for_wake_word(self):
        # TODO: Replace with your Picovoice Access Key
        PICOVOICE_ACCESS_KEY = "YOUR_PICOVOICE_ACCESS_KEY"
        # TODO: To create a custom keyword file for "Hey Jenny", go to the Picovoice Console:
        # https://console.picovoice.ai/
        keyword_paths = [pvporcupine.KEYWORD_PATHS["porcupine"]]

        if PICOVOICE_ACCESS_KEY == "YOUR_PICOVOICE_ACCESS_KEY":
            print("[Wake Word] Please replace the placeholder access key in app/core/main.py")
            return

        try:
            porcupine = pvporcupine.create(
                access_key=PICOVOICE_ACCESS_KEY,
                keyword_paths=keyword_paths
            )

            pa = pyaudio.PyAudio()
            audio_stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length
            )

            print("[Wake Word] Listening for 'Porcupine'...")

            while True:
                if self.wake_word_enabled.get():
                    pcm = audio_stream.read(porcupine.frame_length)
                    pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

                    keyword_index = porcupine.process(pcm)

                    if keyword_index >= 0:
                        print("[Wake Word] Detected 'Porcupine'")
                        self.voice_command()
                else:
                    time.sleep(0.1)

        except Exception as e:
            print(f"[Wake Word Error] {e}")

    def setup_ui(self):
        if os.path.exists(self.icon_path):
            try:
                self.iconbitmap(self.icon_path)
            except Exception:
                pass

        self.setup_navbar()
        self.setup_sidebar()
        self.setup_main_frame()
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def auto_login(self):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    data = json.load(f)
                exp = datetime.datetime.strptime(data["expires_at"], "%Y-%m-%d")
                if datetime.datetime.now() <= exp:
                    self.login_user(data["first_name"], data["last_name"], data["gmail"])
            except Exception as e:
                print(f"[AutoLogin Error] {e}")

    def save_session(self):
        if self.current_user:
            expire_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime(
                "%Y-%m-%d"
            )
            session = {
                "first_name": self.current_user["first_name"],
                "last_name": self.current_user["last_name"],
                "gmail": self.current_user["gmail"],
                "expires_at": expire_date,
            }
            try:
                with open(SESSION_FILE, "w") as f:
                    json.dump(session, f)
            except Exception as e:
                print(f"[Save Session Error] {e}")

    def clear_session(self):
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
            except Exception as e:
                print(f"[Clear Session Error] {e}")

    def setup_navbar(self):
        self.navbar = ctk.CTkFrame(self, height=55, fg_color=["#FFFFFF", "#2C2F33"])  # White navbar
        self.navbar.pack(fill="x", side="top")

        self.title_label = ctk.CTkLabel(
            self.navbar,
            text="🧐 Jenny AI Chatbot",
            font=("Segoe UI", 20, "bold"),
            text_color=["#000000", "#FFFFFF"],
        )
        self.title_label.pack(side="left", padx=20, pady=5)

        self.right_frame = ctk.CTkFrame(self.navbar, fg_color="transparent")
        self.right_frame.pack(side="right", padx=15)

        self.speech_enabled = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.right_frame, text="🔊 Enable Speech", variable=self.speech_enabled, font=("Segoe UI", 12), text_color=["#000000", "#FFFFFF"]).pack(side="left", padx=10)
        self.wake_word_enabled = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.right_frame, text="👂 Wake Word", variable=self.wake_word_enabled, font=("Segoe UI", 12), text_color=["#000000", "#FFFFFF"]).pack(side="left", padx=10)

        self.theme_button = ctk.CTkButton(self.right_frame, text="Toggle Theme", command=self.toggle_theme)
        self.theme_button.pack(side="left", padx=10)

        self.user_button_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.user_button_frame.pack(side="left")

        self.update_navbar_buttons()

    def setup_sidebar(self):
        self.history_sidebar = ctk.CTkScrollableFrame(
            self, width=260, fg_color=["#F7F7F7", "#23272A"], corner_radius=0
        )
        self.history_sidebar.pack(side="left", fill="y")
        self.history_sidebar.pack_forget()

        self.tasks_sidebar = ctk.CTkScrollableFrame(
            self, width=260, fg_color=["#F7F7F7", "#23272A"], corner_radius=0
        )
        self.tasks_sidebar.pack(side="left", fill="y")
        self.tasks_sidebar.pack_forget()

        self.reminders_sidebar = ctk.CTkScrollableFrame(
            self, width=260, fg_color=["#F7F7F7", "#23272A"], corner_radius=0
        )
        self.reminders_sidebar.pack(side="left", fill="y")
        self.reminders_sidebar.pack_forget()

    def setup_main_frame(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=["#FFFFFF", "#2C2F33"])
        self.main_frame.pack(padx=10, pady=(10, 0), fill="both", expand=True, side="left")

        self.chat_display_frame = ctk.CTkFrame(self.main_frame, fg_color=["#FFFFFF", "#2C2F33"])
        self.chat_display_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        self.chat_area = ctk.CTkTextbox(
            self.chat_display_frame,
            font=("Courier New", 12),
            wrap=tk.WORD,
            fg_color=["#FFFFFF", "#2C2F33"],
            text_color=["#000000", "#FFFFFF"],
        )
        self.chat_area.pack(fill="both", expand=True)
        self.chat_area.configure(state="disabled")

        self.thinking_label = ctk.CTkLabel(
            self.main_frame, text="Jenny is thinking...", font=("Segoe UI", 12, "italic"), text_color=["#444444", "#FFFFFF"]
        )

        self.bottom_frame = ctk.CTkFrame(self.main_frame, fg_color=["#F0F0F0", "#23272A"])
        self.bottom_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.input_entry = ctk.CTkEntry(
            self.bottom_frame,
            height=48,
            font=("Segoe UI", 14),
            placeholder_text="Message Jenny...",
            text_color=["#000000", "#FFFFFF"],
            fg_color=["#FFFFFF", "#2C2F33"],
            border_color=["#CCCCCC", "#2C2F33"],
            corner_radius=15,
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", lambda e: self.process_command())

        # Buttons styled light
        ctk.CTkButton(
            self.bottom_frame,
            text="📁 Upload",
            width=80,
            height=48,
            command=self.upload_file,
            font=("Segoe UI", 14),
            corner_radius=15,
            fg_color=["#E6E6E6", "#2C2F33"],
            text_color=["#000000", "#FFFFFF"],
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            self.bottom_frame,
            text="🎤",
            width=45,
            height=48,
            command=self.voice_command,
            font=("Segoe UI", 16),
            corner_radius=15,
            fg_color=["#E6E6E6", "#2C2F33"],
            text_color=["#000000", "#FFFFFF"],
        ).pack(side="left")

        ctk.CTkButton(
            self.bottom_frame,
            text="Send",
            width=80,
            height=48,
            command=self.process_command,
            font=("Segoe UI", 14),
            corner_radius=15,
            fg_color=["#0078D7", "#0078D7"],
            text_color=["#FFFFFF", "#FFFFFF"],
        ).pack(side="left", padx=(10, 0))



    def upload_file(self):
        file_paths = filedialog.askopenfilenames(title="Select file(s)")
        if file_paths:
            self.chat_area.configure(state="normal")
            for file_path in file_paths:
                try:
                    self.rag.index_document(file_path)
                    self.chat_area.insert(tk.END, f"✅ Successfully indexed {os.path.basename(file_path)}\n\n")
                except Exception as e:
                    self.chat_area.insert(tk.END, f"❌ Failed to index {os.path.basename(file_path)}: {e}\n\n")
            self.chat_area.configure(state="disabled")
            self.chat_area.see(tk.END)



    def update_navbar_buttons(self):
        for widget in self.user_button_frame.winfo_children():
            widget.destroy()

        if self.current_user:
            initials = (self.current_user["first_name"][:1] + self.current_user["last_name"][:1]).upper()
            profile_btn = ctk.CTkButton(
                self.user_button_frame,
                text=f"👤 {initials}",
                width=50,
                command=self.toggle_profile_dropdown,
                corner_radius=30,
                font=("Segoe UI", 14),
            )
            profile_btn.pack(side="left", padx=5)

            self.dropdown_menu = tk.Menu(self, tearoff=0)
            self.dropdown_menu.add_command(label="History", command=self.toggle_history_sidebar)
            self.dropdown_menu.add_command(label="Tasks", command=self.toggle_tasks_sidebar)
            self.dropdown_menu.add_command(label="Reminders", command=self.toggle_reminders_sidebar)
            self.dropdown_menu.add_command(label="Logout", command=self.logout_user)
        else:
            ctk.CTkButton(self.user_button_frame, text="Register", width=70, command=self.show_register).pack(side="left", padx=5)
            ctk.CTkButton(self.user_button_frame, text="Login", width=70, command=self.show_login).pack(side="left", padx=5)

    def toggle_profile_dropdown(self):
        try:
            x = self.user_button_frame.winfo_rootx()
            y = self.user_button_frame.winfo_rooty() + self.user_button_frame.winfo_height()
            self.dropdown_menu.tk_popup(x, y)
        finally:
            self.dropdown_menu.grab_release()

    def save_query_response(self, user_gmail, session_id, question, answer):
        response_id = None
        conn = None
        try:
            conn = db_connect()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO responses (user_gmail, session_id, question, answer, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (user_gmail, session_id, question, answer),
            )
            conn.commit()
            response_id = cursor.lastrowid
        except Exception as e:
            print(f"[DB Save Error] {e}")
        finally:
            if conn:
                conn.close()
        return response_id

    def center_window(self, window, width, height):
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def show_login(self):
        show_login_window(parent=self, on_success=self._handle_auth_success, icon_path=self.icon_path)

    def show_register(self):
        show_register_window(parent=self, on_success=self._handle_auth_success, icon_path=self.icon_path)

    def _handle_auth_success(self, first_name, last_name, gmail):
        self.login_user(first_name, last_name, gmail)
        self.focus_set()
        self.deiconify()
        self.respond(f"✅ Welcome, {first_name}! You are now logged in.")

    def login_user(self, first_name, last_name, gmail):
        self.current_user = {"first_name": first_name, "last_name": last_name, "gmail": gmail}
        self.session_id = self.get_or_create_session(gmail)
        self.agent.load_user_preferences(gmail)
        self.update_navbar_buttons()
        self.save_session()
        self.load_chat_history(self.session_id)

    def get_or_create_session(self, user_gmail):
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM sessions WHERE user_gmail = ? ORDER BY created_at DESC LIMIT 1", (user_gmail,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            cursor.execute("INSERT INTO sessions (user_gmail, session_id) VALUES (?, ?)", (user_gmail, datetime.datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            return cursor.lastrowid

    def logout_user(self):
        self.current_user = None
        self.session_id = None
        self.update_navbar_buttons()
        self.history_sidebar.pack_forget()
        self.clear_session()
        self.chat_area.configure(state="normal")
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.configure(state="disabled")
        self.message_history = []
        self.respond("You have been logged out.")

    def handle_image_generation(self, query):
        limit = self.image_limit_logged_in if self.current_user else self.image_limit_guest
        if self.image_generation_count >= limit:
            return "⚠️ You have reached the image generation limit. Please login or wait."

        match = re.search(r"(generate|create) image(?: of| for| with)? (.+)", query.lower())
        prompt = match.group(2) if match else query.replace("generate image", "").replace("create image", "").strip()

        if not prompt:
            return "Please specify what you want to generate."

        image_response = generate_image(prompt)
        image_path = image_response.get('image')

        if not image_path:
            error_message = image_response.get('error', 'Unknown error')
            return f"❌ Failed to generate image: {error_message}"

        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            image_pil_preview = Image.open(io.BytesIO(image_data)).resize((256, 256))
            image_tk_preview = ImageTk.PhotoImage(image_pil_preview)

            self.chat_area.configure(state="normal")
            image_label = tk.Label(self.chat_area, image=image_tk_preview, cursor="hand2", bg="#9C9C9C")
            image_label.image = image_tk_preview
            image_label.pack_propagate(False)
            image_label.bind("<Button-1>", lambda e, data=image_data: self.open_zoom_window(data))
            self.chat_area.window_create(tk.END, window=image_label)
            self.chat_area.configure(state="disabled")
            self.chat_area.see(tk.END)

            if not hasattr(self, "image_refs"):
                self.image_refs = []
            self.image_refs.append(image_tk_preview)

            self.image_generation_count += 1
            if self.speech_enabled.get():
                speech_queue.put("Image generated successfully.")

            return image_path

        except Exception as e:
            print(f"[Image Display Error] {e}")
            return "❌ Failed to display image."

    def toggle_tasks_sidebar(self):
        if self.tasks_sidebar.winfo_ismapped():
            self.tasks_sidebar.pack_forget()
        else:
            self.populate_tasks_sidebar()
            self.tasks_sidebar.pack(side="left", fill="y")

    def populate_tasks_sidebar(self):
        for widget in self.tasks_sidebar.winfo_children():
            widget.destroy()

        back_btn = ctk.CTkButton(
            self.tasks_sidebar,
            text="⬅ Back",
            command=lambda: self.tasks_sidebar.pack_forget(),
            fg_color=["#E6E6E6", "#2C2F33"],
            text_color=["#000000", "#FFFFFF"],
            corner_radius=10,
            width=80,
        )
        back_btn.pack(pady=8, padx=10, anchor="w")

        if not self.current_user or not self.current_user.get("gmail"):
            ctk.CTkLabel(self.tasks_sidebar, text="Login to view tasks").pack(pady=10)
            return

        active_goals = get_active_goals(self.current_user['gmail'])

        if not active_goals:
            ctk.CTkLabel(self.tasks_sidebar, text="No active tasks.").pack(pady=10)
            return

        ctk.CTkLabel(self.tasks_sidebar, text=f"Tasks for {self.current_user['first_name']}", font=("Segoe UI", 13, "bold")).pack(pady=8)

        for goal_id, desc, status in active_goals:
            goal_frame = ctk.CTkFrame(self.tasks_sidebar, fg_color=["#F0F0F0", "#23272A"], corner_radius=8)
            goal_frame.pack(pady=2, padx=5, fill="x")
            ctk.CTkLabel(goal_frame, text=f"ID: {goal_id} - {desc}").pack(side="left", padx=10, pady=5)

    def toggle_reminders_sidebar(self):
        if self.reminders_sidebar.winfo_ismapped():
            self.reminders_sidebar.pack_forget()
        else:
            self.populate_reminders_sidebar()
            self.reminders_sidebar.pack(side="left", fill="y")

    def populate_reminders_sidebar(self):
        for widget in self.reminders_sidebar.winfo_children():
            widget.destroy()

        back_btn = ctk.CTkButton(
            self.reminders_sidebar,
            text="⬅ Back",
            command=lambda: self.reminders_sidebar.pack_forget(),
            fg_color=["#E6E6E6", "#2C2F33"],
            text_color=["#000000", "#FFFFFF"],
            corner_radius=10,
            width=80,
        )
        back_btn.pack(pady=8, padx=10, anchor="w")

        if not self.current_user or not self.current_user.get("gmail"):
            ctk.CTkLabel(self.reminders_sidebar, text="Login to view reminders").pack(pady=10)
            return

        reminders = show_reminders()

        if isinstance(reminders, str):
            ctk.CTkLabel(self.reminders_sidebar, text=reminders).pack(pady=10)
            return

        ctk.CTkLabel(self.reminders_sidebar, text=f"Reminders for {self.current_user['first_name']}", font=("Segoe UI", 13, "bold")).pack(pady=8)

        for r_id, message, time in reminders:
            reminder_frame = ctk.CTkFrame(self.reminders_sidebar, fg_color=["#F0F0F0", "#23272A"], corner_radius=8)
            reminder_frame.pack(pady=2, padx=5, fill="x")
            ctk.CTkLabel(reminder_frame, text=f"ID: {r_id} - {message} at {time}").pack(side="left", padx=10, pady=5)

    def open_zoom_window(self, image_data):
        try:
            zoom_win = Toplevel(self)
            zoom_win.title("Zoomed Image")
            zoom_win.geometry("600x600")
            if os.path.exists(self.icon_path):
                try:
                    zoom_win.iconbitmap(self.icon_path)
                except Exception:
                    pass

            image_pil = Image.open(io.BytesIO(image_data))
            image_tk = ImageTk.PhotoImage(image_pil)

            img_label = tk.Label(zoom_win, image=image_tk)
            img_label.image = image_tk
            img_label.pack(padx=10, pady=10, expand=True)

            def download_image():
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".png",
                    filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
                )
                if file_path:
                    try:
                        image_pil.save(file_path)
                        messagebox.showinfo("Saved", f"Image saved to:\n{file_path}")
                    except Exception as e:
                        messagebox.showerror("Error", f"Could not save image: {e}")

            download_btn = ctk.CTkButton(zoom_win, text="⬇️ Download Image", command=download_image)
            download_btn.pack(pady=(5, 15))

        except Exception as e:
            messagebox.showerror("Error", f"Zoom view failed: {e}")

    def toggle_history_sidebar(self):
        if self.history_sidebar.winfo_ismapped():
            self.history_sidebar.pack_forget()
        else:
            self.populate_history_sidebar()
            self.history_sidebar.pack(side="left", fill="y")

    def populate_history_sidebar(self):
        for widget in self.history_sidebar.winfo_children():
            widget.destroy()

        back_btn = ctk.CTkButton(
            self.history_sidebar,
            text="⬅ Back",
            command=lambda: self.history_sidebar.pack_forget(),
            fg_color=["#E6E6E6", "#2C2F33"],
            text_color=["#000000", "#FFFFFF"],
            corner_radius=10,
            width=80,
        )
        back_btn.pack(pady=8, padx=10, anchor="w")

        if not self.current_user or not self.current_user.get("gmail"):
            ctk.CTkLabel(self.history_sidebar, text="Login to view history").pack(pady=10)
            return

        conn = None
        try:
            conn = db_connect()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT session_id FROM responses
                WHERE user_gmail = ?
                ORDER BY session_id DESC
                LIMIT 30
                """,
                (self.current_user["gmail"],),
            )
            sessions = cursor.fetchall()

            if not sessions:
                ctk.CTkLabel(self.history_sidebar, text="No history found.").pack(pady=10)
                return

            ctk.CTkLabel(self.history_sidebar, text=f"📜 History for {self.current_user['first_name']}", font=("Segoe UI", 13, "bold")).pack(pady=8)

            for session in sessions:
                session_id = session[0]
                btn = ctk.CTkButton(
                    self.history_sidebar,
                    text=session_id,
                    command=lambda s=session_id: (self.load_chat_history(s), self.history_sidebar.pack_forget()),
                    corner_radius=8,
                    fg_color=["#F0F0F0", "#23272A"],
                    text_color=["#000000", "#FFFFFF"],
                )
                btn.pack(pady=2, padx=5, fill="x")

        except Exception as e:
            print("[History Error]", e)
        finally:
            if conn:
                conn.close()

    def load_chat_history(self, session_id):
        self.chat_area.configure(state="normal")
        self.chat_area.delete("1.0", tk.END)
        self.message_history = []

        messages = get_chat_history(session_id)
        for role, content in messages:
            if role == "user":
                self.chat_area.insert(tk.END, f"You: {content}\n")
            else:
                self.chat_area.insert(tk.END, f"Jenny: {content}\n\n")
        self.chat_area.configure(state="disabled")
        self.chat_area.see(tk.END)

        self.session_id = session_id

        self.request_tracker = {}

    def process_command(self, query=None):
        # Data Flow Step 1: Input Handling
        # The user's raw query is processed by the input_handler.
        # This includes sanitization, spell checking, and a safety check.
        raw_query = query if query is not None else self.input_entry.get().strip()
        if not raw_query:
            return

        processed_query, error_message = process_input(raw_query)

        if error_message:
            self.respond(f"⚠️ {error_message}")
            if not query: # Clear input field only if it was a typed message
                self.input_entry.delete(0, tk.END)
            return

        # Rate limiting
        user_id = self.current_user["gmail"] if self.current_user else "guest"
        current_time = datetime.datetime.now()
        if user_id not in self.request_tracker:
            self.request_tracker[user_id] = []
        self.request_tracker[user_id] = [t for t in self.request_tracker[user_id] if (current_time - t).total_seconds() < 60]
        if len(self.request_tracker[user_id]) >= 10: # 10 requests per minute
            self.respond("⚠️ You are making too many requests. Please wait a moment.")
            return
        self.request_tracker[user_id].append(current_time)

        # Session management
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if self.session_id != current_date:
            self.session_id = current_date
            self.chat_area.configure(state="normal")
            self.chat_area.delete("1.0", tk.END)
            self.chat_area.configure(state="disabled")
            self.message_history = []

        # Display user message
        self.chat_area.configure(state="normal")
        self.chat_area.tag_config("user", foreground="#0078D7")
        self.chat_area.insert(tk.END, f"You: {processed_query}\n", "user")
        self.chat_area.configure(state="disabled")
        self.message_history.append({"role": "user", "content": processed_query})
        if self.current_user:
            add_message(self.session_id, "user", processed_query)
        if not query: # Clear input field only if it was a typed message
            self.input_entry.delete(0, tk.END)

        # Data Flow Step 2 & 3: Intent Detection and Decision Making
        # The processed query is sent to the AIAgent, which uses the PlanningEngine
        # to determine the user's intent and create a plan.
        self.thinking_label.pack(pady=5)
        self.start_time = time.perf_counter()
        threading.Thread(target=self._process_query_thread, args=(processed_query,)).start()

    def _process_query_thread(self, query):
        try:
            asyncio.run(self.agent.process_query(query, self.response_queue))
        except Exception as e:
            print(f"[Agent Error] {e}")
            self.response_queue.put("Sorry, I encountered an error. Please try again.")
            self.response_queue.put(None)

    def _check_response_queue(self):
        try:
            chunk = self.response_queue.get(block=False)
            if chunk is None:
                if self.start_time:
                    end_time = time.perf_counter()
                    elapsed_time = (end_time - self.start_time) * 1_000_000  # in microseconds
                    print(f"Response took: {elapsed_time:.2f} microseconds")
                    self.start_time = None
                self.thinking_label.pack_forget()
                # Save the complete response to history
                complete_response = self.chat_area.get("end-2l", "end-1c").strip()
                if self.current_user:
                    add_message(self.session_id, "assistant", complete_response)
                self.message_history.append({"role": "assistant", "content": complete_response})
                return

            if self.thinking_label.winfo_ismapped():
                self.thinking_label.pack_forget()
                self.chat_area.configure(state="normal")
                self.chat_area.insert(tk.END, "Jenny: ")
                self.chat_area.configure(state="disabled")

            self.chat_area.configure(state="normal")
            self.chat_area.tag_config("jenny", foreground="#000000")
            self.chat_area.insert(tk.END, chunk, "jenny")
            self.chat_area.configure(state="disabled")
            self.chat_area.see(tk.END)

        except queue.Empty:
            pass
        self.after(100, self._check_response_queue)

    def _update_chat_with_response(self, answer, query):
        self.thinking_label.pack_forget()
        
        response_to_save = answer
        display_answer = answer

        if isinstance(answer, dict):
            if "itinerary" in answer:
                self._display_itinerary_table(answer["itinerary"])
                response_to_save = json.dumps(answer)
            elif "error" in answer:
                self.respond(f"Trip Planner Error: {answer['error']}")
                response_to_save = json.dumps(answer)
            else:
                display_answer = json.dumps(answer, indent=2)
                response_to_save = json.dumps(answer)

        if answer:
            if "itinerary" not in answer:
                self.respond(display_answer)
        else:
            fallback = "I'm sorry, I don't understand that. Can you please rephrase?"
            self.respond(fallback)

        if self.current_user:
            add_message(self.session_id, "assistant", response_to_save or "")
            response_id = self.save_query_response(self.current_user["gmail"], self.session_id, query, response_to_save or "")
            if response_id:
                self.add_feedback_buttons(response_id)
            if self.history_sidebar.winfo_ismapped():
                self.populate_history_sidebar()
        else:
            self.guest_question_count += 1
            if self.guest_question_count >= self.max_guest_questions:
                self.respond("⚠️ You've reached the free limit. Please log in to continue.")
                self.after(1000, self.show_login)

    def _display_itinerary_table(self, itinerary):
        self.chat_area.configure(state="normal")
        self.chat_area.insert(tk.END, "Here is your trip itinerary:\n\n")
        
        # Define table headers
        headers = ["Day", "Morning", "Afternoon", "Evening"]
        col_widths = [5, 30, 30, 30]

        # Header
        header_line = ""
        for i, header in enumerate(headers):
            header_line += f"{header:<{col_widths[i]}} "
        self.chat_area.insert(tk.END, header_line + "\n")
        self.chat_area.insert(tk.END, "-" * sum(col_widths) + "\n")

        # Table content
        for day_plan in itinerary:
            day = str(day_plan.get("day", ""))
            morning = day_plan.get("morning", "")
            afternoon = day_plan.get("afternoon", "")
            evening = day_plan.get("evening", "")

            # Wrap text
            morning_lines = textwrap.wrap(morning, width=col_widths[1])
            afternoon_lines = textwrap.wrap(afternoon, width=col_widths[2])
            evening_lines = textwrap.wrap(evening, width=col_widths[3])

            max_lines = max(len(morning_lines), len(afternoon_lines), len(evening_lines), 1)

            for i in range(max_lines):
                day_str = f"{day:<{col_widths[0]}} " if i == 0 else " " * (col_widths[0] + 1)
                morning_str = f"{morning_lines[i]:<{col_widths[1]}} " if i < len(morning_lines) else " " * (col_widths[1] + 1)
                afternoon_str = f"{afternoon_lines[i]:<{col_widths[2]}} " if i < len(afternoon_lines) else " " * (col_widths[2] + 1)
                evening_str = f"{evening_lines[i]:<{col_widths[3]}} " if i < len(evening_lines) else ""
                self.chat_area.insert(tk.END, f"{day_str}{morning_str}{afternoon_str}{evening_str}\n")
            
            self.chat_area.configure(state="disabled")
        self.chat_area.see(tk.END)

    def add_feedback_buttons(self, response_id):
        feedback_frame = ctk.CTkFrame(self.chat_area, fg_color="transparent")
        thumb_up_btn = ctk.CTkButton(feedback_frame, text="👍", width=30, command=lambda: self.handle_feedback(response_id, 1, feedback_frame))
        thumb_up_btn.pack(side="left", padx=5)
        thumb_down_btn = ctk.CTkButton(feedback_frame, text="👎", width=30, command=lambda: self.handle_feedback(response_id, -1, feedback_frame))
        thumb_down_btn.pack(side="left", padx=5)
        self.chat_area.configure(state="normal")
        self.chat_area.window_create(tk.END, window=feedback_frame)
        self.chat_area.insert(tk.END, "\n\n")
        self.chat_area.configure(state="disabled")

    def handle_feedback(self, response_id, rating, frame):
        history_json = json.dumps(self.message_history)
        try:
            add_feedback(response_id, self.current_user["gmail"], rating, history_json)
        except Exception as e:
            print(f"[Feedback Error] {e}")
        for widget in frame.winfo_children():
            widget.configure(state="disabled")

    def respond(self, message):
        self.chat_area.configure(state="normal")
        self.chat_area.insert(tk.END, f"Jenny: {message} \n")
        self.chat_area.configure(state="disabled")
        self.chat_area.see(tk.END)
        self.message_history.append({"role": "assistant", "content": message})
        if self.speech_enabled.get():
            speech_queue.put(message)

    def voice_command(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.respond("Listening...")
            try:
                audio = recognizer.listen(source, timeout=5)
                raw_query = recognizer.recognize_google(audio)

                # Translate if necessary
                detected_lang = detect(raw_query)
                if detected_lang != "en":
                    raw_query = GoogleTranslator(source="auto", target="en").translate(raw_query)

                # Process the input
                processed_query, error_message = process_input(raw_query)

                if error_message:
                    self.respond(f"⚠️ {error_message}")
                    return

                self.chat_area.configure(state="normal")
                self.chat_area.insert(tk.END, f"You (Voice): {processed_query}\n")
                self.chat_area.configure(state="disabled")

                self.process_command(processed_query)

            except sr.UnknownValueError:
                self.respond("Sorry, I didn't catch that.")
            except sr.RequestError:
                self.respond("Voice recognition error.")
            except Exception as e:
                self.respond("Something went wrong.")
                print(f"[Voice Error] {e}")



    def stop_speech(self):
        while not speech_queue.empty():
            try:
                speech_queue.get(block=False)
            except queue.Empty:
                continue

    def on_exit(self):
        speech_queue.put(None)
        self.destroy()

    def toggle_theme(self):
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")