FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

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
RUN chmod +x scripts/unified_ocr_pipeline.py

EXPOSE 8000

CMD ["python", "scripts/unified_ocr_pipeline.py"]