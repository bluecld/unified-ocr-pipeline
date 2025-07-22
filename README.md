# Unified OCR Pipeline System

A complete, production-ready system for processing PDF purchase orders with OCR, field extraction, and FileMaker integration.

## 🎯 What This Does

1. **Monitors** incoming PDF files automatically
2. **OCR Processing** - Makes scanned PDFs searchable
3. **Smart Splitting** - Separates PO and Router documents  
4. **Field Extraction** - Pulls key data using AI + regex
5. **FileMaker Integration** - Uploads data and files automatically
6. **Organized Storage** - Files sorted by PO number

## 🚀 Quick Start

```bash
# 1. Extract files to your NAS
# 2. Make setup script executable
chmod +x setup_unified_pipeline.sh

# 3. Run the automated setup
./setup_unified_pipeline.sh

# 4. Start processing PDFs
cp your_purchase_order.pdf OCR_INCOMING/
```

## 📋 Field Extraction

The system extracts these fields automatically:

### Required Fields
- **PO Number** - Must start with "455" (10 digits)
- **MJO Number** - Production order number
- **Quantity Shipped** - Numeric quantity
- **Part Number** - Format: `12345*op06`

### Optional Fields  
- **Delivery Date** - MM/DD/YYYY format
- **DPAS Rating** - Defense priority rating
- **Payment Terms** - With non-Net30 flagging
- **Planner Name** - From predefined list
- **Quality Clauses** - Q## codes with descriptions

## 🏗️ Architecture

### Core Components
- **unified_ocr_pipeline.py** - Main processing engine
- **Docker containers** - Isolated, reproducible environment
- **Ollama AI** - Enhanced field extraction (optional)
- **FileMaker API** - Database integration
- **Cron scheduling** - Automated processing

### Data Flow
```
PDF Files → OCR → Splitting → Extraction → FileMaker → Archive
     ↓         ↓        ↓          ↓          ↓         ↓
Incoming → Searchable → PO+Router → JSON → Database → Folders
```

## 🎛️ Deployment Modes

### 1. Cron-Based (Recommended)
```bash
docker-compose --profile cron up -d
```
- **Business hours**: Every 2 minutes
- **Off hours**: Every 10 minutes  
- **Resource efficient**

### 2. Continuous Monitoring
```bash
docker-compose --profile continuous up -d
```
- **Real-time processing**
- **Higher resource usage**

### 3. One-Shot Processing
```bash
docker-compose --profile oneshot run --rm ocr_oneshot
```
- **Process current files and exit**
- **Good for testing**

### 4. With AI Enhancement
```bash
docker-compose --profile ai --profile cron up -d
```
- **Includes Ollama for better extraction**
- **Fallback to regex if AI unavailable**

## 📁 Directory Structure

```
project/
├── OCR_INCOMING/           # Drop PDF files here
├── OCRProcessed/           # Results appear here
│   ├── PO4551234567/      # Successful processing
│   │   ├── PO_4551234567.pdf
│   │   ├── Router_4551234567.pdf
│   │   ├── extracted_data.json
│   │   └── extracted_text.txt
│   └── ERROR_20240101_123456_filename/  # Failed processing
├── logs/                   # System logs
├── .env                    # FileMaker credentials
└── docker-compose.yml     # Service configuration
```

## ⚙️ Configuration

### Environment Variables
```bash
# Core settings
OCR_INCOMING=/app/incoming
OCR_PROCESSED=/app/processed  
OCR_LOG_LEVEL=INFO

# AI Enhancement
OLLAMA_HOST=http://ollama:11434

# FileMaker Integration
FM_ENABLED=true
FM_HOST=192.168.0.39
FM_DB=PreInventory
FM_LAYOUT=PreInventory
FM_USERNAME=your_username
FM_PASSWORD=your_password
```

### Cron Schedule (Customizable)
```cron
# Business hours: Every 2 minutes
*/2 7-18 * * 1-5 /app/run_pipeline.sh

# Off hours: Every 10 minutes  
*/10 0-6,19-23 * * 1-5 /app/run_pipeline.sh
*/10 * * * 0,6 /app/run_pipeline.sh
```

## 🔧 Management Commands

### Service Management
```bash
# View real-time logs
docker-compose logs -f

# Check service status
docker-compose ps

# Restart services
docker-compose restart

# Stop everything
docker-compose down

# Update and restart
docker-compose build && docker-compose up -d
```

### Monitoring
```bash
# Pipeline logs
tail -f logs/pipeline.log

# Cron logs (if using cron mode)
tail -f logs/cron.log

# Check Ollama models
docker exec ocr_ollama ollama list
```

## 🚨 Troubleshooting

### Common Issues

**No files being processed**
```bash
# Check if service is running
docker-compose ps

# Check logs for errors
docker-compose logs ocr_cron

# Verify file permissions
ls -la OCR_INCOMING/
```

**OCR failures**
```bash
# Check if tesseract is working
docker-compose exec ocr_pipeline tesseract --version

# Test OCR manually
docker-compose exec ocr_pipeline ocrmypdf --version
```

**FileMaker connection issues**
```bash
# Test network connectivity
docker-compose exec ocr_pipeline ping 192.168.0.39

# Check credentials in .env file
cat .env
```

## 🔄 Updates and Maintenance

### Regular Maintenance
```bash
# Update base images
docker-compose pull

# Clean up old containers
docker system prune

# Backup processed files
rsync -av OCRProcessed/ backup_location/
```

## 📞 Support

For issues or enhancements:
1. Check logs first: `docker-compose logs`
2. Verify configuration: `cat .env`
3. Test components individually
4. Upload project files to ChatGPT for assistance

---

**Bottom Line**: This is a production-ready system that handles the complete PDF processing workflow. Drop files in `OCR_INCOMING`, get organized results in `OCRProcessed`, with automatic database integration.