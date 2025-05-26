from flask import Flask, request, jsonify
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Global variables to cache the model and tokenizer
tokenizer = None
model = None
summarizer = None

MODEL_NAME = "t5-small"

def load_model():
    """Lazy load the model, tokenizer, and summarizer on first use"""
    global tokenizer, model, summarizer
    
    if tokenizer is None or model is None or summarizer is None:
        print("🔄 Loading model and tokenizer for the first time...")
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
        
        # Create summarizer pipeline
        summarizer = pipeline(
            "summarization",
            model=model,
            tokenizer=tokenizer,
            device=-1   # CPU; change to 0 if you have a GPU
        )
        
        print("✅ Model loaded successfully!")
    
    return tokenizer, model, summarizer

# ─── Chunking helper ────────────────────────────────────────────────────────
def chunk_text(text, max_tokens=800, overlap_tokens=50):
    """Split text into overlapping chunks based on tokens"""
    # Ensure tokenizer is loaded
    tok, _, _ = load_model()
    
    tokens = tok.tokenize(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk = tok.convert_tokens_to_string(tokens[start:end])
        chunks.append(chunk)
        start = end - overlap_tokens
    return chunks

@app.route("/")
def home():
    return "EchoBreak is running!"

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.json
        text = data.get("text", "")

        if not text:
            return jsonify({"error": "No text provided"}), 400

        # Load model on first request (lazy loading)
        tokenizer_instance, model_instance, summarizer_instance = load_model()

        # ─── Break into token-safe chunks ────────────────────────────────────────
        max_model_tokens = tokenizer_instance.model_max_length  # ~1024 for t5-small
        # Summarize in windows of 800 tokens to leave room for the summary itself
        chunks = chunk_text(text, max_tokens=800, overlap_tokens=50)

        # ─── Summarize each chunk ────────────────────────────────────────────────
        partial_summaries = []
        for i, chunk in enumerate(chunks):
            print(f"📝 Summarizing chunk {i+1}/{len(chunks)}...")
            
            out = summarizer_instance(
                chunk,
                max_length=130,
                min_length=30,
                do_sample=False,
                truncation=True
            )
            partial_summaries.append(out[0]["summary_text"])

        # ─── Combine partial summaries into the final summary ────────────────────
        final_summary = " ".join(partial_summaries)

        return jsonify({
            "summary": final_summary,
            "chunks_summarized": len(chunks)
        })
    
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "model_loaded": summarizer is not None})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    host = "0.0.0.0"
    print(f"🔌 Binding to {host}:{port}…")
    print("📋 Note: Model will be downloaded on first request to /analyze")
    app.run(host=host, port=port)