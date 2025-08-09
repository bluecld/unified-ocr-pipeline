FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with specific versions
RUN pip install --no-cache-dir --upgrade pip && \
    pip uninstall -y PyMuPDF fitz && \
    pip install --no-cache-dir PyMuPDF==1.23.8 && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Create necessary directories
RUN mkdir -p /app/IncomingPW /app/ProcessedPOs

# Fix permissions
RUN chmod +x scripts/unified_ocr_pipeline.py && \
    chmod +x scripts/ollama_entrypoint.sh && \
    chmod +x scripts/ocr_entrypoint.sh

EXPOSE 11434

ENTRYPOINT ["bash", "scripts/ollama_entrypoint.sh"]