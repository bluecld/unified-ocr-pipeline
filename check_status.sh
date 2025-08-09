#!/bin/sh

echo "📊 OCR Pipeline Status Check"
echo "============================"

cd /volume1/Main/Main/scripts/unified_ocr_pipeline

echo "🐳 Docker Services:"
docker-compose ps

echo ""
echo "🧠 AI Model Status:"
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✅ Ollama AI service is running"
    echo "📋 Available models:"
    curl -s http://localhost:11434/api/tags | python3 -m json.tool 2>/dev/null || echo "   (Unable to parse model list)"
else
    echo "❌ Ollama AI service not responding"
fi

echo ""
echo "⚡ Quick AI Test:"
if command -v python3 >/dev/null 2>&1; then
    python3 test_ai_optimization.py 2>/dev/null || echo "   Run 'python3 test_ai_optimization.py' manually"
else
    echo "   Python3 not available for testing"
fi

echo ""
echo "📝 Recent Logs (last 10 lines):"
docker-compose logs --tail=10 ocr_ollama 2>/dev/null || echo "   No logs available"
