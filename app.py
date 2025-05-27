from flask import Flask, request, jsonify
from transformers import pipeline
from flask_cors import CORS
import os
import time

app = Flask(__name__)
CORS(app)

# Try very small models in order of size (all under 500MB)
SMALL_MODELS = [
    "sshleifer/distilbart-cnn-6-6",    # ~300MB - Smallest BART
    "google/pegasus-xsum",             # ~570MB - Good for news
    "facebook/bart-large-cnn",         # ~1.6GB - Last resort
]

summarizer = None
MODEL_NAME = None

print("🔄 Loading summarization model...")
for model_name in SMALL_MODELS:
    try:
        print(f"🔄 Trying model: {model_name}")
        start_time = time.time()
        
        summarizer = pipeline(
            "summarization",
            model=model_name,
            device=-1,  # CPU only
            framework="pt",
            model_kwargs={"torch_dtype": "auto"}  # Use smaller precision if available
        )
        
        load_time = time.time() - start_time
        MODEL_NAME = model_name
        print(f"✅ Loaded {model_name} in {load_time:.1f}s")
        break
        
    except Exception as e:
        print(f"❌ Failed to load {model_name}: {e}")
        continue

if not summarizer:
    print("❌ Could not load any model! Using fallback text extraction.")
    MODEL_NAME = "fallback"

def simple_extractive_summary(text, max_sentences=3):
    """Fallback summarization using sentence extraction"""
    import re
    
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
    
    if len(sentences) <= max_sentences:
        return '. '.join(sentences) + '.'
    
    # Score by length and position
    scored = [(len(s) * (1 + 1/((i+1)**0.5)), s) for i, s in enumerate(sentences)]
    scored.sort(reverse=True)
    
    top_sentences = [s[1] for s in scored[:max_sentences]]
    
    # Maintain original order
    result = []
    for sentence in sentences:
        if sentence in top_sentences:
            result.append(sentence)
            top_sentences.remove(sentence)
    
    return '. '.join(result) + '.'

def chunk_text(text, max_words=200):
    """Split text into smaller chunks"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), max_words):
        chunk = ' '.join(words[i:i + max_words])
        if len(chunk.strip()) > 50:  # Skip tiny chunks
            chunks.append(chunk)
    
    return chunks

@app.route("/")
def home():
    return jsonify({
        "status": "EchoBreak is running!",
        "model": MODEL_NAME,
        "endpoint": "/analyze"
    })

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided", "progress": "error"}), 400
            
        text = data.get("text", "")
        if not text:
            return jsonify({"error": "No text provided", "progress": "error"}), 400

        print(f"📄 Processing article: {len(text)} characters")
        
        # Limit text size for memory constraints
        if len(text) > 6000:
            text = text[:6000]
            print("✂️ Text truncated to 6000 characters")

        start_time = time.time()
        
        # Use fallback if no ML model available
        if MODEL_NAME == "fallback":
            print("🔄 Using extractive summarization...")
            summary = simple_extractive_summary(text, max_sentences=4)
            process_time = time.time() - start_time
            
            return jsonify({
                "summary": summary,
                "method": "extractive",
                "model": "fallback",
                "processing_time": f"{process_time:.1f}s",
                "progress": "complete",
                "original_length": len(text)
            })

        # ML-based summarization
        print(f"🧠 Using {MODEL_NAME} for summarization...")
        
        # For very long text, chunk it
        if len(text) > 3000:
            chunks = chunk_text(text, max_words=400)
            print(f"📊 Split into {len(chunks)} chunks")
            
            partial_summaries = []
            for i, chunk in enumerate(chunks):
                try:
                    print(f"🔄 Processing chunk {i+1}/{len(chunks)}")
                    
                    result = summarizer(
                        chunk,
                        max_length=60,
                        min_length=15,
                        do_sample=False,
                        truncation=True
                    )
                    partial_summaries.append(result[0]["summary_text"])
                    
                except Exception as e:
                    print(f"❌ Error in chunk {i}: {e}")
                    continue
            
            if partial_summaries:
                # Combine and re-summarize if needed
                combined = " ".join(partial_summaries)
                if len(combined) > 1000:
                    try:
                        final_result = summarizer(
                            combined,
                            max_length=120,
                            min_length=30,
                            do_sample=False,
                            truncation=True
                        )
                        summary = final_result[0]["summary_text"]
                    except:
                        summary = combined[:800] + "..."
                else:
                    summary = combined
            else:
                summary = "Could not generate summary from chunks."
                
        else:
            # Direct summarization for shorter text
            print("🔄 Direct summarization...")
            try:
                result = summarizer(
                    text,
                    max_length=100,
                    min_length=25,
                    do_sample=False,
                    truncation=True
                )
                summary = result[0]["summary_text"]
            except Exception as e:
                print(f"❌ Summarization failed: {e}")
                summary = simple_extractive_summary(text)

        process_time = time.time() - start_time
        print(f"✅ Summary complete in {process_time:.1f}s")
        
        return jsonify({
            "summary": summary,
            "model": MODEL_NAME,
            "processing_time": f"{process_time:.1f}s",
            "progress": "complete",
            "original_length": len(text),
            "summary_length": len(summary)
        })

    except Exception as e:
        print(f"❌ Server error: {e}")
        return jsonify({
            "error": f"Server error: {str(e)}", 
            "progress": "error"
        }), 500

# Health check endpoint
@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "model": MODEL_NAME,
        "timestamp": time.time()
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    host = "0.0.0.0"
    print(f"🚀 EchoBreak server starting on {host}:{port}")
    print(f"🤖 Using model: {MODEL_NAME}")
    app.run(host=host, port=port, debug=False)