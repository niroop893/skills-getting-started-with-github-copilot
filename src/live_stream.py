from flask import Flask, Response
import cv2
import pyautogui
import numpy as np

app = Flask(__name__)

def generate_frames():
    while True:
        screen = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5656)
