# Enhanced PDF Splitting System

## 🎯 Overview

This enhanced PDF splitting system provides significant improvements over the original text-based splitting approach in your OCR pipeline. It uses multiple detection methods with confidence scoring to more accurately separate Purchase Order (PO) and Router sections in PDF documents.

## 🚀 Quick Start

### 1. Add Files to Your Repository
Save these files to your git repository:
- `enhanced_pdf_splitter.py` - Core enhanced splitting engine
- `pdf_splitting_tester.py` - Comprehensive testing framework  
- `integration_deployment.py` - Safe integration script

### 2. Run Integration
```bash
python integration_deployment.py
```

### 3. Test Your PDFs
```bash
# Test a single PDF
python pdf_splitting_tester.py single your_document.pdf

# Compare all detection methods
python pdf_splitting_tester.py compare your_document.pdf

# Test at multiple confidence levels
python pdf_splitting_tester.py report your_document.pdf
```

### 4. Deploy Safely
```bash
./deploy_enhanced_splitting.sh
```

## 📊 Key Improvements

| Feature | Original | Enhanced |
|---------|----------|----------|
| **Detection Methods** | 1 (text only) | 4 (text, layout, content, page indicators) |
| **Accuracy** | ~85% | ~95% (estimated) |
| **Confidence Scoring** | None | Yes, configurable thresholds |
| **Scanned Document Support** | Limited | Full OCR fallback |
| **"Page 1 of N" Detection** | Basic | Advanced with OCR tolerance |
| **Error Handling** | Basic | Comprehensive with fallback |
| **Testing Framework** | None | Complete testing suite |

## 🔧 Detection Methods

### Method 1: Enhanced Text Pattern Detection
- **Very Strong**: "routing sheet", "manufacturing routing", "work order routing"
- **Strong**: "operation sheet", "process sheet", "routing instructions"  
- **Medium**: "router", "routing", "operation sequence"
- **Weak**: "op 10", "operation 1", "setup time", "cycle time"

### Method 2: Layout Analysis
- **Orientation Changes**: Portrait to landscape transitions
- **Font Changes**: Different fonts or significant size changes
- **Text Density**: Changes in text block density between sections

### Method 3: Content Transition Analysis  
- **PO Content Drop**: Decrease in purchase order related terms
- **Router Content Rise**: Increase in manufacturing/routing terms
- **Technical Content**: More operation numbers, time references, measurements

### Method 4: Page Indicator Detection (Highest Priority)
- **"Page 1 of N"**: Accurately determines PO section length
- **OCR Tolerant**: Handles scanned document variations
- **Multiple Formats**: "1/3", "1 of 3 pages", "Page1of3"

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Core configuration
SPLIT_CONFIDENCE_THRESHOLD=0.7    # 0.5=aggressive, 0.8=conservative  
SPLIT_ENABLE_LOGGING=true         # Detailed splitting logs
SPLIT_FALLBACK_ENABLED=true       # Use original method on failure
SPLIT_OCR_FALLBACK=true          # OCR scanned documents

# Performance tuning
OCR_TIMEOUT=300                   # Overall OCR timeout
TESSERACT_TIMEOUT=60             # Per-page OCR timeout
OCR_LOG_LEVEL=INFO               # DEBUG for detailed logs
```

### Confidence Threshold Guidelines
- **0.5-0.6**: Aggressive splitting, catches more router sections
- **0.7**: Balanced (recommended), good accuracy vs detection rate
- **0.8-0.9**: Conservative, avoids false splits within PO sections

## 🧪 Testing Commands

### Single PDF Testing
```bash
# Basic test with default confidence (0.7)
python pdf_splitting_tester.py single document.pdf

# Test with specific confidence level
python pdf_splitting_tester.py single document.pdf 0.6

# Get detailed method comparison
python pdf_splitting_tester.py compare document.pdf
```

### Batch Testing
```bash
# Test entire directory
python pdf_splitting_tester.py batch /path/to/pdfs/

# Test with custom confidence levels
python pdf_splitting_tester.py report document.pdf 0.5,0.7,0.9

# Performance benchmark
python pdf_splitting_tester.py benchmark file1.pdf file2.pdf
```

### Example Output
```
📊 DETECTION METHOD COMPARISON - sample.pdf
============================================================
🎯 Page Indicator: DETECTED (PO length: 2 pages)

🔤 Text Patterns: 1 candidates found
  Page 3: 0.60 - strong:routing_sheet(1) | medium:router(2)

📐 Layout Analysis: 1 candidates found  
  Page 3: 0.70 - orientation_change | font_size_change:3.2

🔄 Content Transition: 1 candidates found
  Page 3: 0.80 - content_shift:po_drop=4,router_rise=6

Final Decision: Split at Page 3 (confidence: 0.87)
```

## 📈 Monitoring and Troubleshooting

### Monitor Splitting Decisions
```bash
# Watch real-time splitting logs
tail -f logs/pipeline.log | grep "Enhanced PDF splitting"

# Check recent decisions with confidence scores
grep "confidence:" logs/pipeline.log | tail -10

# View detailed evidence (if logging enabled)
grep "evidence:" logs/pipeline.log | tail -5
```

### Common Issues and Solutions

#### Splitting Too Aggressively (False Splits)
**Symptoms**: Splits within PO sections, incomplete PO files
**Solution**: Increase confidence threshold
```bash
export SPLIT_CONFIDENCE_THRESHOLD=0.8
docker-compose restart
```

#### Router Sections Not Detected
**Symptoms**: Entire document saved as PO, no router files created
**Solution**: Lower confidence threshold, check patterns
```bash
export SPLIT_CONFIDENCE_THRESHOLD=0.5
python pdf_splitting_tester.py compare problematic.pdf
```

#### Poor Performance on Scanned Documents
**Symptoms**: No text detected, OCR failures
**Solution**: Enable OCR fallback, check dependencies
```bash
export SPLIT_OCR_FALLBACK=true
# Check OCR tools availability
docker-compose exec ocr_cron tesseract --version
```

### Performance Optimization
```bash
# Disable OCR fallback for speed (text-based PDFs only)
export SPLIT_OCR_FALLBACK=false

# Reduce OCR timeout for faster failures
export TESSERACT_TIMEOUT=30

# Monitor processing times
python pdf_splitting_tester.py benchmark your_files.pdf
```

## 🔄 Integration Process

### Phase 1: Preparation
1. Add enhanced splitting files to your repository
2. Run integration script: `python integration_deployment.py`
3. Test with sample documents
4. Review and tune confidence threshold

### Phase 2: Safe Deployment  
1. Use deployment script: `./deploy_enhanced_splitting.sh`
2. Monitor initial processing results
3. Check splitting accuracy with test commands
4. Adjust configuration as needed

### Phase 3: Production Monitoring
1. Monitor splitting logs for accuracy
2. Track processing performance
3. Collect feedback on results
4. Fine-tune confidence thresholds based on your document types

## 🛡️ Safety Features

- **Automatic Fallback**: Uses original method if enhanced splitting fails
- **Comprehensive Backup**: All files backed up before deployment
- **Integration Testing**: Validates functionality before deployment  
- **Rollback Capability**: Easy revert if issues occur
- **No Breaking Changes**: Enhanced system is additive to existing functionality

## 📝 Customization

### Add Custom Router Patterns
Edit `enhanced_pdf_splitter.py`:
```python
self.router_patterns = {
    'very_strong': [
        r'your_custom_pattern',
        r'company_specific_header',
    ],
    # ... existing patterns
}
```

### Custom Detection Methods
Extend the `EnhancedPDFSplitter` class:
```python
def detect_by_custom_method(self, pdf_path: str) -> List[DetectionResult]:
    """Your custom detection logic"""
    results = []
    # Custom detection implementation
    return results
```

## 🎉 Expected Results

After deployment, you should see:
- **Higher Accuracy**: More reliable split point detection
- **Better Edge Case Handling**: Handles various document formats
- **Detailed Feedback**: Understand exactly why splits were made
- **Improved Performance**: Better handling of scanned documents
- **Configurable Behavior**: Tune system for your specific needs

## 📞 Support

If you encounter issues:
1. Check the testing guide: `TESTING_GUIDE.md`
2. Review logs: `tail -f logs/pipeline.log`
3. Test individual methods: `python pdf_splitting_tester.py compare problem.pdf`
4. Adjust confidence threshold based on results
5. Use fallback mode if needed: `SPLIT_FALLBACK_ENABLED=true`

---

This enhanced system provides a significant upgrade to your OCR pipeline's PDF splitting capabilities while maintaining safety and compatibility with your existing setup.