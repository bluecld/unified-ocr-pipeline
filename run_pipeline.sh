#!/bin/bash

# Unified OCR Pipeline Runner Script
# This script runs the pipeline with proper logging and error handling

set -e

# Set default environment variables if not set
export OCR_INCOMING=${OCR_INCOMING:-"/app/incoming"}
export OCR_PROCESSED=${OCR_PROCESSED:-"/app/processed"}
export OCR_LOG_LEVEL=${OCR_LOG_LEVEL:-"INFO"}
export OLLAMA_HOST=${OLLAMA_HOST:-"http://ollama:11434"}
export FM_ENABLED=${FM_ENABLED:-"true"}

# Create log entry
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting Unified OCR Pipeline"
echo "  - Incoming: $OCR_INCOMING"
echo "  - Processed: $OCR_PROCESSED"
echo "  - Log Level: $OCR_LOG_LEVEL"
echo "  - Ollama: $OLLAMA_HOST"
echo "  - FileMaker: $FM_ENABLED"

# Check if incoming directory exists and has files
if [ ! -d "$OCR_INCOMING" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Incoming directory does not exist: $OCR_INCOMING"
    exit 1
fi

# Count PDF files
PDF_COUNT=$(find "$OCR_INCOMING" -maxdepth 1 -name "*.pdf" -type f | wc -l)
echo "$(date '+%Y-%m-%d %H:%M:%S') - Found $PDF_COUNT PDF files to process"

# Only run if there are files to process (saves resources)
if [ "$PDF_COUNT" -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - No PDF files found, skipping processing"
    exit 0
fi

# Test Ollama connection if enabled
if [ "$OLLAMA_HOST" != "" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Testing Ollama connection..."
    if curl -s --connect-timeout 5 "$OLLAMA_HOST/api/tags" > /dev/null 2>&1; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Ollama connection successful"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: Ollama not available, will use regex extraction only"
    fi
fi

# Run the Python pipeline
echo "$(date '+%Y-%m-%d %H:%M:%S') - Executing pipeline..."

python /app/unified_ocr_pipeline.py

PIPELINE_EXIT_CODE=$?

if [ $PIPELINE_EXIT_CODE -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Pipeline completed successfully"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Pipeline failed with exit code $PIPELINE_EXIT_CODE"
fi

# Log final status
PROCESSED_COUNT=$(find "$OCR_PROCESSED" -maxdepth 1 -name "PO*" -type d | wc -l)
ERROR_COUNT=$(find "$OCR_PROCESSED" -maxdepth 1 -name "ERROR_*" -type d | wc -l)
REMAINING_COUNT=$(find "$OCR_INCOMING" -maxdepth 1 -name "*.pdf" -type f | wc -l)

echo "$(date '+%Y-%m-%d %H:%M:%S') - Summary:"
echo "  - Processed folders: $PROCESSED_COUNT"
echo "  - Error folders: $ERROR_COUNT" 
echo "  - Remaining files: $REMAINING_COUNT"

# Clean up old log files (keep last 7 days)
find /app/logs -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true

echo "$(date '+%Y-%m-%d %H:%M:%S') - Pipeline run complete"
echo "----------------------------------------"