import cv2
from collections import deque
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time

class DelayedCameraGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Camera Delay Controller - Up to 30 Minutes")
        
        self.cap = cv2.VideoCapture(0)
        
        # Set camera properties for better performance
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
        
        # Default delay
        self.delay_seconds = 3
        self.buffer_size = int(self.delay_seconds * self.fps)
        self.frame_buffer = deque(maxlen=self.buffer_size)
        
        self.running = False
        self.current_photo = None
        
        # For smooth display updates
        self.last_update_time = 0
        self.min_update_interval = 1.0 / self.fps  # Match camera FPS
        
        self.setup_gui()
    
    def setup_gui(self):
        # Video display
        self.video_label = tk.Label(self.root, bg="black")
        self.video_label.pack(padx=10, pady=10)
        
        # Controls frame
        controls = tk.Frame(self.root)
        controls.pack(padx=10, pady=5, fill=tk.X)
        
        # Delay input method selection
        delay_method_frame = tk.Frame(controls)
        delay_method_frame.pack(pady=5)
        
        tk.Label(delay_method_frame, text="Delay Input:").pack(side=tk.LEFT, padx=5)
        
        self.delay_method = tk.StringVar(value="slider")
        tk.Radiobutton(delay_method_frame, text="Slider (0-60s)", 
                      variable=self.delay_method, value="slider",
                      command=self.toggle_delay_method).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(delay_method_frame, text="Manual Input (up to 30 min)", 
                      variable=self.delay_method, value="manual",
                      command=self.toggle_delay_method).pack(side=tk.LEFT, padx=5)
        
        # Slider frame
        self.slider_frame = tk.Frame(controls)
        self.slider_frame.pack(pady=5)
        
        tk.Label(self.slider_frame, text="Delay (seconds):").grid(row=0, column=0, padx=5)
        self.delay_slider = ttk.Scale(self.slider_frame, from_=0, to=60, orient=tk.HORIZONTAL, 
                                      length=300, command=self.update_delay_slider)
        self.delay_slider.set(self.delay_seconds)
        self.delay_slider.grid(row=0, column=1, padx=5)
        
        self.slider_label = tk.Label(self.slider_frame, text=f"{self.delay_seconds:.1f}s")
        self.slider_label.grid(row=0, column=2, padx=5)
        
        # Manual input frame (initially hidden)
        self.manual_frame = tk.Frame(controls)
        
        tk.Label(self.manual_frame, text="Minutes:").grid(row=0, column=0, padx=5)
        self.minutes_entry = tk.Entry(self.manual_frame, width=5)
        self.minutes_entry.insert(0, "0")
        self.minutes_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(self.manual_frame, text="Seconds:").grid(row=0, column=2, padx=5)
        self.seconds_entry = tk.Entry(self.manual_frame, width=5)
        self.seconds_entry.insert(0, "3")
        self.seconds_entry.grid(row=0, column=3, padx=5)
        
        self.apply_btn = tk.Button(self.manual_frame, text="Apply", 
                                   command=self.update_delay_manual)
        self.apply_btn.grid(row=0, column=4, padx=5)
        
        self.manual_label = tk.Label(self.manual_frame, text="Total: 3s")
        self.manual_label.grid(row=0, column=5, padx=5)
        
        # Info label
        self.info_label = tk.Label(controls, text=f"FPS: {self.fps} | Buffer: {self.buffer_size} frames", 
                                   font=("Arial", 9))
        self.info_label.pack(pady=5)
        
        # Memory usage label
        self.memory_label = tk.Label(controls, text="Memory: Calculating...", 
                                     font=("Arial", 9), fg="blue")
        self.memory_label.pack(pady=2)
        
        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.start_btn = tk.Button(button_frame, text="Start", command=self.start, 
                                    bg="green", fg="white", width=10, height=2)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(button_frame, text="Stop", command=self.stop, 
                                   bg="red", fg="white", width=10, height=2, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = tk.Label(self.root, text="Status: Stopped", 
                                     fg="red", font=("Arial", 12, "bold"))
        self.status_label.pack(pady=5)
        
        # Progress bar for buffer filling
        self.progress_frame = tk.Frame(self.root)
        self.progress_frame.pack(pady=5, fill=tk.X, padx=20)
        
        tk.Label(self.progress_frame, text="Buffer:").pack(side=tk.LEFT, padx=5)
        self.progress_bar = ttk.Progressbar(self.progress_frame, length=400, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        
        self.progress_label = tk.Label(self.progress_frame, text="0%")
        self.progress_label.pack(side=tk.LEFT, padx=5)
    
    def toggle_delay_method(self):
        if self.delay_method.get() == "slider":
            self.manual_frame.pack_forget()
            self.slider_frame.pack(pady=5)
        else:
            self.slider_frame.pack_forget()
            self.manual_frame.pack(pady=5)
    
    def update_delay_slider(self, value):
        if not self.running:
            self.delay_seconds = float(value)
            self.slider_label.config(text=f"{self.delay_seconds:.1f}s")
            self.update_buffer_info()
    
    def update_delay_manual(self):
        if not self.running:
            try:
                minutes = int(self.minutes_entry.get() or 0)
                seconds = int(self.seconds_entry.get() or 0)
                
                if minutes < 0 or minutes > 30:
                    self.manual_label.config(text="Minutes: 0-30 only!", fg="red")
                    return
                
                if seconds < 0 or seconds > 59:
                    self.manual_label.config(text="Seconds: 0-59 only!", fg="red")
                    return
                
                self.delay_seconds = minutes * 60 + seconds
                
                if self.delay_seconds > 1800:  # 30 minutes max
                    self.manual_label.config(text="Max 30 minutes!", fg="red")
                    return
                
                self.manual_label.config(text=f"Total: {self.delay_seconds}s ({minutes}m {seconds}s)", 
                                        fg="green")
                self.update_buffer_info()
                
            except ValueError:
                self.manual_label.config(text="Invalid input!", fg="red")
    
    def update_buffer_info(self):
        self.buffer_size = int(self.delay_seconds * self.fps)
        self.info_label.config(text=f"FPS: {self.fps} | Buffer: {self.buffer_size} frames | Delay: {self.delay_seconds}s")
        
        # Estimate memory usage (rough calculation)
        # Assuming 640x480 resolution, 3 channels (BGR), 1 byte per pixel
        bytes_per_frame = 640 * 480 * 3
        total_mb = (self.buffer_size * bytes_per_frame) / (1024 * 1024)
        self.memory_label.config(text=f"Estimated Memory: {total_mb:.1f} MB")
    
    def start(self):
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.delay_slider.config(state=tk.DISABLED)
        self.apply_btn.config(state=tk.DISABLED)
        
        # Clear existing buffer
        self.frame_buffer.clear()
        self.buffer_size = int(self.delay_seconds * self.fps)
        self.frame_buffer = deque(maxlen=self.buffer_size)
        
        self.status_label.config(text="Status: Filling Buffer...", fg="orange")
        
        # Start video thread
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()
    
    def stop(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.delay_slider.config(state=tk.NORMAL)
        self.apply_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Stopped", fg="red")
        self.progress_bar['value'] = 0
        self.progress_label.config(text="0%")
    
    def video_loop(self):
        buffer_filled = False
        frame_count = 0
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame")
                time.sleep(0.01)
                continue
            
            # Add to buffer
            self.frame_buffer.append(frame)
            frame_count += 1
            
            # Update progress during buffer fill
            if not buffer_filled:
                progress = min((len(self.frame_buffer) / self.buffer_size) * 100, 100)
                self.progress_bar['value'] = progress
                self.progress_label.config(text=f"{progress:.0f}%")
                
                if len(self.frame_buffer) >= self.buffer_size:
                    buffer_filled = True
                    self.status_label.config(text="Status: Running (Live)", fg="green")
            
            # Get delayed frame
            if len(self.frame_buffer) >= self.buffer_size:
                delayed_frame = self.frame_buffer[0]
            else:
                delayed_frame = frame  # Show current frame while buffering
            
            # Update display (throttled to prevent flickering)
            current_time = time.time()
            if current_time - self.last_update_time >= self.min_update_interval:
                self.update_display(delayed_frame)
                self.last_update_time = current_time
            
            # Small sleep to prevent CPU overload
            time.sleep(0.001)
    
    def update_display(self, frame):
        try:
            # Convert for tkinter
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            img = img.resize((640, 480), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Keep a reference to prevent garbage collection
            self.current_photo = imgtk
            
            # Update in main thread
            self.root.after(0, self._update_label, imgtk)
            
        except Exception as e:
            print(f"Display error: {e}")
    
    def _update_label(self, imgtk):
        """Update label in main thread"""
        try:
            self.video_label.configure(image=imgtk)
        except:
            pass
    
    def on_closing(self):
        self.running = False
        time.sleep(0.1)  # Give thread time to stop
        if self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        self.root.destroy()

# Usage
if __name__ == "__main__":
    root = tk.Tk()
    app = DelayedCameraGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()