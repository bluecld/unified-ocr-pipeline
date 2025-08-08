#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""
Unified OCR Pipeline for PDF Processing
Handles PyMuPDF import issues with fallback backends
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import subprocess
from datetime import datetime

class UnifiedOCRPipeline:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = self._setup_logging()
        self.pdf_backend = self._initialize_pdf_backend()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = os.getenv("LOG_DIR", "/app/logs")
        # Fallback to local logs if /app/logs doesn't exist
        try:
            os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(os.path.join(log_dir, 'ocr_pipeline.log'))
            handlers = [file_handler, logging.StreamHandler(sys.stdout)]
        except Exception:
            # Final fallback: stdout only
            handlers = [logging.StreamHandler(sys.stdout)]

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )
        return logging.getLogger(__name__)
    
    def _initialize_pdf_backend(self):
        """Initialize PDF processing backend with fallbacks"""
        self.logger.info("Initializing PDF backend...")
        
        # Try PyMuPDF first
        try:
            import fitz
            self.logger.info("✅ Using PyMuPDF backend")
            return "pymupdf"
        except ImportError as e:
            self.logger.warning(f"⚠️  PyMuPDF not available: {e}")
            
        # Fallback to pdfplumber
        try:
            import pdfplumber
            self.logger.info("✅ Using pdfplumber backend (fallback)")
            return "pdfplumber"
        except ImportError:
            self.logger.error("❌ No PDF backend available!")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """System health check"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "pdf_backend": self.pdf_backend,
            "status": "healthy" if self.pdf_backend else "unhealthy",
            "dependencies": {}
        }
        
        # Check dependencies
        deps = ["fitz", "pdfplumber", "pytesseract", "PIL"]
        for dep in deps:
            try:
                __import__(dep)
                status["dependencies"][dep] = "available"
            except ImportError:
                status["dependencies"][dep] = "missing"
        
        return status
    
    def process_pdf(self, pdf_path: str, output_dir: str = None) -> Dict[str, Any]:
        """Main OCR processing function"""
        if not self.pdf_backend:
            raise Exception("No PDF processing backend available")

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Use env-configured output directory with safe defaults
        if output_dir:
            base_output_dir = Path(output_dir)
        else:
            env_out = os.getenv("OCR_PROCESSED")
            if env_out:
                base_output_dir = Path(env_out)
            elif Path("/app/ProcessedPOs").exists():
                base_output_dir = Path("/app/ProcessedPOs")
            else:
                base_output_dir = Path("/volume1/Main/Main/ProcessedPOs")

        self.logger.info(f"Processing PDF: {pdf_path}")

        start_time = datetime.now()

        if self.pdf_backend == "pymupdf":
            results = self._process_with_pymupdf(pdf_path, base_output_dir)
        elif self.pdf_backend == "pdfplumber":
            results = self._process_with_pdfplumber(pdf_path, base_output_dir)
        else:
            raise Exception(f"Unknown backend: {self.pdf_backend}")

        processing_time = (datetime.now() - start_time).total_seconds()
        results["processing_time_seconds"] = processing_time
        results["timestamp"] = datetime.now().isoformat()

        self.logger.info(f"✅ Processing complete in {processing_time:.2f}s")
        return results
    
    def _process_with_pymupdf(self, pdf_path: Path, base_output_dir: Path) -> Dict[str, Any]:
        """Process PDF using PyMuPDF"""
        import fitz

        self.logger.info("Processing with PyMuPDF...")

        doc = fitz.open(pdf_path)
        results = {
            "source_file": str(pdf_path),
            "pages": [],
            "total_pages": len(doc),
            "backend": "pymupdf",
            "total_text_length": 0,
            "total_images": 0,
            "po_number": None
        }

        po_pages: List[int] = []
        po_number: Optional[str] = None

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Extract text
            text = page.get_text()

            # Extract images for potential OCR
            image_list = page.get_images()

            page_result = {
                "page_number": page_num + 1,
                "text": text,
                "text_length": len(text),
                "images_found": len(image_list),
                "has_text": bool(text.strip())
            }

            # Force OCR for first 2 pages if no text found
            if page_num < 2 and (not text.strip()) and image_list:
                self.logger.info(f"Forced OCR for page {page_num + 1}")
                try:
                    import pytesseract
                    from PIL import Image
                    xref = image_list[0][0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha < 4:
                        temp_img_path = f"/tmp/page_{page_num + 1:03d}_ocr.png"
                        pix.save(temp_img_path)
                        pix = None
                        self.logger.info(f"Saved image for OCR: {temp_img_path}")
                        # Run OCR
                        ocr_text = pytesseract.image_to_string(Image.open(temp_img_path), lang="eng")
                        self.logger.info(f"OCR result for page {page_num + 1}: {repr(ocr_text[:100])}")
                        page_result["ocr_text"] = ocr_text
                        page_result["ocr_text_length"] = len(ocr_text)
                        # Use OCR text as main text for this page
                        text = ocr_text
                        page_result["text"] = text
                        page_result["text_length"] = len(text)
                except Exception as e:
                    self.logger.error(f"OCR failed for page {page_num + 1}: {e}")

            # PO extraction: try to find PO number from OCR or text
            if page_num < 2 and page_result.get("text") and not po_number:
                import re
                po_match = re.search(r"Purchase\s*[Oo]rder\s*(\d{10})", page_result["text"], re.IGNORECASE)
                if not po_match:
                    po_match = re.search(r"PO\s*[:\-]?\s*(\d{10})", page_result["text"], re.IGNORECASE)
                if not po_match:
                    po_match = re.search(r"(\d{10})", page_result["text"])  # Any 10-digit number
                if po_match:
                    po_number = po_match.group(1)
                    results["po_number"] = po_number
                    page_result["po_number"] = po_number
                    self.logger.info(f"Extracted PO number from page {page_num + 1}: {po_number}")

            # Determine if this page is part of PO (first 2 pages typically)
            if page_num < 2 or (page_result.get("text") and "purchase order" in page_result.get("text", "").lower()):
                po_pages.append(page_num)

            results["pages"].append(page_result)
            results["total_text_length"] += len(text)
            results["total_images"] += len(image_list)

        # Create output directory structure
        if not po_number:
            po_number = "UNKNOWN_PO"
            self.logger.warning("No PO number found, using UNKNOWN_PO")

        po_output_dir = base_output_dir / po_number
        misc_dir = po_output_dir / "Misc"
        po_output_dir.mkdir(parents=True, exist_ok=True)
        misc_dir.mkdir(exist_ok=True)

        # Split PDF: Create PO PDF and Router PDF
        po_doc = fitz.open()
        router_doc = fitz.open()

        for page_num in range(len(doc)):
            page = doc[page_num]
            if page_num in po_pages:
                po_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            else:
                router_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        # Save PO PDF
        po_pdf_path = po_output_dir / f"{po_number}_PO.pdf"
        if po_doc.page_count > 0:
            po_doc.save(str(po_pdf_path))
            self.logger.info(f"Saved PO PDF: {po_pdf_path}")

        # Save Router PDF
        router_pdf_path = po_output_dir / f"{po_number}_Router.pdf"
        if router_doc.page_count > 0:
            router_doc.save(str(router_pdf_path))
            self.logger.info(f"Saved Router PDF: {router_pdf_path}")

        # Save JSON file for FileMaker
        json_data = {
            "po_number": po_number,
            "source_file": str(pdf_path),
            "processing_timestamp": datetime.now().isoformat(),
            "po_pages": len(po_pages),
            "router_pages": len(doc) - len(po_pages),
            "total_pages": len(doc),
            "extracted_data": self._extract_filemaker_data_with_ai(results, po_number)
        }

        json_file_path = po_output_dir / f"{po_number}_data.json"
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Saved JSON data: {json_file_path}")

        # Save misc files (text extracts, images, etc.)
        for page_result in results["pages"]:
            page_num = page_result["page_number"]
            text_file = misc_dir / f"page_{page_num:03d}.txt"
            text_file.write_text(page_result.get("text", ""), encoding='utf-8')

            if page_result.get("ocr_text"):
                ocr_text_file = misc_dir / f"page_{page_num:03d}_ocr.txt"
                ocr_text_file.write_text(page_result["ocr_text"], encoding='utf-8')

        # Save combined text
        all_text = "\n\n--- PAGE BREAK ---\n\n".join([p.get("text", "") for p in results["pages"]])
        combined_file = misc_dir / f"{pdf_path.stem}_combined.txt"
        combined_file.write_text(all_text, encoding='utf-8')

        doc.close()
        po_doc.close()
        router_doc.close()

        return results
    
    def _extract_vendor(self, results: Dict[str, Any]) -> str:
        """Extract vendor information from text"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            # Look for vendor address section - improved pattern
            vendor_match = re.search(r"Vendor address[^\n]*\n([^\n]+)", text, re.IGNORECASE)
            if vendor_match:
                vendor_name = vendor_match.group(1).strip()
                # Clean up common artifacts
                if vendor_name and not re.match(r'^\d+\s', vendor_name):
                    return vendor_name
            
            # Fallback: Look for company names with common suffixes
            company_match = re.search(r"([A-Z][A-Z\s,\.&]+(?:INC|LLC|CORP|COMPANY|CO|ENTERPRISES)[A-Z\s,\.]*)", text, re.IGNORECASE)
            if company_match:
                return company_match.group(1).strip()
        return ""
    
    def _extract_date(self, results: Dict[str, Any]) -> str:
        """Extract date from text"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            # Look for date patterns
            date_match = re.search(r"Date[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})", text, re.IGNORECASE)
            if date_match:
                return date_match.group(1)
        return ""
    
    def _extract_amount(self, results: Dict[str, Any]) -> str:
        """Extract total amount from text"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            # Look for Total amount or Net value
            amount_patterns = [
                r"Total amount[:\s]*([\d,]+\.?\d*)",
                r"Net value[:\s]*([\d,]+\.?\d*)",
                r"amount[:\s]*\$?([\d,]+\.?\d*)",
                r"\$[\s]*([\d,]+\.?\d*)"
            ]
            
            for pattern in amount_patterns:
                amount_match = re.search(pattern, text, re.IGNORECASE)
                if amount_match:
                    return amount_match.group(1)
        return ""
    
    def _extract_delivery_date(self, results: Dict[str, Any]) -> str:
        """Extract delivery date from text"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            # Look for delivery date patterns - improved
            delivery_match = re.search(r"Delivery Date[^\n]*\n[^\n]*?(\d{1,2}/\d{1,2}/\d{4})", text, re.IGNORECASE | re.DOTALL)
            if delivery_match:
                return delivery_match.group(1)
                
            # Look for dock date patterns
            dock_match = re.search(r"Dockdate[:\s]*(\d{1,2}/\d{1,2}/\d{4})", text, re.IGNORECASE)
            if dock_match:
                return dock_match.group(1)
                
            # Look for date after EA
            ea_date_match = re.search(r"EA[^\n]*?(\d{1,2}/\d{1,2}/\d{4})", text, re.IGNORECASE)
            if ea_date_match:
                return ea_date_match.group(1)
        return ""
    
    def _extract_vendor_number(self, results: Dict[str, Any]) -> str:
        """Extract vendor number from text"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            vendor_num_match = re.search(r"Vendor number[:\s]*(\d+)", text, re.IGNORECASE)
            if vendor_num_match:
                return vendor_num_match.group(1)
        return ""
    
    def _extract_buyer_name(self, results: Dict[str, Any]) -> str:
        """Extract buyer name from text"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            buyer_match = re.search(r"Buyer/phone[:\s]*([^/]+)", text, re.IGNORECASE)
            if buyer_match:
                return buyer_match.group(1).strip()
        return ""
    
    def _extract_buyer_phone(self, results: Dict[str, Any]) -> str:
        """Extract buyer phone from text"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            phone_match = re.search(r"Buyer/phone[:\s]*[^/]+/\s*(\d{3}-\d{3}-\d{4})", text, re.IGNORECASE)
            if phone_match:
                return phone_match.group(1)
        return ""
    
    def _extract_buyer_email(self, results: Dict[str, Any]) -> str:
        """Extract buyer email from text"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            email_match = re.search(r"Buyer E-mail[:\s]*([^\s]+@[^\s]+)", text, re.IGNORECASE)
            if email_match:
                return email_match.group(1)
        return ""
    
    def _extract_part_number(self, results: Dict[str, Any]) -> str:
        """Extract part number from text"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            # Look for part number pattern
            part_match = re.search(r"(\d{6}-\d+[A-Z]*)", text)
            if part_match:
                return part_match.group(1)
        return ""
    
    def _extract_quantity(self, results: Dict[str, Any]) -> str:
        """Extract quantity from text"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            # Look for quantity in delivery section
            qty_match = re.search(r"Quantity[:\s]*(\d+\.?\d*)", text, re.IGNORECASE)
            if qty_match:
                return qty_match.group(1)
        return ""
    
    def _extract_net_per_price(self, results: Dict[str, Any]) -> str:
        """Extract net per price from text"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            # Look for net per price
            price_match = re.search(r"Net Per[:\s]*UM[:\s]*Dockdate[:\s]*Net[:\s]*.*?(\d+,\d+\.\d+)", text, re.IGNORECASE | re.DOTALL)
            if price_match:
                return price_match.group(1)
        return ""

    # FileMaker-specific extraction functions
    def _extract_po_number(self, results: Dict[str, Any]) -> str:
        """Extract PO Number for Whittaker Shipper field (must be 10 digits starting with 45)"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            # Look for PO number pattern: 10 digits starting with 45
            po_match = re.search(r"(45\d{8})", text)
            if po_match:
                po_number = po_match.group(1)
                if len(po_number) == 10 and po_number.startswith('45'):
                    return po_number
        return ""
    
    def _extract_production_order(self, results: Dict[str, Any]) -> str:
        """Extract Production Order for MJO NO field"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            # Look for Production Order pattern
            prod_order_match = re.search(r"Production Order[:\s]*(\d+)", text, re.IGNORECASE)
            if prod_order_match:
                return prod_order_match.group(1)
        return ""
    
    def _extract_quantity_shipped(self, results: Dict[str, Any]) -> str:
        """Extract Quantity Shipped for QTY SHIP field (number near EA line)"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            # Look for delivery quantity pattern
            delivery_qty_match = re.search(r"Delivery Date[^\n]*\n[^\n]*Quantity[^\n]*\n[^\n]*?(\d+\.?\d*)", text, re.IGNORECASE | re.DOTALL)
            if delivery_qty_match:
                qty = delivery_qty_match.group(1)
                return str(int(float(qty)))  # Convert to whole number
            
            # Alternative: look for quantity near EA (each)
            ea_match = re.search(r"(\d+\.?\d*)\s*EA", text, re.IGNORECASE)
            if ea_match:
                qty = ea_match.group(1)
                return str(int(float(qty)))  # Convert to whole number
                
            # Another pattern: Quantity followed by number
            qty_match = re.search(r"Quantity[:\s]*(\d+\.?\d*)", text, re.IGNORECASE)
            if qty_match:
                qty = qty_match.group(1)
                return str(int(float(qty)))  # Convert to whole number
        return ""
    
    def _extract_part_number_with_op(self, results: Dict[str, Any]) -> str:
        """Extract Part Number with OP## in format like 150219*OP20"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            # Look for part number pattern in the text - improved pattern
            part_match = re.search(r"(\d{6}-?\d*[A-Z]*)\s+(OP\d+)", text, re.IGNORECASE)
            if part_match:
                part_base = part_match.group(1)
                op_code = part_match.group(2).upper()
                return f"{part_base}*{op_code}"
            
            # Alternative pattern: look for part numbers near "ASSEMBLY" or "BODY ASSY"
            assembly_match = re.search(r"(\d{6}-?\d*[A-Z]*)\s+(\w+\d+)\s+(?:ASSEMBLY|BODY ASSY)", text, re.IGNORECASE)
            if assembly_match:
                part_base = assembly_match.group(1)
                op_code = assembly_match.group(2).upper()
                if op_code.startswith('OP') or 'OP' in op_code:
                    return f"{part_base}*{op_code}"
        return ""

    def _format_part_number_for_filemaker(self, part_number: str) -> str:
        """Format part number to FileMaker standard: 139038-2SA*OP20"""
        if not part_number:
            return ""
        
        import re
        # If it already has asterisk, return as is
        if '*' in part_number:
            return part_number
            
        # Convert dash-OP format to asterisk-OP format
        formatted = re.sub(r'-OP(\d+)$', r'*OP\1', part_number)
        return formatted
    
    def _extract_dpas_rating(self, results: Dict[str, Any]) -> str:
        """Extract DPAS Rating (can appear multiple times, save last or all)"""
        dpas_ratings = []
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            # Look for DPAS rating patterns
            dpas_matches = re.findall(r"DPAS[:\s]*([A-Z]\d+)", text, re.IGNORECASE)
            dpas_ratings.extend(dpas_matches)
        
        if dpas_ratings:
            # Return all ratings joined with comma, or just the last one
            return ", ".join(dpas_ratings) if len(dpas_ratings) > 1 else dpas_ratings[0]
        return ""
    
    def _check_payment_terms(self, results: Dict[str, Any]) -> str:
        """Check Payment Terms - flag if not '30 Days'"""
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            # Look for payment terms
            payment_match = re.search(r"Payment terms[:\s]*([^\\n]+)", text, re.IGNORECASE)
            if payment_match:
                terms = payment_match.group(1).strip()
                if "30 Days" not in terms:
                    return f"NON_STANDARD: {terms}"
                else:
                    return "STANDARD: 30 Days"
        return ""
    
    def _extract_quality_clauses(self, results: Dict[str, Any]) -> dict:
        """Extract Quality Clauses (Q# codes) for Notes JSON"""
        quality_clauses = {}
        for page in results["pages"]:
            text = page.get("text", "")
            import re
            # Look for Q# patterns with better text capture
            q_matches = re.findall(r"(Q\d+)\s+([A-Z][A-Z\s,\[\]()]+?)(?=\s*Q\d+|\s*$|\n\n)", text, re.IGNORECASE | re.DOTALL)
            for q_code, description in q_matches:
                # Clean up the description
                clean_desc = ' '.join(description.strip().split())
                quality_clauses[q_code.upper()] = clean_desc[:100]  # Limit length
                
            # Also look for standalone Q# codes with descriptions on next lines
            standalone_matches = re.findall(r"(Q\d+)\s*([A-Z][A-Z\s,\[\]()]{10,50})", text, re.IGNORECASE)
            for q_code, description in standalone_matches:
                if q_code.upper() not in quality_clauses:
                    clean_desc = ' '.join(description.strip().split())
                    quality_clauses[q_code.upper()] = clean_desc[:100]
        return quality_clauses
    
    def _extract_filemaker_data_with_ai(self, results: Dict[str, Any], po_number: str) -> Dict[str, Any]:
        """Use Ollama AI to extract FileMaker data from PDF text"""
        # Combine text from first 2 pages (PO pages)
        combined_text = ""
        for page in results["pages"][:2]:  # Only first 2 pages for PO data
            text = page.get("text", "") or page.get("ocr_text", "")
            if text:
                combined_text += f"\n--- PAGE {page['page_number']} ---\n{text}"
        
        if not combined_text.strip():
            self.logger.warning("No text available for AI extraction")
            return self._fallback_regex_extraction(results, po_number)

        # Cap text length to avoid model/context crashes
        max_chars = int(os.getenv("OLLAMA_MAX_CHARS", "6000"))
        if len(combined_text) > max_chars:
            self.logger.info(f"Truncating AI input text from {len(combined_text)} to {max_chars} chars")
            combined_text = combined_text[:max_chars]
        
        # Try Ollama first, fallback to regex if not available
        try:
            ai_extracted = self._query_ollama_for_extraction(combined_text, po_number)
            if ai_extracted:
                self.logger.info("✅ Used Ollama AI for data extraction")
                # Post-process AI-extracted data for FileMaker formatting
                return self._format_ai_data_for_filemaker(ai_extracted)
        except Exception as e:
            self.logger.warning(f"Ollama AI extraction failed: {e}")
        
        # Fallback to regex extraction
        self.logger.info("📝 Using regex fallback for data extraction")
        return self._fallback_regex_extraction(results, po_number)

    def _format_ai_data_for_filemaker(self, ai_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format AI-extracted data to meet FileMaker requirements"""
        if not ai_data:
            return ai_data
            
        # Format part number: change dash-OP to asterisk-OP
        if "PART_NUMBER" in ai_data:
            ai_data["PART_NUMBER"] = self._format_part_number_for_filemaker(ai_data["PART_NUMBER"])
        
        # Format quantity: convert to whole number
        if "QTY_SHIP" in ai_data:
            try:
                qty = ai_data["QTY_SHIP"]
                if isinstance(qty, str) and qty:
                    ai_data["QTY_SHIP"] = str(int(float(qty)))
            except (ValueError, TypeError):
                pass  # Keep original if conversion fails
                
        return ai_data
    
    def _query_ollama_for_extraction(self, text: str, po_number: str) -> Dict[str, Any]:
        """Query Ollama to extract structured data from PO text"""
        import json
        import urllib.request
        import urllib.error
        
        # Check if Ollama is available (default port 11434)
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        
        prompt = f"""Extract the following information from this Purchase Order document text and return it as valid JSON:

Required FileMaker Fields:
- Whittaker_Shipper: PO number (10 digits starting with 45) - should be {po_number}
- MJO_NO: Production Order number (look for "Production Order:")
- QTY_SHIP: Quantity shipped (number near "EA" or "Quantity")  
- PART_NUMBER: Part number with OP code (format: "123456-ABC*OP20")
- Promise_Delivery_Date: Delivery date (MM/DD/YYYY format)
- DPAS_Rating: DPAS rating if present
- Payment_Terms_Flag: "STANDARD: 30 Days" or "NON_STANDARD: [terms]"
- Quality_Clauses: Object with Q# codes and descriptions

Additional fields:
- vendor: Company name from vendor address
- vendor_number: Vendor number
- date: PO date
- amount: Total amount/price
- buyer_name: Buyer name
- buyer_phone: Buyer phone
- buyer_email: Buyer email

Document Text:
{text}

Return only valid JSON with the extracted data. If a field is not found, use empty string "".
"""

        def _post_ollama(data: dict) -> dict:
            payload = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(
                f"{ollama_url}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=600) as resp:
                return json.loads(resp.read().decode("utf-8"))

        # First attempt: request structured JSON output
        try:
            result = _post_ollama({
                "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
                "prompt": prompt,
                "stream": False,
                "format": "json",
            })
        except urllib.error.HTTPError as he:
            # Retry without JSON formatting on server errors (often fixes 500s)
            if 500 <= he.code <= 599:
                self.logger.warning(f"Ollama 5xx error ({he.code}); retrying without JSON format")
                try:
                    retry_prompt = prompt + "\n\nReturn only valid JSON."
                    result = _post_ollama({
                        "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
                        "prompt": retry_prompt,
                        "stream": False,
                    })
                except Exception as e:
                    self.logger.warning(f"Ollama retry failed: {e}")
                    return None
            else:
                self.logger.warning(f"Ollama HTTP error: {he}")
                return None
        except (urllib.error.URLError, TimeoutError) as e:
            self.logger.warning(f"Cannot connect to Ollama: {e}")
            return None

        extracted_text = result.get("response", "")
        try:
            extracted_data = json.loads(extracted_text)
            self.logger.info(f"Ollama extracted {len(extracted_data)} fields")
            return extracted_data
        except json.JSONDecodeError:
            self.logger.warning("Ollama returned invalid JSON")
            return None
    
    def _fallback_regex_extraction(self, results: Dict[str, Any], po_number: str) -> Dict[str, Any]:
        """Fallback regex-based extraction for FileMaker data"""
        raw_part_number = self._extract_part_number_with_op(results)
        formatted_part_number = self._format_part_number_for_filemaker(raw_part_number)
        
        return {
            "Whittaker_Shipper": po_number,  # PO Number for FileMaker
            "MJO_NO": self._extract_production_order(results),      # Production Order
            "QTY_SHIP": self._extract_quantity_shipped(results),    # Quantity Shipped  
            "PART_NUMBER": formatted_part_number,  # Part Number with OP## formatted for FileMaker
            "Promise_Delivery_Date": self._extract_delivery_date(results),  # Promise Delivery Date
            "DPAS_Rating": self._extract_dpas_rating(results),      # DPAS Rating
            "Payment_Terms_Flag": self._check_payment_terms(results),  # Payment Terms Check
            "Quality_Clauses": self._extract_quality_clauses(results),  # Q# codes for Notes
            # Additional useful fields
            "vendor": self._extract_vendor(results),
            "vendor_number": self._extract_vendor_number(results),
            "date": self._extract_date(results),
            "amount": self._extract_amount(results),
            "buyer_name": self._extract_buyer_name(results),
            "buyer_phone": self._extract_buyer_phone(results),
            "buyer_email": self._extract_buyer_email(results)
        }
    
    def _process_with_pdfplumber(self, pdf_path: Path, output_dir: Path) -> Dict[str, Any]:
        """Process PDF using pdfplumber (fallback)"""
        import pdfplumber
        
        self.logger.info("Processing with pdfplumber...")
        
        results = {
            "source_file": str(pdf_path),
            "pages": [],
            "total_pages": 0,
            "backend": "pdfplumber",
            "total_text_length": 0,
            "total_images": 0
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            results["total_pages"] = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                
                page_result = {
                    "page_number": page_num + 1,
                    "text": text,
                    "text_length": len(text),
                    "images_found": len(page.images),
                    "has_text": bool(text.strip())
                }
                
                results["pages"].append(page_result)
                results["total_text_length"] += len(text)
                results["total_images"] += len(page.images)
                
                # Save page text
                text_file = output_dir / f"page_{page_num + 1:03d}.txt"
                text_file.write_text(text, encoding='utf-8')
        
        # Save combined text
        all_text = "\n\n--- PAGE BREAK ---\n\n".join([p["text"] for p in results["pages"]])
        combined_file = output_dir / f"{pdf_path.stem}_combined.txt"
        combined_file.write_text(all_text, encoding='utf-8')
        
        return results

    def sample_logging(self):
        self.logger.info("Sample logging statement added for demonstration purposes.")


def setup_environment():
    """Setup script for fixing PyMuPDF installation"""
    print("🔧 Setting up environment...")
    
    try:
        # Try to fix PyMuPDF installation
        print("📦 Fixing PyMuPDF installation...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "uninstall", "-y", "PyMuPDF", "fitz"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--no-cache-dir", "PyMuPDF==1.23.8"
        ])
        
        print("✅ PyMuPDF installation fixed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to fix PyMuPDF: {e}")
        return False


def main():
    """Main entry point"""
    if "--fix-deps" in sys.argv:
        setup_environment()
        return
    
    if "--health" in sys.argv:
        pipeline = UnifiedOCRPipeline()
        health = pipeline.health_check()
        print(json.dumps(health, indent=2))
        return
    
    # Initialize pipeline
    pipeline = UnifiedOCRPipeline()

    # Check if PDF file provided
    pdf_files = [arg for arg in sys.argv[1:] if arg.endswith('.pdf')]

    if pdf_files:
        for pdf_file in pdf_files:
            try:
                results = pipeline.process_pdf(pdf_file)
                print(f"\n✅ Processed: {pdf_file}")
                print(f"📄 Pages: {results['total_pages']}")
                print(f"📝 Text length: {results['total_text_length']} characters")
                print(f"🖼️  Images: {results['total_images']}")
                print(f"⏱️  Time: {results['processing_time_seconds']:.2f}s")
            except Exception as e:
                print(f"❌ Failed to process {pdf_file}: {e}")
    else:
        # Auto-process all PDFs in IncomingPW directory
        input_dir = os.getenv("OCR_INCOMING", "/app/IncomingPW")
        delete_source = os.getenv("DELETE_SOURCE_FILES", "true").lower() == "true"
        
        pdfs = list(Path(input_dir).glob("*.pdf"))
        if pdfs:
            print(f"Found {len(pdfs)} PDF(s) in {input_dir}. Processing one by one...")
            if delete_source:
                print("🗑️  Source files will be deleted after successful processing")
            
            for pdf_file in pdfs:
                try:
                    print(f"\n🔄 Processing: {pdf_file.name}")
                    results = pipeline.process_pdf(str(pdf_file))
                    po_number = results.get("po_number", "UNKNOWN")
                    
                    print(f"✅ Successfully processed: {pdf_file.name}")
                    print(f"📋 PO Number: {po_number}")
                    print(f"📄 Pages: {results['total_pages']}")
                    print(f"📝 Text length: {results['total_text_length']} characters")
                    print(f"🖼️  Images: {results['total_images']}")
                    print(f"⏱️  Time: {results['processing_time_seconds']:.2f}s")
                    
                    # Delete source file after successful processing
                    if delete_source:
                        try:
                            pdf_file.unlink()
                            print(f"🗑️  Deleted source file: {pdf_file.name}")
                        except Exception as delete_error:
                            print(f"⚠️  Could not delete {pdf_file.name}: {delete_error}")
                            
                except Exception as e:
                    print(f"❌ Failed to process {pdf_file.name}: {e}")
                    print(f"🔄 Continuing with next file...")
                    # Do not delete file if processing failed
                    
        else:
            print("No PDF files found in IncomingPW directory.")
            print("📋 Unified OCR Pipeline")
            print("Usage:")
            print("  python unified_ocr_pipeline.py file.pdf [file2.pdf ...]")
            print("  python unified_ocr_pipeline.py --health")
            print("  python unified_ocr_pipeline.py --fix-deps")
            print(f"\nInput folder: {input_dir}")
            print("Output folder: /volume1/Main/Main/ProcessedPOs")
            # Show health status
            health = pipeline.health_check()
            print(f"\n🏥 Status: {health['status']}")
            print(f"🔧 Backend: {health['pdf_backend']}")


if __name__ == "__main__":
    main()