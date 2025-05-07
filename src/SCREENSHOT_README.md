# Screenshot Tool with OCR

This tool allows you to take screenshots and automatically extract text from them using Optical Character Recognition (OCR).

## Features

- Take screenshots of selected areas by clicking and dragging
- Take full-screen screenshots
- Automatically extract text from screenshots using OCR
- Save both images and extracted text to the screenshots folder

## Requirements

- Python 3.6 or higher
- Required Python packages (install with `pip install -r requirements.txt`):
  - Pillow (PIL)
  - pytesseract
  - tkinter (usually comes with Python)

- Tesseract OCR engine:
  - **Windows**: Download and install from [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
  - **macOS**: Install with Homebrew: `brew install tesseract`
  - **Linux**: Install with apt: `sudo apt install tesseract-ocr`

## Usage

### Taking a Screenshot of a Selected Area

```python
from src.screenshot import take_screenshot

take_screenshot()
```

This will:
1. Open a transparent fullscreen window
2. Allow you to click and drag to select an area
3. Take a screenshot of the selected area
4. Extract text from the screenshot using OCR
5. Save both the image and text to the screenshots folder

### Taking a Full-Screen Screenshot

```python
from src.screenshot import take_full_screenshot

take_full_screenshot()
```

This will:
1. Take a screenshot of the entire screen
2. Extract text from the screenshot using OCR
3. Save both the image and text to the screenshots folder

## Output Files

The tool creates two files for each screenshot:
- `YYYY-MM-DD_HH-MM-SS.png`: The screenshot image
- `YYYY-MM-DD_HH-MM-SS.txt`: The extracted text from the image

Both files are saved in the `screenshots` folder, which is created automatically if it doesn't exist.

## Testing

You can run the included test script to verify that the tool is working correctly:

```
python src/test_screenshot.py
```

To run a manual test that takes a full screenshot and performs OCR, uncomment the `manual_test()` line at the end of the test script.

## Troubleshooting

If you encounter issues with OCR:

1. Make sure Tesseract is installed correctly
2. If using Windows, ensure the Tesseract executable is in your PATH or set the path explicitly:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```
3. Check that the image quality is good enough for OCR to work effectively
4. Try adjusting the image before OCR (e.g., converting to grayscale, increasing contrast)