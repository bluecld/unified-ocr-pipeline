#!/bin/bash

# Deploy Improved PDF Splitting to NAS
# Run this script from your development machine

set -e

# Configuration - UPDATE THESE FOR YOUR NAS
NAS_HOST="192.168.0.39"           # Your NAS IP
NAS_USER="your_username"          # Your NAS username  
NAS_OCR_PATH="/volume1/docker/ocr" # Path to your OCR directory on NAS

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we can connect to NAS
log "Testing connection to NAS..."
if ! ssh ${NAS_USER}@${NAS_HOST} "echo 'Connection successful'"; then
    error "Cannot connect to NAS. Check SSH access and credentials."
    exit 1
fi

# Create backup on NAS
log "Creating backup on NAS..."
ssh ${NAS_USER}@${NAS_HOST} "cd ${NAS_OCR_PATH} && cp -r . ../ocr_backup_\$(date +%Y%m%d_%H%M%S)"

# Copy improved splitting code
log "Deploying improved_pdf_splitting.py..."
scp improved_pdf_splitting.py ${NAS_USER}@${NAS_HOST}:${NAS_OCR_PATH}/

# Create updated unified_ocr_pipeline.py with improved splitting
log "Creating updated pipeline integration..."

# Generate the integration patch
cat > pipeline_integration.py << 'EOF'
#!/usr/bin/env python3
"""
Integration patch for improved PDF splitting
This replaces the split_po_router method in EnhancedPDFProcessor
"""

def create_improved_split_method():
    """Returns the improved split_po_router method"""
    
    def split_po_router(self, input_pdf: str, po_pdf: str, router_pdf: str) -> bool:
        """
        Enhanced PDF splitting with multi-method detection
        Replaces the original text-only approach
        """
        try:
            # Import the improved splitter
            from improved_pdf_splitting import ImprovedPDFSplitter
            
            # Get configuration from environment
            import os
            min_confidence = float(os.getenv('SPLIT_CONFIDENCE_THRESHOLD', '0.7'))
            log_evidence = os.getenv('SPLIT_LOG_EVIDENCE', 'false').lower() == 'true'
            
            # Create splitter and run enhanced splitting
            splitter = ImprovedPDFSplitter()
            success, explanation = splitter.split_pdf_enhanced(
                input_pdf, po_pdf, router_pdf, 
                min_confidence=min_confidence
            )
            
            if success:
                logger.info(f"Enhanced PDF splitting successful: {explanation}")
                if log_evidence:
                    logger.debug(f"Splitting evidence: {explanation}")
            else:
                logger.error(f"Enhanced PDF splitting failed: {explanation}")
            
            return success
            
        except ImportError as e:
            logger.error(f"Cannot import improved splitter, falling back to original method: {e}")
            # Fall back to original method if import fails
            return self._original_split_po_router(input_pdf, po_pdf, router_pdf)
        except Exception as e:
            logger.error(f"Enhanced splitting error: {e}")
            return False
    
    return split_po_router

# Instructions for manual integration
print("=" * 60)
print("MANUAL INTEGRATION REQUIRED")
print("=" * 60)
print()
print("1. Edit unified_ocr_pipeline.py on your NAS")
print("2. In the EnhancedPDFProcessor class, rename the current split_po_router method:")
print("   def split_po_router(self, ...) -> def _original_split_po_router(self, ...)")
print()
print("3. Add this new method to replace it:")
print()
print("   def split_po_router(self, input_pdf: str, po_pdf: str, router_pdf: str) -> bool:")
print('       """Enhanced PDF splitting with multi-method detection"""')
print("       try:")
print("           from improved_pdf_splitting import ImprovedPDFSplitter")
print("           import os")
print("           ")
print("           min_confidence = float(os.getenv('SPLIT_CONFIDENCE_THRESHOLD', '0.7'))")
print("           ")
print("           splitter = ImprovedPDFSplitter()")
print("           success, explanation = splitter.split_pdf_enhanced(")
print("               input_pdf, po_pdf, router_pdf, min_confidence=min_confidence")
print("           )")
print("           ")
print("           if success:")
print("               logger.info(f'Enhanced PDF splitting: {explanation}')")
print("           else:")
print("               logger.error(f'Enhanced PDF splitting failed: {explanation}')")
print("           ")
print("           return success")
print("       except Exception as e:")
print("           logger.error(f'Enhanced splitting error: {e}, falling back')")
print("           return self._original_split_po_router(input_pdf, po_pdf, router_pdf)")
print()
print("4. Update your .env file with new configuration options")
print("5. Rebuild and restart the Docker containers")
print()
EOF

python pipeline_integration.py

# Copy the integration instructions
scp pipeline_integration.py ${NAS_USER}@${NAS_HOST}:${NAS_OCR_PATH}/

# Update .env with new configuration options
log "Adding improved splitting configuration to .env..."
ssh ${NAS_USER}@${NAS_HOST} "cd ${NAS_OCR_PATH} && cat >> .env << 'EOL'

# Enhanced PDF Splitting Configuration
SPLIT_CONFIDENCE_THRESHOLD=0.7
SPLIT_LOG_EVIDENCE=true
SPLIT_FALLBACK_MODE=entire_po
EOL"

# Copy deployment documentation
scp SPLITTING_IMPROVEMENTS.md ${NAS_USER}@${NAS_HOST}:${NAS_OCR_PATH}/

log "Files deployed successfully!"
warn "Manual integration required - see instructions above"
log "Next steps:"
echo "  1. SSH to your NAS: ssh ${NAS_USER}@${NAS_HOST}"
echo "  2. Edit unified_ocr_pipeline.py as instructed"
echo "  3. Run: docker-compose build && docker-compose restart"
echo "  4. Test with: docker-compose --profile oneshot run --rm ocr_oneshot"