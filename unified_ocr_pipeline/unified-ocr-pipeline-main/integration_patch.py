#!/usr/bin/env python3
"""
Safe Integration Patch for Improved PDF Splitting
Creates a patched version of unified_ocr_pipeline.py with improved splitting
"""

import re
import shutil
from pathlib import Path

def create_patched_pipeline():
    """Create a patched version of the pipeline with improved splitting"""
    
    # Read the original file
    with open('unified_ocr_pipeline.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create backup
    shutil.copy('unified_ocr_pipeline.py', 'unified_ocr_pipeline.py.backup')
    
    # Find and replace the split_po_router method
    # Pattern to match the method definition and its content
    pattern = r'(def split_po_router\(self, input_pdf: str, po_pdf: str, router_pdf: str\) -> bool:.*?)(?=\n    def |\nclass |\n\n[a-zA-Z]|\Z)'
    
    replacement = '''def split_po_router(self, input_pdf: str, po_pdf: str, router_pdf: str) -> bool:
        """
        Enhanced PDF splitting with multi-method detection
        Uses improved splitting algorithm with confidence scoring
        """
        try:
            # Import the improved splitter
            from improved_pdf_splitting import ImprovedPDFSplitter
            
            # Get configuration from environment
            min_confidence = float(os.getenv('SPLIT_CONFIDENCE_THRESHOLD', '0.7'))
            log_evidence = os.getenv('SPLIT_LOG_EVIDENCE', 'false').lower() == 'true'
            
            logger.info(f"Using enhanced PDF splitting (confidence threshold: {min_confidence})")
            
            # Create splitter and run enhanced splitting
            splitter = ImprovedPDFSplitter()
            success, explanation = splitter.split_pdf_enhanced(
                input_pdf, po_pdf, router_pdf, 
                min_confidence=min_confidence
            )
            
            if success:
                logger.info(f"Enhanced PDF splitting successful: {explanation}")
                if log_evidence:
                    logger.debug(f"Detailed evidence: {explanation}")
            else:
                logger.error(f"Enhanced PDF splitting failed: {explanation}")
            
            return success
            
        except ImportError as e:
            logger.error(f"Cannot import improved splitter: {e}")
            logger.info("Falling back to original splitting method")
            return self._fallback_split_po_router(input_pdf, po_pdf, router_pdf)
        except Exception as e:
            logger.error(f"Enhanced splitting error: {e}")
            logger.info("Falling back to original splitting method")  
            return self._fallback_split_po_router(input_pdf, po_pdf, router_pdf)
    
    def _fallback_split_po_router(self, input_pdf: str, po_pdf: str, router_pdf: str) -> bool:
        """
        Original splitting method as fallback
        """'''
    
    # Add the original method content as fallback
    original_method_match = re.search(pattern, content, re.DOTALL)
    if original_method_match:
        original_content = original_method_match.group(1)
        # Extract just the method body (remove the def line)
        method_body = '\n'.join(original_content.split('\n')[1:])
        replacement += method_body
    
    # Perform the replacement
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Also rename the original find_router_start_page method to avoid conflicts
    new_content = new_content.replace(
        'def find_router_start_page(self,',
        'def _original_find_router_start_page(self,'
    )
    
    # Write the patched version
    with open('unified_ocr_pipeline_improved.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Created unified_ocr_pipeline_improved.py")
    print("Original backed up to unified_ocr_pipeline.py.backup")
    
    return True

def create_safe_deployment_script():
    """Create a script for safe deployment to NAS"""
    
    script_content = '''#!/bin/bash

# Safe Deployment Script for Improved PDF Splitting
set -e

# Colors
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
RED='\\033[0;31m'
NC='\\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

log "Starting safe deployment of improved PDF splitting..."

# Step 1: Stop current services
log "Stopping OCR services..."
docker-compose down

# Step 2: Backup current files
log "Creating backup..."
cp unified_ocr_pipeline.py unified_ocr_pipeline.py.backup.$(date +%Y%m%d_%H%M%S)

# Step 3: Deploy improved version
log "Deploying improved pipeline..."
if [ -f "unified_ocr_pipeline_improved.py" ]; then
    mv unified_ocr_pipeline.py unified_ocr_pipeline.py.original
    mv unified_ocr_pipeline_improved.py unified_ocr_pipeline.py
    log "✅ Pipeline updated with improved splitting"
else
    error "unified_ocr_pipeline_improved.py not found!"
    exit 1
fi

# Step 4: Update configuration
log "Updating configuration..."
if ! grep -q "SPLIT_CONFIDENCE_THRESHOLD" .env; then
    cat >> .env << 'EOL'

# Enhanced PDF Splitting Configuration  
SPLIT_CONFIDENCE_THRESHOLD=0.7
SPLIT_LOG_EVIDENCE=true
SPLIT_FALLBACK_MODE=entire_po
EOL
    log "✅ Configuration updated"
fi

# Step 5: Rebuild and test
log "Rebuilding containers..."
docker-compose build

log "Running test..."
docker-compose --profile oneshot run --rm ocr_oneshot

if [ $? -eq 0 ]; then
    log "✅ Test successful! Starting production services..."
    docker-compose --profile cron up -d
    log "🎉 Deployment complete!"
else
    error "Test failed! Rolling back..."
    mv unified_ocr_pipeline.py unified_ocr_pipeline.py.failed
    mv unified_ocr_pipeline.py.original unified_ocr_pipeline.py
    docker-compose build
    docker-compose --profile cron up -d
    error "❌ Rollback complete. Check logs for issues."
    exit 1
fi
'''
    
    with open('safe_deploy.sh', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # Make executable
    import os
    os.chmod('safe_deploy.sh', 0o755)
    
    print("Created safe_deploy.sh")

if __name__ == "__main__":
    print("Creating improved PDF splitting integration...")
    print("=" * 50)
    
    if create_patched_pipeline():
        create_safe_deployment_script()
        
        print("\nDEPLOYMENT INSTRUCTIONS:")
        print("=" * 50)
        print("1. Copy these files to your NAS:")
        print("   - improved_pdf_splitting.py")
        print("   - unified_ocr_pipeline_improved.py") 
        print("   - safe_deploy.sh")
        print()
        print("2. On your NAS, run:")
        print("   chmod +x safe_deploy.sh")
        print("   ./safe_deploy.sh")
        print()
        print("3. Monitor the deployment:")
        print("   tail -f logs/pipeline.log")
        print()
        print("4. If issues occur, the script will auto-rollback")
        print()
        print("Ready for deployment!")
    else:
        print("Failed to create patched version")