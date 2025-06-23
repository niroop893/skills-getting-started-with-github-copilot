import webview
import threading
import subprocess
import os
import sys

# Get absolute path to gemini_server.py (PyInstaller safe)
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

server_script = os.path.join(BASE_DIR, "gemini_server.py")

def start_server():
    subprocess.Popen([sys.executable, server_script])

threading.Thread(target=start_server).start()

# --- Minimal HTML chat UI ---
html = """
<!DOCTYPE html>
<html>
<head>
  <title>Gemini Chat</title>
  <style>
    body { font-family: sans-serif; margin: 20px; }
    #chatbox { height: 300px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; }
    #input { width: 80%; }
  </style>
</head>
<body>
  <h2>Gemini Chat</h2>
  <div id="chatbox"></div>
  <input type="text" id="input" placeholder="Type a message..." />
  <button onclick="send()">Send</button>

  <script>
    async function send() {
      const msg = document.getElementById("input").value;
      document.getElementById("chatbox").innerHTML += "<b>You:</b> " + msg + "<br/>";
      const res = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg })
      });
      const data = await res.json();
      document.getElementById("chatbox").innerHTML += "<b>Gemini:</b> " + data.reply + "<br/>";
      document.getElementById("input").value = "";
    }
  </script>
</body>
</html>
"""

webview.create_window("Gemini Bot", html=html)
webview.start()
