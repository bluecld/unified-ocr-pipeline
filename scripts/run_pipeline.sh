#!/bin/bash

# Enhanced Unified OCR Pipeline Runner Script
# This script runs the pipeline with proper logging and error handling

set -e

# Set default environment variables if not set
export OCR_INCOMING=${OCR_INCOMING:-"/volume1/Main/Main/IncomingPW/"}
export OCR_PROCESSED=${OCR_PROCESSED:-"/volume1/Main/Main/ProcessedPOs/"}
export OCR_LOG_LEVEL=${OCR_LOG_LEVEL:-"INFO"}
export OLLAMA_HOST=${OLLAMA_HOST:-"http://ollama:11434"}
export FM_ENABLED=${FM_ENABLED:-"true"}

# Create log entry
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting Enhanced OCR Pipeline"
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

# Test FileMaker connection if enabled
if [ "$FM_ENABLED" = "true" ] && [ "$FM_HOST" != "" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Testing FileMaker connection..."
    if curl -s --connect-timeout 5 --insecure "https://$FM_HOST/fmi/data/v1" > /dev/null 2>&1; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - FileMaker connection successful"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: FileMaker not reachable, records will not be uploaded"
    fi
fi

# Run the Python pipeline
echo "$(date '+%Y-%m-%d %H:%M:%S') - Executing enhanced pipeline..."

python3 /volume1/Main/Main/scripts/unified_ocr_pipeline/scripts/unified_ocr_pipeline.py

PIPELINE_EXIT_CODE=$?

if [ $PIPELINE_EXIT_CODE -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Pipeline completed successfully"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Pipeline failed with exit code $PIPELINE_EXIT_CODE"
fi

# Log final status with enhanced metrics
PROCESSED_COUNT=$(find "$OCR_PROCESSED" -maxdepth 1 -name "PO_*" -type d | wc -l)
ERROR_COUNT=$(find "$OCR_PROCESSED" -maxdepth 1 -name "ERROR_*" -type d | wc -l)
REMAINING_COUNT=$(find "$OCR_INCOMING" -maxdepth 1 -name "*.pdf" -type f | wc -l)

echo "$(date '+%Y-%m-%d %H:%M:%S') - Processing Summary:"
echo "  - Successfully processed: $PROCESSED_COUNT folders"
echo "  - Error folders created: $ERROR_COUNT" 
echo "  - Files remaining: $REMAINING_COUNT"

# Check for recent successful processing
if [ $PROCESSED_COUNT -gt 0 ]; then
    LATEST_FOLDER=$(find "$OCR_PROCESSED" -maxdepth 1 -name "PO_*" -type d -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    if [ -n "$LATEST_FOLDER" ]; then
        echo "  - Latest processed: $(basename "$LATEST_FOLDER")"
    fi
fi

# Clean up old log files (keep last 7 days)
find /app/logs -name "*.log" -type f -mtime +7 -exec rm {} \; 2>/dev/null || true

# Clean up old error folders (keep last 30 days)
find "$OCR_PROCESSED" -maxdepth 1 -name "ERROR_*" -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true

echo "$(date '+%Y-%m-%d %H:%M:%S') - Enhanced pipeline run complete"
echo "========================================================"