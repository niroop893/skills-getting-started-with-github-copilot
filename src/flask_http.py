from flask import Flask, request
import time

app = Flask(__name__)

received_requests = []

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    request_info = {
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'method': request.method,
        'path': f"/{path}",
        'query': request.query_string.decode(),
        'headers': dict(request.headers),
        'remote_addr': request.remote_addr
    }
    received_requests.append(request_info)
    
    print("\n" + "="*70)
    print("[+] REQUEST RECEIVED!")
    print("="*70)
    print(f"Time: {request_info['time']}")
    print(f"Method: {request_info['method']}")
    print(f"Path: {request_info['path']}")
    print(f"Query: {request_info['query']}")
    print(f"From: {request_info['remote_addr']}")
    print(f"Headers:")
    for key, value in request_info['headers'].items():
        print(f"  {key}: {value}")
    print("="*70 + "\n")
    
    return "OK", 200

if __name__ == "__main__":
    print("="*70)
    print("HTTP Server for Out-of-Band SQL Injection Detection")
    print("="*70)
    print("Listening on port 8080...")
    print("="*70 + "\n")
    app.run(host='0.0.0.0', port=8080, debug=False)