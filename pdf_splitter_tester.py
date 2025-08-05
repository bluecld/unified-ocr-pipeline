#!/usr/bin/env python3
"""
Comprehensive Testing Framework for Enhanced PDF Splitting
Tests the improved splitting against various document types and scenarios
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import tempfile
import shutil

# Assuming the enhanced splitter is available
try:
    from enhanced_pdf_splitter import EnhancedPDFSplitter, DetectionResult
except ImportError:
    print("Error: enhanced_pdf_splitter.py not found. Please ensure it's in the same directory.")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFSplittingTester:
    """Comprehensive testing framework for PDF splitting improvements"""
    
    def __init__(self, test_dir: str = "test_results"):
        self.test_dir = Path(test_dir)
        self.test_dir.mkdir(exist_ok=True)
        self.splitter = EnhancedPDFSplitter()
        
        # Test scenarios with expected results
        self.test_scenarios = {
            'page_indicator_simple': {
                'description': 'PDF with clear "Page 1 of N" indicator',
                'expected_method': 'page_indicator',
                'expected_confidence': 1.0
            },
            'router_keywords': {
                'description': 'PDF with router section keywords',
                'expected_method': 'text_patterns',
                'min_confidence': 0.6
            },
            'layout_change': {
                'description': 'PDF with orientation or font changes',
                'expected_method': 'layout_analysis',
                'min_confidence': 0.5
            },
            'content_transition': {
                'description': 'PDF with content shift from PO to router',
                'expected_method': 'content_transition',
                'min_confidence': 0.5
            },
            'no_router_section': {
                'description': 'PDF with only PO content (no router)',
                'expected_split': None,
                'expected_confidence': 0.0
            },
            'scanned_document': {
                'description': 'Scanned PDF requiring OCR',
                'expected_method': 'any',
                'min_confidence': 0.3
            }
        }
    
    def create_test_report(self, pdf_file: Path, confidence_levels: List[float] = None) -> Dict:
        """Test splitting at different confidence levels"""
        if confidence_levels is None:
            confidence_levels = [0.3, 0.5, 0.7, 0.8, 0.9]
        
        logger.info(f"Testing {pdf_file.name} at confidence levels: {confidence_levels}")
        
        test_results = {
            'pdf_file': str(pdf_file),
            'file_size_mb': pdf_file.stat().st_size / (1024 * 1024),
            'test_timestamp': datetime.now().isoformat(),
            'confidence_tests': [],
            'method_analysis': {}
        }
        
        # Run detection methods individually for analysis
        try:
            split_point, actual_confidence, explanation = self.splitter.find_optimal_split_point(str(pdf_file))
            
            # Get detailed method results
            text_results = self.splitter.detect_by_text_patterns(str(pdf_file))
            layout_results = self.splitter.detect_by_layout_analysis(str(pdf_file))
            content_results = self.splitter.detect_by_content_transition(str(pdf_file))
            
            test_results['method_analysis'] = {
                'text_patterns': [
                    {
                        'page': r.page_num + 1,
                        'confidence': r.confidence,
                        'evidence': r.evidence
                    } for r in text_results
                ],
                'layout_analysis': [
                    {
                        'page': r.page_num + 1,
                        'confidence': r.confidence,
                        'evidence': r.evidence
                    } for r in layout_results
                ],
                'content_transition': [
                    {
                        'page': r.page_num + 1,
                        'confidence': r.confidence,
                        'evidence': r.evidence
                    } for r in content_results
                ]
            }
            
            # Test at different confidence levels
            for confidence in confidence_levels:
                would_split = split_point is not None and actual_confidence >= confidence
                
                test_result = {
                    'confidence_threshold': confidence,
                    'detected_split_point': split_point,
                    'actual_confidence': actual_confidence,
                    'would_split': would_split,
                    'split_page': split_point + 1 if split_point is not None else None,
                    'explanation': explanation
                }
                
                test_results['confidence_tests'].append(test_result)
                
                logger.info(f"Confidence {confidence}: {'SPLIT' if would_split else 'NO SPLIT'} "
                           f"(page {split_point + 1 if split_point else 'N/A'}, confidence: {actual_confidence:.2f})")
        
        except Exception as e:
            logger.error(f"Error