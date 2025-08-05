# Enhanced Unified OCR Pipeline System

A complete, production-ready system for processing PDF purchase orders with intelligent OCR, advanced field extraction, and FileMaker integration.

## 🎯 What This Enhanced System Does

1. **Smart PDF Analysis** - Text-based detection to split PO and Router sections
2. **Advanced OCR Processing** - Full PO OCR + first page Router OCR
3. **Comprehensive Field Extraction** - Extracts 10+ business-critical fields
4. **FileMaker Integration** - Automatic database uploads with file attachments
5. **Quality Assurance** - Quality clause matching and payment term validation
6. **Organized Storage** - Files sorted by PO number with complete audit trail

## 🚀 Quick Start

```bash
# 1. Download all files to your NAS Linux directory
# 2. Make setup script executable
chmod +x setup_unified_pipeline.sh

# 3. Run the automated setup (interactive)
./setup_unified_pipeline.sh

# 4. Start processing PDFs
cp your_purchase_order.pdf OCR_INCOMING/
```

## 📋 Enhanced Field Extraction

The system now extracts these fields automatically:

### Required Fields (PO Validation)
- **PO Number** - 10 digits starting with "45" (e.g., 4551234567)
- **MJO Number** - Manufacturing Job Order number
- **Quantity Shipped** - Numeric quantity with comma handling
- **Part Number** - Format: `12345*op06` (with operation number)

### Business Logic Fields
- **Promise Delivery Date** - MM/DD/YYYY format with parsing
- **Whittaker Shipper** - Purchase Order reference number
- **DPAS Rating** - Defense Priority Allocation System codes (A1, B2, etc.)
- **Payment Terms** - Automatic flagging if not standard Net 30
- **Planner Name** - Matched against predefined planner list

### Quality Assurance Fields
- **Quality Clauses** - Q## codes with full descriptions:
  - Q8: Material certification and test reports required
  - Q10: First article inspection required
  - Q43: AS9102 First Article Inspection Report required
  - Plus 8 additional quality clauses with descriptions

## 🏗️ Enhanced Architecture

### Intelligent PDF Processing
```
Input PDF → Text Analysis → Smart Splitting → Targeted OCR → Field Extraction
     ↓            ↓              ↓              ↓              ↓
  Multi-page → Router Detection → PO + Router → OCR Optimization → Business Logic
```

### Advanced Features
- **Text-based splitting** - No longer relies on page orientation
- **Selective OCR** - Full PO processing, Router first page only
- **Business rule validation** - Payment terms, PO format, quality clauses
- **Error handling** - Comprehensive logging and error folder creation
- **FileMaker API integration** - Direct database uploads with file containers

## 🎛️ Deployment Modes

### 1. Production Cron Mode (Recommended)
```bash
docker-compose --profile cron up -d
```
- **Intelligent scheduling**: 2-min intervals during business hours, 10-min off-hours
- **Resource efficient**: Only processes when files are present
- **Automatic cleanup**: Log rotation and error folder maintenance

### 2. Continuous Monitoring
```bash
docker-compose --profile continuous up -d
```
- **Real-time processing**: Immediate file detection
- **Higher resource usage**: Constant monitoring

### 3. One-shot Testing
```bash
docker-compose --profile oneshot run --rm ocr_oneshot
```
- **Single execution**: Process current files and exit
- **Perfect for testing**: Debug mode with detailed logging

### 4. AI-Enhanced Mode (Optional)
```bash
docker-compose --profile ai,cron up -d
```
- **Ollama integration**: AI-powered field extraction
- **Automatic fallback**: Uses regex if AI unavailable

## 📁 Enhanced Directory Structure

```
project/
├── OCR_INCOMING/                    # Drop PDF files here
├── OCRProcessed/                    # Results organized by PO
│   ├── PO_4551234567/              # Successful processing
│   │   ├── 4551234567_PO.pdf       # OCR'd Purchase Order
│   │   ├── 4551234567_ROUTER.pdf   # OCR'd Router (first page)
│   │   ├── extracted_data.json     # All extracted fields
│   │   └── extracted_text.txt      # Raw OCR text for debugging
│   └── ERROR_20240101_123456/      # Failed processing with timestamp
│       ├── original_filename.pdf   # Failed source file
│       ├── error_log.txt          # Specific error details
│       └── partial_results.json   # Any fields that were extracted
├── logs/                           # Comprehensive logging
│   ├── pipeline.log               # Main processing log
│   ├── cron.log                   # Scheduled execution log
│   └── cron_errors.log           # Error tracking
└── temp/                          # Temporary processing files (auto-cleanup)
```

## ⚙️ Enhanced Configuration

### Core Environment Variables (.env)
```bash
# FileMaker Integration
FM_ENABLED=true
FM_HOST=192.168.0.39
FM_DB=PreInventory
FM_LAYOUT=PreInventory
FM_USERNAME=Anthony
FM_PASSWORD=your_password

# Processing Configuration
OCR_LOG_LEVEL=INFO
OCR_TIMEOUT=300
TESSERACT_TIMEOUT=30
DELETE_SOURCE_FILES=true

# Business Logic
PO_NUMBER_PATTERN=45\d{8}
STANDARD_PAYMENT_TERMS=Net 30,NET 30,30 Days,NET30
ROUTER_MAX_PAGES=1

# Performance Tuning
MAX_CONCURRENT_FILES=2
OCR_MEMORY_LIMIT_MB=512
```

### Advanced Cron Configuration
```cron
# Business hours: Every 2 minutes (7 AM - 6 PM, Mon-Fri)
*/2 7-18 * * 1-5 /app/run_pipeline.sh

# Off hours: Every 10 minutes
*/10 0-6,19-23 * * 1-5 /app/run_pipeline.sh
*/10 * * * 0,6 /app/run_pipeline.sh

# Daily maintenance at 2 AM
0 2 * * * find /app/logs -name "*.log.*" -mtime +7 -delete

# Weekly cleanup on Sunday at 3 AM
0 3 * * 0 find /app/processed -name "ERROR_*" -mtime +30 -exec rm -rf {} \;
```

## 🔧 Management & Monitoring

### Service Management
```bash
# View real-time logs with color coding
docker-compose logs -f

# Check service health
docker-compose ps

# View processing statistics
tail -f logs/pipeline.log | grep "Processing Summary"

# Monitor FileMaker uploads
tail -f logs/pipeline.log | grep "FileMaker"

# Restart services
docker-compose restart

# Update and restart
docker-compose build && docker-compose up -d
```

### Advanced Monitoring
```bash
# Check OCR performance
grep "OCR completed" logs/pipeline.log | tail -10

# Monitor field extraction success rates
grep "Successfully extracted" logs/pipeline.log | tail -10

# View FileMaker integration status
grep "FileMaker" logs/pipeline.log | tail -10

# Check error patterns
tail -f logs/cron_errors.log

# Monitor disk usage
df -h OCRProcessed/
```

## 🚨 Enhanced Troubleshooting

### Common Issues & Solutions

**No files being processed**
```bash
# Check service status
docker-compose ps

# Verify file permissions
ls -la OCR_INCOMING/

# Check cron execution
tail -f logs/cron.log

# Manual test run
docker-compose --profile oneshot run --rm ocr_oneshot
```

**OCR failures**
```bash
# Test OCR tools
docker-compose exec ocr_cron tesseract --version
docker-compose exec ocr_cron ocrmypdf --version

# Check memory usage
docker stats

# Review OCR-specific errors
grep "OCR failed" logs/pipeline.log
```

**Field extraction issues**
```bash
# Check extraction patterns
grep "extract_" logs/pipeline.log | tail -20

# Review raw text output
cat OCRProcessed/PO_*/extracted_text.txt

# Test with sample data
echo "PO Number: 4551234567" | docker-compose exec -T ocr_cron python3 -c "
import re
text = input()
match = re.search(r'\b45\d{8}\b', text)
print('Found:', match.group(0) if match else 'None')
"
```

**FileMaker connection problems**
```bash
# Test network connectivity
docker-compose exec ocr_cron ping 192.168.0.39

# Test HTTPS connection
docker-compose exec ocr_cron curl -k https://192.168.0.39/fmi/data/v1

# Check credentials
cat .env | grep FM_

# Review FileMaker API errors
grep "FileMaker.*failed" logs/pipeline.log
```

### Performance Optimization

**Speed up processing**
```bash
# Reduce OCR timeout for faster failures
OCR_TIMEOUT=120

# Increase concurrent processing
MAX_CONCURRENT_FILES=4

# Use lower OCR quality for speed
OCR_OPTIMIZE_LEVEL=0
```

**Reduce resource usage**
```bash
# Limit memory usage
OCR_MEMORY_LIMIT_MB=256

# Reduce cron frequency during off-hours
*/15 0-6,19-23 * * 1-5 /app/run_pipeline.sh
```

## 🔄 Updates and Maintenance

### Regular Maintenance Tasks
```bash
# Weekly: Update base images
docker-compose pull

# Monthly: Clean up old containers
docker system prune -f

# Quarterly: Backup processed files
rsync -av OCRProcessed/ /backup/ocr_processed_$(date +%Y%m%d)/

# Check log sizes
du -sh logs/
```

### System Health Monitoring
```bash
# Daily health check script
#!/bin/bash
echo "=== Daily OCR Pipeline Health Check ==="
echo "Services running: $(docker-compose ps -q | wc -l)"
echo "Files processed today: $(find OCRProcessed -name "PO_*" -newermt "1 day ago" | wc -l)"
echo "Errors today: $(find OCRProcessed -name "ERROR_*" -newermt "1 day ago" | wc -l)"
echo "Disk usage: $(df -h . | tail -1 | awk '{print $5}')"
```

## 📞 Support & Customization

### Customizing Field Extraction
1. Edit the `PLANNERS` list in `enhanced_unified_ocr_pipeline.py`
2. Add new quality clauses to `QualityClauseReference.CLAUSES`
3. Modify regex patterns for your specific document formats
4. Update business logic in the `FieldExtractor` class

### Adding New Features
1. Extend the `FieldExtractor` class with new extraction methods
2. Update the `extracted_data` dictionary structure
3. Modify FileMaker field mappings if needed
4. Update the JSON output schema

---

**Production Ready**: This enhanced system handles real-world complexities including error recovery, performance optimization, comprehensive logging, and business rule validation. Drop files in `OCR_INCOMING`, get structured results in `OCRProcessed`, with automatic database integration and complete audit trails.