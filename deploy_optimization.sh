#!/bin/sh

echo "🚀 Starting Optimized OCR Pipeline with llama3.2:1b"
echo "=================================================="

# Navigate to project directory
cd /volume1/Main/Main/scripts/unified_ocr_pipeline

# Stop any existing services
echo "🛑 Stopping existing services..."
docker-compose down 2>/dev/null || true

# Build with optimized configuration  
echo "🔨 Building optimized containers..."
docker-compose build --no-cache

# Start AI service first
echo "🧠 Starting AI service (llama3.2:1b)..."
docker-compose up -d ocr_ollama

# Wait for AI service to be ready
echo "⏳ Waiting for AI service to initialize..."
sleep 15

# Check if Ollama is responding
echo "🔍 Testing AI service connectivity..."
for i in $(seq 1 20); do
  if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✅ AI service is ready!"
    break
  fi
  echo "   Waiting... ($i/20)"
  sleep 3
done

# Start OCR processing service
echo "📄 Starting OCR processing service..."
docker-compose up -d ocr_oneshot

# Final status check
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🎯 Next Steps:"
echo "1. Wait for llama3.2:1b model to download (if first run)"
echo "2. Test with: python3 test_ai_optimization.py"
echo "3. Monitor logs: docker-compose logs -f ocr_ollama"
echo ""
echo "✨ Optimization Complete - AI should now work under 2 minutes!"
