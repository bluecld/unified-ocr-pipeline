#!/usr/bin/env python3
"""
Test script for Enhanced OCR capabilities
"""

import os
import sys
import tempfile
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, '/volume1/Main/Main/scripts/unified_ocr_pipeline/scripts')

from unified_ocr_pipeline import UnifiedOCRPipeline

def test_enhanced_ocr():
    """Test the enhanced OCR processing"""
    print("🧪 Testing Enhanced OCR Pipeline")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = UnifiedOCRPipeline()
    
    # Check health
    health = pipeline.health_check()
    print(f"🏥 Pipeline Status: {health['status']}")
    print(f"🔧 PDF Backend: {health['pdf_backend']}")
    print(f"📦 Dependencies: {health['dependencies']}")
    
    # Test with existing PO
    test_file = "/volume1/Main/Main/scripts/unified_ocr_pipeline/output/ProcessedPOs/4551230999/4551230999_PO.pdf"
    
    if Path(test_file).exists():
        print(f"\n🔍 Testing with: {test_file}")
        try:
            # Process with enhanced OCR
            results = pipeline.process_pdf(test_file, "/tmp/test_output")
            
            print(f"\n📊 Enhanced OCR Results:")
            print(f"📄 Total Pages: {results['total_pages']}")
            print(f"📝 Total Text Length: {results['total_text_length']}")
            print(f"⏱️  Processing Time: {results['processing_time_seconds']:.2f}s")
            
            # Show quality assessment for each page
            for page in results['pages']:
                page_num = page['page_number']
                quality = page.get('ocr_quality', 'N/A')
                confidence = page.get('ocr_confidence', 0)
                text_length = page.get('text_length', 0)
                
                print(f"\n📄 Page {page_num}:")
                print(f"   Quality: {quality}")
                print(f"   Confidence: {confidence:.1f}%")
                print(f"   Text Length: {text_length}")
                print(f"   Text Preview: {page.get('text', '')[:100]}...")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
    else:
        print(f"❌ Test file not found: {test_file}")
        print("📋 Available PO files:")
        po_dir = Path("/volume1/Main/Main/scripts/unified_ocr_pipeline/output/ProcessedPOs")
        if po_dir.exists():
            for po_folder in po_dir.iterdir():
                if po_folder.is_dir():
                    pdf_files = list(po_folder.glob("*_PO.pdf"))
                    if pdf_files:
                        print(f"   {pdf_files[0]}")

if __name__ == "__main__":
    test_enhanced_ocr()
