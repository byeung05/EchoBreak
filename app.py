from flask import Flask, request, jsonify
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# LED summarizer setup 
LED_MODEL   = "allenai/led-base-16384"
tokenizer   = AutoTokenizer.from_pretrained(LED_MODEL)
model       = AutoModelForSeq2SeqLM.from_pretrained(LED_MODEL)
summarizer  = pipeline(
    "summarization",
    model=model,
    tokenizer=tokenizer,
    device=-1   # CPU; change to 0 if you have a GPU
)


@app.route("/")
def home():
    return "EchoBreak is running!"

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    # --- 2) Hard token-length cutoff check ---
    enc_len = tokenizer(text, return_tensors="pt", truncation=False).input_ids.shape[-1]
    max_len = tokenizer.model_max_length
    if enc_len > max_len:
        return (
            jsonify({
                "error": f"Text too long: {enc_len} tokens (max {max_len})."
            }),
            413
        )

    # --- 3) Summarize (with trimming to LED’s window if needed) ---
    summary = summarizer(
        text,
        max_length=130,
        min_length=30,
        do_sample=False,
        truncation=True)[0]["summary_text"]

    return jsonify({"summary": summary})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    host = "0.0.0.0"
    print(f"🔌 Binding to {host}:{port}…")
    app.run(host=host, port=port)
