# Ollama Setup for Enhanced FileMaker Data Extraction

## � **Memory Requirements**

Your NAS has **2.7GB available RAM**. Here are compatible AI models:

### ✅ **Models That Work (< 2.7GB RAM)**
| Model | RAM Needed | Speed | Accuracy | Status |
|-------|------------|-------|----------|---------|
| `gemma2:2b` | ~1.5GB | Fast | Good | **Recommended** |
| `qwen2:1.5b` | ~1.2GB | Very Fast | Good | Alternative |
| `phi3:mini` | ~2.3GB | Fast | Very Good | If available |

### ❌ **Models Too Large**
| Model | RAM Needed | Status |
|-------|------------|---------|
| `llama3.2:3b` | ~3.4GB | ❌ Too large |
| `llama3.1` | ~4.7GB | ❌ Too large |

## 🚀 **Quick Setup for Your NAS**

### 1. Install Compatible Model

```bash
# Option 1: Gemma 2B (Recommended)
curl -X POST http://localhost:11434/api/pull -d '{"name": "gemma2:2b"}'

# Option 2: Qwen 1.5B (Fastest)
curl -X POST http://localhost:11434/api/pull -d '{"name": "qwen2:1.5b"}'
```

### 2. Update Pipeline Configuration

```bash
# Update docker-compose.yml to use the smaller model
cd /volume1/Main/Main/scripts/unified_ocr_pipeline
# Edit OLLAMA_MODEL to: gemma2:2b or qwen2:1.5b
```

### 3. Test the Setup

```bash
# Test if model works
curl -s http://localhost:11434/api/generate -d '{
  "model": "gemma2:2b",
  "prompt": "Extract PO number from: Purchase order 4551239207",
  "stream": false
}'
```

## 🎯 **Current Status**

✅ **OCR Working Excellently** - PO extraction and page splitting perfect  
📝 **Using Regex Fallback** - Reliable FileMaker data extraction  
🤖 **AI Ready** - Just needs smaller model for your RAM

## � **Memory Solutions**

### Option A: Use Smaller Model (Immediate)
- Install `gemma2:2b` model
- Good accuracy, fits in your RAM
- **Recommended for production**

### Option B: Increase RAM (Future)
- Upgrade NAS to 8GB+ RAM
- Use larger models like `llama3.1`
- Better accuracy for complex documents

### Option C: External AI (Advanced)
- Use cloud AI service (OpenAI, Anthropic)
- Requires internet connection
- Higher cost but excellent accuracy

## � **Installation Commands**

```bash
# Install Gemma 2B (works with your RAM)
curl -X POST http://localhost:11434/api/pull -d '{"name": "gemma2:2b"}'

# Update pipeline
cd /volume1/Main/Main/scripts/unified_ocr_pipeline
# Change OLLAMA_MODEL=gemma2:2b in docker-compose.yml

# Rebuild and test
docker-compose build
docker-compose run --rm ocr_oneshot
```

## 📊 **Performance Expectations**

**With Gemma 2B:**
- ✅ Better vendor name extraction
- ✅ Improved part number detection
- ✅ Good quality clause parsing
- ✅ Context-aware data extraction
- ⚡ Fast processing (fits in your RAM)

**Current Regex Fallback:**
- ✅ Reliable and fast
- ✅ Works without additional RAM
- ✅ Already producing good results
- 📝 Less context-aware than AI

Your OCR pipeline is **already working excellently** - AI enhancement is just a bonus for even better FileMaker data accuracy!
