from operator import is_
import os
import time
import string
from datetime import datetime
import json
import subprocess

# os.system("pip install pywin32 pyautogui pywinauto keyboard transformers torch yt-dlp requests beautifulsoup4 pygame")

# import pyautogui
# from pywinauto import Desktop
# import keyboard
# from transformers import pipeline
# import sys
# import argparse
# import requests
# from bs4 import BeautifulSoup
# import urllib.parse
# import re

import json
import tkinter as tk
from tkinter import ttk
import time
import random
import os
import pygame
import shutil
from tkinter import filedialog, messagebox
import requests

CONTEXT_CACHE_FILENAME = "context_cache.json"

def load_context_cache():
    """Loads the context cache from a JSON file."""
    try:
        if os.path.exists(CONTEXT_CACHE_FILENAME):
            with open(CONTEXT_CACHE_FILENAME, 'r') as f:
                return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Could not load context cache file '{CONTEXT_CACHE_FILENAME}'. Starting fresh. Error: {e}")
    return {}

def save_context_cache(cache):
    """Saves the context cache to a JSON file."""
    try:
        with open(CONTEXT_CACHE_FILENAME, 'w') as f:
            json.dump(cache, f, indent=4)
    except IOError as e:
        print(f"Could not write to context cache file '{CONTEXT_CACHE_FILENAME}'. Error: {e}")

def get_topics_from_paragraph(paragraph: str) -> list:
    context_cache = load_context_cache()
    if paragraph in context_cache:
        print("Found context in cache.")
        return context_cache[paragraph]

    print("Context not in cache, calling AI server.")
    
    prompt = f'''
From the following paragraph, extract a list of key topics or subjects the user is interested in. The user is a student.
Return a JSON object with a single key "safe_topics" which is a list of strings.
Paragraph: "{paragraph}"
Your response must be a valid JSON object. Only return the JSON object, with no other text or explanations.
'''
    
    server_url = "http://localhost:8000/ai_req"
    headers = {"Content-Type": "application/json"}
    data = {"prompt": prompt}

    try:
        # The server now decides which model to use based on userData.json
        response = requests.post(server_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        api_response = response.json()
        
        # The actual AI response is expected to be a JSON string inside the 'response' key
        json_response_str = api_response.get('response')

        if not json_response_str:
            print(f"AI server returned an empty response for context extraction.")
            return []

        # The response from the AI is a JSON string, so we parse it.
        result = json.loads(json_response_str)
        
        if 'safe_topics' in result and isinstance(result['safe_topics'], list):
            topics = result['safe_topics']
            # Add to cache
            context_cache[paragraph] = topics
            save_context_cache(context_cache)
            return topics
        else:
            print("AI server response for context is not in the expected format.")
            return []

    except requests.exceptions.RequestException as e:
        print(f"An error occurred with the AI server request for context: {e}")
        return []
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Failed to parse AI server response for context: {e}")
        if 'response' in locals():
            print(f"Raw response: {response.text}")
        return []





# os.environ["CUDA_VISIBLE_DEVICES"] = "1"
# classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=0)
# hashmap = {}

def get_current_datetime():
    return datetime.now().strftime("%d/%m/%y %H:%M:%S")



def install_music_files():
    target_dir = filedialog.askdirectory(title="Select Folder to Install Music")
    if not target_dir:
        return

    source_dir = "assets/music"
    files = [f for f in os.listdir(source_dir) if f.endswith(".mp3")]

    try:
        for file in files:
            src = os.path.join(source_dir, file)
            dst = os.path.join(target_dir, file)
            shutil.copy2(src, dst)
        messagebox.showinfo("Success", f"Installed {len(files)} music files to:\n{target_dir}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to install music files:\n{e}")



def count_distractions_today():
    json_path = 'distractionHistory.json'
    with open(json_path, "r") as f:
        data = json.load(f)

    today = datetime.now().strftime("%d/%m/%y")
    distractions = data.get("Distractions", [])
    
    count = sum(1 for _, timestamp in distractions if timestamp.startswith(today))
    return count

def total_session_time_today():
    json_path = 'userSessions.json'
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    today = datetime.now().strftime("%d/%m/%y")
    sessions = data.get("Sessions", [])

    total_time = sum(duration for duration, timestamp in sessions if timestamp.startswith(today))
    return total_time


def animate_button_hover(widget, original_color, hover_color):
    """Add hover animation effect to buttons"""
    def on_enter(event):
        widget.configure(bg=hover_color)
    
    def on_leave(event):
        widget.configure(bg=original_color)
    
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)




class FocusApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Focus Dashboard")
        self.root.geometry("800x600")
        self.root.configure(bg="#f8fafc")
        self.theme = tk.StringVar(value="Light")
        self.focus_mode = tk.BooleanVar()
        self.timer_running = False
        self.time_left = 25 * 60
        self.style = ttk.Style()

        # Modern color palette inspired by Windows 11
        self.bg_primary = "#f8fafc"  # Light background
        self.bg_secondary = "#ffffff"  # Card background
        self.bg_accent = "#e2e8f0"   # Subtle accent
        self.text_primary = "#1e293b"  # Dark text
        self.text_secondary = "#64748b"  # Muted text
        self.accent_blue = "#3b82f6"  # Primary blue
        self.accent_purple = "#8b5cf6"  # Purple accent
        self.accent_green = "#10b981"  # Success green
        self.accent_orange = "#f59e0b"  # Warning orange
        self.border_color = "#e2e8f0"  # Border color
        self.shadow_color = "#00000010"  # Subtle shadow
        
        self.root.configure(bg=self.bg_primary)
        self.style.theme_use("default")
        
        # Configure modern button styles
        self.style.configure("Modern.TButton", 
                           font=("Segoe UI", 11, "normal"),
                           padding=(20, 12),
                           relief="flat",
                           borderwidth=0,
                           focuscolor="none")
        self.style.map("Modern.TButton",
                      background=[("active", "#f1f5f9"),
                                 ("pressed", "#e2e8f0")])
        
        self.style.configure("Primary.TButton",
                           font=("Segoe UI", 11, "bold"),
                           padding=(20, 12),
                           relief="flat",
                           borderwidth=0,
                           focuscolor="none")
        self.style.map("Primary.TButton",
                      background=[("active", "#2563eb"),
                                 ("pressed", "#1d4ed8")])

        self.build_ui()


    def build_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        # Create main container with padding
        main_container = tk.Frame(self.root, bg=self.bg_primary)
        main_container.pack(fill="both", expand=True, padx=30, pady=30)

        # Header section
        header_frame = tk.Frame(main_container, bg=self.bg_primary)
        header_frame.pack(fill="x", pady=(0, 30))
        
        title_label = tk.Label(header_frame, text="🎯 Focus Dashboard", 
                              font=("Segoe UI", 24, "bold"), 
                              bg=self.bg_primary, fg=self.text_primary)
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame, text="Stay focused, achieve more", 
                                font=("Segoe UI", 12), 
                                bg=self.bg_primary, fg=self.text_secondary)
        subtitle_label.pack(pady=(5, 0))

        # Quick Actions Card
        actions_card = self.create_card(main_container)
        actions_card.pack(fill="x", pady=(0, 20))
        
        actions_title = tk.Label(actions_card, text="⚡ Quick Actions", 
                                font=("Segoe UI", 16, "bold"), 
                                bg=self.bg_secondary, fg=self.text_primary)
        actions_title.pack(pady=(20, 15))
        
        # Button container with grid layout
        button_frame = tk.Frame(actions_card, bg=self.bg_secondary)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Create modern buttons with icons and descriptions
        buttons_data = [
            ("📊 View Distraction History", self.view_distractions, "Track your focus patterns"),
            ("⚙️ Customize Settings", self.open_settings, "Personalize your experience"),
            ("🎮 Gamification & Rewards", self.open_gamification, "Earn XP and achievements"),
            ("⏱️ Open Timer Screen", self.open_timer_screen, "Start a focused session")
        ]
        
        for i, (text, command, description) in enumerate(buttons_data):
            btn_frame = tk.Frame(button_frame, bg=self.bg_secondary)
            btn_frame.grid(row=i//2, column=i%2, padx=10, pady=8, sticky="ew")
            button_frame.grid_columnconfigure(i%2, weight=1)
            
            btn = ttk.Button(btn_frame, text=text, command=command, 
                           style="Modern.TButton")
            btn.pack(fill="x")
            
            desc_label = tk.Label(btn_frame, text=description, 
                                font=("Segoe UI", 9), 
                                bg=self.bg_secondary, fg=self.text_secondary)
            desc_label.pack(pady=(2, 0))

    def create_card(self, parent):
        """Create a modern card with rounded appearance"""
        card = tk.Frame(parent, bg=self.bg_secondary, relief="flat", bd=0)
        # Add subtle border effect
        border_frame = tk.Frame(card, bg=self.border_color, height=1)
        border_frame.pack(fill="x", side="bottom")
        return card

    def switch_theme(self, *_):
        self.configure_theme()
        self.build_ui()

    def view_distractions(self):
        DistractionLogViewer(self.root)

    def open_settings(self):
        SettingsPanel(self.root)

    def open_gamification(self):
        GamificationPanel(self.root)

    def open_timer_screen(self):
        TimerScreen(tk.Toplevel(self.root))

class TimerScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Focus Timer")
        self.root.geometry("900x580")
        self.root.configure(bg="#f8fafc")
        
        # Modern color palette
        self.bg_primary = "#f8fafc"
        self.bg_secondary = "#ffffff"
        self.bg_accent = "#e2e8f0"
        self.text_primary = "#1e293b"
        self.text_secondary = "#64748b"
        self.accent_blue = "#3b82f6"
        self.accent_purple = "#8b5cf6"
        self.accent_green = "#10b981"
        self.accent_orange = "#f59e0b"
        self.border_color = "#e2e8f0"
        
        with open("userData.json", 'r') as f:
            self.session_time_def = json.load(f)["Session Time"] * 60
        self.time_left = self.session_time_def
        self.timer_running = False
        self.paused = False
        self.music_on = False
        self.music_index = 0
        self.music_files = [
            "assets/music/Ambient 1.mp3",
            "assets/music/Ambient 2.mp3",
            "assets/music/Ambient 3.mp3",
            "assets/music/Ambient 4.mp3",
            "assets/music/Ambient 5.mp3"
        ]
        
        self.quotes = [
            "Stay focused and never give up.",
            "Small steps lead to big results.",
            "Discipline is the bridge to success.",
            "Your future is created by what you do today.",
            "Push yourself, because no one else will."
        ]
        pygame.mixer.init()
        self.build_ui()

    def build_ui(self):
        # Main container
        main_container = tk.Frame(self.root, bg=self.bg_primary)
        main_container.pack(fill="both", expand=True, padx=20, pady=15)

        # Timer Card
        timer_card = self.create_card(main_container)
        timer_card.pack(fill="x", pady=(0, 15))
        
        # Timer display
        timer_frame = tk.Frame(timer_card, bg=self.bg_secondary)
        timer_frame.pack(fill="x", padx=25, pady=20)
        
        self.timer_label = tk.Label(timer_frame, text=self.format_time(self.time_left),
                                    font=("Segoe UI", 40, "bold"), 
                                    bg=self.bg_secondary, fg=self.accent_blue)
        self.timer_label.pack()

        # Quote Card
        quote_card = self.create_card(main_container)
        quote_card.pack(fill="x", pady=(0, 15))
        
        quote_frame = tk.Frame(quote_card, bg=self.bg_secondary)
        quote_frame.pack(fill="x", padx=25, pady=15)
        
        self.quote_label = tk.Label(quote_frame, text=random.choice(self.quotes),
                                    font=("Segoe UI", 12, "italic"), 
                                    wraplength=600, justify="center",
                                    bg=self.bg_secondary, fg=self.text_secondary)
        self.quote_label.pack()

        # Progress Card
        progress_card = self.create_card(main_container)
        progress_card.pack(fill="x", pady=(0, 15))
        
        progress_frame = tk.Frame(progress_card, bg=self.bg_secondary)
        progress_frame.pack(fill="x", padx=25, pady=15)
        
        # Configure modern progress bar
        style = ttk.Style()
        style.configure("Modern.Horizontal.TProgressbar",
                       background=self.accent_blue,
                       troughcolor=self.bg_accent,
                       borderwidth=0,
                       lightcolor=self.accent_blue,
                       darkcolor=self.accent_blue)
        
        self.progress = ttk.Progressbar(progress_frame, length=400, mode="determinate",
                                      style="Modern.Horizontal.TProgressbar")
        self.progress.pack()
        self.progress["maximum"] = self.time_left

        # Summary Card
        summary_card = self.create_card(main_container)
        summary_card.pack(fill="x", pady=(0, 15))
        
        summary_frame = tk.Frame(summary_card, bg=self.bg_secondary)
        summary_frame.pack(fill="x", padx=25, pady=15)
        
        summary_title = tk.Label(summary_frame, text="📊 Today's Summary", 
                                font=("Segoe UI", 16, "bold"),
                                bg=self.bg_secondary, fg=self.text_primary)
        summary_title.pack(anchor="w", pady=(0, 15))

        stats_frame = tk.Frame(summary_frame, bg=self.bg_secondary)
        stats_frame.pack(fill="x")

        self.time_focused_label = tk.Label(stats_frame, 
                                          text=f"⏱️ Time Focused: {total_session_time_today()} minutes",
                                          bg=self.bg_secondary, fg=self.text_primary, 
                                          font=("Segoe UI", 12))
        self.time_focused_label.pack(anchor="w", pady=2)

        self.distractions_label = tk.Label(stats_frame, 
                                          text=f"🚫 Distractions: {count_distractions_today()}",
                                          bg=self.bg_secondary, fg=self.text_primary, 
                                          font=("Segoe UI", 12))
        self.distractions_label.pack(anchor="w", pady=2)

        # Music Player Card
        music_card = self.create_card(main_container)
        music_card.pack(fill="x", pady=(0, 15))
        
        music_frame = tk.Frame(music_card, bg=self.bg_secondary)
        music_frame.pack(fill="x", padx=25, pady=20)
        
        # Music player header
        music_header = tk.Frame(music_frame, bg=self.bg_secondary)
        music_header.pack(fill="x", pady=(0, 15))
        
        music_title = tk.Label(music_header, text="🎵 Background Music", 
                              font=("Segoe UI", 16, "bold"),
                              bg=self.bg_secondary, fg=self.text_primary)
        music_title.pack(side="left")
        
        # Music status indicator
        self.music_status = tk.Label(music_header, text="● Stopped", 
                                   font=("Segoe UI", 10),
                                   bg=self.bg_secondary, fg=self.accent_orange)
        self.music_status.pack(side="right")

        # Track selection section
        track_section = tk.Frame(music_frame, bg=self.bg_secondary)
        track_section.pack(fill="x", pady=(0, 15))
        
        track_label = tk.Label(track_section, text="🎼 Select Track", 
                              font=("Segoe UI", 12, "bold"),
                              bg=self.bg_secondary, fg=self.text_primary)
        track_label.pack(anchor="w", pady=(0, 10))

        self.selected_track = tk.StringVar()
        self.selected_track.set("Ambient 1.mp3") 

        # Modern track selection with better styling
        track_names = [f"Ambient_{i}.mp3" for i in range(1, 6)]
        track_display_names = [f"Ambient {i}" for i in range(1, 6)]
        
        track_menu_frame = tk.Frame(track_section, bg=self.bg_secondary)
        track_menu_frame.pack(fill="x")
        
        track_menu = ttk.OptionMenu(track_menu_frame, self.selected_track, 
                                  "Ambient 1", *track_display_names)
        track_menu.pack(side="left", padx=(0, 15))
        
        # Track info display
        self.track_info = tk.Label(track_menu_frame, text="🎵 Ambient 1 - Focus Music", 
                                  font=("Segoe UI", 10),
                                  bg=self.bg_secondary, fg=self.text_secondary)
        self.track_info.pack(side="left")

        # Music visualization section
        visualization_section = tk.Frame(music_frame, bg=self.bg_secondary)
        visualization_section.pack(fill="x", pady=(0, 15))
        
        viz_label = tk.Label(visualization_section, text="🎨 Music Visualization", 
                            font=("Segoe UI", 12, "bold"),
                            bg=self.bg_secondary, fg=self.text_primary)
        viz_label.pack(anchor="w", pady=(0, 10))
        
        # Create a simple music visualization bar
        viz_frame = tk.Frame(visualization_section, bg=self.bg_secondary)
        viz_frame.pack(fill="x")
        
        # Music bars visualization
        self.music_bars = []
        bar_colors = [self.accent_blue, self.accent_purple, self.accent_green, self.accent_orange]
        
        for i in range(8):
            bar_frame = tk.Frame(viz_frame, bg=self.bg_secondary)
            bar_frame.pack(side="left", fill="both", expand=True, padx=2)
            
            bar_height = random.randint(20, 60)
            bar = tk.Frame(bar_frame, bg=bar_colors[i % len(bar_colors)], 
                          height=bar_height, width=8)
            bar.pack(side="bottom", pady=(0, 5))
            self.music_bars.append(bar)
        
        # Add animation effect for music bars
        self.animate_music_bars()

        # Track progress section
        # progress_section = tk.Frame(music_frame, bg=self.bg_secondary)
        # progress_section.pack(fill="x", pady=(0, 15))
        
        # progress_label = tk.Label(progress_section, text="⏱️ Track Progress", 
        #                          font=("Segoe UI", 12, "bold"),
        #                          bg=self.bg_secondary, fg=self.text_primary)
        # progress_label.pack(anchor="w", pady=(0, 10))
        
        # # Track progress bar
        # track_progress_frame = tk.Frame(progress_section, bg=self.bg_secondary)
        # track_progress_frame.pack(fill="x")
        
        # Configure track progress bar style
        # track_progress_style = ttk.Style()
        # track_progress_style.configure("TrackProgress.Horizontal.TProgressbar",
        #                              background=self.accent_purple,
        #                              troughcolor=self.bg_accent,
        #                              borderwidth=0,
        #                              lightcolor=self.accent_purple,
        #                              darkcolor=self.accent_purple)
        
        # self.track_progress = ttk.Progressbar(track_progress_frame, length=300, mode="determinate",
        #                                     style="TrackProgress.Horizontal.TProgressbar")
        # self.track_progress.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Time display
        # self.track_time = tk.Label(track_progress_frame, text="0:00 / 3:45", 
        #                           font=("Segoe UI", 10),
        #                           bg=self.bg_secondary, fg=self.text_secondary)
        # self.track_time.pack(side="right")

        # Music control buttons section
        controls_section = tk.Frame(music_frame, bg=self.bg_secondary)
        controls_section.pack(fill="x", pady=(0, 15))

        controls_label = tk.Label(controls_section, text="🎮 Controls", 
                                 font=("Segoe UI", 12, "bold"),
                                 bg=self.bg_secondary, fg=self.text_primary)
        controls_label.pack(anchor="w", pady=(0, 15))

        # Frame containing both buttons and volume on same row
        controls_frame = tk.Frame(controls_section, bg=self.bg_secondary)
        controls_frame.pack(fill="x")

        # --- Music button styles ---
        music_btn_style = ttk.Style()
        music_btn_style.configure("MusicPlay.TButton",
                                font=("Segoe UI", 12, "bold"),
                                padding=(20, 12),
                                relief="flat",
                                borderwidth=0,
                                focuscolor="none")
        music_btn_style.map("MusicPlay.TButton",
                          background=[("active", "#22c55e"),
                                     ("pressed", "#16a34a")])

        music_btn_style.configure("MusicControl.TButton",
                                font=("Segoe UI", 11),
                                padding=(15, 10),
                                relief="flat",
                                borderwidth=0,
                                focuscolor="none")
        music_btn_style.map("MusicControl.TButton",
                          background=[("active", "#f1f5f9"),
                                     ("pressed", "#e2e8f0")])

        # --- Control Buttons ---
        self.play_btn = ttk.Button(controls_frame, text="▶️", 
                                  command=self.toggle_play_pause, 
                                  style="MusicPlay.TButton")
        self.play_btn.pack(side="left", padx=(0, 10))

        stop_btn = ttk.Button(controls_frame, text="⏹️", 
                              command=self.stop_music, 
                              style="MusicControl.TButton")
        stop_btn.pack(side="left", padx=5)

        prev_btn = ttk.Button(controls_frame, text="⏮️", 
                              command=self.previous_track, 
                              style="MusicControl.TButton")
        prev_btn.pack(side="left", padx=5)

        next_btn = ttk.Button(controls_frame, text="⏭️", 
                              command=self.next_track, 
                              style="MusicControl.TButton")
        next_btn.pack(side="left", padx=5)

        # --- Volume control to the right ---
        volume_frame = tk.Frame(controls_frame, bg=self.bg_secondary)
        volume_frame.pack(side="right", padx=(15, 0))

        volume_label = tk.Label(volume_frame, text="🔊", 
                               font=("Segoe UI", 12, "bold"),
                               bg=self.bg_secondary, fg=self.text_primary)
        volume_label.pack(side="left", padx=(0, 5))

        self.volume_value = tk.IntVar(value=50)

        slider_style = ttk.Style()
        slider_style.configure("MusicVolume.Horizontal.TScale",
                              troughcolor=self.bg_accent,
                              sliderthickness=10,
                              background=self.accent_blue,
                              bordercolor=self.border_color,
                              relief="flat",
                              sliderrelief="flat")

        self.volume_slider = ttk.Scale(volume_frame, from_=0, to=100, 
                                     orient="horizontal",
                                     variable=self.volume_value, 
                                     command=self.set_volume,
                                     style="MusicVolume.Horizontal.TScale",
                                     length=120)
        self.volume_slider.pack(side="left", padx=(0, 5))

        self.volume_label = tk.Label(volume_frame, text="50%", 
                                   font=("Segoe UI", 11, "bold"),
                                   bg=self.bg_secondary, fg=self.accent_blue)
        self.volume_label.pack(side="left")


        # Start/Stop Button
        button_card = self.create_card(main_container)
        button_card.pack(fill="x")
        
        button_frame = tk.Frame(button_card, bg=self.bg_secondary)
        button_frame.pack(fill="x", padx=30, pady=30)
        
        # Modern start button
        start_style = ttk.Style()
        start_style.configure("Start.TButton",
                             font=("Segoe UI", 14, "bold"),
                             padding=(30, 12),
                             relief="flat",
                             borderwidth=0)
        start_style.map("Start.TButton",
                       background=[("active", "#2563eb"),
                                  ("pressed", "#1d4ed8")])
        
        self.start_but = ttk.Button(button_frame, text="🚀 Start Focus Session", 
                                   command=self.start_timer, style="Start.TButton")
        self.start_but.pack()

    def create_card(self, parent):
        """Create a modern card with subtle styling"""
        card = tk.Frame(parent, bg=self.bg_secondary, relief="flat", bd=0)
        # Add subtle border effect
        border_frame = tk.Frame(card, bg=self.border_color, height=1)
        border_frame.pack(fill="x", side="bottom")
        return card

    def start_timer(self):
        if "Start" in self.start_but.cget("text"):
            self.start_but.config(text="🛑 Stop Focus Session")
            self.resume_timer()
            
            with open("userData.json", "r") as f:
                data = json.load(f)
            ai_model = data.get("ai_model", "Deepseek")

            if ai_model == "Hugging Face":
                backend_script = "backend.py"
                subprocess.Popen(["start", "cmd", "/k", f"python {backend_script}"], shell=True)
            else:
                backend_script = "backend_api.py"
                # Pass model name as argument
                subprocess.Popen(["start", "cmd", "/k", f"python {backend_script} --model \"{ai_model}\""], shell=True)

            try:
                with open("userData.json", "r") as f:
                    data = json.load(f)
                with open("userData.json", "w") as f:
                    data["backendActive"] = True
                    json.dump(data, f, indent=4)
            except PermissionError as e:
                time.sleep(1)
                with open("userData.json", "r") as f:
                    data = json.load(f)
                with open("userData.json", "w") as f:
                    data["backendActive"] = True
                    json.dump(data, f, indent=4)
            except OSError as e1:
                time.sleep(1)
                with open("userData.json", "r") as f:
                    data = json.load(f)
                with open("userData.json", "w") as f:
                    data["backendActive"] = True
                    json.dump(data, f, indent=4)
            except Exception as e2:
                print("Fatal Error: JSON file loading or dumping couldn't work. Rewriting the JSON file to its default.")
                with open("userData.json", 'w') as f:
                    json.dump({"backendActive" : True}, f, indent=4)
        else:
            self.start_but.config(text="🚀 Start Focus Session")
            try:
                with open("userData.json", "r") as f:
                    data = json.load(f)
                with open("userData.json", "w") as f:
                    data["backendActive"] = False
                    json.dump(data, f, indent=4)
            except PermissionError as e:
                time.sleep(1)
                with open("userData.json", "r") as f:
                    data = json.load(f)
                with open("userData.json", "w") as f:
                    data["backendActive"] = False
                    json.dump(data, f, indent=4)
            except OSError as e1:
                time.sleep(1)
                with open("userData.json", "r") as f:
                    data = json.load(f)
                with open("userData.json", "w") as f:
                    data["backendActive"] = False
                    json.dump(data, f, indent=4)
            except Exception as e2:
                print("Fatal Error: JSON file loading or dumping couldn't work. Rewriting the JSON file to its default.")
                with open("userData.json", 'w') as f:
                    json.dump({"backendActive" : False}, f, indent=4)
            self.end_timer()

    def format_time(self, seconds):
        return f"{seconds // 60:02}:{seconds % 60:02}"

    def toggle_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.update_timer()

    def update_timer(self):
        if self.timer_running and not self.paused and self.time_left > 0:
            self.time_left -= 1
            self.timer_label.config(text=self.format_time(self.time_left))
            self.progress["value"] = self.session_time_def - self.time_left
            self.root.after(1000, self.update_timer)
        elif self.time_left == 0:
            # self.timer_running = False
            self.start_but.config(text="🚀 Start Focus Session")
            try:
                with open("userData.json", "r") as f:
                    data = json.load(f)
                with open("userData.json", "w") as f:
                    data["backendActive"] = False
                    json.dump(data, f, indent=4)
            except PermissionError as e:
                time.sleep(1)
                with open("userData.json", "r") as f:
                    data = json.load(f)
                with open("userData.json", "w") as f:
                    data["backendActive"] = False
                    json.dump(data, f, indent=4)
            except OSError as e1:
                time.sleep(1)
                with open("userData.json", "r") as f:
                    data = json.load(f)
                with open("userData.json", "w") as f:
                    data["backendActive"] = False
                    json.dump(data, f, indent=4)
            except Exception as e2:
                print("Fatal Error: JSON file loading or dumping couldn't work. Rewriting the JSON file to its default.")
                with open("userData.json", 'w') as f:
                    json.dump({"backendActive" : False}, f, indent=4)
            self.end_timer()
            self.timer_label.config(text="00:00")
            self.quote_label.config(text="Session Complete! Great job 🎉")
            # self.time_focused_label.config(text="Time Elapsed: 25 min")
            # self.distractions_label.config(text="Distraction Count: 3")

    def pause_timer(self):
        self.paused = True

    def resume_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.update_timer()
        self.paused = False

    def end_timer(self):
        self.timer_running = False
        with open('userSessions.json', "r") as f:
            sesdat = json.load(f)
            sesdat['Sessions'].append([int((self.session_time_def - self.time_left)/60), get_current_datetime()])
        with open("userSessions.json", 'w') as f:
            json.dump(sesdat, f, indent=4)
        with open('userXP.json', 'r') as f:
            xpdat = json.load(f)
            xpdat["XP"] += int(int((self.session_time_def - self.time_left)/60)/6)
        with open('userXP.json', 'w') as f:
            json.dump(xpdat, f, indent=4)


        self.time_left = self.session_time_def
        self.timer_label.config(text=self.format_time(self.time_left))
        self.progress["value"] = 0
        self.quote_label.config(text=random.choice(self.quotes))
        
    def play_music(self):
        track = f"assets/music/{self.selected_track.get()}.mp3"
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.set_volume(self.volume_slider.get())
            pygame.mixer.music.play(-1, fade_ms=2000) 
            self.music_on = True
            self.music_status.config(text="● Playing", fg=self.accent_green)
            self.play_btn.config(text="⏸️")
            self.update_track_info()
        except Exception as e:
            print(f"Error playing music: {e}")

    def pause_music(self):
        if self.music_on:
            pygame.mixer.music.pause() 
            self.music_on = False
            self.music_status.config(text="● Paused", fg=self.accent_orange)
            self.play_btn.config(text="▶️")

    def resume_music(self):
        try:
            pygame.mixer.music.unpause()
            self.music_on = True
            self.music_status.config(text="● Playing", fg=self.accent_green)
            self.play_btn.config(text="⏸️")
        except Exception as e:
            print(f"Error resuming music: {e}")

    def stop_music(self):
        try:
            pygame.mixer.music.stop()
            self.music_on = False
            self.music_status.config(text="● Stopped", fg=self.accent_orange)
            self.play_btn.config(text="▶️")
        except Exception as e:
            print(f"Error stopping music: {e}")

    def toggle_play_pause(self):
        if self.music_on:
            self.pause_music()
        else:
            if pygame.mixer.music.get_busy():
                self.resume_music()
            else:
                self.play_music()

    def previous_track(self):
        current_track = int(self.selected_track.get().split('Ambient ')[1].split('.')[0])
        new_track = max(1, current_track - 1)
        self.selected_track.set(f"Ambient {new_track}.mp3")
        self.update_track_info()
        if self.music_on:
            self.play_music()

    def next_track(self):
        current_track = int(self.selected_track.get().split('Ambient ')[1].split('.')[0])
        new_track = min(5, current_track + 1)
        self.selected_track.set(f"Ambient {new_track}.mp3")
        self.update_track_info()
        if self.music_on:
            self.play_music()

    def update_track_info(self):
        track_num = self.selected_track.get().split('Ambient ')[1].split('.')[0]
        self.track_info.config(text=f"🎵 Ambient {track_num} - Focus Music")

    def set_volume(self, val):
        volume = int(float(val))
        pygame.mixer.music.set_volume(volume / 100)
        self.volume_label.config(text=f"{volume}%")

    def animate_music_bars(self):
        """Animate the music visualization bars and track progress"""
        if hasattr(self, 'music_bars') and self.music_bars:
            for bar in self.music_bars:
                if self.music_on:
                    # Animate bars when music is playing
                    new_height = random.randint(15, 80)
                    bar.configure(height=new_height)
                else:
                    # Static bars when music is stopped
                    bar.configure(height=20)
        
        # Update track progress if music is playing
        if hasattr(self, 'track_progress') and self.music_on:
            # Simulate track progress (since we can't get actual track length easily)
            current_progress = self.track_progress['value']
            if current_progress >= 100:
                current_progress = 0
            else:
                current_progress += 0.5
            self.track_progress['value'] = current_progress
            
            # Update time display
            current_time = int(current_progress * 2.25)  # Approximate seconds
            minutes = current_time // 60
            seconds = current_time % 60
            self.track_time.config(text=f"{minutes}:{seconds:02d} / 3:45")
        
        # Schedule next animation
        self.root.after(200, self.animate_music_bars)

class SettingsPanel(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("⚙️ Settings")
        self.geometry("450x850")
        self.configure(bg="#f8fafc")
        
        # Modern color palette
        self.bg_primary = "#f8fafc"
        self.bg_secondary = "#ffffff"
        self.bg_accent = "#e2e8f0"
        self.text_primary = "#1e293b"
        self.text_secondary = "#64748b"
        self.accent_blue = "#3b82f6"
        self.accent_purple = "#8b5cf6"
        self.accent_green = "#10b981"
        self.accent_orange = "#f59e0b"
        self.border_color = "#e2e8f0"

        with open("userData.json", "r") as f:
            user_data = json.load(f)

        intervention_style = user_data.get("Intervention Style", "nudge")
        session_time = user_data.get("Session Time", 60)
        context_paragraph = user_data.get("context_paragraph", "")

        # Configure modern styles
        self.style = ttk.Style()
        self.style.configure("Modern.TButton", 
                           font=("Segoe UI", 11, "normal"),
                           padding=(20, 10),
                           relief="flat",
                           borderwidth=0,
                           focuscolor="none")
        self.style.map("Modern.TButton",
                      background=[("active", "#f1f5f9"),
                                 ("pressed", "#e2e8f0")])
        
        self.style.configure("Primary.TButton",
                           font=("Segoe UI", 11, "bold"),
                           padding=(20, 10),
                           relief="flat",
                           borderwidth=0,
                           focuscolor="none")
        self.style.map("Primary.TButton",
                      background=[("active", "#2563eb"),
                                 ("pressed", "#1d4ed8")])

        self.build_ui(intervention_style, session_time, context_paragraph)

    def build_ui(self, intervention_style, session_time, context_paragraph):
        # Main container
        main_container = tk.Frame(self, bg=self.bg_primary)
        main_container.pack(fill="both", expand=True, padx=30, pady=30)

        # Header
        header_frame = tk.Frame(main_container, bg=self.bg_primary)
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = tk.Label(header_frame, text="⚙️ Customize Your Experience", 
                              font=("Segoe UI", 18, "bold"), 
                              bg=self.bg_primary, fg=self.text_primary)
        title_label.pack()

        # Intervention Style Card
        intervention_card = self.create_card(main_container)
        intervention_card.pack(fill="x", pady=(0, 15))
        
        intervention_frame = tk.Frame(intervention_card, bg=self.bg_secondary)
        intervention_frame.pack(fill="x", padx=25, pady=20)
        
        intervention_title = tk.Label(intervention_frame, text="🎯 Intervention Style", 
                                    font=("Segoe UI", 14, "bold"),
                                    bg=self.bg_secondary, fg=self.text_primary)
        intervention_title.pack(anchor="w", pady=(0, 15))

        self.intervention_var = tk.StringVar(value=intervention_style)
        
        # Modern radio buttons
        radio_frame = tk.Frame(intervention_frame, bg=self.bg_secondary)
        radio_frame.pack(fill="x")
        
        for i, style_option in enumerate(["nudge", "auto-close"]):
            radio_btn = ttk.Radiobutton(radio_frame, text=style_option.capitalize(),
                                       variable=self.intervention_var, value=style_option,
                                       style="Modern.TRadiobutton")
            radio_btn.pack(anchor="w", pady=5)

        # Session Time Card
        time_card = self.create_card(main_container)
        time_card.pack(fill="x", pady=(0, 15))
        
        time_frame = tk.Frame(time_card, bg=self.bg_secondary)
        time_frame.pack(fill="x", padx=25, pady=20)
        
        time_title = tk.Label(time_frame, text="⏱️ Pomodoro Timer (minutes)", 
                             font=("Segoe UI", 14, "bold"),
                             bg=self.bg_secondary, fg=self.text_primary)
        time_title.pack(anchor="w", pady=(0, 15))

        self.session_time_var = tk.IntVar(value=session_time)
        
        # Modern spinbox
        spinbox_frame = tk.Frame(time_frame, bg=self.bg_secondary)
        spinbox_frame.pack(fill="x")
        
        session_spinbox = ttk.Spinbox(spinbox_frame, from_=10, to=180, 
                                     textvariable=self.session_time_var, width=15,
                                     font=("Segoe UI", 11))
        session_spinbox.pack(anchor="w")

        # Context Paragraph Card
        context_card = self.create_card(main_container)
        context_card.pack(fill="x", pady=(0, 15))
        
        context_frame = tk.Frame(context_card, bg=self.bg_secondary)
        context_frame.pack(fill="x", padx=25, pady=20)
        
        context_title = tk.Label(context_frame, text="🧠 Your Interests", 
                                    font=("Segoe UI", 14, "bold"),
                                    bg=self.bg_secondary, fg=self.text_primary)
        context_title.pack(anchor="w", pady=(0, 15))

        context_desc = tk.Label(context_frame, text="Describe your interests and study subjects in a paragraph. This will help the AI to identify safe topics for you.",
                                 font=("Segoe UI", 10),
                                 bg=self.bg_secondary, fg=self.text_secondary,
                                 wraplength=350, justify="left")
        context_desc.pack(anchor="w", pady=(0, 10))

        self.context_text = tk.Text(context_frame, height=5, width=40,
                                     font=("Segoe UI", 11),
                                     relief="solid", bd=1,
                                     bg=self.bg_primary, fg=self.text_primary,
                                     highlightcolor=self.accent_blue,
                                     highlightbackground=self.border_color,
                                     highlightthickness=1,
                                     padx=10, pady=10)
        self.context_text.pack(fill="x", expand=True)
        self.context_text.insert("1.0", context_paragraph)

        # Music Installation Card
        music_card = self.create_card(main_container)
        music_card.pack(fill="x", pady=(0, 20))
        
        music_frame = tk.Frame(music_card, bg=self.bg_secondary)
        music_frame.pack(fill="x", padx=25, pady=20)
        
        music_title = tk.Label(music_frame, text="🎵 Music Files", 
                              font=("Segoe UI", 14, "bold"),
                              bg=self.bg_secondary, fg=self.text_primary)
        music_title.pack(anchor="w", pady=(0, 15))
        
        music_desc = tk.Label(music_frame, text="Install default ambient music files to your system", 
                             font=("Segoe UI", 10),
                             bg=self.bg_secondary, fg=self.text_secondary)
        music_desc.pack(anchor="w", pady=(0, 10))
        
        install_btn = ttk.Button(music_frame, text="📁 Install Default Music", 
                                command=install_music_files, style="Modern.TButton")
        install_btn.pack(anchor="w")

        # Apply Button
        apply_frame = tk.Frame(main_container, bg=self.bg_primary)
        apply_frame.pack(fill="x")
        
        apply_btn = ttk.Button(apply_frame, text="✅ Apply Settings", 
                              command=self.apply_settings, style="Primary.TButton")
        apply_btn.pack(pady=(10, 0))

    def create_card(self, parent):
        """Create a modern card with subtle styling"""
        card = tk.Frame(parent, bg=self.bg_secondary, relief="flat", bd=0)
        # Add subtle border effect
        border_frame = tk.Frame(card, bg=self.border_color, height=1)
        border_frame.pack(fill="x", side="bottom")
        return card

    def apply_settings(self):
        with open("userData.json", "r") as f:
            data = json.load(f)

        data["Intervention Style"] = self.intervention_var.get()
        data["Session Time"] = self.session_time_var.get()
        
        new_paragraph = self.context_text.get("1.0", "end-1c").strip()
        data["context_paragraph"] = new_paragraph

        if new_paragraph:
            new_topics = get_topics_from_paragraph(new_paragraph)
            if new_topics:
                data["safe_topics"] = new_topics
                print(f"New safe topics from AI: {new_topics}")
            else:
                print("Could not get new topics from AI. Keeping existing topics.")
        else:
            data["safe_topics"] = []

        with open("userData.json", "w") as f:
            json.dump(data, f, indent=4)

        print(f"Intervention style: {data['Intervention Style']}")
        print(f"Pomodoro session time: {data['Session Time']} minutes")
        print(f"Context paragraph: {data['context_paragraph']}")
        print(f"Safe topics: {data['safe_topics']}")

        self.destroy()

class GamificationPanel(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("🎮 Gamification & Rewards")
        self.geometry("700x750")
        self.configure(bg="#f8fafc")
        
        # Modern color palette
        self.bg_primary = "#f8fafc"
        self.bg_secondary = "#ffffff"
        self.bg_accent = "#e2e8f0"
        self.text_primary = "#1e293b"
        self.text_secondary = "#64748b"
        self.accent_blue = "#3b82f6"
        self.accent_purple = "#8b5cf6"
        self.accent_green = "#10b981"
        self.accent_orange = "#f59e0b"
        self.border_color = "#e2e8f0"

        with open("userXP.json", 'r') as f:
            xp = json.load(f)["XP"]

        # Configure modern styles
        self.style = ttk.Style()
        self.style.configure("Modern.TButton", 
                           font=("Segoe UI", 11, "normal"),
                           padding=(20, 10),
                           relief="flat",
                           borderwidth=0,
                           focuscolor="none")
        self.style.map("Modern.TButton",
                      background=[("active", "#f1f5f9"),
                                 ("pressed", "#e2e8f0")])

        self.build_ui(xp)

    def build_ui(self, xp):
        # Main container
        main_container = tk.Frame(self, bg=self.bg_primary)
        main_container.pack(fill="both", expand=True, padx=30, pady=30)

        # Header
        header_frame = tk.Frame(main_container, bg=self.bg_primary)
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = tk.Label(header_frame, text="🎮 Your Progress & Achievements", 
                              font=("Segoe UI", 20, "bold"), 
                              bg=self.bg_primary, fg=self.text_primary)
        title_label.pack()

        # XP Progress Card
        xp_card = self.create_card(main_container)
        xp_card.pack(fill="x", pady=(0, 20))
        
        xp_frame = tk.Frame(xp_card, bg=self.bg_secondary)
        xp_frame.pack(fill="x", padx=30, pady=25)
        
        xp_title = tk.Label(xp_frame, text="⭐ Experience Points", 
                           font=("Segoe UI", 16, "bold"),
                           bg=self.bg_secondary, fg=self.text_primary)
        xp_title.pack(anchor="w", pady=(0, 20))

        # Level display
        level_frame = tk.Frame(xp_frame, bg=self.bg_secondary)
        level_frame.pack(fill="x", pady=(0, 15))
        
        level_label = tk.Label(level_frame, text=f"Level {int(xp/100 + 1)}", 
                              font=("Segoe UI", 14, "bold"),
                              bg=self.bg_secondary, fg=self.accent_blue)
        level_label.pack(side="left")
        
        xp_amount_label = tk.Label(level_frame, text=f"{xp} XP Total", 
                                 font=("Segoe UI", 12),
                                 bg=self.bg_secondary, fg=self.text_secondary)
        xp_amount_label.pack(side="right")

        # Modern progress bar
        progress_frame = tk.Frame(xp_frame, bg=self.bg_secondary)
        progress_frame.pack(fill="x", pady=(0, 10))
        
        # Configure modern progress bar style
        style = ttk.Style()
        style.configure("XP.Horizontal.TProgressbar",
                       background=self.accent_green,
                       troughcolor=self.bg_accent,
                       borderwidth=0,
                       lightcolor=self.accent_green,
                       darkcolor=self.accent_green)
        
        self.xp_bar = ttk.Progressbar(progress_frame, maximum=100, value=xp%100,
                                    style="XP.Horizontal.TProgressbar")
        self.xp_bar.pack(fill="x", pady=(0, 10))
        
        # Progress text
        progress_text_frame = tk.Frame(xp_frame, bg=self.bg_secondary)
        progress_text_frame.pack(fill="x")
        
        progress_text = tk.Label(progress_text_frame, text=f"{xp%100} / 100 XP to next level", 
                                font=("Segoe UI", 11),
                                bg=self.bg_secondary, fg=self.text_secondary)
        progress_text.pack(side="left")
        
        next_level_xp = tk.Label(progress_text_frame, text=f"{100 - (xp%100)} XP needed", 
                                font=("Segoe UI", 11, "bold"),
                                bg=self.bg_secondary, fg=self.accent_green)
        next_level_xp.pack(side="right")

        # Achievements Card
        achievements_card = self.create_card(main_container)
        achievements_card.pack(fill="x", pady=(0, 20))
        
        achievements_frame = tk.Frame(achievements_card, bg=self.bg_secondary)
        achievements_frame.pack(fill="x", padx=30, pady=25)
        
        achievements_title = tk.Label(achievements_frame, text="🏆 Recent Achievements", 
                                    font=("Segoe UI", 16, "bold"),
                                    bg=self.bg_secondary, fg=self.text_primary)
        achievements_title.pack(anchor="w", pady=(0, 15))
        
        # Achievement items
        achievements = [
            ("🎯 First Focus Session", "Completed your first focused work session"),
            ("⏰ Time Master", f"Accumulated {xp} XP through focused work"),
            ("🚀 Consistency Champion", "Maintained focus across multiple sessions")
        ]
        
        for achievement, description in achievements:
            achievement_frame = tk.Frame(achievements_frame, bg=self.bg_secondary)
            achievement_frame.pack(fill="x", pady=5)
            
            achievement_name = tk.Label(achievement_frame, text=achievement, 
                                      font=("Segoe UI", 12, "bold"),
                                      bg=self.bg_secondary, fg=self.accent_purple)
            achievement_name.pack(anchor="w")
            
            achievement_desc = tk.Label(achievement_frame, text=description, 
                                      font=("Segoe UI", 10),
                                      bg=self.bg_secondary, fg=self.text_secondary)
            achievement_desc.pack(anchor="w")

        # Close Button
        close_frame = tk.Frame(main_container, bg=self.bg_primary)
        close_frame.pack(fill="x")
        
        close_btn = ttk.Button(close_frame, text="✖️ Close", 
                              command=self.destroy, style="Modern.TButton")
        close_btn.pack(pady=(10, 0))

    def create_card(self, parent):
        """Create a modern card with subtle styling"""
        card = tk.Frame(parent, bg=self.bg_secondary, relief="flat", bd=0)
        # Add subtle border effect
        border_frame = tk.Frame(card, bg=self.border_color, height=1)
        border_frame.pack(fill="x", side="bottom")
        return card


class DistractionLogViewer(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("🚫 Distraction Intervention Log")
        self.geometry("800x900")
        self.configure(bg="#f8fafc")
        
        # Modern color palette
        self.bg_primary = "#f8fafc"
        self.bg_secondary = "#ffffff"
        self.bg_accent = "#e2e8f0"
        self.text_primary = "#1e293b"
        self.text_secondary = "#64748b"
        self.accent_blue = "#3b82f6"
        self.accent_purple = "#8b5cf6"
        self.accent_green = "#10b981"
        self.accent_orange = "#f59e0b"
        self.border_color = "#e2e8f0"

        with open("distractionHistory.json", "r") as f:
            data = json.load(f)
        data = data["Distractions"]
        counter = 0
        log_entries = []
        for i in data:
            log_entries.append(f'{i[1]}: {i[0]}')
            counter += 1

        print(log_entries)

        self.build_ui(log_entries, data)

    def build_ui(self, log_entries, data):
        # Main container
        main_container = tk.Frame(self, bg=self.bg_primary)
        main_container.pack(fill="both", expand=True, padx=30, pady=30)

        # Header
        header_frame = tk.Frame(main_container, bg=self.bg_primary)
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = tk.Label(header_frame, text="🚫 Distraction Report", 
                              font=("Segoe UI", 20, "bold"), 
                              bg=self.bg_primary, fg=self.text_primary)
        title_label.pack()

        # Log Entries Card
        log_card = self.create_card(main_container)
        log_card.pack(fill="both", expand=True, pady=(0, 20))
        
        log_frame = tk.Frame(log_card, bg=self.bg_secondary)
        log_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        log_title = tk.Label(log_frame, text="📋 Distraction History", 
                            font=("Segoe UI", 16, "bold"),
                            bg=self.bg_secondary, fg=self.text_primary)
        log_title.pack(anchor="w", pady=(0, 15))

        # Scrollable frame for log entries
        canvas_frame = tk.Frame(log_frame, bg=self.bg_secondary)
        canvas_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg=self.bg_secondary, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.bg_secondary)
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Create modern log entries
        for i, entry in enumerate(log_entries, start=1):
            entry_card = tk.Frame(scroll_frame, bg=self.bg_accent, relief="flat", bd=0)
            entry_card.pack(fill="x", pady=5, padx=5)
            
            entry_frame = tk.Frame(entry_card, bg=self.bg_accent)
            entry_frame.pack(fill="x", padx=15, pady=10)
            
            # Entry number and content
            entry_number = tk.Label(entry_frame, text=f"{i}.", 
                                   font=("Segoe UI", 12, "bold"),
                                   bg=self.bg_accent, fg=self.accent_blue)
            entry_number.pack(side="left", padx=(0, 10))
            
            entry_text = tk.Label(entry_frame, text=entry, wraplength=600,
                                 font=("Segoe UI", 11),
                                 bg=self.bg_accent, fg=self.text_primary,
                                 justify="left")
            entry_text.pack(side="left", fill="x", expand=True)

        # Summary Card
        summary_card = self.create_card(main_container)
        summary_card.pack(fill="x", pady=(0, 20))
        
        summary_frame = tk.Frame(summary_card, bg=self.bg_secondary)
        summary_frame.pack(fill="x", padx=25, pady=20)
        
        summary_title = tk.Label(summary_frame, text="📊 Summary", 
                                font=("Segoe UI", 16, "bold"),
                                bg=self.bg_secondary, fg=self.text_primary)
        summary_title.pack(anchor="w", pady=(0, 15))
        
        summary = self.generate_summary(data)
        print(summary)
        
        summary_lines = summary.split('\n')
        for line in summary_lines:
            summary_line = tk.Label(summary_frame, text=line, wraplength=700,
                                   font=("Segoe UI", 12),
                                   bg=self.bg_secondary, fg=self.text_primary,
                                   justify="left")
            summary_line.pack(anchor="w", pady=2)

        # Close Button
        close_frame = tk.Frame(main_container, bg=self.bg_primary)
        close_frame.pack(fill="x")
        
        close_btn = ttk.Button(close_frame, text="✖️ Close", 
                              command=self.destroy, style="Modern.TButton")
        close_btn.pack(pady=(10, 0))

    def create_card(self, parent):
        """Create a modern card with subtle styling"""
        card = tk.Frame(parent, bg=self.bg_secondary, relief="flat", bd=0)
        # Add subtle border effect
        border_frame = tk.Frame(card, bg=self.border_color, height=1)
        border_frame.pack(fill="x", side="bottom")
        return card

    def generate_summary(self, entries):
        out = ''

        # total distractions detected
        out = f"Total Distractions Detected: {len(entries)}"

        # most frequent distraction
        dist_hash = {}
        for i in entries:
            if i[0] in dist_hash:
                dist_hash[i[0]] += 1
            else:
                dist_hash[i[0]] = 1
        maximum = 0
        mfd = ''
        for i in entries:
            if dist_hash[i[0]] > maximum:
                maximum = dist_hash[i[0]]
                mfd = i[0]
        out += f'\nMost Frequent Distraction: {mfd} -> {maximum} times!'

        return out




if __name__ == "__main__":
    print("Select the AI model to use:")
    print("1. Deepseek")
    print("2. Llama 3.1 (via Ollama)")
    print("3. Hugging Face (local, facebook/bart-large-mnli)")
    
    choice = ""
    while choice not in ["1", "2", "3"]:
        choice = input("Enter your choice (1, 2, or 3): ")

    model_map = {
        "1": "Deepseek",
        "2": "Llama-3.1",
        "3": "Hugging Face"
    }
    selected_model = model_map[choice]

    try:
        with open("userData.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Default data if file is missing or corrupt
        data = {
            "Intervention Style": "nudge",
            "Session Time": 25,
            "context_paragraph": "",
            "safe_topics": [],
            "backendActive": False
        }

    data["ai_model"] = selected_model

    with open("userData.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"Selected model: {selected_model}")

    root = tk.Tk()
    root.geometry("800x600")
    app = FocusApp(root)
    root.mainloop()


# cux xf dpvme'wf kvtu ejsfdumz sbo uif nbjo.qz cbdlfoe qsphsbn boe vtfe uif ktpo vtfsebub gjmf up hfu tubsu tupq dpnnboet cz svoojoh ju jo b dne (opu pt.tztufn) (xifsf ju pqfot tfqbsbufmz) cvu epjoh ju vtjoh kbwb boe b qbsbmmfm uisfbe jt dppmfs tp xf eje ju uibu xbz 
# own j foefe vq opu vtjoh kbwb