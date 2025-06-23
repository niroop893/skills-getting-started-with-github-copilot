import threading
import webview
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
import pyautogui
import base64
from io import BytesIO
from PIL import Image, ImageTk
from pynput import keyboard
import tkinter as tk
from tkinter import messagebox
import ctypes
from ctypes import wintypes
import sys
import random
import string
import subprocess
import time

# === Integrated Pearson Bypass ===
class PearsonBypass:
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.ntdll = ctypes.windll.ntdll
        self.user32 = ctypes.windll.user32
        
    def hide_from_enumeration(self):
        try:
            current_process = self.kernel32.GetCurrentProcess()
            self.ntdll.NtSetInformationProcess(current_process, 0x1D, ctypes.byref(ctypes.c_int(1)), 4)
        except: pass
    
    def spoof_process_name(self):
        try:
            new_name = "dwm.exe\x00"
            name_ptr = ctypes.c_char_p(new_name.encode())
            self.kernel32.SetConsoleTitleA(name_ptr)
        except: pass
    
    def disable_hooks(self):
        try:
            hooks = [('kernel32.dll', 'CreateProcessA'), ('user32.dll', 'FindWindowA')]
            for dll_name, func_name in hooks:
                try:
                    dll = ctypes.windll.LoadLibrary(dll_name)
                    func_addr = ctypes.windll.kernel32.GetProcAddress(dll._handle, func_name.encode())
                    if func_addr:
                        old_protect = ctypes.c_ulong()
                        self.kernel32.VirtualProtect(func_addr, 1, 0x40, ctypes.byref(old_protect))
                        ctypes.c_ubyte.from_address(func_addr).value = 0xC3
                except: continue
        except: pass
    
    def run_bypass(self):
        self.hide_from_enumeration()
        self.spoof_process_name()
        self.disable_hooks()
        threading.Thread(target=self.monitor_detection, daemon=True).start()
    
    def monitor_detection(self):
        while True:
            try:
                result = os.popen('tasklist /FI "IMAGENAME eq *pearson*"').read()
                if 'pearson' in result.lower():
                    self.hide_from_enumeration()
                    self.spoof_process_name()
                time.sleep(5)
            except: break

# === Stealth Injection ===
def inject_into_system_process():
    try:
        processes = ['explorer.exe', 'dwm.exe']
        for proc_name in processes:
            try:
                result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {proc_name}'], capture_output=True, text=True)
                if proc_name in result.stdout:
                    return True
            except: continue
        return False
    except: return False

# Initialize bypass
bypass = PearsonBypass()
bypass.run_bypass()
inject_into_system_process()

# === Configure Gemini ===
genai.configure(api_key="AIzaSyB-buiM1EOFqBi10I8sisGw7b29PYsyRAY")

# === Start Flask server ===
app = Flask(__name__)
CORS(app)
model = genai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat()

@app.route("/chat", methods=["POST"])
def chat_with_gemini():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"reply": "⚠️ No message provided"})
        
        message = data['message']
        if not message.strip():
            return jsonify({"reply": "⚠️ Empty message"})
            
        response = chat.send_message(message)
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": f"⚠️ Error: {str(e)}"}), 500

def select_area():
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-alpha', 0.3)
    root.configure(bg='grey')
    root.attributes('-topmost', True)
    
    canvas = tk.Canvas(root, highlightthickness=0)
    canvas.pack(fill='both', expand=True)
    
    start_x = start_y = end_x = end_y = 0
    rect_id = None
    
    def on_click(event):
        nonlocal start_x, start_y, rect_id
        start_x, start_y = event.x, event.y
        if rect_id:
            canvas.delete(rect_id)
    
    def on_drag(event):
        nonlocal rect_id, end_x, end_y
        end_x, end_y = event.x, event.y
        if rect_id:
            canvas.delete(rect_id)
        rect_id = canvas.create_rectangle(start_x, start_y, end_x, end_y, outline='red', width=2)
    
    def on_release(event):
        root.quit()
    
    canvas.bind('<Button-1>', on_click)
    canvas.bind('<B1-Motion>', on_drag)
    canvas.bind('<ButtonRelease-1>', on_release)
    
    root.mainloop()
    root.destroy()
    
    return min(start_x, end_x), min(start_y, end_y), abs(end_x - start_x), abs(end_y - start_y)

@app.route("/screenshot", methods=["POST"])
def screenshot_chat():
    try:
        data = request.get_json()
        message = data.get('message', 'Analyze this multiple choice question and provide the correct answer with explanation.')
        
        # Select area
        x, y, width, height = select_area()
        
        if width < 10 or height < 10:
            return jsonify({"reply": "⚠️ Selected area too small"})
        
        # Take screenshot of selected area
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        
        # Convert to base64
        buffer = BytesIO()
        screenshot.save(buffer, format='PNG')
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        # Optimized prompt for MCQ
        mcq_prompt = "Analyze this multiple choice question. Provide: 1) The correct answer (A, B, C, or D), 2) Brief explanation why it's correct. Be concise and direct."
        
        # Send to Gemini with image
        response = model.generate_content([mcq_prompt, {'mime_type': 'image/png', 'data': img_data}])
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": f"⚠️ Error: {str(e)}"}), 500

def run_flask():
    app.run(port=5000, debug=False, use_reloader=False)

# === Start Flask in background ===
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# === HTML frontend ===
html = """
<!DOCTYPE html>
<html>
<head>
  <title>Gemini Bot</title>
  <style>
    body { font-family: Arial; margin: 20px; background-color: #f8f8f8; }
    #chatbox { height: 300px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; background: white; }
    #input { width: 80%; }
    button { padding: 6px 12px; }
  </style>
</head>
<body>
  <h2>Gemini Chat</h2>
  <div id="chatbox"></div>
  <input type="text" id="input" placeholder="Type a message..." />
  <button onclick="send()">Send</button>
  <button onclick="screenshot()">Screenshot</button>

  <script>
    async function send() {
      const msg = document.getElementById("input").value;
      if (!msg.trim()) return;
      document.getElementById("chatbox").innerHTML += "<b>You:</b> " + msg + "<br/>";
      const res = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg })
      });
      const data = await res.json();
      document.getElementById("chatbox").innerHTML += "<b>Gemini:</b> " + data.reply + "<br/>";
      document.getElementById("input").value = "";
      document.getElementById("chatbox").scrollTop = document.getElementById("chatbox").scrollHeight;
    }
    
    async function screenshot() {
      const msg = document.getElementById("input").value || "What do you see in this screenshot?";
      document.getElementById("chatbox").innerHTML += "<b>You:</b> [Screenshot] " + msg + "<br/>";
      const res = await fetch("http://localhost:5000/screenshot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg })
      });
      const data = await res.json();
      document.getElementById("chatbox").innerHTML += "<b>Gemini:</b> " + data.reply + "<br/>";
      document.getElementById("input").value = "";
      document.getElementById("chatbox").scrollTop = document.getElementById("chatbox").scrollHeight;
    }
  </script>
</body>
</html>
"""

# === Global window reference ===
window = None
window_visible = False

def set_window_topmost():
    try:
        hwnd = ctypes.windll.user32.FindWindowW(None, random_title)
        if hwnd:
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.BringWindowToTop(hwnd)
    except: pass

def toggle_window():
    global window_visible
    if window:
        if window_visible:
            window.minimize()
            window_visible = False
        else:
            window.restore()
            set_window_topmost()
            window_visible = True

# === Setup hotkey ===
def on_press(key):
    try:
        if key.char == '1':
            toggle_window()
    except AttributeError:
        pass

listener = keyboard.Listener(on_press=on_press)
listener.start()

# === Launch stealth window ===
system_titles = ["Windows Security", "System Configuration", "Device Manager", "Services"]
random_title = random.choice(system_titles)

# Create window with system-like appearance
window = webview.create_window(
    random_title, 
    html=html, 
    width=600, 
    height=500, 
    on_top=True,
    shadow=False,
    resizable=False
)
window_visible = True

# Advanced stealth mode
def stealth_mode():
    try:
        # Find and modify window properties
        hwnd = ctypes.windll.user32.FindWindowW(None, random_title)
        if hwnd:
            # Remove from Alt+Tab
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, ex_style | 0x80)
            
            # Set as system window
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
    except:
        pass

def on_window_loaded():
    threading.Timer(0.5, stealth_mode).start()

webview.start(on_window_loaded)
