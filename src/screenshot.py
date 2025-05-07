from PIL import ImageGrab
from datetime import datetime
import os
import tkinter as tk
from tkinter import messagebox
import ctypes

try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    print(f"OCR initialized with Tesseract at: {pytesseract.pytesseract.tesseract_cmd}")
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("pytesseract module not found. OCR functionality will be disabled.")
except Exception as e:
    OCR_AVAILABLE = False
    print(f"Error initializing pytesseract: {e}. OCR functionality will be disabled.")

def get_scaling_factor():
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    
    root = tk.Tk()
    tk_width = root.winfo_screenwidth()
    tk_height = root.winfo_screenheight()
    root.destroy()

    scale_x = screen_width / tk_width
    scale_y = screen_height / tk_height
    return scale_x, scale_y

class ScreenshotApp:
    def __init__(self, root):
        self.root = root
        self.scale_x, self.scale_y = get_scaling_factor()
        self.root.title("Screenshot Tool")
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3) 
        self.root.configure(cursor="cross")
        
        # Variables to store rectangle coordinates
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.current_rect = None
                
        # Create canvas
        self.canvas = tk.Canvas(root, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.root.bind("<ButtonPress-1>", self.on_button_press)
        self.root.bind("<B1-Motion>", self.on_mouse_drag)
        self.root.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<Escape>", self.cancel)
        
        instructions = "Click and drag to select area. Press ESC to cancel."
        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2, 20,
            text=instructions, fill="black",
            font=("Arial", 16, "bold")
        )

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=2
        )

    def on_mouse_drag(self, event):
        self.end_x = event.x
        self.end_y = event.y
        self.canvas.coords(self.current_rect, self.start_x, self.start_y, self.end_x, self.end_y)

    def on_button_release(self, event):
        self.end_x, self.end_y = event.x, event.y
        self.root.withdraw()
        self.root.after(200, self.take_screenshot)

    def take_screenshot(self):
        left = int(min(self.start_x, self.end_x) * self.scale_x)
        top = int(min(self.start_y, self.end_y) * self.scale_y)
        right = int(max(self.start_x, self.end_x) * self.scale_x)
        bottom = int(max(self.start_y, self.end_y) * self.scale_y)

        if right-left < 10 or bottom-top < 10:
            messagebox.showinfo("Selection too small", "Please select a larger area")
            self.root.destroy()
            return

        folder = "screenshots"
        os.makedirs(folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        img_path = os.path.join(folder, f"{timestamp}.png")

        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        screenshot.save(img_path)
        print(f"Screenshot saved at: {img_path}")
        
        if OCR_AVAILABLE:
            try:
                print("Attempting OCR...")
                text = pytesseract.image_to_string(screenshot)
                txt_path = os.path.join(folder, f"{timestamp}.txt")
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"OCR text saved at: {txt_path}")
            except Exception as e:
                print(f"OCR Error: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("OCR not available")
        self.root.destroy()

    def cancel(self, event):
        self.root.destroy()

def take_screenshot():
    root = tk.Tk()
    ScreenshotApp(root)
    root.mainloop()

if __name__ == "__main__":
    take_screenshot()