from flask import Flask, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)
genai.configure(api_key="AIzaSyB-buiM1EOFqBi10I8sisGw7b29PYsyRAY")
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat()

@app.route("/chat", methods=["POST"])
def chat_with_gemini():
    message = request.json.get("message")
    response = chat.send_message(message)
    return jsonify({"reply": response.text})

if __name__ == "__main__":
    app.run(port=5000)
