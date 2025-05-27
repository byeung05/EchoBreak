# Use a slim Python base image
FROM python:3.10-slim

# Avoid interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the smallest model to avoid runtime delays and rate limits
RUN python -c "from transformers import pipeline; pipeline('summarization', model='sshleifer/distilbart-cnn-6-6', device=-1)"

# Install Gunicorn for production serving
RUN pip install --no-cache-dir gunicorn

# Copy the rest of your application code
COPY . .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Launch the app with Gunicorn (single worker to manage memory)
CMD ["gunicorn", "--workers", "1", "--threads", "2", "--bind", "0.0.0.0:8080", "--timeout", "120", "app:app"]