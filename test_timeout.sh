#!/bin/sh

echo "🧪 Testing AI Enhancement with Increased Timeout"
echo "================================================"

# Check current setup
echo "📊 Current Status:"
echo "   • RAM Available: $(free -h | grep Mem | awk '{print $7}')"
echo "   • Ollama Running: $(curl -s http://localhost:11434/api/tags > /dev/null && echo '✅ Yes' || echo '❌ No')"

# Test AI speed
echo ""
echo "⏱️  AI Response Time Test (5 min timeout):"
START=$(date +%s)
RESPONSE=$(timeout 300 curl -s http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Extract PO number from: Purchase order 4551230999",
  "stream": false
}' 2>/dev/null)
END=$(date +%s)
DURATION=$((END - START))

if echo "$RESPONSE" | grep -q "4551230999"; then
    echo "   ✅ AI working! Response time: ${DURATION}s"
elif [ $DURATION -ge 300 ]; then
    echo "   ⏰ AI timeout after 300s (5 min) - very slow NAS"
elif echo "$RESPONSE" | grep -q "response"; then
    echo "   🤖 AI responding in ${DURATION}s (check accuracy)"
else
    echo "   ❌ AI not responding properly"
fi

echo ""
echo "🎯 Recommendations:"
if [ $DURATION -lt 120 ]; then
    echo "   ✅ AI should work excellently with 5 min timeout"
elif [ $DURATION -lt 300 ]; then
    echo "   ⚠️  AI is slow but will work with 5 min patience"
else
    echo "   💡 Consider using regex fallback for production speed"
fi

echo ""
echo "📋 Next: Test full pipeline with patience..."
