from flask import Flask, request, jsonify
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Current Render Process only has 512 MiB of memory. Switching approach 

# LED summarizer setup 
# LED_MODEL   = "allenai/led-base-16384"
# tokenizer   = AutoTokenizer.from_pretrained(LED_MODEL)
# model       = AutoModelForSeq2SeqLM.from_pretrained(LED_MODEL)
# summarizer  = pipeline(
#     "summarization",
#     model=model,
#     tokenizer=tokenizer,
#     device=-1   # CPU; change to 0 if you have a GPU
# )

# ─── 1) Load BART summarization pipeline ───────────────────────────────────────
MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
summarizer = pipeline(
    "summarization",
    model=MODEL_NAME,
    
    device=-1   # change to 0 if you have a GPU
)


# ─── 2) Chunking helper ────────────────────────────────────────────────────────
def chunk_text(text, max_tokens=800, overlap_tokens=50):
    """
    Splits `text` into chunks of ≤ max_tokens (with a small overlap to maintain context).
    Returns a list of strings.
    """
    tokens = summarizer.tokenizer.tokenize(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk = summarizer.tokenizer.convert_tokens_to_string(tokens[start:end])
        chunks.append(chunk)
        start = end - overlap_tokens
    return chunks

@app.route("/")
def home():
    return "EchoBreak is running!"

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    # ─── 3) Break into token-safe chunks ────────────────────────────────────────
    max_model_tokens = tokenizer.model_max_length  # ~1024
    # we'll summarize in windows of 800 tokens to leave room for the summary itself
    chunks = chunk_text(text, max_tokens=800, overlap_tokens=50)

    # ─── 4) Summarize each chunk ────────────────────────────────────────────────
    partial_summaries = []
    for chunk in chunks:
        out = summarizer(
            chunk,
            max_length=130,
            min_length=30,
            do_sample=False,
            truncation=True
        )
        partial_summaries.append(out[0]["summary_text"])

    # ─── 5) Combine partial summaries into the final summary ────────────────────
    # Option A: Just concatenate
    final_summary = " ".join(partial_summaries)

    return jsonify({
        "summary": final_summary,
        "chunks_summarized": len(chunks)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    host = "0.0.0.0"
    print(f"🔌 Binding to {host}:{port}…")
    app.run(host=host, port=port)
