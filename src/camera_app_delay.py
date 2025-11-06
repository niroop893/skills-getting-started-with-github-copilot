import cv2
from collections import deque
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import threading
import time
import pyvirtualcam
import webbrowser
import os
import pickle

class VirtualDelayedCameraGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Delayed Camera - Works with ALL Apps")
        
        # Set window size to fit screen
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Window size
        window_width = min(900, int(screen_width * 0.8))
        window_height = min(750, int(screen_height * 0.85))
        
        # Center window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(True, True)
        
        # Camera setup
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
        
        self.delay_seconds = 3
        self.buffer_size = int(self.delay_seconds * self.fps)
        self.frame_buffer = deque(maxlen=self.buffer_size)
        
        # Loop mode variables
        self.loop_mode = False
        self.frozen_buffer = []
        self.loop_index = 0
        
        # File replay variables
        self.file_mode = False
        self.save_folder = r"C:\Users\NiroopkumarShetty\Documents\Niroop"
        
        self.running = False
        self.preview_running = False
        self.virtual_cam = None
        
        self.setup_gui()
        self.start_preview()
    
    def setup_gui(self):
        # Main container with canvas for scrolling
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas and scrollbar
        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # ===== HEADER =====
        header = tk.Label(scrollable_frame, text="Virtual Camera Delay + Loop", 
                         font=("Arial", 14, "bold"), bg="lightblue", pady=8)
        header.pack(fill=tk.X)
        
        # ===== OBS WARNING =====
        warning_frame = tk.Frame(scrollable_frame, bg="#ffebcc", pady=5)
        warning_frame.pack(fill=tk.X, padx=10, pady=5)
        
        warning_text = "⚠️ OBS Studio Required! Click here to download if not installed ⚠️"
        warning_label = tk.Label(warning_frame, text=warning_text, bg="#ffebcc", 
                                font=("Arial", 9, "bold"), fg="red", cursor="hand2")
        warning_label.pack()
        warning_label.bind("<Button-1>", lambda e: webbrowser.open("https://obsproject.com/download"))
        
        # ===== INFO FRAME =====
        info_frame = tk.Frame(scrollable_frame, bg="lightyellow", pady=5)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        info_text = "Creates VIRTUAL CAMERA for: Zoom • Teams • Meet • OBS • Discord"
        tk.Label(info_frame, text=info_text, bg="lightyellow", 
                font=("Arial", 9)).pack()
        
        # ===== PREVIEW =====
        preview_frame = tk.LabelFrame(scrollable_frame, text="Camera Preview (Live Feed)", 
                                     padx=5, pady=5)
        preview_frame.pack(padx=10, pady=5)
        
        self.video_label = tk.Label(preview_frame, bg="black")
        self.video_label.pack()
        
        # ===== CONTROLS =====
        controls = tk.LabelFrame(scrollable_frame, text="Delay Settings", padx=15, pady=8)
        controls.pack(padx=10, pady=5, fill=tk.X)
        
        # Quick Delay Slider
        slider_frame = tk.Frame(controls)
        slider_frame.pack(pady=3)
        
        tk.Label(slider_frame, text="Quick Delay:", font=("Arial", 9)).grid(row=0, column=0, padx=5)
        self.quick_slider = ttk.Scale(slider_frame, from_=1, to=60, 
                                     orient=tk.HORIZONTAL, length=180,
                                     command=self.update_quick_delay)
        self.quick_slider.set(3)
        self.quick_slider.grid(row=0, column=1, padx=5)
        
        self.quick_label = tk.Label(slider_frame, text="3s", font=("Arial", 9, "bold"))
        self.quick_label.grid(row=0, column=2, padx=5)
        
        # Separator
        ttk.Separator(controls, orient='horizontal').pack(fill='x', pady=8)
        
        # Manual Entry
        manual_frame = tk.Frame(controls)
        manual_frame.pack(pady=3)
        
        tk.Label(manual_frame, text="Custom Delay:", font=("Arial", 9)).grid(row=0, column=0, padx=5)
        tk.Label(manual_frame, text="Min:", font=("Arial", 9)).grid(row=0, column=1, padx=2)
        
        self.min_entry = tk.Entry(manual_frame, width=4)
        self.min_entry.insert(0, "0")
        self.min_entry.grid(row=0, column=2, padx=2)
        
        tk.Label(manual_frame, text="Sec:", font=("Arial", 9)).grid(row=0, column=3, padx=2)
        
        self.sec_entry = tk.Entry(manual_frame, width=4)
        self.sec_entry.insert(0, "0")
        self.sec_entry.grid(row=0, column=4, padx=2)
        
        tk.Button(manual_frame, text="Apply", command=self.set_manual_delay,
                 bg="lightblue", font=("Arial", 9)).grid(row=0, column=5, padx=8)
        
        # Info Display
        self.info_label = tk.Label(controls, 
                                   text=f"Camera: {self.width}x{self.height} @ {self.fps}fps",
                                   font=("Arial", 8), fg="blue")
        self.info_label.pack(pady=3)
        
        self.buffer_label = tk.Label(controls, text="Buffer: Not started", 
                                     font=("Arial", 8), fg="darkgreen")
        self.buffer_label.pack(pady=2)
        
        # Progress Bar
        progress_frame = tk.Frame(controls)
        progress_frame.pack(pady=5)
        
        tk.Label(progress_frame, text="Buffer Progress:", font=("Arial", 8)).pack()
        self.progress = ttk.Progressbar(progress_frame, length=350, mode='determinate')
        self.progress.pack(pady=3)
        
        # ===== BUTTONS (Modified with 3 rows) =====
        btn_frame = tk.Frame(scrollable_frame, pady=10)
        btn_frame.pack()
        
        # Row 1 - Main controls
        self.start_btn = tk.Button(btn_frame, text="▶ START DELAYED", 
                                   command=self.start, bg="green", fg="white",
                                   font=("Arial", 10, "bold"), width=18, height=2)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.freeze_btn = tk.Button(btn_frame, text="🔄 FREEZE & LOOP", 
                                    command=self.toggle_loop,
                                    bg="orange", fg="white", font=("Arial", 10, "bold"),
                                    width=18, height=2, state=tk.DISABLED)
        self.freeze_btn.grid(row=0, column=1, padx=5)
        
        self.stop_btn = tk.Button(btn_frame, text="⬛ STOP", command=self.stop,
                                  bg="red", fg="white", font=("Arial", 10, "bold"),
                                  width=15, height=2, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, padx=5)
        
        # Row 2 - Save button
        self.save_replay_btn = tk.Button(btn_frame, text="💾 SAVE BUFFER TO FILE", 
                                         command=self.save_and_replay,
                                         bg="purple", fg="white", font=("Arial", 9, "bold"),
                                         width=55, height=2, state=tk.DISABLED)
        self.save_replay_btn.grid(row=1, column=0, columnspan=3, pady=5)
        
        # Row 3 - NEW Load and Play button
        self.load_play_btn = tk.Button(btn_frame, text="📂 LOAD & PLAY FILE (Select .pkl)", 
                                       command=self.load_and_play_file,
                                       bg="teal", fg="white", font=("Arial", 9, "bold"),
                                       width=55, height=2)
        self.load_play_btn.grid(row=2, column=0, columnspan=3, pady=5)
        
        # ===== MODE INDICATOR =====
        self.mode_frame = tk.Frame(scrollable_frame, bg="white", relief=tk.RIDGE, bd=3)
        self.mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.mode_label = tk.Label(self.mode_frame, text="MODE: Live Delayed", 
                                   font=("Arial", 11, "bold"), fg="blue", bg="white", pady=5)
        self.mode_label.pack()
        
        # ===== STATUS =====
        status_frame = tk.Frame(scrollable_frame, bg="white", relief=tk.SUNKEN, bd=2)
        status_frame.pack(fill=tk.X, padx=10, pady=8)
        
        self.status = tk.Label(status_frame, text="● Preview Mode (Virtual Camera Not Started)", 
                              font=("Arial", 10, "bold"), fg="orange", bg="white", pady=8)
        self.status.pack()
        
        # ===== INSTRUCTIONS =====
        help_frame = tk.LabelFrame(scrollable_frame, text="📖 How to Use", padx=10, pady=8)
        help_frame.pack(padx=10, pady=5, fill=tk.X)
        
        help_text = """SETUP (One-time):
1. Install OBS Studio (click warning link above if not installed)
2. Open OBS → Tools → Start Virtual Camera → Close OBS

USAGE - DELAYED MODE:
1. Set your delay time
2. Click "START DELAYED" - video will be delayed continuously
3. Camera keeps updating with live feed (delayed)

USAGE - LOOP MODE:
1. After starting, click "FREEZE & LOOP"
2. Current buffer freezes and plays repeatedly forever
3. Click "FREEZE & LOOP" again to resume live delayed mode

USAGE - SAVE BUFFER:
1. After starting, click "SAVE BUFFER TO FILE"
2. Buffer is saved to: C:\\Users\\NiroopkumarShetty\\Documents\\Niroop
3. Plays saved buffer in loop

USAGE - LOAD FILE (NEW):
1. Click "LOAD & PLAY FILE" (works anytime, even without camera)
2. Select a .pkl file from your computer
3. Plays selected file in loop forever
4. Perfect for pre-recorded loops!

Select "OBS Virtual Camera" in Zoom/Teams/Meet."""
        
        tk.Label(help_frame, text=help_text, font=("Courier", 7), 
                justify=tk.LEFT, anchor="w").pack(fill=tk.X)
        
        # Add padding at bottom
        tk.Label(scrollable_frame, text="", height=2).pack()
    
    def start_preview(self):
        """Start camera preview (not virtual camera)"""
        self.preview_running = True
        threading.Thread(target=self.preview_loop, daemon=True).start()
    
    def preview_loop(self):
        """Show live camera feed in preview"""
        while self.preview_running:
            if not self.running:
                ret, frame = self.cap.read()
                if ret:
                    self.update_preview(frame)
            time.sleep(0.033)
    
    def update_quick_delay(self, value):
        if not self.running:
            self.delay_seconds = int(float(value))
            self.quick_label.config(text=f"{self.delay_seconds}s")
            self.update_buffer_info()
    
    def set_manual_delay(self):
        if not self.running:
            try:
                mins = int(self.min_entry.get() or 0)
                secs = int(self.sec_entry.get() or 0)
                
                if mins < 0 or mins > 30:
                    messagebox.showerror("Error", "Minutes must be 0-30!")
                    return
                
                if secs < 0 or secs > 59:
                    messagebox.showerror("Error", "Seconds must be 0-59!")
                    return
                
                self.delay_seconds = mins * 60 + secs
                
                if self.delay_seconds == 0:
                    self.delay_seconds = 1
                
                self.update_buffer_info()
                self.quick_label.config(text=f"{mins}m {secs}s")
                messagebox.showinfo("Success", f"Delay set to {mins}m {secs}s")
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers!")
        else:
            messagebox.showwarning("Warning", "Stop the camera first!")
    
    def update_buffer_info(self):
        self.buffer_size = int(self.delay_seconds * self.fps)
        ram_mb = (self.buffer_size * self.width * self.height * 3) / (1024**2)
        self.buffer_label.config(
            text=f"Buffer: {self.buffer_size} frames | ~{ram_mb:.0f} MB RAM | {self.delay_seconds}s delay"
        )
    
    def toggle_loop(self):
        """Toggle between live delayed and loop mode"""
        if not self.loop_mode:
            # Enter loop mode
            self.loop_mode = True
            self.file_mode = False
            # Freeze current buffer
            self.frozen_buffer = list(self.frame_buffer)
            self.loop_index = 0
            
            self.freeze_btn.config(text="▶ RESUME LIVE", bg="blue")
            self.mode_label.config(text="MODE: Looping Frozen Video 🔄", fg="orange")
            self.status.config(
                text=f"● LOOPING {len(self.frozen_buffer)} frames ({self.delay_seconds}s) repeatedly", 
                fg="purple"
            )
            
            messagebox.showinfo(
                "Loop Mode Active",
                f"Buffer FROZEN!\n\n"
                f"The same {self.delay_seconds} seconds of video will now\n"
                f"play repeatedly forever until you click 'RESUME LIVE'.\n\n"
                f"Frames in loop: {len(self.frozen_buffer)}\n"
                f"Loop duration: {self.delay_seconds} seconds"
            )
        else:
            # Exit loop mode - resume live
            self.loop_mode = False
            self.file_mode = False
            self.frozen_buffer = []
            
            self.freeze_btn.config(text="🔄 FREEZE & LOOP", bg="orange")
            self.mode_label.config(text="MODE: Live Delayed", fg="blue")
            self.status.config(
                text="● LIVE - Delayed feed (updating continuously)", 
                fg="green"
            )
    
    def save_and_replay(self):
        """Save buffer to file and replay from file"""
        if len(self.frame_buffer) == 0:
            messagebox.showwarning("Warning", "No buffer to save!")
            return
        
        try:
            # Create folder if doesn't exist
            os.makedirs(self.save_folder, exist_ok=True)
            
            # Save buffer to file
            file_path = os.path.join(self.save_folder, "delayed_video_buffer.pkl")
            
            self.status.config(text="● Saving buffer to file...", fg="orange")
            
            buffer_list = list(self.frame_buffer)
            with open(file_path, 'wb') as f:
                pickle.dump(buffer_list, f)
            
            # Load from file and start looping
            with open(file_path, 'rb') as f:
                self.frozen_buffer = pickle.load(f)
            
            self.file_mode = True
            self.loop_mode = True
            self.loop_index = 0
            
            self.freeze_btn.config(text="▶ RESUME LIVE", bg="blue")
            self.mode_label.config(text="MODE: Replaying from File 💾🔄", fg="purple")
            self.status.config(
                text=f"● REPLAYING FROM FILE: {len(self.frozen_buffer)} frames in loop", 
                fg="purple"
            )
            
            file_size_mb = os.path.getsize(file_path) / (1024**2)
            
            messagebox.showinfo(
                "File Replay Active",
                f"Buffer SAVED and LOADED from file!\n\n"
                f"File: {file_path}\n"
                f"Size: {file_size_mb:.1f} MB\n"
                f"Frames: {len(self.frozen_buffer)}\n"
                f"Duration: {self.delay_seconds} seconds\n\n"
                f"Video will now loop from saved file forever!\n"
                f"Click 'RESUME LIVE' to go back to live mode."
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save/load buffer:\n{str(e)}")
    
    def load_and_play_file(self):
        """NEW: Load a .pkl file and play it in loop"""
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select Video Buffer File",
            initialdir=self.save_folder,
            filetypes=[
                ("Pickle files", "*.pkl"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Load the file
            self.status.config(text="● Loading file...", fg="orange")
            
            with open(file_path, 'rb') as f:
                loaded_buffer = pickle.load(f)
            
            if not isinstance(loaded_buffer, list) or len(loaded_buffer) == 0:
                messagebox.showerror("Error", "Invalid file format or empty buffer!")
                return
            
            # Check if virtual camera is already running
            if not self.running:
                # Start virtual camera first
                try:
                    self.virtual_cam = pyvirtualcam.Camera(
                        width=self.width, 
                        height=self.height,
                        fps=self.fps, 
                        fmt=pyvirtualcam.PixelFormat.BGR
                    )
                    self.running = True
                    self.start_btn.config(state=tk.DISABLED)
                    self.stop_btn.config(state=tk.NORMAL)
                    
                except Exception as e:
                    messagebox.showerror("OBS Error", 
                        "Failed to start virtual camera!\n\n"
                        "Make sure OBS Virtual Camera is installed and started.")
                    return
            
            # Set loaded buffer for looping
            self.frozen_buffer = loaded_buffer
            self.file_mode = True
            self.loop_mode = True
            self.loop_index = 0
            
            # Update UI
            self.mode_label.config(text="MODE: Playing Loaded File 📂🔄", fg="teal")
            self.status.config(
                text=f"● PLAYING FILE: {len(self.frozen_buffer)} frames in loop", 
                fg="teal"
            )
            
            file_size_mb = os.path.getsize(file_path) / (1024**2)
            duration_sec = len(loaded_buffer) / self.fps
            
            # Start playback thread if not already running
            if not hasattr(self, 'playback_thread') or not self.playback_thread.is_alive():
                self.playback_thread = threading.Thread(target=self.file_playback_loop, daemon=True)
                self.playback_thread.start()
            
            messagebox.showinfo(
                "File Loaded Successfully!",
                f"File: {os.path.basename(file_path)}\n"
                f"Size: {file_size_mb:.1f} MB\n"
                f"Frames: {len(loaded_buffer)}\n"
                f"Duration: ~{duration_sec:.1f} seconds\n\n"
                f"Video will now loop continuously!\n\n"
                f"Use 'OBS Virtual Camera' in your video app.\n"
                f"Click STOP to end playback."
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
    
    def file_playback_loop(self):
        """Separate loop for file playback"""
        frame_count = 0
        
        while self.running and self.file_mode:
            if len(self.frozen_buffer) > 0:
                frame = self.frozen_buffer[self.loop_index]
                self.loop_index = (self.loop_index + 1) % len(self.frozen_buffer)
                
                # Send to virtual camera
                if self.virtual_cam:
                    self.virtual_cam.send(frame)
                    self.virtual_cam.sleep_until_next_frame()
                
                # Update preview every 10 frames
                if frame_count % 10 == 0:
                    self.update_preview(frame)
                
                frame_count += 1
    
    def start(self):
        if self.delay_seconds == 0:
            messagebox.showwarning("Warning", "Please set a delay time first!")
            return
        
        # Check if OBS is installed
        try:
            test_cam = pyvirtualcam.Camera(width=640, height=480, fps=30)
            test_cam.close()
        except Exception as e:
            messagebox.showerror(
                "OBS Not Found!",
                "OBS Virtual Camera is not installed!\n\n"
                "STEPS TO FIX:\n"
                "1. Download OBS Studio from:\n"
                "   https://obsproject.com/download\n\n"
                "2. Install it\n\n"
                "3. Open OBS Studio\n\n"
                "4. Click Tools → Start Virtual Camera\n\n"
                "5. Close OBS and try again\n\n"
                "Click OK to open download page..."
            )
            webbrowser.open("https://obsproject.com/download")
            return
        
        self.running = True
        self.loop_mode = False
        self.file_mode = False
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.quick_slider.config(state=tk.DISABLED)
        self.status.config(text="● Initializing...", fg="orange")
        
        self.frame_buffer.clear()
        self.buffer_size = int(self.delay_seconds * self.fps)
        self.frame_buffer = deque(maxlen=self.buffer_size)
        
        threading.Thread(target=self.camera_loop, daemon=True).start()
    
    def stop(self):
        self.running = False
        self.loop_mode = False
        self.file_mode = False
        self.frozen_buffer = []
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.freeze_btn.config(state=tk.DISABLED)
        self.save_replay_btn.config(state=tk.DISABLED)
        self.quick_slider.config(state=tk.NORMAL)
        
        self.mode_label.config(text="MODE: Stopped", fg="red")
        self.status.config(text="● Stopped - Preview Mode", fg="orange")
        self.progress['value'] = 0
        
        if self.virtual_cam:
            try:
                self.virtual_cam.close()
            except:
                pass
            self.virtual_cam = None
    
    def camera_loop(self):
        """Main loop for virtual camera with delay"""
        # Fill buffer
        self.status.config(text="● Filling Buffer... Please wait", fg="orange")
        
        for i in range(self.buffer_size):
            if not self.running:
                return
            
            ret, frame = self.cap.read()
            if ret:
                self.frame_buffer.append(frame)
                progress = ((i + 1) / self.buffer_size) * 100
                self.progress['value'] = progress
                
                if i % 30 == 0:
                    self.update_preview(frame)
        
        # Enable buttons
        self.freeze_btn.config(state=tk.NORMAL)
        self.save_replay_btn.config(state=tk.NORMAL)
        
        # Start virtual camera
        try:
            self.virtual_cam = pyvirtualcam.Camera(
                width=self.width, 
                height=self.height,
                fps=self.fps, 
                fmt=pyvirtualcam.PixelFormat.BGR
            )
            
            device_name = "OBS Virtual Camera"
            self.mode_label.config(text="MODE: Live Delayed", fg="blue")
            self.status.config(
                text=f"● LIVE! Select '{device_name}' in Zoom/Teams/Meet", 
                fg="green"
            )
            
            messagebox.showinfo(
                "Virtual Camera Started!",
                f"Virtual camera is now ACTIVE!\n\n"
                f"In your video app (Zoom, Teams, etc.):\n"
                f"1. Open Settings\n"
                f"2. Go to Video/Camera settings\n"
                f"3. Select: {device_name}\n\n"
                f"Your video will be delayed by {self.delay_seconds} seconds!\n\n"
                f"Options:\n"
                f"• Click 'FREEZE & LOOP' to loop current buffer\n"
                f"• Click 'SAVE BUFFER TO FILE' to save and replay\n"
                f"• Click 'LOAD & PLAY FILE' to play saved .pkl files\n"
                f"Keep this window open (can minimize it)."
            )
            
            frame_count = 0
            
            while self.running:
                if self.loop_mode and not self.file_mode:
                    # LOOP MODE: Play frozen buffer repeatedly
                    if len(self.frozen_buffer) > 0:
                        delayed_frame = self.frozen_buffer[self.loop_index]
                        self.loop_index = (self.loop_index + 1) % len(self.frozen_buffer)
                    else:
                        ret, delayed_frame = self.cap.read()
                        if not ret:
                            continue
                elif self.file_mode:
                    # File mode is handled in separate thread
                    time.sleep(0.1)
                    continue
                else:
                    # LIVE DELAYED MODE: Continue reading camera
                    ret, frame = self.cap.read()
                    if not ret:
                        time.sleep(0.01)
                        continue
                    
                    # Add to buffer
                    self.frame_buffer.append(frame)
                    
                    # Get delayed frame
                    delayed_frame = self.frame_buffer[0]
                
                # Send to virtual camera
                self.virtual_cam.send(delayed_frame)
                self.virtual_cam.sleep_until_next_frame()
                
                # Update preview every 10 frames
                if frame_count % 10 == 0:
                    self.update_preview(delayed_frame)
                
                frame_count += 1
        
        except Exception as e:
            error_msg = str(e)
            self.status.config(text=f"● Error: Virtual camera failed", fg="red")
            messagebox.showerror("Virtual Camera Error", 
                f"Failed to start virtual camera:\n{error_msg}\n\n"
                "Make sure:\n"
                "1. OBS Studio is installed\n"
                "2. OBS Virtual Camera is started (Tools → Start Virtual Camera)\n"
                "3. No other app is using the virtual camera")
            self.stop()
    
    def update_preview(self, frame):
        """Update preview image"""
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb).resize((480, 360), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.root.after(0, self._set_preview_image, imgtk)
        except Exception as e:
            pass
    
    def _set_preview_image(self, imgtk):
        """Set preview image in main thread"""
        try:
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        except:
            pass
    
    def on_closing(self):
        self.running = False
        self.preview_running = False
        time.sleep(0.3)
        
        if self.virtual_cam:
            try:
                self.virtual_cam.close()
            except:
                pass
        
        if self.cap.isOpened():
            self.cap.release()
        
        cv2.destroyAllWindows()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualDelayedCameraGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()