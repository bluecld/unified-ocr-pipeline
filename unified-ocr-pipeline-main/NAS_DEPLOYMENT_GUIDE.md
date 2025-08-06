# NAS Deployment Guide - Improved PDF Splitting

## Quick Start (5 Minutes)

### 1. Prepare Files on Your Development Machine
```bash
# Run the integration patch to create improved version
python integration_patch.py

# This creates:
# - unified_ocr_pipeline_improved.py (patched version)
# - safe_deploy.sh (deployment script)
```

### 2. Copy Files to NAS
```bash
# Replace with your NAS details
scp improved_pdf_splitting.py username@192.168.0.39:/volume1/docker/ocr/
scp unified_ocr_pipeline_improved.py username@192.168.0.39:/volume1/docker/ocr/
scp safe_deploy.sh username@192.168.0.39:/volume1/docker/ocr/
scp test_splitting.py username@192.168.0.39:/volume1/docker/ocr/
```

### 3. Deploy on NAS
```bash
# SSH to your NAS
ssh username@192.168.0.39

# Navigate to OCR directory
cd /volume1/docker/ocr

# Run safe deployment (includes automatic rollback on failure)
chmod +x safe_deploy.sh
./safe_deploy.sh
```

## Step-by-Step Deployment

### Phase 1: Backup and Preparation

```bash
# On NAS - Create comprehensive backup
cd /volume1/docker/ocr
cp -r . ../ocr_backup_$(date +%Y%m%d_%H%M%S)

# Stop current services
docker-compose down
```

### Phase 2: Deploy Improved Code

```bash
# Copy the improved files (from your dev machine)
scp improved_pdf_splitting.py user@nas:/volume1/docker/ocr/
scp unified_ocr_pipeline_improved.py user@nas:/volume1/docker/ocr/  
scp safe_deploy.sh user@nas:/volume1/docker/ocr/
scp test_splitting.py user@nas:/volume1/docker/ocr/

# On NAS - Deploy safely
chmod +x safe_deploy.sh
./safe_deploy.sh
```

### Phase 3: Configuration

The deployment script automatically adds these to your `.env`:
```bash
# Enhanced PDF Splitting Configuration
SPLIT_CONFIDENCE_THRESHOLD=0.7    # Lower = more likely to split
SPLIT_LOG_EVIDENCE=true          # Show detailed splitting decisions  
SPLIT_FALLBACK_MODE=entire_po    # What to do when unsure
```

### Phase 4: Testing

```bash
# Test with existing PDFs in OCR_INCOMING
docker-compose --profile oneshot run --rm ocr_oneshot

# Or test specific PDF
python test_splitting.py single /path/to/test.pdf

# Compare detection methods
python test_splitting.py compare /path/to/test.pdf

# Test at different confidence levels
python test_splitting.py report /path/to/test.pdf
```

### Phase 5: Production Deployment

```bash
# Start production services
docker-compose --profile cron up -d

# Monitor logs
tail -f logs/pipeline.log | grep -E "(Enhanced PDF splitting|split.*confidence)"
```

## Testing Your PDFs

### Test Single PDF
```bash
# Test with default confidence (0.7)
python test_splitting.py single your_po.pdf

# Test with lower confidence (more likely to split)
python test_splitting.py single your_po.pdf 0.5

# Test with higher confidence (less likely to split)  
python test_splitting.py single your_po.pdf 0.9
```

### Compare Detection Methods
```bash
# See what each method detects
python test_splitting.py compare your_po.pdf
```

Example output:
```
📊 DETECTION METHOD COMPARISON - sample_po.pdf
============================================================
Text Patterns: 2 candidates found
  Page 3: 0.60 - strong:routing sheet | medium:router
  Page 5: 0.30 - weak:op 10 | weak:operation 1

Layout Analysis: 1 candidates found  
  Page 3: 0.70 - orientation_change | font_size_change

Content Transition: 1 candidates found
  Page 3: 0.80 - content_transition:po_drop=5,router_rise=8
```

### Batch Test Directory
```bash
# Test all PDFs in a directory
python test_splitting.py batch /path/to/pdf/directory
```

## Monitoring and Tuning

### Check Splitting Decisions
```bash
# Monitor splitting in real-time
tail -f logs/pipeline.log | grep "Enhanced PDF splitting"

# Check confidence levels
grep "confidence" logs/pipeline.log | tail -10

# See detailed evidence (if SPLIT_LOG_EVIDENCE=true)
grep "Detailed evidence" logs/pipeline.log | tail -5
```

### Tune Configuration

If splits are **too aggressive** (splitting within PO):
```bash
# Increase confidence threshold
echo "SPLIT_CONFIDENCE_THRESHOLD=0.8" >> .env
docker-compose restart
```

If router sections **aren't being detected**:
```bash
# Lower confidence threshold  
echo "SPLIT_CONFIDENCE_THRESHOLD=0.5" >> .env
docker-compose restart
```

If you want **more debugging info**:
```bash
# Enable detailed logging
echo "OCR_LOG_LEVEL=DEBUG" >> .env
echo "SPLIT_LOG_EVIDENCE=true" >> .env
docker-compose restart
```

## Rollback if Needed

### Automatic Rollback
The `safe_deploy.sh` script automatically rolls back if tests fail.

### Manual Rollback
```bash
# Stop services
docker-compose down

# Restore original file
mv unified_ocr_pipeline.py unified_ocr_pipeline.py.improved
mv unified_ocr_pipeline.py.original unified_ocr_pipeline.py

# Rebuild and restart
docker-compose build
docker-compose --profile cron up -d
```

## Performance Comparison

### Before (Original Method)
- Single text pattern matching
- Binary decision (split or don't split)
- No confidence scoring
- Limited error feedback

### After (Improved Method)
- Three detection methods with confidence scoring
- Configurable confidence thresholds
- Detailed splitting evidence in logs
- Graceful fallback to original method
- Comprehensive testing framework

## Troubleshooting

### Split Detection Issues
```bash
# Check what patterns are being found
python test_splitting.py compare problematic.pdf

# Test at multiple confidence levels
python test_splitting.py report problematic.pdf
```

### Import Errors
```bash
# Check if improved_pdf_splitting.py is in the right place
ls -la improved_pdf_splitting.py

# Test import
python -c "from improved_pdf_splitting import ImprovedPDFSplitter; print('Import OK')"
```

### Performance Issues
```bash
# Check processing times
grep "Processing Summary" logs/pipeline.log | tail -10

# Monitor resource usage
docker stats
```

## Success Indicators

✅ **Successful Deployment:**
- `safe_deploy.sh` completes without errors
- Test run processes PDFs successfully
- Logs show "Enhanced PDF splitting successful"
- No import errors in logs

✅ **Improved Splitting:**
- More accurate split points
- Detailed explanations in logs  
- Configurable confidence thresholds working
- Fallback to original method when needed

## Next Steps

1. **Monitor** splitting decisions for first few days
2. **Tune** confidence threshold based on your document types
3. **Add custom patterns** if needed for your specific PDFs
4. **Create document-specific profiles** for different PO formats

The improved system should significantly reduce splitting errors while providing detailed feedback on why splitting decisions were made.