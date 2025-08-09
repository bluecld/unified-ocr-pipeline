#!/bin/bash

echo "Starting OCR processing service..."

# Wait for Ollama service to be available
echo "Waiting for Ollama service to be ready..."
for i in $(seq 1 60); do
  if curl -s http://ocr_ollama:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama service is ready!"
    break
  fi
  echo "Waiting for Ollama service... ($i/60)"
  sleep 5
done

# Check if Ollama service is available
if ! curl -s http://ocr_ollama:11434/api/tags >/dev/null 2>&1; then
  echo "ERROR: Could not connect to Ollama service after 5 minutes"
  exit 1
fi

# Run the OCR pipeline
echo "Starting OCR processing..."
python3 /app/scripts/unified_ocr_pipeline.py

echo "OCR processing completed"
