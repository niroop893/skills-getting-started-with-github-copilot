# Getting Started with GitHub Copilot

<img src="https://octodex.github.com/images/Professortocat_v2.png" align="right" height="200px" />

Hey **niroop893**!

Mona here. I'm done preparing your exercise. Hope you enjoy! 💚

Remember, it's self-paced so feel fee to take a break! ☕️

[![](https://img.shields.io/badge/Go%20to%20Exercise-%E2%86%92-1f883d?style=for-the-badge&logo=github&labelColor=197935)](https://github.com/niroop893/skills-getting-started-with-github-copilot/issues/1)

## Screenshot Tool with OCR

This repository includes a screenshot tool with OCR (Optical Character Recognition) functionality. The tool allows you to:

1. Take screenshots of selected areas or the full screen
2. Extract text from the screenshots using OCR
3. Save both the screenshot image and the extracted text in the screenshots folder

### Dependencies

To use the screenshot tool, you need to install the following dependencies:

```
pip install -r requirements.txt
```

Additionally, you need to install Tesseract OCR:

- **Windows**: Download and install from [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt install tesseract-ocr`

### Usage

To use the screenshot tool:

```python
from src.screenshot import take_screenshot, take_full_screenshot

# To take a screenshot of a selected area
take_screenshot()

# To take a screenshot of the entire screen
take_full_screenshot()
```

---

&copy; 2025 GitHub &bull; [Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/code_of_conduct.md) &bull; [MIT License](https://gh.io/mit)