#!/bin/sh

# Build without cache and start services
docker-compose build --no-cache
echo "Starting Ollama service..."
docker-compose up -d ocr_ollama

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
sleep 10

# Check if Ollama is responding
for i in $(seq 1 30); do
  if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama is ready!"
    break
  fi
  echo "Waiting for Ollama... ($i/30)"
  sleep 2
done

# Start the OCR processing
echo "Starting OCR processing..."
docker-compose up ocr_oneshot