"""
Example script demonstrating how to use the screenshot tool with OCR functionality.
"""

import os
import sys
import time

# Add the parent directory to the path so we can import the screenshot module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.screenshot import take_screenshot, take_full_screenshot

def main():
    """
    Demonstrate the screenshot tool functionality.
    """
    print("Screenshot Tool with OCR Example")
    print("===============================")
    
    while True:
        print("\nOptions:")
        print("1. Take a screenshot of a selected area")
        print("2. Take a full-screen screenshot")
        print("3. View saved screenshots and OCR text")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            print("\nClick and drag to select an area for the screenshot.")
            print("Press ESC to cancel.")
            take_screenshot()
        
        elif choice == '2':
            print("\nTaking a full-screen screenshot...")
            take_full_screenshot()
            print("Done!")
        
        elif choice == '3':
            screenshots_dir = "screenshots"
            if not os.path.exists(screenshots_dir):
                print("\nNo screenshots found. Take a screenshot first.")
                continue
                
            files = os.listdir(screenshots_dir)
            image_files = [f for f in files if f.endswith('.png')]
            
            if not image_files:
                print("\nNo screenshots found. Take a screenshot first.")
                continue
                
            print("\nAvailable screenshots:")
            for i, img_file in enumerate(image_files, 1):
                print(f"{i}. {img_file}")
                
            try:
                file_idx = int(input("\nEnter the number of the screenshot to view OCR text (0 to cancel): "))
                if file_idx == 0:
                    continue
                    
                img_file = image_files[file_idx - 1]
                txt_file = img_file.replace('.png', '.txt')
                txt_path = os.path.join(screenshots_dir, txt_file)
                
                if os.path.exists(txt_path):
                    print(f"\nOCR Text from {txt_file}:")
                    print("-" * 40)
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        print(f.read())
                    print("-" * 40)
                else:
                    print(f"\nNo OCR text file found for {img_file}")
            except (ValueError, IndexError):
                print("\nInvalid selection.")
        
        elif choice == '4':
            print("\nExiting the example script. Goodbye!")
            break
        
        else:
            print("\nInvalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main()