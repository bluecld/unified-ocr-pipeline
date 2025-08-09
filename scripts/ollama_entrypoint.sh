#!/bin/bash

echo "Starting Ollama service..."

# Set Ollama to listen on all interfaces for Docker networking
export OLLAMA_HOST=0.0.0.0:11434

# Start Ollama in the background
ollama serve &

# Wait for Ollama to be available
echo "Waiting for Ollama to start..."
for i in $(seq 1 60); do
  if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama is ready!"
    break
  fi
  echo "Waiting for Ollama... ($i/60)"
  sleep 3
done

# Check if Ollama started successfully
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "ERROR: Ollama failed to start after 3 minutes"
  exit 1
fi

# Pull the model if it doesn't exist
echo "Checking for model: ${OLLAMA_MODEL:-llama3.2:1b}"
if ! ollama list | grep -q "${OLLAMA_MODEL:-llama3.2:1b}"; then
  echo "Pulling model: ${OLLAMA_MODEL:-llama3.2:1b}"
  ollama pull "${OLLAMA_MODEL:-llama3.2:1b}"
fi

echo "Ollama service is ready and model is available"

# Keep the container running and maintain the AI service
while true; do
  sleep 30
  
  # Health check
  if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "ERROR: Ollama service stopped unexpectedly"
    exit 1
  fi
done
