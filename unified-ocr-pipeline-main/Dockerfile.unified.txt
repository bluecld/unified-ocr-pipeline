FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ocrmypdf \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    ghostscript \
    qpdf \
    curl \
    cron \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    PyMuPDF \
    ocrmypdf \
    requests \
    urllib3 \
    python-dateutil

WORKDIR /app
COPY . /app

ENV PYTHONUNBUFFERED=1

CMD ["python3", "unified_ocr_pipeline.py"]
