#!/usr/bin/env python3
"""
Safe Integration and Deployment Script for Enhanced PDF Splitting
Integrates the improved splitting system with your existing OCR pipeline
"""

import os
import sys
import shutil
import re
from pathlib import Path
from datetime import datetime
import json
import subprocess

class PipelineIntegrator:
    """Safely integrates enhanced PDF splitting with existing pipeline"""
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir)
        self.backup_dir = self.project_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Key files to work with
        self.main_pipeline = self.project_dir / "unified_ocr_pipeline.py"
        self.enhanced_splitter = self.project_dir / "enhanced_pdf_splitter.py"
        self.tester = self.project_dir / "pdf_splitting_tester.py"
        
        # Configuration
        self.config = {
            'confidence_threshold': 0.7,
            'enable_logging': True,
            'fallback_enabled': True,
            'ocr_fallback': True
        }
    
    def create_backup(self) -> str:
        """Create a timestamped backup of current files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"pipeline_backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        files_to_backup = [
            "unified_ocr_pipeline.py",
            "docker-compose.yml",
            ".env",
        ]
        
        for file_name in files_to_backup:
            source = self.project_dir / file_name
            if source.exists():
                shutil.copy2(source, backup_path / file_name)
        
        print(f"✅ Backup created: {backup_path}")
        return str(backup_path)
    
    def patch_main_pipeline(self) -> bool:
        """Patch the main pipeline to use enhanced splitting"""
        
        if not self.main_pipeline.exists():
            print(f"❌ Main pipeline not found: {self.main_pipeline}")
            return False
        
        # Read the current pipeline
        with open(self.main_pipeline, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create the enhanced split_po_router method
        enhanced_method = '''    def split_po_router(self, input_pdf: str, po_pdf: str, router_pdf: str, temp_dir: str = None) -> bool:
        """
        Enhanced PDF splitting with multi-method detection
        Uses improved splitting algorithm with confidence scoring and fallback
        """
        try:
            # Import the enhanced splitter
            from enhanced_pdf_splitter import EnhancedPDFSplitter
            
            # Get configuration from environment
            min_confidence = float(os.getenv('SPLIT_CONFIDENCE_THRESHOLD', '0.7'))
            enable_logging = os.getenv('SPLIT_ENABLE_LOGGING', 'true').lower() == 'true'
            
            if enable_logging:
                logger.info(f"Using enhanced PDF splitting (confidence threshold: {min_confidence})")
            
            # Create splitter and run enhanced splitting
            splitter = EnhancedPDFSplitter()
            success, explanation = splitter.split_pdf_enhanced(
                input_pdf, po_pdf, router_pdf, 
                min_confidence=min_confidence
            )
            
            if success:
                if enable_logging:
                    logger.info(f"Enhanced PDF splitting successful: {explanation}")
            else:
                logger.error(f"Enhanced PDF splitting failed: {explanation}")
            
            return success
            
        except ImportError as e:
            logger.warning(f"Enhanced splitter not available: {e}")
            logger.info("Falling back to original splitting method")
            return self._original_split_po_router(input_pdf, po_pdf, router_pdf, temp_dir)
        except Exception as e:
            logger.error(f"Enhanced splitting error: {e}")
            logger.info("Falling back to original splitting method")
            return self._original_split_po_router(input_pdf, po_pdf, router_pdf, temp_dir)
    
    def _original_split_po_router(self, input_pdf: str, po_pdf: str, router_pdf: str, temp_dir: str = None) -> bool:
        """Original splitting method as fallback"""'''
        
        # Find the current split_po_router method
        pattern = r'(\s+def split_po_router\(self[^:]+:.*?)(?=\n\s+def |\nclass |\n\n[a-zA-Z]|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            print("❌ Could not find split_po_router method in pipeline")
            return False
        
        # Get the original method content (excluding the def line)
        original_method = match.group(1)
        original_lines = original_method.split('\n')
        original_body = '\n'.join(original_lines[1:])  # Skip the def line
        
        # Create the complete replacement
        replacement = enhanced_method + original_body
        
        # Replace in content
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Write the patched version
        patched_file = self.project_dir / "unified_ocr_pipeline_enhanced.py"
        with open(patched_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Enhanced pipeline created: {patched_file}")
        return True
    
    def update_environment_config(self) -> bool:
        """Update .env file with enhanced splitting configuration"""
        env_file = self.project_dir / ".env"
        
        # Configuration to add
        new_config = """
# Enhanced PDF Splitting Configuration
SPLIT_CONFIDENCE_THRESHOLD=0.7
SPLIT_ENABLE_LOGGING=true
SPLIT_FALLBACK_ENABLED=true
SPLIT_OCR_FALLBACK=true
"""
        
        if env_file.exists():
            # Read existing content
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Check if already configured
            if "SPLIT_CONFIDENCE_THRESHOLD" in content:
                print("✅ Environment already configured for enhanced splitting")
                return True
            
            # Append new configuration
            with open(env_file, 'a') as f:
                f.write(new_config)
        else:
            # Create new .env file
            with open(env_file, 'w') as f:
                f.write(new_config.strip())
        
        print("✅ Environment configuration updated")
        return True
    
    def update_dockerfile(self) -> bool:
        """Update Dockerfile to include dependencies for enhanced splitting"""
        dockerfile = self.project_dir / "Dockerfile.unified"
        
        if not dockerfile.exists():
            print("⚠️ Dockerfile.unified not found - skipping Docker update")
            return True
        
        with open(dockerfile, 'r') as f:
            content = f.read()
        
        # Check if pdf2image is already included (for OCR fallback)
        if "pdf2image" not in content:
            # Add pdf2image dependency for OCR fallback
            pip_pattern = r'(RUN pip install[^\n]*)'
            if re.search(pip_pattern, content):
                new_content = re.sub(
                    pip_pattern, 
                    r'\1 \\\n    pdf2image \\\n    opencv-python-headless \\\n    pytesseract',
                    content
                )
                
                with open(dockerfile, 'w') as f:
                    f.write(new_content)
                
                print("✅ Dockerfile updated with enhanced splitting dependencies")
            else:
                print("⚠️ Could not update Dockerfile - please add pdf2image manually")
        else:
            print("✅ Dockerfile already has required dependencies")
        
        return True
    
    def create_deployment_script(self) -> str:
        """Create a safe deployment script"""
        script_content = '''#!/bin/bash

# Safe Deployment Script for Enhanced PDF Splitting
set -e

# Colors
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
RED='\\033[0;31m'
NC='\\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

log "Starting safe deployment of enhanced PDF splitting..."

# Step 1: Stop current services
log "Stopping OCR services..."
docker-compose down || true

# Step 2: Backup current files
log "Creating deployment backup..."
BACKUP_DIR="backups/deployment_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp unified_ocr_pipeline.py "$BACKUP_DIR/" 2>/dev/null || true
cp .env "$BACKUP_DIR/" 2>/dev/null || true

# Step 3: Deploy enhanced version
log "Deploying enhanced pipeline..."
if [ -f "unified_ocr_pipeline_enhanced.py" ]; then
    cp unified_ocr_pipeline.py unified_ocr_pipeline.py.original
    cp unified_ocr_pipeline_enhanced.py unified_ocr_pipeline.py
    log "✅ Pipeline updated with enhanced splitting"
else
    error "Enhanced pipeline file not found!"
    exit 1
fi

# Step 4: Update Docker image
log "Rebuilding Docker image..."
docker-compose build

# Step 5: Run test
log "Running integration test..."
if docker-compose --profile oneshot run --rm ocr_oneshot python -c "
from enhanced_pdf_splitter import EnhancedPDFSplitter
splitter = EnhancedPDFSplitter()
print('✅ Enhanced splitter import successful')
"; then
    log "✅ Integration test passed"
else
    error "Integration test failed! Rolling back..."
    cp unified_ocr_pipeline.py.original unified_ocr_pipeline.py
    docker-compose build
    error "❌ Rollback complete. Check logs for issues."
    exit 1
fi

# Step 6: Start production services
log "Starting production services..."
docker-compose --profile cron up -d

log "🎉 Enhanced PDF splitting deployment complete!"
log "Monitor logs with: docker-compose logs -f"
log "Test splitting with: python pdf_splitting_tester.py single <pdf_file>"
'''
        
        script_path = self.project_dir / "deploy_enhanced_splitting.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(script_path, 0o755)
        
        print(f"✅ Deployment script created: {script_path}")
        return str(script_path)
    
    def create_testing_guide(self) -> str:
        """Create a comprehensive testing guide"""
        guide_content = '''# Enhanced PDF Splitting - Testing Guide

## Quick Test Commands

### Test Single PDF
```bash
# Basic test with default confidence (0.7)
python pdf_splitting_tester.py single sample.pdf

# Test with different confidence levels
python pdf_splitting_tester.py single sample.pdf 0.5  # More aggressive
python pdf_splitting_tester.py single sample.pdf 0.9  # More conservative
```

### Compare Detection Methods
```bash
# See what each method detects
python pdf_splitting_tester.py compare sample.pdf
```

### Test Multiple Confidence Levels
```bash
# Test at confidence levels: 0.3, 0.5, 0.7, 0.8, 0.9
python pdf_splitting_tester.py report sample.pdf

# Custom confidence levels
python pdf_splitting_tester.py report sample.pdf 0.4,0.6,0.8
```

### Batch Test Directory
```bash
python pdf_splitting_tester.py batch /path/to/pdf/directory
```

### Performance Benchmark
```bash
python pdf_splitting_tester.py benchmark file1.pdf file2.pdf file3.pdf
```

## Integration Testing

### Test Enhanced Pipeline
```bash
# Test the enhanced pipeline directly
python unified_ocr_pipeline_enhanced.py

# Test with Docker
docker-compose --profile oneshot run --rm ocr_oneshot
```

### Monitor Splitting Decisions
```bash
# Watch splitting logs in real-time
tail -f logs/pipeline.log | grep -E "(Enhanced PDF splitting|confidence)"

# Check recent splitting decisions
grep "Enhanced PDF splitting" logs/pipeline.log | tail -10
```

## Configuration Tuning

### Environment Variables
```bash
# Lower confidence = more likely to split
export SPLIT_CONFIDENCE_THRESHOLD=0.5

# Higher confidence = less likely to split  
export SPLIT_CONFIDENCE_THRESHOLD=0.8

# Enable detailed logging
export SPLIT_ENABLE_LOGGING=true
export OCR_LOG_LEVEL=DEBUG
```

### Common Scenarios

**If splitting is too aggressive (splitting within PO):**
- Increase `SPLIT_CONFIDENCE_THRESHOLD` to 0.8 or 0.9
- Check what patterns are being detected with `compare` command

**If router sections aren't being detected:**
- Decrease `SPLIT_CONFIDENCE_THRESHOLD` to 0.5 or 0.6
- Use `compare` command to see if any method detects the router

**If documents have "Page 1 of N" but wrong split:**
- Check OCR quality - scanned documents may need better preprocessing
- Enable OCR fallback with `SPLIT_OCR_FALLBACK=true`

## Troubleshooting

### Import Errors
```bash
# Check if enhanced splitter is accessible
python -c "from enhanced_pdf_splitter import EnhancedPDFSplitter; print('OK')"

# Check dependencies
python -c "import fitz, cv2, pytesseract; print('Dependencies OK')"
```

### Performance Issues
```bash
# Check processing times
python pdf_splitting_tester.py benchmark sample.pdf

# Monitor Docker resources
docker stats
```

### Splitting Accuracy Issues
```bash
# Analyze specific PDF
python pdf_splitting_tester.py compare problematic.pdf

# Test at multiple confidence levels
python pdf_splitting_tester.py report problematic.pdf 0.3,0.5,0.7,0.9
```

## Expected Improvements

- **Better accuracy**: Multi-method detection with confidence scoring
- **"Page 1 of N" detection**: Accurate PO length determination
- **OCR fallback**: Handles scanned documents automatically  
- **Detailed logging**: Understand why splitting decisions were made
- **Graceful fallback**: Uses original method if enhanced fails
- **Performance monitoring**: Track processing times and accuracy

## Success Indicators

✅ **Successful Integration:**
- No import errors in logs
- Enhanced splitting messages in logs
- Confidence scores reported
- Fallback works when needed

✅ **Improved Accuracy:**
- More accurate split points
- Better handling of edge cases
- Detailed explanations in logs
- Configurable thresholds working

Run these tests after deployment to verify everything is working correctly.
'''
        
        guide_path = self.project_dir / "TESTING_GUIDE.md"
        with open(guide_path, 'w') as f:
            f.write(guide_content)
        
        print(f"✅ Testing guide created: {guide_path}")
        return str(guide_path)
    
    def run_integration_tests(self) -> bool:
        """Run basic integration tests"""
        print("\n🧪 Running integration tests...")
        
        # Test 1: Import test
        try:
            if not self.enhanced_splitter.exists():
                print("❌ Enhanced splitter file not found")
                return False
            
            # Test Python import
            result = subprocess.run([
                sys.executable, "-c", 
                "from enhanced_pdf_splitter import EnhancedPDFSplitter; print('Import OK')"
            ], capture_output=True, text=True, cwd=self.project_dir)
            
            if result.returncode == 0:
                print("✅ Enhanced splitter import test passed")
            else:
                print(f"❌ Import test failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Integration test error: {e}")
            return False
        
        # Test 2: Basic functionality test
        try:
            # Create a simple test to verify the splitter works
            test_code = '''
from enhanced_pdf_splitter import EnhancedPDFSplitter
import tempfile
import fitz

# Create a simple test PDF
with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "Page 1 of 2\\nPO Content")
    page = doc.new_page()  
    page.insert_text((100, 100), "Router Section\\nOperation 10")
    doc.save(tmp.name)
    doc.close()
    
    # Test the splitter
    splitter = EnhancedPDFSplitter()
    split_point, confidence, explanation = splitter.find_optimal_split_point(tmp.name)
    
    print(f"Split point: {split_point}, Confidence: {confidence:.2f}")
    print("Functionality test passed")

import os
os.unlink(tmp.name)
'''
            
            result = subprocess.run([
                sys.executable, "-c", test_code
            ], capture_output=True, text=True, cwd=self.project_dir)
            
            if result.returncode == 0:
                print("✅ Functionality test passed")
                return True
            else:
                print(f"❌ Functionality test failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Functionality test error: {e}")
            return False
    
    def generate_deployment_report(self, backup_path: str) -> str:
        """Generate a deployment report"""
        report = {
            'deployment_timestamp': datetime.now().isoformat(),
            'backup_location': backup_path,
            'files_created': [
                'enhanced_pdf_splitter.py',
                'pdf_splitting_tester.py', 
                'unified_ocr_pipeline_enhanced.py',
                'deploy_enhanced_splitting.sh',
                'TESTING_GUIDE.md'
            ],
            'configuration': self.config,
            'next_steps': [
                '1. Review the enhanced pipeline: unified_ocr_pipeline_enhanced.py',
                '2. Test splitting: python pdf_splitting_tester.py single <pdf_file>',
                '3. Deploy safely: ./deploy_enhanced_splitting.sh',
                '4. Monitor logs: tail -f logs/pipeline.log',
                '5. Tune confidence threshold if needed'
            ]
        }
        
        report_path = self.project_dir / f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return str(report_path)

def main():
    """Main integration and deployment orchestrator"""
    print("🚀 Enhanced PDF Splitting Integration")
    print("=" * 40)
    
    # Initialize integrator
    integrator = PipelineIntegrator()
    
    try:
        # Step 1: Create backup
        print("\n📦 Creating backup...")
        backup_path = integrator.create_backup()
        
        # Step 2: Patch main pipeline
        print("\n🔧 Patching main pipeline...")
        if not integrator.patch_main_pipeline():
            print("❌ Pipeline patching failed")
            return False
        
        # Step 3: Update environment
        print("\n⚙️ Updating environment configuration...")
        integrator.update_environment_config()
        
        # Step 4: Update Dockerfile
        print("\n🐳 Updating Docker configuration...")
        integrator.update_dockerfile()
        
        # Step 5: Create deployment tools
        print("\n📜 Creating deployment tools...")
        script_path = integrator.create_deployment_script()
        guide_path = integrator.create_testing_guide()
        
        # Step 6: Run integration tests
        print("\n🧪 Running integration tests...")
        if not integrator.run_integration_tests():
            print("⚠️ Integration tests failed - please check dependencies")
        
        # Step 7: Generate report
        print("\n📊 Generating deployment report...")
        report_path = integrator.generate_deployment_report(backup_path)
        
        # Success summary
        print(f"\n✅ Enhanced PDF Splitting Integration Complete!")
        print("=" * 50)
        print(f"📦 Backup created: {backup_path}")
        print(f"🔧 Enhanced pipeline: unified_ocr_pipeline_enhanced.py")
        print(f"📜 Deployment script: {script_path}")
        print(f"📚 Testing guide: {guide_path}")
        print(f"📊 Report: {report_path}")
        print(f"\n🚀 Next Steps:")
        print(f"1. Test splitting: python pdf_splitting_tester.py single <pdf_file>")
        print(f"2. Deploy safely: {script_path}")
        print(f"3. Monitor logs: tail -f logs/pipeline.log")
        print(f"4. Read testing guide: {guide_path}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)