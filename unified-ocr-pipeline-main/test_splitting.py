#!/usr/bin/env python3
"""
Test Framework for PDF Splitting Improvements
Tests the improved splitting against sample PDFs and compares results
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from improved_pdf_splitting import ImprovedPDFSplitter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SplittingTester:
    """Test framework for PDF splitting improvements"""
    
    def __init__(self, test_dir: str = "test_pdfs"):
        self.test_dir = Path(test_dir)
        self.test_dir.mkdir(exist_ok=True)
        self.results_dir = Path("test_results")  
        self.results_dir.mkdir(exist_ok=True)
        self.splitter = ImprovedPDFSplitter()
        
    def create_test_report(self, pdf_file: Path, confidence_levels: List[float]) -> Dict:
        """Test splitting at different confidence levels"""
        logger.info(f"Testing {pdf_file.name} at confidence levels: {confidence_levels}")
        
        test_results = {
            'pdf_file': str(pdf_file),
            'test_timestamp': datetime.now().isoformat(),
            'confidence_tests': []
        }
        
        for confidence in confidence_levels:
            logger.info(f"Testing confidence level: {confidence}")
            
            # Run split point detection
            split_point, actual_confidence, explanation = self.splitter.find_optimal_split_point(str(pdf_file))
            
            # Determine if split would occur at this confidence level
            would_split = split_point is not None and actual_confidence >= confidence
            
            test_result = {
                'confidence_threshold': confidence,
                'detected_split_point': split_point,
                'actual_confidence': actual_confidence,
                'would_split': would_split,
                'explanation': explanation
            }
            
            test_results['confidence_tests'].append(test_result)
            
            logger.info(f"Confidence {confidence}: {'SPLIT' if would_split else 'NO SPLIT'} "
                       f"(page {split_point + 1 if split_point else 'N/A'}, confidence: {actual_confidence:.2f})")
        
        return test_results
    
    def test_single_pdf(self, pdf_path: str, confidence: float = 0.7) -> Dict:
        """Test splitting on a single PDF"""
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        logger.info(f"Testing PDF splitting: {pdf_file.name}")
        
        # Create output files
        output_dir = self.results_dir / f"test_{pdf_file.stem}_{datetime.now().strftime('%H%M%S')}"
        output_dir.mkdir(exist_ok=True)
        
        po_file = output_dir / f"{pdf_file.stem}_PO.pdf"
        router_file = output_dir / f"{pdf_file.stem}_ROUTER.pdf"
        
        # Run the improved splitting
        success, explanation = self.splitter.split_pdf_enhanced(
            str(pdf_file), str(po_file), str(router_file), 
            min_confidence=confidence
        )
        
        # Collect results
        result = {
            'input_file': str(pdf_file),
            'output_dir': str(output_dir),
            'confidence_threshold': confidence,
            'success': success,
            'explanation': explanation,
            'po_file_created': po_file.exists(),
            'router_file_created': router_file.exists(),
            'po_file_size': po_file.stat().st_size if po_file.exists() else 0,
            'router_file_size': router_file.stat().st_size if router_file.exists() else 0
        }
        
        # Save test result
        result_file = output_dir / "test_result.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Test complete: {explanation}")
        logger.info(f"Results saved to: {output_dir}")
        
        return result
    
    def batch_test_directory(self, pdf_dir: str, confidence_levels: List[float] = None) -> List[Dict]:
        """Test all PDFs in a directory"""
        if confidence_levels is None:
            confidence_levels = [0.5, 0.6, 0.7, 0.8, 0.9]
        
        pdf_dir = Path(pdf_dir)
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_dir}")
            return []
        
        logger.info(f"Batch testing {len(pdf_files)} PDFs with confidence levels: {confidence_levels}")
        
        all_results = []
        
        for pdf_file in pdf_files:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Testing: {pdf_file.name}")
                logger.info(f"{'='*60}")
                
                test_result = self.create_test_report(pdf_file, confidence_levels)
                all_results.append(test_result)
                
            except Exception as e:
                logger.error(f"Error testing {pdf_file}: {e}")
                error_result = {
                    'pdf_file': str(pdf_file),
                    'error': str(e),
                    'test_timestamp': datetime.now().isoformat()
                }
                all_results.append(error_result)
        
        # Save batch results
        batch_result_file = self.results_dir / f"batch_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(batch_result_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        logger.info(f"\nBatch test complete. Results saved to: {batch_result_file}")
        return all_results
    
    def compare_methods(self, pdf_path: str) -> Dict:
        """Compare all three detection methods on a single PDF"""
        pdf_file = Path(pdf_path)
        
        logger.info(f"Comparing detection methods for: {pdf_file.name}")
        
        # Run each method individually
        text_results = self.splitter.detect_by_text_patterns(str(pdf_file))
        layout_results = self.splitter.detect_by_layout_analysis(str(pdf_file))
        content_results = self.splitter.detect_by_content_transition(str(pdf_file))
        
        comparison = {
            'pdf_file': str(pdf_file),
            'test_timestamp': datetime.now().isoformat(),
            'text_pattern_results': [
                {
                    'page': r.page_num + 1,
                    'confidence': r.confidence,
                    'evidence': r.evidence
                } for r in text_results
            ],
            'layout_analysis_results': [
                {
                    'page': r.page_num + 1, 
                    'confidence': r.confidence,
                    'evidence': r.evidence
                } for r in layout_results
            ],
            'content_transition_results': [
                {
                    'page': r.page_num + 1,
                    'confidence': r.confidence, 
                    'evidence': r.evidence
                } for r in content_results
            ]
        }
        
        # Save comparison
        comparison_file = self.results_dir / f"method_comparison_{pdf_file.stem}_{datetime.now().strftime('%H%M%S')}.json"
        with open(comparison_file, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        logger.info(f"Method comparison saved to: {comparison_file}")
        
        # Print summary
        print(f"\n📊 DETECTION METHOD COMPARISON - {pdf_file.name}")
        print("=" * 60)
        print(f"Text Patterns: {len(text_results)} candidates found")
        for r in text_results:
            print(f"  Page {r.page_num + 1}: {r.confidence:.2f} - {r.evidence}")
        
        print(f"\nLayout Analysis: {len(layout_results)} candidates found")  
        for r in layout_results:
            print(f"  Page {r.page_num + 1}: {r.confidence:.2f} - {r.evidence}")
        
        print(f"\nContent Transition: {len(content_results)} candidates found")
        for r in content_results:
            print(f"  Page {r.page_num + 1}: {r.confidence:.2f} - {r.evidence}")
        
        return comparison

def main():
    """Main test runner"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_splitting.py single <pdf_file> [confidence]")
        print("  python test_splitting.py batch <pdf_directory>")
        print("  python test_splitting.py compare <pdf_file>")
        print("  python test_splitting.py report <pdf_file>")
        sys.exit(1)
    
    command = sys.argv[1]
    tester = SplittingTester()
    
    if command == "single":
        if len(sys.argv) < 3:
            print("Error: PDF file path required")
            sys.exit(1)
        
        pdf_path = sys.argv[2]
        confidence = float(sys.argv[3]) if len(sys.argv) > 3 else 0.7
        
        result = tester.test_single_pdf(pdf_path, confidence)
        print(f"\n✅ Test Result: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"📄 Explanation: {result['explanation']}")
        
    elif command == "batch":
        if len(sys.argv) < 3:
            print("Error: PDF directory path required")
            sys.exit(1)
        
        pdf_dir = sys.argv[2]
        results = tester.batch_test_directory(pdf_dir)
        print(f"\n✅ Batch test completed. Tested {len(results)} files.")
        
    elif command == "compare":
        if len(sys.argv) < 3:
            print("Error: PDF file path required")
            sys.exit(1)
        
        pdf_path = sys.argv[2]
        tester.compare_methods(pdf_path)
        
    elif command == "report":
        if len(sys.argv) < 3:
            print("Error: PDF file path required")
            sys.exit(1)
        
        pdf_path = sys.argv[2]
        confidence_levels = [0.5, 0.6, 0.7, 0.8, 0.9]
        result = tester.create_test_report(Path(pdf_path), confidence_levels)
        
        print(f"\n📊 CONFIDENCE LEVEL REPORT - {Path(pdf_path).name}")
        print("=" * 60)
        for test in result['confidence_tests']:
            threshold = test['confidence_threshold']
            would_split = test['would_split']
            split_point = test['detected_split_point']
            confidence = test['actual_confidence']
            
            status = "SPLIT" if would_split else "NO SPLIT"
            page_info = f"page {split_point + 1}" if split_point else "N/A"
            print(f"Confidence {threshold}: {status:8} ({page_info}, actual: {confidence:.2f})")
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()