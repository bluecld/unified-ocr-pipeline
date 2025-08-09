#!/bin/bash

# Entrypoint script for ocr_ollama container

# Wait for Ollama to be available
for i in $(seq 1 30); do
  if curl -s http://localhost:11434/api/tags >/dev/null; then
    echo "Ollama is up!"
    break
  fi
  echo "Waiting for Ollama... ($i/30)"
  sleep 2
done

# Ensure the IncomingPW directory exists
if [ ! -d "/app/IncomingPW" ]; then
  echo "Error: /app/IncomingPW directory does not exist."
  exit 1
fi

# Check for PDF files in the IncomingPW directory
PDF_FILES=$(ls /app/IncomingPW/*.pdf 2>/dev/null)

if [ -z "$PDF_FILES" ]; then
  echo "No PDF files found in /app/IncomingPW."
  exit 0
fi

# Process each PDF file
for PDF in $PDF_FILES; do
  echo "Processing PDF: $PDF"
  python3 /app/scripts/unified_ocr_pipeline.py "$PDF"
  if [ $? -ne 0 ]; then
    echo "Error processing $PDF"
  else
    echo "Successfully processed $PDF"
  fi
done

# Exit successfully
exit 0
