# Unified OCR Pipeline

A robust OCR pipeline for PDF processing with automatic fallback mechanisms.

## 🚀 Quick Start

### Docker (Recommended)

```bash
# Build and run
docker-compose up --build

# Run one-off processing
docker-compose run ocr_oneshot python scripts/unified_ocr_pipeline.py input/document.pdf
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Fix PyMuPDF if needed
python scripts/unified_ocr_pipeline.py --fix-deps

# Process a PDF
python scripts/unified_ocr_pipeline.py document.pdf
```

## 🔧 Features

- **Automatic Backend Selection**: Falls back from PyMuPDF to pdfplumber
- **Robust Error Handling**: Handles import and processing errors gracefully  
- **Multiple Output Formats**: Individual pages + combined text
- **Health Monitoring**: Built-in health checks and logging
- **Docker Ready**: Optimized Dockerfile with proper dependency management

## 📁 Project Structure

```
unified-ocr-pipeline/
├── scripts/
│   └── unified_ocr_pipeline.py    # Main OCR pipeline
├── input/                         # Input PDFs
├── output/                        # Processed results
├── logs/                          # Application logs
├── Dockerfile                     # Container definition
├── docker-compose.yml            # Orchestration
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🐛 Troubleshooting

### PyMuPDF Import Error ("No module named 'frontend'")

This is a common issue with PyMuPDF installation. The pipeline includes automatic fixes:

```bash
# Automatic fix
python scripts/unified_ocr_pipeline.py --fix-deps

# Manual fix
pip uninstall PyMuPDF fitz
pip install --no-cache-dir PyMuPDF==1.23.8
```

### Docker Build Issues

```bash
# Force rebuild without cache
docker-compose build --no-cache

# Clean rebuild
docker-compose down
docker system prune -f
docker-compose up --build
```

## 📊 Usage Examples

### Basic Processing
```bash
python scripts/unified_ocr_pipeline.py document.pdf
```

### Multiple Files
```bash
python scripts/unified_ocr_pipeline.py file1.pdf file2.pdf file3.pdf
```

### Health Check
```bash
python scripts/unified_ocr_pipeline.py --health
```

### Web API (Optional)
```bash
# Start web interface
docker-compose up ocr_web

# Access at http://localhost:8080
curl -X POST -F "file=@document.pdf" http://localhost:8080/process
```

## 🔧 Configuration

The pipeline automatically detects and configures the best available backend:

1. **PyMuPDF** (Primary) - Fast, feature-rich
2. **pdfplumber** (Fallback) - Reliable text extraction

## 📝 Output

For each processed PDF, you'll get:

- `page_001.txt` - Individual page text files
- `document_combined.txt` - All text combined  
- `document_results.json` - Processing metadata
- `page_001_img_001.png` - Extracted images (if any)

## 🏥 Health Monitoring

```json
{
  "timestamp": "2025-01-01T12:00:00",
  "pdf_backend": "pymupdf",
  "status": "healthy",
  "dependencies": {
    "fitz": "available",
    "pdfplumber": "available",
    "pytesseract": "available"
  }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.