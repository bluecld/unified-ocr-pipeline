# PDF Splitting Improvements

## Current Issues with Text-Based Detection

The current approach in `unified_ocr_pipeline.py` has several limitations:

1. **Relies on raw PDF text** which may be missing or corrupted before OCR
2. **Limited pattern matching** - only 6 basic router indicators  
3. **No validation** of detected split points
4. **No fallback strategies** when text extraction fails
5. **Single-method approach** without confidence scoring

## Improved Multi-Layer Detection Strategy

The new `ImprovedPDFSplitter` class uses three complementary detection methods:

### Method 1: Enhanced Text Pattern Detection
- **Strong indicators**: "routing sheet", "manufacturing routing", "work order routing"
- **Medium indicators**: "router", "routing", "operation sequence"  
- **Weak indicators**: "op 10", "operation 1", "setup time", "cycle time"
- **Confidence scoring** based on pattern strength
- **PO content penalty** when PO patterns still present

### Method 2: Layout and Structure Analysis
- **Page orientation changes** (portrait to landscape)
- **Font size and type changes** between sections
- **Text density analysis** (router pages often have less dense text)
- **Margin and formatting changes**

### Method 3: Content Transition Analysis
- **Content scoring** for PO vs Router indicators per page
- **Transition detection** when PO content drops and router content rises
- **Numeric operation detection** (Op 10, Op 20, etc.)
- **Time reference analysis** (setup time, cycle time appear in router)

## Integration Steps

### 1. Replace Current Splitting Logic

In `unified_ocr_pipeline.py`, replace the `EnhancedPDFProcessor.split_po_router()` method:

```python
# Replace lines 152-193 with:
def split_po_router(self, input_pdf: str, po_pdf: str, router_pdf: str) -> bool:
    """Enhanced PDF splitting with multi-method detection"""
    from improved_pdf_splitting import ImprovedPDFSplitter
    
    splitter = ImprovedPDFSplitter()
    success, explanation = splitter.split_pdf_enhanced(
        input_pdf, po_pdf, router_pdf, 
        min_confidence=0.7  # Configurable threshold
    )
    
    if success:
        logger.info(f"PDF splitting successful: {explanation}")
    else:
        logger.error(f"PDF splitting failed: {explanation}")
    
    return success
```

### 2. Add Configuration Options

Add to `.env` file:
```bash
# PDF Splitting Configuration
SPLIT_CONFIDENCE_THRESHOLD=0.7    # Minimum confidence for splitting
SPLIT_FALLBACK_MODE=entire_po     # What to do when confidence is low
SPLIT_LOG_EVIDENCE=true          # Log detailed evidence for splitting decisions
```

### 3. Update Dependencies

Add to `Dockerfile.unified`:
```dockerfile
# No additional dependencies needed - uses existing PyMuPDF
```

### 4. Testing Commands

```bash
# Test the improved splitter standalone
python improved_pdf_splitting.py input.pdf output_po.pdf output_router.pdf

# Test with different confidence thresholds
SPLIT_CONFIDENCE_THRESHOLD=0.5 python unified_ocr_pipeline.py

# Enable detailed splitting logs
SPLIT_LOG_EVIDENCE=true OCR_LOG_LEVEL=DEBUG python unified_ocr_pipeline.py
```

## Expected Improvements

### Accuracy Improvements
- **Multi-method validation**: Split points must be detected by multiple methods
- **Confidence scoring**: Only split when confidence > threshold
- **Better pattern recognition**: More comprehensive router indicators
- **Layout awareness**: Detects structural changes between sections

### Robustness Improvements  
- **Graceful degradation**: Falls back to treating entire document as PO
- **Detailed logging**: Explains why splits were made or not made
- **Configurable thresholds**: Tune for your specific document types
- **Evidence tracking**: Shows what indicators were found

### Performance Improvements
- **Early termination**: Stops analysis when high confidence achieved
- **Caching**: Reuses text extraction across methods
- **Selective processing**: Focuses on most promising pages first

## Troubleshooting Split Issues

### If splits are too aggressive (splitting within PO):
```bash
# Increase confidence threshold
SPLIT_CONFIDENCE_THRESHOLD=0.8

# Check what evidence is being found
SPLIT_LOG_EVIDENCE=true OCR_LOG_LEVEL=DEBUG
```

### If router sections aren't being detected:
```bash
# Lower confidence threshold
SPLIT_CONFIDENCE_THRESHOLD=0.5

# Add custom router patterns for your documents
# Edit router_patterns in ImprovedPDFSplitter.__init__()
```

### If documents have unusual layouts:
```bash
# Check layout analysis results
grep "layout_analysis" logs/pipeline.log

# Adjust layout change thresholds in detect_by_layout_analysis()
```

## Migration Path

1. **Phase 1**: Deploy improved splitter alongside current method
2. **Phase 2**: Compare results and tune confidence thresholds  
3. **Phase 3**: Replace current method entirely
4. **Phase 4**: Add document-specific pattern customization

This approach provides much more reliable PO/Router splitting with detailed feedback on why splitting decisions were made.