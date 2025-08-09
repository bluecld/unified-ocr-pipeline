#!/usr/bin/env python3
"""
Test script to verify AI optimization improvements
Tests the faster llama3.2:1b model with reduced timeout
"""

import time
import urllib.request
import urllib.parse
import json
import sys

def test_ai_speed():
    """Test AI response time with optimized configuration"""
    
    # Test configuration
    ollama_url = "http://localhost:11434"
    model = "llama3.2:1b"
    timeout = 120
    
    print("🔬 Testing AI Optimization")
    print(f"Model: {model}")
    print(f"Timeout: {timeout}s")
    print("-" * 50)
    
    # Test prompt (simplified for speed)
    test_prompt = """Extract key data from this text:
    Invoice #12345
    Date: 2024-01-15
    Amount: $150.00
    
    Return only: invoice_number, date, amount"""
    
    try:
        # Prepare request
        data = {
            "model": model,
            "prompt": test_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 200  # Limit response length
            }
        }
        
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=json_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print("⏱️  Starting AI inference test...")
        start_time = time.time()
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"✅ AI Response Time: {response_time:.2f} seconds")
        print(f"📝 AI Response: {result.get('response', 'No response')[:100]}...")
        
        # Evaluate performance
        if response_time < 30:
            print("🚀 EXCELLENT: Sub-30 second response!")
        elif response_time < 60:
            print("✅ GOOD: Under 1 minute response")
        elif response_time < 120:
            print("⚠️  ACCEPTABLE: Under 2 minutes")
        else:
            print("❌ SLOW: Exceeds 2 minute target")
            
        return response_time < 120
        
    except urllib.error.URLError as e:
        print(f"❌ Connection Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        return False

def test_ollama_connection():
    """Test basic Ollama connectivity"""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = [model['name'] for model in data.get('models', [])]
            print(f"📋 Available models: {models}")
            return "llama3.2:1b" in models
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 AI Optimization Test Suite")
    print("=" * 50)
    
    # Test 1: Connectivity
    print("\n1. Testing Ollama connectivity...")
    if not test_ollama_connection():
        print("❌ Ollama service not available")
        sys.exit(1)
    
    # Test 2: AI Speed
    print("\n2. Testing AI inference speed...")
    if test_ai_speed():
        print("\n🎉 OPTIMIZATION SUCCESS!")
        print("AI is working with faster response times")
    else:
        print("\n❌ OPTIMIZATION NEEDED")
        print("AI response still too slow or failing")
