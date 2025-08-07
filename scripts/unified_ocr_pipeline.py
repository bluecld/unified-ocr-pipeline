#!/usr/bin/env python3
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
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/app/ocr_pipeline.log'),
                logging.StreamHandler(sys.stdout)
            ]
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
            
        output_dir = Path(output_dir or pdf_path.parent / "ocr_output")
        output_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"Processing PDF: {pdf_path}")
        
        start_time = datetime.now()
        
        if self.pdf_backend == "pymupdf":
            results = self._process_with_pymupdf(pdf_path, output_dir)
        elif self.pdf_backend == "pdfplumber":
            results = self._process_with_pdfplumber(pdf_path, output_dir)
        else:
            raise Exception(f"Unknown backend: {self.pdf_backend}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        results["processing_time_seconds"] = processing_time
        results["timestamp"] = datetime.now().isoformat()
        
        # Save results
        results_file = output_dir / f"{pdf_path.stem}_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✅ Processing complete in {processing_time:.2f}s")
        return results
    
    def _process_with_pymupdf(self, pdf_path: Path, output_dir: Path) -> Dict[str, Any]:
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
            "total_images": 0
        }
        
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
            
            results["pages"].append(page_result)
            results["total_text_length"] += len(text)
            results["total_images"] += len(image_list)
            
            # Save individual page text
            text_file = output_dir / f"page_{page_num + 1:03d}.txt"
            text_file.write_text(text, encoding='utf-8')
            
            # Extract images if needed
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_file = output_dir / f"page_{page_num + 1:03d}_img_{img_index + 1:03d}.png"
                        pix.save(str(img_file))
                    pix = None
                except Exception as e:
                    self.logger.warning(f"Failed to extract image {img_index} from page {page_num + 1}: {e}")
        
        doc.close()
        
        # Save combined text
        all_text = "\n\n--- PAGE BREAK ---\n\n".join([p["text"] for p in results["pages"]])
        combined_file = output_dir / f"{pdf_path.stem}_combined.txt"
        combined_file.write_text(all_text, encoding='utf-8')
        
        return results
    
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
        # Auto-process all PDFs in input directory
        input_dir = os.getenv("OCR_INCOMING", "/app/input")
        pdfs = list(Path(input_dir).glob("*.pdf"))
        if pdfs:
            print(f"Found {len(pdfs)} PDF(s) in {input_dir}. Starting processing...")
            for pdf_file in pdfs:
                try:
                    results = pipeline.process_pdf(str(pdf_file))
                    print(f"\n✅ Processed: {pdf_file}")
                    print(f"� Pages: {results['total_pages']}")
                    print(f"📝 Text length: {results['total_text_length']} characters")
                    print(f"🖼️  Images: {results['total_images']}")
                    print(f"⏱️  Time: {results['processing_time_seconds']:.2f}s")
                except Exception as e:
                    print(f"❌ Failed to process {pdf_file}: {e}")
        else:
            print("No PDF files found in input directory.")
            print("�📋 Unified OCR Pipeline")
            print("Usage:")
            print("  python unified_ocr_pipeline.py file.pdf [file2.pdf ...]")
            print("  python unified_ocr_pipeline.py --health")
            print("  python unified_ocr_pipeline.py --fix-deps")
            # Show health status
            health = pipeline.health_check()
            print(f"\n🏥 Status: {health['status']}")
            print(f"🔧 Backend: {health['pdf_backend']}")


if __name__ == "__main__":
    main()