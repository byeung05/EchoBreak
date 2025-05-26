# Use a slim Python base image
FROM python:3.10-slim

# Avoid interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# 1) Install Python dependencies (including transformers, flask, etc.)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# # 2) Pre-download the HF model into the image cache
# RUN python -c "from transformers import AutoTokenizer, AutoModelForSeq2SeqLM; model='t5-small'; AutoTokenizer.from_pretrained(model); AutoModelForSeq2SeqLM.from_pretrained(model)"

# 3) Copy the rest of your application code
COPY . .

# 4) Install Gunicorn for production serving
RUN pip install --no-cache-dir gunicorn

# 5) Tell Cloud Run which port to listen on
ENV PORT=8080
EXPOSE 8080

# 6) Launch the app with Gunicorn
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:8080", "app:app"]