#!/bin/sh

# Quick AI Connection Test
echo "🧪 Testing AI Connection from Container..."

# Test 1: Check Ollama from host
echo "📡 1. Testing Ollama from host..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ✅ Ollama accessible from host"
    OLLAMA_HOST=true
else
    echo "   ❌ Ollama not accessible from host"
    OLLAMA_HOST=false
fi

# Test 2: Check container network access
echo "🐳 2. Testing from container with host network..."
if docker run --rm --network host curlimages/curl:latest curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ✅ Container can reach Ollama"
    CONTAINER_ACCESS=true
else
    echo "   ❌ Container cannot reach Ollama"
    CONTAINER_ACCESS=false
fi

# Test 3: Simple AI query
if [ "$CONTAINER_ACCESS" = "true" ]; then
    echo "🤖 3. Testing AI extraction..."
    RESPONSE=$(docker run --rm --network host curlimages/curl:latest curl -s http://localhost:11434/api/generate -d '{
        "model": "llama3.2:3b",
        "prompt": "Extract the PO number from this text: Purchase order 4551239207",
        "stream": false
    }' | head -1)
    
    if echo "$RESPONSE" | grep -q "4551239207"; then
        echo "   ✅ AI extraction working!"
    else
        echo "   📝 AI response: $RESPONSE"
    fi
fi

echo ""
echo "🎯 Summary:"
if [ "$OLLAMA_HOST" = "true" ] && [ "$CONTAINER_ACCESS" = "true" ]; then
    echo "✅ AI enhancement should work!"
else
    echo "📝 Will use regex fallback"
fi
