#!/bin/sh
cd /volume1/Main/Main/scripts/unified_ocr_pipeline
echo "Building container..."
docker-compose build ocr_ollama
echo "Restarting containers..."
docker-compose down
docker-compose up -d
echo "Done!"
