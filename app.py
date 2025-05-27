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

# Initialize T5 model and tokenizer
MODEL_NAME = "t5-small"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
summarizer = pipeline(
    "summarization",
    model=MODEL_NAME,
    device=-1   # CPU; change to 0 if you have a GPU
)

def chunk_text(text, max_tokens=400, overlap_tokens=50):
    """Split text into chunks that fit within model limits"""
    try:
        # Simple word-based chunking since T5 tokenizer can be memory intensive
        words = text.split()
        chunks = []
        
        # Rough estimate: ~4 characters per token
        words_per_chunk = max_tokens * 3  # Conservative estimate
        
        start = 0
        while start < len(words):
            end = min(start + words_per_chunk, len(words))
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start = end - (overlap_tokens * 3)  # Overlap in words
            
        return chunks
    except Exception as e:
        print(f"Chunking error: {e}")
        return [text[:2000]]  # Fallback: just truncate

@app.route("/")
def home():
    return jsonify({"status": "EchoBreak is running!", "endpoint": "/analyze"})

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        text = data.get("text", "")
        if not text:
            return jsonify({"error": "No text provided"}), 400

        print(f"Received text length: {len(text)} characters")

        # Limit input size to prevent memory issues
        if len(text) > 10000:
            text = text[:10000]
            print("Text truncated to 10000 characters")

        # Break into manageable chunks
        chunks = chunk_text(text, max_tokens=400, overlap_tokens=50)
        print(f"Created {len(chunks)} chunks")

        # Summarize each chunk
        partial_summaries = []
        for i, chunk in enumerate(chunks):
            try:
                print(f"Processing chunk {i+1}/{len(chunks)}")
                
                # Skip very short chunks
                if len(chunk.strip()) < 50:
                    continue
                    
                result = summarizer(
                    chunk,
                    max_length=100,
                    min_length=20,
                    do_sample=False,
                    truncation=True
                )
                partial_summaries.append(result[0]["summary_text"])
                
            except Exception as e:
                print(f"Error processing chunk {i}: {e}")
                continue

        if not partial_summaries:
            return jsonify({"error": "Failed to generate summary"}), 500

        # Combine summaries
        final_summary = " ".join(partial_summaries)
        
        # If combined summary is too long, summarize it again
        if len(final_summary) > 1000:
            try:
                final_result = summarizer(
                    final_summary,
                    max_length=200,
                    min_length=50,
                    do_sample=False,
                    truncation=True
                )
                final_summary = final_result[0]["summary_text"]
            except Exception as e:
                print(f"Final summarization error: {e}")

        print(f"Generated summary length: {len(final_summary)}")
        
        return jsonify({
            "summary": final_summary,
            "chunks_processed": len(partial_summaries),
            "original_length": len(text)
        })

    except Exception as e:
        print(f"❌ Server error: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    host = "0.0.0.0"
    print(f"🔌 Starting EchoBreak server on {host}:{port}")
    print(f"📝 Model: {MODEL_NAME}")
    app.run(host=host, port=port, debug=False)