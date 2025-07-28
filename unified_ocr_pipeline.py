#!/usr/bin/env python3
"""
Unified OCR Pipeline System
Combines splitting, processing, and FileMaker integration into a single cron-driven pipeline
"""

import os
import sys
import json
import logging
import shutil
import subprocess
import re
import fitz  # PyMuPDF
import requests
from datetime import datetime
from pathlib import Path
import time
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for FileMaker
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Configuration
INCOMING = os.getenv('OCR_INCOMING', '/mnt/incoming')
PROCESSED = os.getenv('OCR_PROCESSED', '/mnt/processed')
OCR_LOG_LEVEL = os.getenv('OCR_LOG_LEVEL', 'INFO')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://ollama:11434')

# FileMaker Configuration
FM_HOST = os.getenv('FM_HOST', '192.168.0.39')
FM_DB = os.getenv('FM_DB', 'PreInventory')
FM_LAYOUT = os.getenv('FM_LAYOUT', 'PreInventory')
FM_USERNAME = os.getenv('FM_USERNAME', 'Anthony')
FM_PASSWORD = os.getenv('FM_PASSWORD', 'rynrin12')
FM_ENABLED = os.getenv('FM_ENABLED', 'true').lower() == 'true'

# Planner names for extraction
PLANNER_NAMES = [
    "Steven Huynh", "Lisa Munoz", "Frank Davis", "William Estrada", "Glenn Castellon",
    "Sean Klesert", "Michael Reyes", "Nataly Hernandez", "Robert Lopez", "Daniel Rodriguez",
    "Diana Betancourt", "Diane Crone", "Amy Schlock", "Cesar Sarabia", "Anthony Frederick"
]

# Quality clause descriptions
QUALITY_CLAUSES = {
    "Q8": "Certificate of Compliance required",
    "Q10": "First Article Inspection required", 
    "Q19": "Source Control Drawing required",
    "Q29": "Traceability required",
    "Q30": "Statistical Process Control required",
    "Q43": "AS9102 First Article Inspection required"
}

# Configure logging
logging.basicConfig(
    level=getattr(logging, OCR_LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"{PROCESSED}/pipeline.log") if os.path.exists(PROCESSED) else logging.NullHandler()
    ]
)
logger = logging.getLogger('OCRPipeline')

class UnifiedOCRProcessor:
    def __init__(self):
        self.incoming_dir = Path(INCOMING)
        self.processed_dir = Path(PROCESSED)
        
        # Create directories
        self.incoming_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("=== Unified OCR Pipeline Starting ===")
        logger.info(f"Incoming: {self.incoming_dir}")
        logger.info(f"Processed: {self.processed_dir}")
        logger.info(f"FileMaker: {'Enabled' if FM_ENABLED else 'Disabled'}")

    def is_pdf_searchable(self, pdf_path):
        """Check if PDF contains searchable text"""
        try:
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    if page.get_text().strip():
                        return True
            return False
        except Exception as e:
            logger.error(f"Error checking PDF searchability: {e}")
            return False

    def run_ocr(self, input_pdf, output_pdf):
        """Run OCR using ocrmypdf"""
        try:
            if self.is_pdf_searchable(input_pdf):
                logger.info(f"PDF already searchable, copying: {input_pdf.name}")
                shutil.copy2(input_pdf, output_pdf)
                return True
            
            logger.info(f"Running OCR on: {input_pdf.name}")
            cmd = [
                'ocrmypdf',
                '--rotate-pages',
                '--deskew', 
                '--clean',
                '--force-ocr',
                '--output-type', 'pdf', '--fast-web-view', '100', '--optimize', '1',
                str(input_pdf),
                str(output_pdf)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            
            if result.returncode == 0:
                logger.info(f"OCR completed successfully: {input_pdf.name}")
                return True
            else:
                logger.error(f"OCR failed for {input_pdf.name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"OCR timeout for {input_pdf.name}")
            return False
        except Exception as e:
            logger.error(f"OCR error for {input_pdf.name}: {e}")
            return False

    def split_po_and_router(self, input_pdf, po_pdf, router_pdf):
        """Split PDF into PO and Router sections"""
        try:
            doc = fitz.open(input_pdf)
            po_doc = fitz.open()
            router_doc = fitz.open()
            
            po_done = False
            
            for i, page in enumerate(doc):
                text = page.get_text().lower()
                
                # Look for purchase order pages
                if not po_done and "purchase order" in text and re.search(r"page\s+\d+", text):
                    po_doc.insert_pdf(doc, from_page=i, to_page=i)
                    logger.debug(f"Added page {i+1} to PO section")
                else:
                    po_done = True
                    router_doc.insert_pdf(doc, from_page=i, to_page=i)
                    logger.debug(f"Added page {i+1} to Router section")
            
            # Save split documents
            if po_doc.page_count > 0:
                po_doc.save(po_pdf)
                logger.info(f"Created PO document with {po_doc.page_count} pages")
            else:
                logger.warning("No PO pages found")
                
            if router_doc.page_count > 0:
                router_doc.save(router_pdf)
                logger.info(f"Created Router document with {router_doc.page_count} pages")
            else:
                logger.warning("No Router pages found")
            
            # Cleanup
            doc.close()
            po_doc.close()
            router_doc.close()
            
            return po_doc.page_count > 0, router_doc.page_count > 0
            
        except Exception as e:
            logger.error(f"Error splitting PDF: {e}")
            return False, False

    def extract_text_from_pdf(self, pdf_path):
        """Extract all text from PDF"""
        try:
            text = ""
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    text += page.get_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""

    def extract_fields_with_ollama(self, text):
        """Use Ollama for enhanced field extraction"""
        if not OLLAMA_HOST:
            return {}
            
        prompt = f"""Extract fields from this purchase order text. Return ONLY valid JSON:
{{
    "po_number": "string starting with 455 or null",
    "mjo_number": "production order number or null", 
    "quantity_shipped": "number or null",
    "part_number": "string containing *op## pattern or null",
    "delivery_date": "date in MM/DD/YYYY format or null",
    "dpas_rating": "string or null",
    "payment_terms": "string or null",
    "planner_name": "planner name if found or null",
    "quality_clauses": ["array of Q## codes"]
}}

Text: {text[:3000]}"""

        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": "llama2",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return json.loads(result.get('response', '{}'))
            else:
                logger.warning(f"Ollama API error: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.warning(f"Ollama extraction failed: {e}")
            return {}

    def extract_fields_regex(self, text):
        """Fallback regex-based field extraction"""
        fields = {
            "po_number": None,
            "mjo_number": None,
            "quantity_shipped": None,
            "part_number": None,
            "delivery_date": None,
            "dpas_rating": None,
            "payment_terms": None,
            "planner_name": None,
            "quality_clauses": []
        }
        
        # PO Number (must start with 455)
        po_match = re.search(r'Purchase\s+order\s*(\d+)', text, re.IGNORECASE)
        if po_match and po_match.group(1).startswith('455'):
            fields['po_number'] = po_match.group(1)
        
        # MJO/Production Order Number
        mjo_match = re.search(r'Production\s+Order[:\s]+(\d+)', text, re.IGNORECASE)
        if mjo_match:
            fields['mjo_number'] = mjo_match.group(1)
        
        # Quantity Shipped
        qty_match = re.search(r'\b(\d{1,4}\.\d{2})\s+(EA|UM)\b', text)
        if qty_match:
            fields['quantity_shipped'] = int(float(qty_match.group(1)))
        
        # Part Number with operation
        for line in text.splitlines():
            part_match = re.search(r'\b(\d{4,10})\b', line)
            op_match = re.search(r'\*?op(\d{2})', line, re.IGNORECASE)
            if part_match and op_match:
                fields['part_number'] = f"{part_match.group(1)}*op{op_match.group(1)}"
                break
        
        # Delivery Date
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
        if date_match:
            fields['delivery_date'] = date_match.group(1)
        
        # DPAS Rating
        dpas_match = re.search(r'DPAS[:\s]+([A-Z]\d+)', text, re.IGNORECASE)
        if dpas_match:
            fields['dpas_rating'] = dpas_match.group(1)
        
        # Payment Terms
        payment_match = re.search(r'(?:payment\s+terms?|terms)[:\s]+([^,\n]+)', text, re.IGNORECASE)
        if payment_match:
            fields['payment_terms'] = payment_match.group(1).strip()
        
        # Planner Name
        for planner in PLANNER_NAMES:
            if planner.lower() in text.lower():
                fields['planner_name'] = planner
                break
        
        # Quality Clauses
        quality_matches = re.findall(r'Q\d{2}', text)
        fields['quality_clauses'] = list(set(quality_matches))
        
        return fields

    def send_to_filemaker(self, fields, po_pdf, router_pdf):
        """Upload data and files to FileMaker"""
        if not FM_ENABLED:
            logger.info("FileMaker integration disabled")
            return True
            
        try:
            base_url = f"https://{FM_HOST}/fmi/data/vLatest/databases/{FM_DB}"
            
            # Login
            session = requests.Session()
            auth_response = session.post(
                f"{base_url}/sessions", 
                auth=(FM_USERNAME, FM_PASSWORD), 
                json={}, 
                verify=False
            )
            auth_response.raise_for_status()
            
            token = auth_response.json()['response']['token']
            headers = {"Authorization": f"Bearer {token}"}
            
            # Create record
            logger.info("Creating FileMaker record...")
            record_response = session.post(
                f"{base_url}/layouts/{FM_LAYOUT}/records",
                headers=headers,
                json={"fieldData": fields},
                verify=False
            )
            record_response.raise_for_status()
            
            record_id = record_response.json()['response']['recordId']
            logger.info(f"Created record {record_id}")
            
            # Upload PO PDF
            if po_pdf and os.path.exists(po_pdf):
                with open(po_pdf, 'rb') as f:
                    upload_response = session.post(
                        f"{base_url}/layouts/{FM_LAYOUT}/records/{record_id}/containers/IncomingPO/1",
                        headers=headers,
                        files={"upload": f},
                        verify=False
                    )
                    upload_response.raise_for_status()
                    logger.info("Uploaded PO PDF")
            
            # Upload Router PDF
            if router_pdf and os.path.exists(router_pdf):
                with open(router_pdf, 'rb') as f:
                    upload_response = session.post(
                        f"{base_url}/layouts/{FM_LAYOUT}/records/{record_id}/containers/IncomingRouter/1",
                        headers=headers,
                        files={"upload": f},
                        verify=False
                    )
                    upload_response.raise_for_status()
                    logger.info("Uploaded Router PDF")
            
            # Logout
            session.delete(f"{base_url}/sessions/{token}", headers=headers, verify=False)
            
            return True
            
        except Exception as e:
            logger.error(f"FileMaker upload failed: {e}")
            return False

    def process_file(self, pdf_file):
        """Process a single PDF file through the complete pipeline"""
        logger.info(f"🔍 Processing: {pdf_file.name}")
        
        # Create temporary file paths
        ocr_pdf = self.incoming_dir / f"temp_ocr_{pdf_file.name}"
        po_pdf = self.incoming_dir / f"temp_po_{pdf_file.name}"
        router_pdf = self.incoming_dir / f"temp_router_{pdf_file.name}"
        
        try:
            # Step 1: OCR
            if not self.run_ocr(pdf_file, ocr_pdf):
                raise Exception("OCR failed")
            
            # Step 2: Split into PO and Router
            has_po, has_router = self.split_po_and_router(ocr_pdf, po_pdf, router_pdf)
            
            if not has_po:
                raise Exception("No PO pages found")
            
            # Step 3: Extract text and fields
            text = self.extract_text_from_pdf(po_pdf)
            
            # Try Ollama first, fallback to regex
            fields = self.extract_fields_with_ollama(text)
            if not fields or not fields.get('po_number'):
                logger.info("Using regex extraction as fallback")
                fields = self.extract_fields_regex(text)
            
            # Add metadata
            fields.update({
                "source_file": pdf_file.name,
                "processed_date": datetime.now().isoformat(),
                "has_router": has_router,
                "quality_descriptions": [QUALITY_CLAUSES.get(q, q) for q in fields.get('quality_clauses', [])],
                "payment_terms_flag": fields.get('payment_terms', '').lower() not in ['net 30', '30 days', 'net30']
            })
            
            # Determine output directory
            po_number = fields.get('po_number')
            if po_number and po_number.startswith('455'):
                output_dir = self.processed_dir / f"PO{po_number}"
                success = True
            else:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_dir = self.processed_dir / f"ERROR_{timestamp}_{pdf_file.stem}"
                logger.warning(f"Invalid/missing PO number: {po_number}")
                success = False
            
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 4: Save files
            final_po_path = output_dir / f"PO_{po_number or 'UNKNOWN'}.pdf"
            final_router_path = output_dir / f"Router_{po_number or 'UNKNOWN'}.pdf" if has_router else None
            
            shutil.move(str(po_pdf), str(final_po_path))
            if has_router and router_pdf.exists():
                shutil.move(str(router_pdf), str(final_router_path))
            
            # Save extracted data
            json_path = output_dir / "extracted_data.json"
            with open(json_path, 'w') as f:
                json.dump(fields, f, indent=2)
            
            # Save extracted text
            text_path = output_dir / "extracted_text.txt"
            with open(text_path, 'w') as f:
                f.write(text)
            
            # Step 5: FileMaker integration
            if success:
                fm_success = self.send_to_filemaker(fields, final_po_path, final_router_path)
                fields['filemaker_uploaded'] = fm_success
                
                # Update JSON with FileMaker status
                with open(json_path, 'w') as f:
                    json.dump(fields, f, indent=2)
            
            # Step 6: Archive original
            archive_path = output_dir / pdf_file.name
            shutil.move(str(pdf_file), str(archive_path))
            
            logger.info(f"✅ Successfully processed: {pdf_file.name} -> {output_dir.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process {pdf_file.name}: {e}")
            
            # Move to error directory
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            error_dir = self.processed_dir / f"ERROR_{timestamp}_{pdf_file.stem}"
            error_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                shutil.move(str(pdf_file), str(error_dir / pdf_file.name))
                
                # Save error info
                error_info = {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "source_file": pdf_file.name
                }
                with open(error_dir / "error.json", 'w') as f:
                    json.dump(error_info, f, indent=2)
                    
            except Exception as move_error:
                logger.error(f"Failed to move error file: {move_error}")
            
            return False
            
        finally:
            # Cleanup temporary files
            for temp_file in [ocr_pdf, po_pdf, router_pdf]:
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except Exception:
                        pass

    def run(self):
        """Main processing loop"""
        logger.info("Starting pipeline scan...")
        
        # Find all PDF files in incoming directory
        pdf_files = [f for f in self.incoming_dir.iterdir() 
                    if f.is_file() and f.suffix.lower() == '.pdf']
        
        if not pdf_files:
            logger.info("No PDF files found")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        processed_count = 0
        error_count = 0
        
        for pdf_file in pdf_files:
            try:
                if self.process_file(pdf_file):
                    processed_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Unexpected error processing {pdf_file.name}: {e}")
                error_count += 1
        
        logger.info(f"Pipeline complete: {processed_count} successful, {error_count} errors")

def main():
    """Entry point"""
    processor = UnifiedOCRProcessor()
    processor.run()

if __name__ == "__main__":
    main()