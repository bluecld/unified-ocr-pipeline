#!/bin/bash

# OCR Pipeline Test Script with AI Enhancement
# Tests both OCR functionality and Ollama AI integration

echo "🧪 Testing OCR Pipeline with AI Enhancement..."
echo "============================================="

# Test 1: Check if Docker service is built
echo "📦 1. Checking Docker service..."
if docker-compose images | grep -q ocr_oneshot; then
    echo "   ✅ Docker service image present (ocr_oneshot)"
else
    echo "   ❌ Service image not found; building..."
    docker-compose build ocr_oneshot || exit 1
fi

# Test 2: Check if Ollama is available (optional)
echo "🤖 2. Checking Ollama availability..."
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "   ✅ Ollama is running locally"
    OLLAMA_AVAILABLE=true
else
    echo "   📝 Ollama not available - will use regex fallback"
    OLLAMA_AVAILABLE=false
fi

# Test 3: Check required host folders
echo "📁 3. Checking host folder structure..."
HOST_INCOMING="/volume1/Main/Main/IncomingPW"
HOST_PROCESSED="/volume1/Main/Main/ProcessedPOs"
mkdir -p "$HOST_INCOMING" "$HOST_PROCESSED"
echo "   ✅ Folders ensured: $HOST_INCOMING, $HOST_PROCESSED"

echo "📄 4. Place a test PDF in $HOST_INCOMING and re-run if needed."

# Test 5: Run OCR Pipeline
echo "🔍 5. Running OCR Pipeline with AI enhancement..."
echo "   Processing: $TEST_PDF"

if $OLLAMA_AVAILABLE; then
    echo "   🤖 Using AI-enhanced extraction"
else
    echo "   📝 Using regex fallback extraction"
fi

// Run the pipeline (auto-processes PDFs in $HOST_INCOMING mounted at /app/IncomingPW)
docker-compose run --rm ocr_oneshot

echo "📊 6. Checking results..."
LATEST=$(find "$HOST_PROCESSED" -maxdepth 1 -type d -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
if [ -n "$LATEST" ]; then
    echo "   ✅ Latest processed folder: $(basename "$LATEST")"
    ls -la "$LATEST" | sed 's/^/      /'
else
    echo "   📝 No processed folders found yet in $HOST_PROCESSED"
fi

echo "\n🎉 Test Complete!\n==================="
echo "� Check $HOST_PROCESSED for results"
echo "📖 See OLLAMA_SETUP.md for AI enhancement setup"
