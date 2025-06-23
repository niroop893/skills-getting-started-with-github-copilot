import os
from datetime import datetime
import keyboard
import smtplib, ssl
from email.message import EmailMessage
import mss
from PIL import Image

# Email configuration - Confirmed working credentials
sender_email = "niroop893@gmail.com"
sender_password = "lwvloqnewxqtawlw"
receiver_email = "niroop893@gmail.com"

# Screenshot directory
folder = "screenshots"
os.makedirs(folder, exist_ok=True)

def send_email(img_filepath):
    subject = "Screenshot Captured"
    body = "Screenshot attached."

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.set_content(body)

    try:
        with open(img_filepath, "rb") as f:
            img_data = f.read()
            file_name = os.path.basename(img_filepath)
            msg.add_attachment(img_data, maintype="image", subtype="png", filename=file_name)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)

        print("Email sent successfully.")

    except Exception as e:
        print(f"Failed to send email: {e}")

# Updated function using mss (Desktop Duplication API)
def take_screenshot_and_email():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    img_path = os.path.join(folder, f"{timestamp}_screenshot.png")

    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Capture the first monitor
            sct_img = sct.grab(monitor)

            # Save image with PIL
            img = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
            img.save(img_path)
            print(f"Screenshot saved to {img_path}")

        send_email(img_path)

    except Exception as ex:
        print("Error capturing screenshot:", ex)

def main():
    print("Listening for Ctrl + Alt + S to screenshot & email (press ESC to quit).")

    keyboard.add_hotkey('ctrl+alt+s', take_screenshot_and_email)
    keyboard.wait('esc')

if __name__ == "__main__":
    main()