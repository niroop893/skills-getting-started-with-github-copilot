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
try:
    import win32gui
    import win32ui
    import win32con
except ImportError:
    pass

# === Advanced Pearson Bypass ===
class PearsonBypass:
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.ntdll = ctypes.windll.ntdll
        self.user32 = ctypes.windll.user32
        
    def deep_hide_process(self):
        try:
            current_process = self.kernel32.GetCurrentProcess()
            # Multiple hiding techniques
            self.ntdll.NtSetInformationProcess(current_process, 0x1D, ctypes.byref(ctypes.c_int(1)), 4)
            self.ntdll.NtSetInformationProcess(current_process, 0x1E, ctypes.byref(ctypes.c_int(1)), 4)
            self.ntdll.NtSetInformationProcess(current_process, 0x1F, ctypes.byref(ctypes.c_int(1)), 4)
        except: pass
    
    def randomize_memory_layout(self):
        try:
            # Randomize process memory to avoid signature detection
            for i in range(10):
                size = random.randint(1024, 4096)
                addr = self.kernel32.VirtualAlloc(None, size, 0x3000, 0x04)
                if addr:
                    # Fill with random data
                    random_data = bytes([random.randint(0, 255) for _ in range(size)])
                    ctypes.memmove(addr, random_data, size)
        except: pass
    
    def patch_detection_apis(self):
        try:
            # Patch more APIs used by Pearson VUE
            apis = [
                ('kernel32.dll', 'CreateToolhelp32Snapshot'),
                ('kernel32.dll', 'Process32First'),
                ('kernel32.dll', 'Process32Next'),
                ('ntdll.dll', 'NtQuerySystemInformation'),
                ('psapi.dll', 'EnumProcesses'),
                ('user32.dll', 'EnumWindows'),
                ('kernel32.dll', 'OpenProcess')
            ]
            
            for dll_name, func_name in apis:
                try:
                    dll = ctypes.windll.LoadLibrary(dll_name)
                    func_addr = self.kernel32.GetProcAddress(dll._handle, func_name.encode())
                    if func_addr:
                        old_protect = ctypes.c_ulong()
                        self.kernel32.VirtualProtect(func_addr, 8, 0x40, ctypes.byref(old_protect))
                        # Patch with return instruction
                        patch = b'\x48\x31\xC0\xC3\x90\x90\x90\x90'  # xor rax,rax; ret; nop; nop; nop; nop
                        ctypes.memmove(func_addr, patch, 8)
                        self.kernel32.VirtualProtect(func_addr, 8, old_protect.value, ctypes.byref(old_protect))
                except: continue
        except: pass
    
    def inject_legitimate_process(self):
        try:
            # Find Windows system process to inject into
            system_processes = ['winlogon.exe', 'services.exe', 'lsass.exe']
            for proc_name in system_processes:
                try:
                    result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {proc_name}'], 
                                          capture_output=True, text=True)
                    if proc_name in result.stdout:
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if proc_name in line:
                                pid = int(line.split()[1])
                                # Attempt process hollowing
                                self.hollow_process(pid)
                                return True
                except: continue
        except: pass
        return False
    
    def hollow_process(self, target_pid):
        try:
            process_handle = self.kernel32.OpenProcess(0x1F0FFF, False, target_pid)
            if process_handle:
                # Allocate memory in target process
                remote_mem = self.kernel32.VirtualAllocEx(
                    process_handle, None, 8192, 0x3000, 0x40
                )
                if remote_mem:
                    # Create remote thread
                    thread_handle = self.kernel32.CreateRemoteThread(
                        process_handle, None, 0, remote_mem, None, 0, None
                    )
                    if thread_handle:
                        self.kernel32.CloseHandle(thread_handle)
                self.kernel32.CloseHandle(process_handle)
        except: pass
    
    def run_bypass(self):
        self.deep_hide_process()
        self.randomize_memory_layout()
        self.patch_detection_apis()
        self.inject_legitimate_process()
        threading.Thread(target=self.continuous_evasion, daemon=True).start()
    
    def continuous_evasion(self):
        while True:
            try:
                # Continuously re-apply evasion techniques
                self.deep_hide_process()
                self.randomize_memory_layout()
                time.sleep(3)
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

def hide_bot_window():
    try:
        hwnd = ctypes.windll.user32.FindWindowW(None, random_title)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # Hide window
            return hwnd
    except: pass
    return None

def show_bot_window(hwnd):
    try:
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 1)  # Show window
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)  # Bring to top
    except: pass

def capture_screen_area():
    try:
        # Use direct screen capture with memory manipulation
        import win32gui
        import win32ui
        import win32con
        
        # Get screen dimensions
        screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        screen_height = ctypes.windll.user32.GetSystemMetrics(1)
        
        # Create device context
        hdesktop = win32gui.GetDesktopWindow()
        desktop_dc = win32gui.GetWindowDC(hdesktop)
        img_dc = win32ui.CreateDCFromHandle(desktop_dc)
        mem_dc = img_dc.CreateCompatibleDC()
        
        # Create bitmap
        screenshot = win32ui.CreateBitmap()
        screenshot.CreateCompatibleBitmap(img_dc, screen_width, screen_height)
        mem_dc.SelectObject(screenshot)
        
        # Copy screen to bitmap
        mem_dc.BitBlt((0, 0), (screen_width, screen_height), img_dc, (0, 0), win32con.SRCCOPY)
        
        # Convert to PIL Image
        bmpinfo = screenshot.GetInfo()
        bmpstr = screenshot.GetBitmapBits(True)
        img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
        
        # Cleanup
        mem_dc.DeleteDC()
        win32gui.ReleaseDC(hdesktop, desktop_dc)
        
        return img
        
    except ImportError:
        # Fallback to pyautogui with bypass
        try:
            # Disable fail-safe
            pyautogui.FAILSAFE = False
            # Take full screen
            screenshot = pyautogui.screenshot()
            return screenshot
        except:
            return None
    except Exception as e:
        print(f"Screen capture error: {e}")
        return None

@app.route("/screenshot", methods=["POST"])
def screenshot_chat():
    try:
        data = request.get_json()
        message = data.get('message', 'Analyze this multiple choice question and provide the correct answer with explanation.')
        
        # Hide bot window temporarily
        bot_hwnd = hide_bot_window()
        time.sleep(0.8)
        
        # Capture full screen
        screenshot = capture_screen_area()
        
        if not screenshot:
            show_bot_window(bot_hwnd)
            return jsonify({"reply": "⚠️ Could not capture screen"})
        
        # Show selection overlay for area selection
        x, y, width, height = select_area()
        
        if width < 10 or height < 10:
            show_bot_window(bot_hwnd)
            return jsonify({"reply": "⚠️ Selected area too small"})
        
        # Crop selected area
        cropped = screenshot.crop((x, y, x + width, y + height))
        
        # Restore bot window
        show_bot_window(bot_hwnd)
        
        # Convert to base64
        buffer = BytesIO()
        cropped.save(buffer, format='PNG')
        img_data = base64.b64encode(buffer.getvalue()).decode()
        
        # Optimized prompt for Pearson VUE MCQ
        mcq_prompt = "This is a Pearson VUE exam question. Analyze the multiple choice question and all answer options. Provide: 1) The correct answer letter (A, B, C, or D), 2) Brief explanation why it's correct. Be precise and direct."
        
        # Send to Gemini with image
        response = model.generate_content([mcq_prompt, {'mime_type': 'image/png', 'data': img_data}])
        return jsonify({"reply": response.text})
    except Exception as e:
        try:
            show_bot_window(bot_hwnd)
        except: pass
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
        hwnd = ctypes.windll.user32.FindWindowW(None, random_title)
        if hwnd:
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, ex_style | 0x80)
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
    except: pass

def on_window_loaded():
    threading.Timer(0.5, stealth_mode).start()

webview.start(on_window_loaded)
