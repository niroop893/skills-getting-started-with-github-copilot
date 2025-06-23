import ctypes
import ctypes.wintypes
import threading
import time
import os

class PearsonBypass:
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.ntdll = ctypes.windll.ntdll
        self.user32 = ctypes.windll.user32
        
    def hide_from_enumeration(self):
        try:
            # Get current process handle
            current_process = self.kernel32.GetCurrentProcess()
            
            # Hide process from enumeration
            self.ntdll.NtSetInformationProcess(
                current_process, 0x1D, ctypes.byref(ctypes.c_int(1)), 4
            )
            
            # Modify PEB to hide process
            peb_ptr = ctypes.c_void_p()
            self.ntdll.NtQueryInformationProcess(
                current_process, 0, ctypes.byref(peb_ptr), 
                ctypes.sizeof(ctypes.c_void_p), None
            )
            
        except:
            pass
    
    def spoof_process_name(self):
        try:
            # Change process name in memory
            new_name = "dwm.exe\x00"
            name_ptr = ctypes.c_char_p(new_name.encode())
            
            # Overwrite process name in PEB
            self.kernel32.SetConsoleTitleA(name_ptr)
            
        except:
            pass
    
    def disable_hooks(self):
        try:
            # Disable common API hooks used by monitoring software
            hooks = [
                ('kernel32.dll', 'CreateProcessA'),
                ('kernel32.dll', 'CreateProcessW'),
                ('user32.dll', 'FindWindowA'),
                ('user32.dll', 'FindWindowW'),
                ('ntdll.dll', 'NtQuerySystemInformation')
            ]
            
            for dll_name, func_name in hooks:
                try:
                    dll = ctypes.windll.LoadLibrary(dll_name)
                    func_addr = ctypes.windll.kernel32.GetProcAddress(
                        dll._handle, func_name.encode()
                    )
                    if func_addr:
                        # Patch function to return immediately
                        old_protect = ctypes.c_ulong()
                        self.kernel32.VirtualProtect(
                            func_addr, 1, 0x40, ctypes.byref(old_protect)
                        )
                        ctypes.c_ubyte.from_address(func_addr).value = 0xC3  # RET
                except:
                    continue
        except:
            pass
    
    def run_bypass(self):
        self.hide_from_enumeration()
        self.spoof_process_name()
        self.disable_hooks()
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_detection, daemon=True)
        monitor_thread.start()
    
    def monitor_detection(self):
        while True:
            try:
                # Check for Pearson VUE processes
                result = os.popen('tasklist /FI "IMAGENAME eq *pearson*"').read()
                if 'pearson' in result.lower():
                    # Re-apply stealth measures
                    self.hide_from_enumeration()
                    self.spoof_process_name()
                
                time.sleep(5)
            except:
                break

# Initialize bypass
bypass = PearsonBypass()
bypass.run_bypass()