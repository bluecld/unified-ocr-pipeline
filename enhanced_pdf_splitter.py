#!/usr/bin/env python3
"""
Enhanced PDF Splitting System for OCR Pipeline
Provides multiple detection methods with confidence scoring for accurate PO/Router separation
"""

import fitz  # PyMuPDF
import re
import os
import logging
from typing import Optional, Tuple, List, Dict, NamedTuple
from dataclasses import dataclass
from pathlib import Path
import subprocess

logger = logging.getLogger(__name__)

@dataclass
class DetectionResult:
    """Result from a detection method"""
    page_num: int
    confidence: float
    method: str
    evidence: str
    details: Dict = None

class EnhancedPDFSplitter:
    """
    Advanced PDF splitter with multiple detection strategies and confidence scoring
    
    Features:
    - Multi-method detection (text patterns, layout analysis, content transitions)
    - Confidence scoring with configurable thresholds
    - "Page X of Y" detection for accurate PO length determination
    - OCR fallback for scanned documents
    - Detailed logging and evidence tracking
    - Graceful degradation and fallback strategies
    """
    
    def __init__(self):
        # Enhanced router detection patterns by strength
        self.router_patterns = {
            'very_strong': [
                r'routing\s+sheet',
                r'manufacturing\s+routing',
                r'work\s+order\s+routing',
                r'router\s+sheet',
                r'process\s+routing\s+sheet'
            ],
            'strong': [
                r'operation\s+sheet',
                r'process\s+sheet',
                r'routing\s+instructions',
                r'work\s+instructions',
                r'manufacturing\s+instructions'
            ],
            'medium': [
                r'\brouter\b',
                r'routing',
                r'operation\s+sequence',
                r'job\s+routing',
                r'process\s+flow'
            ],
            'weak': [
                r'op\s*\d+',
                r'operation\s+\d+',
                r'setup\s+time',
                r'cycle\s+time',
                r'machine\s+center',
                r'work\s+center'
            ]
        }
        
        # PO-specific patterns (should decrease in router section)
        self.po_patterns = [
            r'purchase\s+order',
            r'po\s+number',
            r'vendor\s+name',
            r'ship\s+to',
            r'bill\s+to',
            r'payment\s+terms',
            r'delivery\s+date',
            r'quantity\s+ordered',
            r'unit\s+price',
            r'total\s+amount'
        ]
        
        # Page numbering patterns for PO length detection
        self.page_patterns = [
            r'page\s+1\s+of\s+(\d+)',           # "Page 1 of 3"
            r'page\s*1\s*of\s*(\d+)',           # "Page1of3"
            r'page\s+1\s*/\s*(\d+)',            # "Page 1/3"
            r'1\s+of\s+(\d+)\s+pages?',         # "1 of 3 pages"
            r'\b1\s*[/|-]\s*(\d+)\b',          # "1/3" or "1-3"
        ]
        
        # OCR-tolerant page patterns (for scanned documents)
        self.ocr_page_patterns = [
            r'page\s*[il1|]\s*of?\s*(\d+)',     # OCR might read "1" as "l" or "|"
            r'page\s*[\dilo|]+\s*of\s*(\d+)',   # Multiple OCR variations
            r'[il1|]\s*of\s*(\d+)\s*page',      # Different word order
        ]
    
    def extract_text_with_ocr_fallback(self, pdf_path: str, page_num: int = 0) -> str:
        """
        Extract text from a specific page with OCR fallback for scanned documents
        """
        try:
            # Try direct text extraction first
            doc = fitz.open(pdf_path)
            if page_num < len(doc):
                page = doc[page_num]
                text = page.get_text()
                doc.close()
                
                # If we have substantial text, use it
                if len(text.strip()) > 50:
                    return text
                
                # Otherwise, try OCR on this page
                return self.ocr_single_page(pdf_path, page_num)
            
            doc.close()
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting text from page {page_num}: {e}")
            return ""
    
    def ocr_single_page(self, pdf_path: str, page_num: int) -> str:
        """
        OCR a single page for text extraction
        """
        try:
            # Create temporary single-page PDF
            doc = fitz.open(pdf_path)
            if page_num >= len(doc):
                doc.close()
                return ""
            
            temp_pdf = Path(pdf_path).parent / f"temp_page_{page_num}.pdf"
            single_page_doc = fitz.open()
            single_page_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            single_page_doc.save(str(temp_pdf))
            single_page_doc.close()
            doc.close()
            
            # OCR the single page
            temp_ocr = temp_pdf.with_suffix('.ocr.pdf')
            cmd = [
                "ocrmypdf", "--force-ocr", "--rotate-pages", "--deskew",
                "--tesseract-timeout", "30", str(temp_pdf), str(temp_ocr)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Extract text from OCR'd PDF
                ocr_doc = fitz.open(str(temp_ocr))
                text = ocr_doc[0].get_text()
                ocr_doc.close()
                
                # Cleanup
                temp_pdf.unlink(missing_ok=True)
                temp_ocr.unlink(missing_ok=True)
                
                return text
            
            # Cleanup on failure
            temp_pdf.unlink(missing_ok=True)
            temp_ocr.unlink(missing_ok=True)
            return ""
            
        except Exception as e:
            logger.error(f"OCR failed for page {page_num}: {e}")
            return ""
    
    def detect_po_length_from_page_indicators(self, pdf_path: str) -> Optional[int]:
        """
        Detect PO section length using "Page 1 of N" indicators
        Returns the number of PO pages, or None if not found
        """
        try:
            # Extract text from first page with OCR fallback
            first_page_text = self.extract_text_with_ocr_fallback(pdf_path, 0)
            
            if not first_page_text:
                return None
            
            # Try standard page patterns first
            for pattern in self.page_patterns:
                match = re.search(pattern, first_page_text, re.IGNORECASE)
                if match:
                    total_pages = int(match.group(1))
                    logger.info(f"Found page indicator: 'Page 1 of {total_pages}'")
                    return total_pages
            
            # Try OCR-tolerant patterns for scanned documents
            for pattern in self.ocr_page_patterns:
                match = re.search(pattern, first_page_text, re.IGNORECASE)
                if match:
                    total_pages = int(match.group(1))
                    logger.info(f"Found OCR page indicator: {total_pages} pages")
                    return total_pages
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting PO length: {e}")
            return None
    
    def detect_by_text_patterns(self, pdf_path: str) -> List[DetectionResult]:
        """
        Method 1: Enhanced text pattern detection with confidence scoring
        """
        results = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                text = self.extract_text_with_ocr_fallback(pdf_path, page_num).lower()
                
                if not text.strip():
                    continue
                
                confidence = 0.0
                evidence_parts = []
                pattern_counts = {}
                
                # Check patterns by strength
                for strength, patterns in self.router_patterns.items():
                    for pattern in patterns:
                        matches = len(re.findall(pattern, text, re.IGNORECASE))
                        if matches > 0:
                            # Weight by pattern strength
                            weight = {
                                'very_strong': 0.5,
                                'strong': 0.3,
                                'medium': 0.2,
                                'weak': 0.1
                            }[strength]
                            
                            confidence += matches * weight
                            evidence_parts.append(f"{strength}:{pattern}({matches})")
                            pattern_counts[pattern] = matches
                
                # Penalty for PO patterns still being present
                po_indicators = 0
                for pattern in self.po_patterns:
                    po_matches = len(re.findall(pattern, text, re.IGNORECASE))
                    po_indicators += po_matches
                
                if po_indicators > 3:
                    confidence -= 0.2
                    evidence_parts.append(f"po_penalty:{po_indicators}")
                
                # Bonus for multiple different patterns
                if len(pattern_counts) > 2:
                    confidence += 0.1
                    evidence_parts.append("pattern_diversity_bonus")
                
                if confidence > 0.3:  # Minimum threshold
                    results.append(DetectionResult(
                        page_num=page_num,
                        confidence=min(confidence, 1.0),  # Cap at 1.0
                        method="text_patterns",
                        evidence=" | ".join(evidence_parts),
                        details={"pattern_counts": pattern_counts, "po_indicators": po_indicators}
                    ))
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Text pattern detection failed: {e}")
        
        return results
    
    def detect_by_layout_analysis(self, pdf_path: str) -> List[DetectionResult]:
        """
        Method 2: Layout and structure analysis
        """
        results = []
        
        try:
            doc = fitz.open(pdf_path)
            prev_page_info = None
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Analyze page layout
                page_info = {
                    'width': page.rect.width,
                    'height': page.rect.height,
                    'orientation': 'landscape' if page.rect.width > page.rect.height else 'portrait'
                }
                
                # Get text blocks with positioning
                text_dict = page.get_text("dict")
                text_blocks = []
                fonts = []
                sizes = []
                
                for block in text_dict.get("blocks", []):
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text_blocks.append({
                                    'text': span['text'],
                                    'bbox': span['bbox'],
                                    'font': span['font'],
                                    'size': span['size']
                                })
                                fonts.append(span['font'])
                                sizes.append(span['size'])
                
                if text_blocks:
                    page_info['dominant_font'] = max(set(fonts), key=fonts.count) if fonts else None
                    page_info['avg_font_size'] = sum(sizes) / len(sizes) if sizes else 0
                    page_info['text_block_count'] = len(text_blocks)
                    page_info['font_variety'] = len(set(fonts))
                
                confidence = 0.0
                evidence_parts = []
                
                if prev_page_info:
                    # Check for significant layout changes
                    if page_info['orientation'] != prev_page_info['orientation']:
                        confidence += 0.6
                        evidence_parts.append("orientation_change")
                    
                    # Font size changes
                    if 'avg_font_size' in page_info and 'avg_font_size' in prev_page_info:
                        size_diff = abs(page_info['avg_font_size'] - prev_page_info['avg_font_size'])
                        if size_diff > 2:
                            confidence += 0.4
                            evidence_parts.append(f"font_size_change:{size_diff:.1f}")
                    
                    # Font type changes
                    if (page_info.get('dominant_font') != prev_page_info.get('dominant_font') and
                        page_info.get('dominant_font') and prev_page_info.get('dominant_font')):
                        confidence += 0.3
                        evidence_parts.append("font_type_change")
                    
                    # Text density changes
                    if 'text_block_count' in page_info and 'text_block_count' in prev_page_info:
                        density_change = (page_info['text_block_count'] - prev_page_info['text_block_count']) / max(prev_page_info['text_block_count'], 1)
                        if density_change < -0.4:  # Significant decrease
                            confidence += 0.3
                            evidence_parts.append(f"text_density_drop:{density_change:.2f}")
                
                if confidence > 0.4:
                    results.append(DetectionResult(
                        page_num=page_num,
                        confidence=min(confidence, 1.0),
                        method="layout_analysis",
                        evidence=" | ".join(evidence_parts),
                        details=page_info
                    ))
                
                prev_page_info = page_info
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Layout analysis failed: {e}")
        
        return results
    
    def detect_by_content_transition(self, pdf_path: str) -> List[DetectionResult]:
        """
        Method 3: Content transition analysis
        """
        results = []
        
        try:
            doc = fitz.open(pdf_path)
            page_contents = []
            
            # Analyze content for each page
            for page_num in range(len(doc)):
                text = self.extract_text_with_ocr_fallback(pdf_path, page_num).lower()
                
                content_score = {
                    'po_content': 0,
                    'router_content': 0,
                    'numeric_ops': len(re.findall(r'op\s*\d+|operation\s+\d+', text, re.IGNORECASE)),
                    'time_references': len(re.findall(r'setup|cycle|run\s+time|minutes?|hours?', text, re.IGNORECASE)),
                    'machine_references': len(re.findall(r'machine|center|station|mill|lathe|drill', text, re.IGNORECASE)),
                    'measurements': len(re.findall(r'\d+\.?\d*\s*(?:in|inches|mm|cm)', text, re.IGNORECASE))
                }
                
                # Score PO content
                for pattern in self.po_patterns:
                    content_score['po_content'] += len(re.findall(pattern, text, re.IGNORECASE))
                
                # Score router content (weighted by strength)
                for strength, patterns in self.router_patterns.items():
                    weight = {'very_strong': 4, 'strong': 3, 'medium': 2, 'weak': 1}[strength]
                    for pattern in patterns:
                        content_score['router_content'] += len(re.findall(pattern, text, re.IGNORECASE)) * weight
                
                page_contents.append(content_score)
            
            # Analyze transitions between pages
            for i in range(1, len(page_contents)):
                prev_content = page_contents[i-1]
                curr_content = page_contents[i]
                
                confidence = 0.0
                evidence_parts = []
                
                # Major content shift from PO to router
                po_drop = prev_content['po_content'] - curr_content['po_content']
                router_rise = curr_content['router_content'] - prev_content['router_content']
                
                if po_drop > 2 and router_rise > 3:
                    confidence += 0.7
                    evidence_parts.append(f"content_shift:po_drop={po_drop},router_rise={router_rise}")
                
                # Increase in technical content
                if curr_content['numeric_ops'] > prev_content['numeric_ops'] + 1:
                    confidence += 0.3
                    evidence_parts.append(f"ops_increase:{curr_content['numeric_ops']}")
                
                if curr_content['time_references'] > prev_content['time_references']:
                    confidence += 0.2
                    evidence_parts.append("time_refs_appear")
                
                if curr_content['machine_references'] > prev_content['machine_references']:
                    confidence += 0.2
                    evidence_parts.append("machine_refs_increase")
                
                if curr_content['measurements'] > prev_content['measurements']:
                    confidence += 0.1
                    evidence_parts.append("measurements_increase")
                
                if confidence > 0.5:
                    results.append(DetectionResult(
                        page_num=i,
                        confidence=min(confidence, 1.0),
                        method="content_transition",
                        evidence=" | ".join(evidence_parts),
                        details={'prev_content': prev_content, 'curr_content': curr_content}
                    ))
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Content transition analysis failed: {e}")
        
        return results
    
    def find_optimal_split_point(self, pdf_path: str) -> Tuple[Optional[int], float, str]:
        """
        Combine all detection methods to find the best split point
        Returns (page_number, confidence, explanation)
        """
        logger.info("Running comprehensive PDF split point detection...")
        
        # First, check for "Page 1 of N" indicator
        po_length = self.detect_po_length_from_page_indicators(pdf_path)
        
        if po_length is not None:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            doc.close()
            
            if total_pages > po_length:
                # Router starts after PO pages
                explanation = f"Page {po_length + 1} based on 'Page 1 of {po_length}' indicator (confidence: 1.0)"
                logger.info(f"Using page indicator: {explanation}")
                return po_length, 1.0, explanation
            else:
                explanation = f"Document contains only PO pages ({po_length} pages, no router section)"
                logger.info(explanation)
                return None, 1.0, explanation
        
        # Fall back to multi-method detection
        logger.info("No page indicator found, using multi-method detection...")
        
        # Run all detection methods
        text_results = self.detect_by_text_patterns(pdf_path)
        layout_results = self.detect_by_layout_analysis(pdf_path)
        content_results = self.detect_by_content_transition(pdf_path)
        
        all_results = text_results + layout_results + content_results
        
        if not all_results:
            logger.warning("No split points detected by any method")
            return None, 0.0, "No router section detected by any method"
        
        # Group results by page number and calculate combined confidence
        page_scores = {}
        for result in all_results:
            page_num = result.page_num
            if page_num not in page_scores:
                page_scores[page_num] = {
                    'total_confidence': 0.0,
                    'method_count': 0,
                    'methods': [],
                    'evidence': [],
                    'details': []
                }
            
            page_scores[page_num]['total_confidence'] += result.confidence
            page_scores[page_num]['method_count'] += 1
            page_scores[page_num]['methods'].append(result.method)
            page_scores[page_num]['evidence'].append(f"{result.method}: {result.evidence}")
            if result.details:
                page_scores[page_num]['details'].append(result.details)
        
        # Find the best candidate
        best_page = None
        best_confidence = 0.0
        best_explanation = ""
        
        for page_num, score_info in page_scores.items():
            # Average confidence across methods, with bonus for multiple methods
            avg_confidence = score_info['total_confidence'] / score_info['method_count']
            method_bonus = (len(set(score_info['methods'])) - 1) * 0.1  # Bonus for method agreement
            final_confidence = avg_confidence + method_bonus
            
            if final_confidence > best_confidence:
                best_confidence = final_confidence
                best_page = page_num
                best_explanation = (f"Page {page_num + 1} (confidence: {final_confidence:.2f}, "
                                  f"methods: {score_info['method_count']}): " + 
                                  " | ".join(score_info['evidence']))
        
        logger.info(f"Best split point: {best_explanation}")
        return best_page, best_confidence, best_explanation
    
    def split_pdf_enhanced(self, input_pdf: str, po_pdf: str, router_pdf: str, 
                          min_confidence: float = 0.7) -> Tuple[bool, str]:
        """
        Enhanced PDF splitting with comprehensive detection
        Returns (success, explanation)
        """
        try:
            split_point, confidence, explanation = self.find_optimal_split_point(input_pdf)
            
            doc = fitz.open(input_pdf)
            total_pages = len(doc)
            
            if split_point is None or confidence < min_confidence:
                # Treat entire document as PO
                po_doc = fitz.open()
                po_doc.insert_pdf(doc)
                po_doc.save(po_pdf)
                po_doc.close()
                doc.close()
                
                result_explanation = f"No confident split point found (confidence: {confidence:.2f} < {min_confidence}), saved entire document as PO"
                logger.info(result_explanation)
                return True, result_explanation
            
            # Split the document
            po_doc = fitz.open()
            router_doc = fitz.open()
            
            # PO section: pages 0 to split_point-1
            if split_point > 0:
                po_doc.insert_pdf(doc, from_page=0, to_page=split_point-1)
                po_doc.save(po_pdf)
                logger.info(f"PO section saved (pages 1-{split_point}): {po_pdf}")
            
            # Router section: pages split_point to end
            if split_point < total_pages:
                router_doc.insert_pdf(doc, from_page=split_point, to_page=total_pages-1)
                router_doc.save(router_pdf)
                logger.info(f"Router section saved (pages {split_point+1}-{total_pages}): {router_pdf}")
            
            po_doc.close()
            router_doc.close()
            doc.close()
            
            result_explanation = f"Successfully split at {explanation}"
            logger.info(result_explanation)
            return True, result_explanation
            
        except Exception as e:
            error_msg = f"Enhanced PDF splitting failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

def main():
    """Test the enhanced splitter"""
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python enhanced_pdf_splitter.py input.pdf output_po.pdf output_router.pdf")
        sys.exit(1)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    splitter = EnhancedPDFSplitter()
    success, explanation = splitter.split_pdf_enhanced(sys.argv[1], sys.argv[2], sys.argv[3])
    
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"Explanation: {explanation}")

if __name__ == "__main__":
    main()