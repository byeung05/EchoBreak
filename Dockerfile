FROM python:3.10-slim
ENV DEBIAN_FRONTEND=noninteractive

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1) Install Python deps first (including transformers)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Pre-download the HF model into the image cache
RUN python - <<EOF
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
model="sshleifer/distilbart-cnn-12-6"
AutoTokenizer.from_pretrained(model)
AutoModelForSeq2SeqLM.from_pretrained(model)
EOF

# 3) Copy your code last
COPY . .

# Cloud Run expects PORT=8080
ENV PORT=8080
EXPOSE 8080

# (Optional) Use gunicorn for faster startup and robust serving
RUN pip install --no-cache-dir gunicorn
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:8080", "app:app"]
