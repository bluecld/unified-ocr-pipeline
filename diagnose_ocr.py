#!/usr/bin/env python3
"""
OCR Pipeline Diagnostic and Cleanup Tool
"""

import os
import json
from pathlib import Path

def diagnose_processing_issues():
    """Diagnose and report OCR pipeline issues"""
    print("🔍 OCR Pipeline Diagnostic Report")
    print("=" * 50)
    
    output_dir = Path("/volume1/Main/Main/scripts/unified_ocr_pipeline/output/ProcessedPOs")
    
    if not output_dir.exists():
        print("❌ Output directory does not exist")
        return
    
    po_folders = [d for d in output_dir.iterdir() if d.is_dir()]
    print(f"📁 Found {len(po_folders)} PO folders")
    
    for po_folder in po_folders:
        po_number = po_folder.name
        print(f"\n📋 PO: {po_number}")
        
        # Check for required files
        po_pdf = po_folder / f"{po_number}_PO.pdf"
        router_pdf = po_folder / f"{po_number}_Router.pdf"
        json_file = po_folder / f"{po_number}_data.json"
        misc_dir = po_folder / "Misc"
        
        print(f"   PO PDF: {'✅' if po_pdf.exists() else '❌'}")
        print(f"   Router PDF: {'✅' if router_pdf.exists() else '❌'}")
        print(f"   JSON Data: {'✅' if json_file.exists() else '❌'}")
        print(f"   Misc Dir: {'✅' if misc_dir.exists() else '❌'}")
        
        # Analyze JSON data if exists
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                extracted_data = data.get('extracted_data', {})
                field_count = len(extracted_data)
                ocr_quality = extracted_data.get('OCR Quality', 'Unknown')
                
                print(f"   📊 Fields Extracted: {field_count}")
                print(f"   🎯 OCR Quality: {ocr_quality}")
                print(f"   📅 Processed: {data.get('processing_timestamp', 'Unknown')}")
                print(f"   📄 Source: {Path(data.get('source_file', 'Unknown')).name}")
                
                # Check data quality
                if field_count < 5:
                    print(f"   ⚠️  LOW FIELD COUNT (expected 6+)")
                
                # Show key fields
                key_fields = ['Vendor', 'Date', 'Amount', 'Part Number', 'Qty Ship']
                missing_fields = [f for f in key_fields if f not in extracted_data]
                if missing_fields:
                    print(f"   ❌ Missing: {', '.join(missing_fields)}")
                
            except Exception as e:
                print(f"   ❌ JSON Error: {e}")
        else:
            print(f"   ❌ INCOMPLETE PROCESSING")

def suggest_fixes():
    """Suggest fixes for common issues"""
    print("\n\n🛠️  SUGGESTED FIXES:")
    print("=" * 30)
    
    print("1. For missing JSON files:")
    print("   - Reprocess the source PDF")
    print("   - Check OCR service logs for errors")
    print("   - Ensure Ollama service is running")
    
    print("\n2. For poor field extraction:")
    print("   - Check OCR quality assessment")
    print("   - Review source PDF image quality")
    print("   - Consider manual text extraction")
    
    print("\n3. For PO number misreads:")
    print("   - Enhanced validation now active")
    print("   - Common digit confusions (5↔6, 3↔8) detected")
    print("   - Manual verification recommended")

if __name__ == "__main__":
    diagnose_processing_issues()
    suggest_fixes()
