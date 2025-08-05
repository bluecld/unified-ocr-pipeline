# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an Enhanced Unified OCR Pipeline System for processing PDF purchase orders with intelligent OCR, advanced field extraction, and FileMaker integration. The system automatically processes PDFs dropped into an incoming directory, extracts business-critical fields, and uploads results to FileMaker.

## Commands

### Setup and Deployment
```bash
# Initial setup (interactive)
chmod +x setup_unified_pipeline.sh
./setup_unified_pipeline.sh

# Build containers manually
docker build -f Dockerfile.unified -t ocr-unified:enhanced .

# Start production (cron-based) - recommended
docker-compose --profile cron up -d

# Start continuous monitoring
docker-compose --profile continuous up -d

# One-shot processing for testing
docker-compose --profile oneshot run --rm ocr_oneshot

# With AI enhancement (optional)
docker-compose --profile ai,cron up -d
```

### Management and Monitoring
```bash
# View logs
docker-compose logs -f

# Check service status
docker-compose ps

# Restart services
docker-compose restart

# Update and restart
docker-compose build && docker-compose up -d

# Monitor pipeline logs
tail -f logs/pipeline.log

# Monitor cron execution
tail -f logs/cron.log

# Check processing statistics
grep "Processing Summary" logs/pipeline.log | tail -10
```

### Testing and Debugging
```bash
# Manual pipeline run for debugging
python unified_ocr_pipeline.py

# Test OCR tools in container
docker-compose exec ocr_cron tesseract --version
docker-compose exec ocr_cron ocrmypdf --version

# Test FileMaker connectivity
docker-compose exec ocr_cron curl -k https://192.168.0.39/fmi/data/v1

# View extracted text for debugging
cat OCR_PROCESSED/PO_*/extracted_text.txt
```

## Architecture

### Core Components

1. **EnhancedPDFProcessor** (`unified_ocr_pipeline.py:107-248`)
   - Intelligent PDF splitting using text analysis (not page orientation)
   - Selective OCR: full PO processing, Router first page only
   - Router detection via text patterns (router, routing sheet, operation sequence, etc.)

2. **FieldExtractor** (`unified_ocr_pipeline.py:249-471`) 
   - Comprehensive business field extraction using regex patterns
   - Extracts 10+ fields including PO number, MJO, quantities, dates, quality clauses
   - Business logic validation (payment terms, PO format validation)

3. **FileMakerIntegration** (`unified_ocr_pipeline.py:472-608`)
   - FileMaker Data API integration for automatic database uploads
   - Container field uploads for PDF attachments
   - Authentication and session management

4. **QualityClauseReference** (`unified_ocr_pipeline.py:43-83`)
   - Database of quality clause codes (Q8, Q10, Q43, etc.) with descriptions
   - Automatic quality clause detection and description lookup

### Data Flow
```
PDF Input → Text Analysis → Smart Splitting → Targeted OCR → Field Extraction → FileMaker Upload
     ↓            ↓              ↓              ↓              ↓              ↓
  Multi-page → Router Detection → PO + Router → OCR Optimization → Business Logic → Database Record
```

### Directory Structure
- `OCR_INCOMING/` - Drop PDF files here for processing
- `OCR_PROCESSED/` - Results organized by PO number
  - `PO_4551234567/` - Successful processing folder
  - `ERROR_timestamp/` - Failed processing with error details
- `logs/` - Pipeline, cron, and error logs
- `temp/` - Temporary processing files (auto-cleanup)

### Configuration

The system uses environment variables configured in `.env`:

**FileMaker Integration:**
- `FM_ENABLED` - Enable/disable FileMaker uploads
- `FM_HOST`, `FM_DB`, `FM_LAYOUT` - FileMaker server details
- `FM_USERNAME`, `FM_PASSWORD` - Authentication credentials

**Processing Configuration:**
- `OCR_LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `OCR_TIMEOUT` - OCR processing timeout in seconds
- `DELETE_SOURCE_FILES` - Remove source files after processing

**Business Logic:**
- `PO_NUMBER_PATTERN` - Regex for valid PO numbers (default: 10 digits starting with 45)
- `STANDARD_PAYMENT_TERMS` - List of acceptable payment terms
- `ROUTER_MAX_PAGES` - Maximum pages to OCR from Router section

### Deployment Modes

1. **Cron-based (Production)**: Scheduled processing every 2-10 minutes based on business hours
2. **Continuous Monitoring**: Real-time file detection with higher resource usage  
3. **One-shot Processing**: Single execution for testing and debugging
4. **AI-Enhanced**: Optional Ollama integration for advanced field extraction

### Key Business Logic

- **PO Validation**: Must be 10 digits starting with "45" (e.g., 4551234567)
- **Payment Terms Flagging**: Non-standard payment terms (not Net 30) are flagged
- **Quality Clause Matching**: Automatic detection and description lookup for Q## codes
- **Planner Validation**: Matches against predefined planner list
- **Date Parsing**: Standardizes various date formats to MM/DD/YYYY

### Error Handling

- Failed processing creates timestamped ERROR folders with detailed logs
- Partial extraction results are saved even on failure
- Comprehensive logging at multiple levels (pipeline, cron, errors)
- Automatic cleanup of old logs and error folders
- Graceful degradation when FileMaker or AI services unavailable

### File Processing Rules

- Only processes PDF files from `OCR_INCOMING/`
- Source files are deleted after successful processing
- Results include OCR'd PDFs, extracted JSON data, and raw text
- Router section OCR limited to first page for performance
- Business hours have more frequent processing (2min vs 10min intervals)

## Development Notes

- Python 3.10-based with OCR tools (tesseract, ocrmypdf, poppler-utils)
- Uses PyMuPDF for PDF manipulation and text extraction
- FileMaker integration via REST API with container field support
- Docker-based deployment with multiple service profiles
- Cron-based scheduling for production efficiency
- Comprehensive logging and monitoring capabilities