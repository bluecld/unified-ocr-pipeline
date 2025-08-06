#!/bin/bash

# Safe Deployment Script for Improved PDF Splitting
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

log "Starting safe deployment of improved PDF splitting..."

# Step 1: Stop current services
log "Stopping OCR services..."
docker-compose down

# Step 2: Backup current files
log "Creating backup..."
cp unified_ocr_pipeline.py unified_ocr_pipeline.py.backup.$(date +%Y%m%d_%H%M%S)

# Step 3: Deploy improved version
log "Deploying improved pipeline..."
if [ -f "unified_ocr_pipeline_improved.py" ]; then
    mv unified_ocr_pipeline.py unified_ocr_pipeline.py.original
    mv unified_ocr_pipeline_improved.py unified_ocr_pipeline.py
    log "✅ Pipeline updated with improved splitting"
else
    error "unified_ocr_pipeline_improved.py not found!"
    exit 1
fi

# Step 4: Update configuration
log "Updating configuration..."
if ! grep -q "SPLIT_CONFIDENCE_THRESHOLD" .env; then
    cat >> .env << 'EOL'

# Enhanced PDF Splitting Configuration  
SPLIT_CONFIDENCE_THRESHOLD=0.7
SPLIT_LOG_EVIDENCE=true
SPLIT_FALLBACK_MODE=entire_po
EOL
    log "✅ Configuration updated"
fi

# Step 5: Rebuild and test
log "Rebuilding containers..."
docker-compose build

log "Running test..."
docker-compose --profile oneshot run --rm ocr_oneshot

if [ $? -eq 0 ]; then
    log "✅ Test successful! Starting production services..."
    docker-compose --profile cron up -d
    log "🎉 Deployment complete!"
else
    error "Test failed! Rolling back..."
    mv unified_ocr_pipeline.py unified_ocr_pipeline.py.failed
    mv unified_ocr_pipeline.py.original unified_ocr_pipeline.py
    docker-compose build
    docker-compose --profile cron up -d
    error "❌ Rollback complete. Check logs for issues."
    exit 1
fi
