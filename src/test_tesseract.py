import pytesseract
from PIL import Image
import os

# Set the path to the Tesseract executable
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Check if the file exists
if os.path.isfile(tesseract_path):
    print(f"Tesseract executable found at: {tesseract_path}")
else:
    print(f"Tesseract executable NOT found at: {tesseract_path}")
    
try:
    print("Tesseract version:", pytesseract.get_tesseract_version())
except Exception as e:
    print(f"Error getting Tesseract version: {e}")

print("Tesseract path setting:", pytesseract.pytesseract.tesseract_cmd)
