from flask import Flask, request, jsonify
from transformers import pipeline

app = Flask(__name__)

# Load summarization model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

@app.route("/")
def home():
    return "EchoBreak is running!"

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    summary = summarizer(text, max_length=130, min_length=30, do_sample=False)
    return jsonify({"summary": summary[0]['summary_text']})
