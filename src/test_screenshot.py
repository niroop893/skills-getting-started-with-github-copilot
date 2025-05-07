"""
Test script for the screenshot tool with OCR functionality.
This script demonstrates how to use the screenshot tool and tests its functionality.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
import io

# Add the parent directory to the path so we can import the screenshot module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.screenshot import take_full_screenshot

class TestScreenshotOCR(unittest.TestCase):
    """Test cases for the screenshot tool with OCR functionality."""
    
    @patch('src.screenshot.ImageGrab')
    @patch('src.screenshot.pytesseract')
    @patch('builtins.open', create=True)
    def test_take_full_screenshot_with_ocr(self, mock_open, mock_pytesseract, mock_imagegrab):
        """Test that take_full_screenshot captures a screenshot and performs OCR."""
        # Create a mock image
        mock_image = MagicMock(spec=Image.Image)
        mock_imagegrab.grab.return_value = mock_image
        
        # Mock the OCR result
        mock_pytesseract.image_to_string.return_value = "Test OCR Text"
        
        # Mock the file open operation
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Call the function
        take_full_screenshot()
        
        # Assert that ImageGrab.grab was called
        mock_imagegrab.grab.assert_called_once()
        
        # Assert that the image was saved
        mock_image.save.assert_called_once()
        
        # Assert that OCR was performed
        mock_pytesseract.image_to_string.assert_called_once_with(mock_image)
        
        # Assert that the text file was written
        mock_file.write.assert_called_once_with("Test OCR Text")

def manual_test():
    """Manual test function to demonstrate the screenshot tool."""
    print("Taking a full screenshot with OCR...")
    take_full_screenshot()
    print("Check the 'screenshots' folder for the image and text files.")

if __name__ == "__main__":
    # Run the unit tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    # Uncomment the line below to run a manual test
    # manual_test()