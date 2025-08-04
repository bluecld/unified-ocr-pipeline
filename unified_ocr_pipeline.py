#!/usr/bin/env python3
"""
Enhanced Unified OCR Pipeline
Processes PDFs containing PO and Router sections with intelligent text-based splitting
and comprehensive field extraction for FileMaker integration.
"""

import os
import sys
import json
import fitz  # PyMuPDF
import subprocess
import logging
import re
import requests
import urllib3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Disable SSL warnings for FileMaker connections (if using self-signed certs)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
def setup_logging():
    """Set up comprehensive logging for the pipeline"""
    log_level = os.getenv('OCR_LOG_LEVEL', 'INFO').upper()
    log_dir = Path(os.getenv('OCR_LOG_DIR', '/app/logs'))
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'pipeline.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class QualityClauseReference:
    """Reference database for quality clauses and their descriptions"""
    
    CLAUSES = {
        'Q8': 'Material certification and test reports required',
        'Q10': 'First article inspection required',
        'Q15': 'Statistical process control documentation',
        'Q20': 'Source inspection required',
        'Q25': 'Certificate of compliance required',
        'Q30': 'Serialization and traceability required',
        'Q35': 'Special packaging and handling requirements',
        'Q40': 'Government source inspection required',
        'Q43': 'AS9102 First Article Inspection Report required',
        'Q45': 'NADCAP certification required',
        'Q50': 'Customer source inspection required'
    }
    
    @classmethod
    def get_description(cls, code: str) -> Optional[str]:
        """Get description for a quality clause code"""
        return cls.CLAUSES.get(code.upper())
    
    @classmethod
    def find_all_clauses(cls, text: str) -> List[Dict[str, str]]:
        """Find all quality clause codes in text and return with descriptions"""
        clauses = []
        # Look for Q followed by digits
        pattern = r'\bQ(\d+)\b'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            code = match.group(0).upper()
            description = cls.get_description(code)
            if description:
                clauses.append({
                    'code': code,
                    'description': description
                })
        
        return clauses

class PlannerReference:
    """Reference list of known planners for validation"""
    
    PLANNERS = [
        'SMITH, JOHN',
        'JOHNSON, MARY',
        'WILLIAMS, ROBERT',
        'BROWN, PATRICIA',
        'DAVIS, MICHAEL',
        'MILLER, LINDA',
        'WILSON, WILLIAM',
        'MOORE, ELIZABETH'
    ]
    
    @classmethod
    def find_planner(cls, text: str) -> Optional[str]:
        """Find a planner name in the text"""
        text_upper = text.upper()
        for planner in cls.PLANNERS:
            if planner.upper() in text_upper:
                return planner
        return None

class EnhancedPDFProcessor:
    """Enhanced PDF processor with intelligent splitting and field extraction"""
    
    def __init__(self, incoming_dir: str, processed_dir: str):
        self.incoming_dir = Path(incoming_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(exist_ok=True)
        
        # Text patterns that indicate transition from PO to Router
        self.router_indicators = [
            r'router',
            r'routing\s+sheet',
            r'manufacturing\s+routing',
            r'operation\s+sequence',
            r'work\s+instructions',
            r'process\s+sheet'
        ]
        
    def ocr_first_page_for_analysis(self, pdf_path: str, temp_dir: str) -> Optional[str]:
        """
        OCR only the first page to extract text for page count detection
        Returns extracted text from first page or None if failed
        """
        try:
            temp_first_page_pdf = os.path.join(temp_dir, "first_page_temp.pdf")
            temp_first_page_ocr = os.path.join(temp_dir, "first_page_ocr_temp.pdf")
            
            # Extract just the first page
            doc = fitz.open(pdf_path)
            first_page_doc = fitz.open()
            first_page_doc.insert_pdf(doc, from_page=0, to_page=0)
            first_page_doc.save(temp_first_page_pdf)
            first_page_doc.close()
            doc.close()
            
            # OCR just the first page
            if self.run_ocr_on_file(temp_first_page_pdf, temp_first_page_ocr):
                # Extract text from OCR'd first page
                text = self.extract_text_from_pdf(temp_first_page_ocr)
                
                # Clean up temp files
                try:
                    os.remove(temp_first_page_pdf)
                    os.remove(temp_first_page_ocr)
                except:
                    pass
                
                logger.info("Successfully OCR'd first page for analysis")
                return text
            else:
                logger.error("Failed to OCR first page")
                return None
                
        except Exception as e:
            logger.error(f"Error OCR'ing first page: {e}")
            return None

    def find_router_start_page(self, pdf_path: str, temp_dir: str = None) -> Optional[int]:
        """
        Find the page where Router section begins using text analysis
        For raw scanned files: OCR first page only to detect "Page 1 of N"
        For text PDFs: Extract text directly
        Returns page number (0-indexed) or None if not found
        """
        try:
            doc = fitz.open(pdf_path)
            first_page_text = ""
            
            # First, try to extract text directly (for already OCR'd PDFs)
            if len(doc) > 0:
                first_page = doc[0]
                first_page_text = first_page.get_text()
                
                # If no text found, this is likely a raw scanned file - OCR first page only
                if not first_page_text.strip() and temp_dir:
                    logger.info("No text found on first page - OCR'ing first page only for analysis")
                    first_page_text = self.ocr_first_page_for_analysis(pdf_path, temp_dir)
                    if not first_page_text:
                        doc.close()
                        return None
                
                # Look for "Page 1 of N" pattern in first page text
                page_pattern = r'page\s+1\s+of\s+(\d+)'
                match = re.search(page_pattern, first_page_text, re.IGNORECASE)
                
                if match:
                    total_po_pages = int(match.group(1))
                    logger.info(f"Found 'Page 1 of {total_po_pages}' indicator - PO section is {total_po_pages} pages")
                    
                    # If the document has more pages than the PO section, 
                    # the router starts after the PO pages
                    if len(doc) > total_po_pages:
                        router_start = total_po_pages  # 0-indexed
                        logger.info(f"Router section starts at page {router_start + 1} based on page count")
                        doc.close()
                        return router_start
                    else:
                        # Document only contains PO pages
                        logger.info("Document contains only PO pages (no router section)")
                        doc.close()
                        return None
            
            # Fall back to keyword-based detection if no page indicator found
            logger.info("No 'Page 1 of N' indicator found, falling back to keyword detection")
            
            # For keyword detection, we need to check each page
            # If this is a raw scanned file, we'll need to OCR more pages
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text().lower()
                
                # If no text and this is a scanned file, we'd need to OCR this page
                # For now, skip keyword detection on scanned files to save time
                if not text.strip() and temp_dir:
                    logger.info("Skipping keyword detection on raw scanned file to save OCR time")
                    break
                
                # Check if any router indicators are present
                for pattern in self.router_indicators:
                    if re.search(pattern, text, re.IGNORECASE):
                        logger.info(f"Found router indicator '{pattern}' on page {page_num + 1}")
                        doc.close()
                        return page_num
                        
            doc.close()
            logger.warning("No router section indicators found - assuming single PO document")
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing PDF for router section: {e}")
            return None
    
    def split_po_router(self, input_pdf: str, po_pdf: str, router_pdf: str, temp_dir: str = None) -> bool:
        """
        Split PDF into PO and Router sections based on text content analysis
        Returns True if splitting was successful
        """
        try:
            router_start_page = self.find_router_start_page(input_pdf, temp_dir)
            
            doc = fitz.open(input_pdf)
            po_doc = fitz.open()
            
            if router_start_page is None:
                # No router section found - entire document is PO
                po_doc.insert_pdf(doc)
                po_doc.save(po_pdf)
                logger.info(f"No router section found - saved entire document as PO: {po_pdf}")
                doc.close()
                po_doc.close()
                return True
            
            # Split document at router start page
            # PO section: pages 0 to router_start_page-1
            if router_start_page > 0:
                po_doc.insert_pdf(doc, from_page=0, to_page=router_start_page-1)
                po_doc.save(po_pdf)
                logger.info(f"Saved PO section (pages 1-{router_start_page}): {po_pdf}")
            
            # Router section: pages router_start_page to end
            if router_start_page < len(doc):
                router_doc = fitz.open()
                router_doc.insert_pdf(doc, from_page=router_start_page, to_page=len(doc)-1)
                router_doc.save(router_pdf)
                router_doc.close()
                logger.info(f"Saved Router section (pages {router_start_page+1}-{len(doc)}): {router_pdf}")
            
            doc.close()
            po_doc.close()
            return True
            
        except Exception as e:
            logger.error(f"Error splitting PDF {input_pdf}: {e}")
            return False
    
    def run_ocr_on_file(self, input_pdf: str, output_pdf: str, pages_only: Optional[str] = None) -> bool:
        """
        Run OCR on PDF file, optionally limiting to specific pages
        pages_only: e.g., "1" for first page only, "1-3" for pages 1-3
        """
        try:
            cmd = [
                "ocrmypdf",
                "--force-ocr",
                "--rotate-pages",
                "--tesseract-timeout", "30",
                "--optimize", "1"
            ]
            
            # Add page selection if specified
            if pages_only:
                cmd.extend(["--pages", pages_only])
                
            cmd.extend([input_pdf, output_pdf])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"OCR completed successfully: {output_pdf}")
                return True
            else:
                logger.error(f"OCR failed for {input_pdf}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"OCR timeout for {input_pdf}")
            return False
        except Exception as e:
            logger.error(f"OCR error for {input_pdf}: {e}")
            return False

    def selective_ocr_with_split_info(self, input_pdf: str, po_pdf: str, router_pdf: str, 
                                    router_start_page: Optional[int], temp_dir: str) -> Tuple[str, Optional[str]]:
        """
        Perform selective OCR based on discovered split information
        Returns (po_ocr_path, router_ocr_path) or (None, None) if failed
        """
        try:
            po_ocr_path = os.path.join(temp_dir, f"{Path(input_pdf).stem}_po_ocr.pdf")
            router_ocr_path = None
            
            # OCR the PO section (all PO pages)
            if router_start_page is not None:
                # We know exactly which pages are PO - OCR only those pages
                po_page_range = f"1-{router_start_page}"
                logger.info(f"OCR'ing PO section (pages {po_page_range}) with selective strategy")
                
                if self.run_ocr_on_file(input_pdf, po_ocr_path, pages_only=po_page_range):
                    logger.info(f"Selective OCR of PO pages completed: {po_ocr_path}")
                else:
                    logger.error("Failed to OCR PO section with selective strategy")
                    return None, None
                
                # OCR only first page of Router section
                doc = fitz.open(input_pdf)
                if router_start_page < len(doc):
                    router_first_page = router_start_page + 1  # Convert to 1-based for ocrmypdf
                    router_ocr_path = os.path.join(temp_dir, f"{Path(input_pdf).stem}_router_ocr.pdf")
                    
                    logger.info(f"OCR'ing Router first page (page {router_first_page}) with selective strategy")
                    if self.run_ocr_on_file(input_pdf, router_ocr_path, pages_only=str(router_first_page)):
                        logger.info(f"Selective OCR of Router first page completed: {router_ocr_path}")
                    else:
                        logger.warning("Failed to OCR Router first page - continuing without it")
                        router_ocr_path = None
                doc.close()
                
            else:
                # No router section found - OCR entire document as PO
                logger.info("OCR'ing entire document as PO (no router section detected)")
                if self.run_ocr_on_file(input_pdf, po_ocr_path):
                    logger.info(f"Full document OCR completed: {po_ocr_path}")
                else:
                    logger.error("Failed to OCR entire document")
                    return None, None
            
            return po_ocr_path, router_ocr_path
            
        except Exception as e:
            logger.error(f"Error in selective OCR strategy: {e}")
            return None, None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text from OCR'd PDF"""
        try:
            result = subprocess.run(
                ["pdftotext", pdf_path, "-"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"pdftotext failed for {pdf_path}: {result.stderr}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""

class FieldExtractor:
    """Enhanced field extraction with comprehensive business logic"""
    
    def __init__(self, text: str):
        self.text = text
        self.text_lines = text.split('\n')
        
    def extract_po_number(self) -> Optional[str]:
        """Extract 10-digit PO number starting with 45"""
        # Look for 10-digit number starting with 45
        pattern = r'\b45\d{8}\b'
        match = re.search(pattern, self.text)
        if match:
            logger.info(f"Found PO number: {match.group(0)}")
            return match.group(0)
        
        logger.warning("No valid PO number found (10 digits starting with 45)")
        return None
    
    def extract_mjo_number(self) -> Optional[str]:
        """Extract MJO number - typically follows 'MJO' or 'MJO NO'"""
        patterns = [
            r'MJO\s*NO\.?\s*:?\s*(\w+)',
            r'MJO\s*:?\s*(\w+)',
            r'Manufacturing\s+Job\s+Order\s*:?\s*(\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                mjo = match.group(1).strip()
                logger.info(f"Found MJO number: {mjo}")
                return mjo
                
        logger.warning("No MJO number found")
        return None
    
    def extract_quantity_shipped(self) -> Optional[str]:
        """Extract quantity shipped - look for QTY SHIP or similar"""
        patterns = [
            r'QTY\s+SHIP\w*\s*:?\s*(\d+(?:,\d{3})*(?:\.\d+)?)',
            r'QUANTITY\s+SHIPPED\s*:?\s*(\d+(?:,\d{3})*(?:\.\d+)?)',
            r'QTY\s*:?\s*(\d+(?:,\d{3})*(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                qty = match.group(1).replace(',', '')
                logger.info(f"Found quantity shipped: {qty}")
                return qty
                
        logger.warning("No quantity shipped found")
        return None
    
    def extract_part_number(self) -> Optional[str]:
        """Extract part number with *op## format"""
        # Look for part numbers that include *op followed by digits
        pattern = r'(\w+\*op\d+)'
        match = re.search(pattern, self.text, re.IGNORECASE)
        if match:
            part_num = match.group(1)
            logger.info(f"Found part number: {part_num}")
            return part_num
            
        # Fallback: look for PART NUMBER or P/N labels
        patterns = [
            r'PART\s+NUMBER\s*:?\s*(\S+)',
            r'P/N\s*:?\s*(\S+)',
            r'PART\s*#\s*:?\s*(\S+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                part_num = match.group(1)
                logger.info(f"Found part number (fallback): {part_num}")
                return part_num
                
        logger.warning("No part number found")
        return None
    
    def extract_delivery_date(self) -> Optional[str]:
        """Extract promise delivery date - often after EA quantity or labeled as Dock Date"""
        patterns = [
            r'PROMISE\s+DELIVERY\s+DATE\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'DOCK\s+DATE\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'DELIVERY\s+DATE\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'EA\s+.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Date after EA quantity
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Standardize date format
                try:
                    # Try to parse and reformat the date
                    for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y']:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            formatted_date = parsed_date.strftime('%m/%d/%Y')
                            logger.info(f"Found delivery date: {formatted_date}")
                            return formatted_date
                        except ValueError:
                            continue
                except:
                    pass
                    
                # If parsing fails, return as-is
                logger.info(f"Found delivery date (unparsed): {date_str}")
                return date_str
                
        logger.warning("No delivery date found")
        return None
    
    def extract_whittaker_shipper(self) -> Optional[str]:
        """Extract Whittaker Shipper (Purchase Order number)"""
        patterns = [
            r'WHITTAKER\s+SHIPPER\s*:?\s*(\w+)',
            r'PURCHASE\s+ORDER\s*:?\s*(\w+)',
            r'PO\s*:?\s*(\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                shipper = match.group(1)
                logger.info(f"Found Whittaker Shipper: {shipper}")
                return shipper
                
        logger.warning("No Whittaker Shipper found")
        return None
    
    def extract_dpas_rating(self) -> List[str]:
        """Extract DPAS rating(s) - may appear multiple times"""
        pattern = r'DPAS\s*:?\s*([A-Z]\d+)'
        matches = re.findall(pattern, self.text, re.IGNORECASE)
        
        if matches:
            ratings = [match.upper() for match in matches]
            logger.info(f"Found DPAS ratings: {ratings}")
            return ratings
            
        logger.warning("No DPAS ratings found")
        return []
    
    def extract_payment_terms(self) -> Tuple[Optional[str], bool]:
        """
        Extract payment terms and flag if not '30 Days'
        Returns (terms, is_non_standard) where is_non_standard=True if not 30 days
        """
        patterns = [
            r'PAYMENT\s+TERMS\s*:?\s*([^,\n]+)',
            r'TERMS\s*:?\s*([^,\n]+)',
            r'NET\s+(\d+)\s*DAYS?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                terms = match.group(1).strip()
                
                # Check if it's standard 30-day terms
                is_non_standard = not any([
                    '30' in terms and 'day' in terms.lower(),
                    'net 30' in terms.lower(),
                    'net30' in terms.lower()
                ])
                
                logger.info(f"Found payment terms: {terms} (non-standard: {is_non_standard})")
                return terms, is_non_standard
                
        logger.warning("No payment terms found")
        return None, False
    
    def extract_quality_clauses(self) -> List[Dict[str, str]]:
        """Extract quality clauses with descriptions"""
        clauses = QualityClauseReference.find_all_clauses(self.text)
        if clauses:
            logger.info(f"Found {len(clauses)} quality clauses")
        else:
            logger.warning("No quality clauses found")
        return clauses
    
    def extract_planner_name(self) -> Optional[str]:
        """Extract planner name from predefined list"""
        planner = PlannerReference.find_planner(self.text)
        if planner:
            logger.info(f"Found planner: {planner}")
        else:
            logger.warning("No known planner found")
        return planner
    
    def extract_all_fields(self) -> Dict[str, Any]:
        """Extract all fields and return as structured dictionary"""
        logger.info("Starting comprehensive field extraction...")
        
        # Extract payment terms
        payment_terms, non_standard_payment = self.extract_payment_terms()
        
        extracted_data = {
            'po_number': self.extract_po_number(),
            'mjo_number': self.extract_mjo_number(),
            'quantity_shipped': self.extract_quantity_shipped(),
            'part_number': self.extract_part_number(),
            'delivery_date': self.extract_delivery_date(),
            'whittaker_shipper': self.extract_whittaker_shipper(),
            'dpas_ratings': self.extract_dpas_rating(),
            'payment_terms': payment_terms,
            'non_standard_payment': non_standard_payment,
            'quality_clauses': self.extract_quality_clauses(),
            'planner_name': self.extract_planner_name(),
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        # Count successfully extracted fields
        extracted_count = sum(1 for v in extracted_data.values() 
                            if v is not None and v != [] and v != False)
        logger.info(f"Successfully extracted {extracted_count} fields")
        
        return extracted_data

class FileMakerIntegration:
    """FileMaker Data API integration for uploading records and files"""
    
    def __init__(self):
        self.enabled = os.getenv('FM_ENABLED', 'false').lower() == 'true'
        if not self.enabled:
            logger.info("FileMaker integration disabled")
            return
            
        self.host = os.getenv('FM_HOST', '192.168.0.39')
        self.database = os.getenv('FM_DB', 'PreInventory')
        self.layout = os.getenv('FM_LAYOUT', 'PreInventory')
        self.username = os.getenv('FM_USERNAME', 'Anthony')
        self.password = os.getenv('FM_PASSWORD', '')
        
        self.base_url = f"https://{self.host}/fmi/data/v1/databases/{self.database}"
        self.token = None
        
        logger.info(f"FileMaker integration enabled - Host: {self.host}, DB: {self.database}")
    
    def authenticate(self) -> bool:
        """Authenticate with FileMaker Data API"""
        if not self.enabled:
            return False
            
        try:
            auth_url = f"{self.base_url}/sessions"
            response = requests.post(
                auth_url,
                json={},
                auth=(self.username, self.password),
                verify=False,  # For self-signed certificates
                timeout=30
            )
            
            if response.status_code == 200:
                self.token = response.json()['response']['token']
                logger.info("FileMaker authentication successful")
                return True
            else:
                logger.error(f"FileMaker authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"FileMaker authentication error: {e}")
            return False
    
    def create_record(self, field_data: Dict[str, Any]) -> Optional[str]:
        """Create a new record in FileMaker and return record ID"""
        if not self.enabled or not self.token:
            return None
            
        try:
            create_url = f"{self.base_url}/layouts/{self.layout}/records"
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            # Prepare field data for FileMaker (remove None values and format properly)
            fm_data = {}
            for key, value in field_data.items():
                if value is not None:
                    if isinstance(value, list):
                        # Convert lists to JSON strings for FileMaker
                        fm_data[key] = json.dumps(value)
                    else:
                        fm_data[key] = str(value)
            
            payload = {
                'fieldData': fm_data
            }
            
            response = requests.post(
                create_url,
                json=payload,
                headers=headers,
                verify=False,
                timeout=60
            )
            
            if response.status_code == 200:
                record_id = response.json()['response']['recordId']
                logger.info(f"FileMaker record created successfully: {record_id}")
                return record_id
            else:
                logger.error(f"FileMaker record creation failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"FileMaker record creation error: {e}")
            return None
    
    def upload_file_to_container(self, record_id: str, field_name: str, file_path: str) -> bool:
        """Upload file to FileMaker container field"""
        if not self.enabled or not self.token or not record_id:
            return False
            
        try:
            upload_url = f"{self.base_url}/layouts/{self.layout}/records/{record_id}/containers/{field_name}"
            headers = {
                'Authorization': f'Bearer {self.token}'
            }
            
            with open(file_path, 'rb') as file:
                files = {'upload': file}
                response = requests.post(
                    upload_url,
                    files=files,
                    headers=headers,
                    verify=False,
                    timeout=120
                )
            
            if response.status_code == 200:
                logger.info(f"File uploaded to FileMaker container {field_name}: {file_path}")
                return True
            else:
                logger.error(f"FileMaker file upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"FileMaker file upload error: {e}")
            return False
    
    def logout(self):
        """Logout from FileMaker session"""
        if not self.enabled or not self.token:
            return
            
        try:
            logout_url = f"{self.base_url}/sessions/{self.token}"
            response = requests.delete(logout_url, verify=False, timeout=30)
            logger.info("FileMaker session closed")
        except Exception as e:
            logger.error(f"FileMaker logout error: {e}")

class UnifiedOCRPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self):
        self.incoming_dir = os.getenv('OCR_INCOMING', '/app/incoming')
        self.processed_dir = os.getenv('OCR_PROCESSED', '/app/processed')
        
        self.pdf_processor = EnhancedPDFProcessor(self.incoming_dir, self.processed_dir)
        self.filemaker = FileMakerIntegration()
        
        logger.info(f"Pipeline initialized - Incoming: {self.incoming_dir}, Processed: {self.processed_dir}")
    
    def create_output_folder(self, po_number: str) -> Path:
        """Create output folder named with PO number"""
        if po_number:
            folder_name = f"PO_{po_number}"
        else:
            # Use timestamp for files without valid PO numbers
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = f"ERROR_{timestamp}"
            
        output_folder = Path(self.processed_dir) / folder_name
        output_folder.mkdir(exist_ok=True)
        return output_folder
    
    def process_single_file(self, input_file: Path) -> bool:
        """Process a single PDF file through the complete pipeline"""
        logger.info(f"🔄 Processing file: {input_file.name}")
        
        try:
            # Step 1: Analyze PDF and determine split strategy
            temp_dir = Path(self.processed_dir) / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            logger.info("🔍 Analyzing PDF structure for optimal OCR strategy...")
            
            # Get split information (this now includes smart first-page OCR for raw scans)
            router_start_page = self.pdf_processor.find_router_start_page(str(input_file), str(temp_dir))
            
            # Step 2: Use selective OCR strategy based on discovered split point
            logger.info("⚡ Applying selective OCR strategy...")
            ocr_po_path, ocr_router_path = self.pdf_processor.selective_ocr_with_split_info(
                str(input_file), "", "", router_start_page, str(temp_dir)
            )
            
            if not ocr_po_path:
                logger.error(f"Failed to OCR PDF with selective strategy: {input_file}")
                return False
            
            # Step 3: Extract text and fields from OCR'd PO section
            po_text = self.pdf_processor.extract_text_from_pdf(ocr_po_path)
            if not po_text:
                logger.error(f"No text extracted from PO file: {ocr_po_path}")
                return False
            
            extractor = FieldExtractor(po_text)
            extracted_data = extractor.extract_all_fields()
            
            # Step 5: Create output folder using PO number
            po_number = extracted_data.get('po_number')
            output_folder = self.create_output_folder(po_number)
            
            # Step 6: Save files to output folder
            if po_number:
                final_po_name = f"{po_number}_PO.pdf"
                final_router_name = f"{po_number}_ROUTER.pdf"
            else:
                final_po_name = f"{input_file.stem}_PO.pdf"
                final_router_name = f"{input_file.stem}_ROUTER.pdf"
            
            final_po = output_folder / final_po_name
            final_router = output_folder / final_router_name
            
            # Copy OCR'd files to final location
            import shutil
            shutil.copy2(ocr_po_path, str(final_po))
            if ocr_router_path and Path(ocr_router_path).exists():
                shutil.copy2(ocr_router_path, str(final_router))
            
            # Save extracted data as JSON
            json_file = output_folder / "extracted_data.json"
            with open(json_file, 'w') as f:
                json.dump(extracted_data, f, indent=2)
            
            # Save raw text for debugging
            text_file = output_folder / "extracted_text.txt"
            with open(text_file, 'w') as f:
                f.write(po_text)
            
            # Step 7: Upload to FileMaker (if enabled)
            if self.filemaker.enabled and po_number:
                if self.filemaker.authenticate():
                    record_id = self.filemaker.create_record(extracted_data)
                    if record_id:
                        # Upload PO file
                        self.filemaker.upload_file_to_container(record_id, 'IncomingPO', str(final_po))
                        # Upload Router file if it exists
                        if final_router.exists():
                            self.filemaker.upload_file_to_container(record_id, 'IncomingRouter', str(final_router))
                    self.filemaker.logout()
            
            # Step 8: Clean up temp files
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            
            # Step 9: Remove original file from incoming
            input_file.unlink()
            
            logger.info(f"✅ Successfully processed: {input_file.name} -> {output_folder.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing {input_file}: {e}")
            return False
    
    def run(self):
        """Main pipeline execution"""
        logger.info("🚀 Starting Unified OCR Pipeline")
        
        incoming_path = Path(self.incoming_dir)
        if not incoming_path.exists():
            logger.error(f"Incoming directory does not exist: {self.incoming_dir}")
            return
        
        # Find all PDF files in incoming directory
        pdf_files = list(incoming_path.glob("*.pdf"))
        
        if not pdf_files:
            logger.info("No PDF files found in incoming directory")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each file
        processed_count = 0
        error_count = 0
        
        for pdf_file in pdf_files:
            try:
                if self.process_single_file(pdf_file):
                    processed_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Unexpected error processing {pdf_file}: {e}")
                error_count += 1
        
        logger.info(f"📊 Pipeline completed - Processed: {processed_count}, Errors: {error_count}")

def main():
    """Main entry point"""
    try:
        pipeline = UnifiedOCRPipeline()
        pipeline.run()
        
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()