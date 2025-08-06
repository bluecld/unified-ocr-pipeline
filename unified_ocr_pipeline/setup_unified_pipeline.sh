#!/bin/sh

# Enhanced Unified OCR Pipeline Setup Script
set -e

echo "🚀 Setting up Enhanced OCR Pipeline System..."
echo "==============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="unified_ocr_pipeline"

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    log "✅ Docker is running"
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is not installed. Please install it first."
        exit 1
    fi
    log "✅ docker-compose is available"
    
    # Check available disk space (need at least 2GB)
    AVAILABLE_SPACE=$(df "$SCRIPT_DIR" | awk 'NR==2 {print $4}')
    if [[ $AVAILABLE_SPACE -lt 2097152 ]]; then  # 2GB in KB
        warn "Less than 2GB of disk space available. Consider freeing up space."
    fi
    log "✅ Disk space check completed"
}

# Function to create directory structure
create_directories() {
    log "📁 Creating directory structure..."
    
    mkdir -p OCR_INCOMING
    mkdir -p OCR_PROCESSED
    mkdir -p logs
    mkdir -p temp
    
    # Set proper permissions
    chmod 755 OCR_INCOMING OCR_PROCESSED logs temp
    
    log "✅ Directory structure created"
}

# Function to configure environment
configure_environment() {
    log "⚙️ Configuring environment..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f .env ]]; then
        cp .env.example .env
        log "Created .env file from template"
    fi
    
    # Get current directory paths for Docker volumes
    CURRENT_DIR=$(pwd)
    export HOST_INCOMING_DIR="$CURRENT_DIR/OCR_INCOMING"
    export HOST_PROCESSED_DIR="$CURRENT_DIR/OCR_PROCESSED"
    export HOST_LOG_DIR="$CURRENT_DIR/logs"
    
    # Update docker-compose.yml with correct paths if needed
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        # Windows paths need conversion
        warn "Windows environment detected. You may need to adjust volume paths manually."
    fi
    
    log "✅ Environment configured"
}

# Function to configure FileMaker integration
configure_filemaker() {
    echo ""
    echo -e "${BLUE}📊 FileMaker Integration Setup${NC}"
    echo "======================================"
    
    read -p "Enable FileMaker integration? (y/n) [y]: " enable_fm
    enable_fm=${enable_fm:-y}
    
    if [[ $enable_fm =~ ^[Yy]$ ]]; then
        log "Configuring FileMaker integration..."
        
        echo "Enter FileMaker server details:"
        read -p "Server IP [192.168.0.39]: " FM_HOST
        FM_HOST=${FM_HOST:-192.168.0.39}
        
        read -p "Database name [PreInventory]: " FM_DB
        FM_DB=${FM_DB:-PreInventory}
        
        read -p "Layout name [PreInventory]: " FM_LAYOUT
        FM_LAYOUT=${FM_LAYOUT:-PreInventory}
        
        read -p "Username [Anthony]: " FM_USERNAME
        FM_USERNAME=${FM_USERNAME:-Anthony}
        
        read -s -p "Password: " FM_PASSWORD
        echo
        
        # Test FileMaker connection
        log "Testing FileMaker connection..."
        if curl -s --connect-timeout 10 --insecure "https://$FM_HOST/fmi/data/v1" > /dev/null 2>&1; then
            log "✅ FileMaker server is reachable"
        else
            warn "⚠️  FileMaker server not reachable. Check network connectivity."
        fi
        
        # Update .env file
        {
            echo "# FileMaker Configuration"
            echo "FM_ENABLED=true"
            echo "FM_HOST=$FM_HOST"
            echo "FM_DB=$FM_DB"
            echo "FM_LAYOUT=$FM_LAYOUT"
            echo "FM_USERNAME=$FM_USERNAME"
            echo "FM_PASSWORD=$FM_PASSWORD"
            echo ""
            echo "# OCR Configuration"
            echo "OCR_LOG_LEVEL=INFO"
            echo "OLLAMA_HOST=http://ollama:11434"
            echo ""
            echo "# Directory Configuration"
            echo "HOST_INCOMING_DIR=$HOST_INCOMING_DIR"
            echo "HOST_PROCESSED_DIR=$HOST_PROCESSED_DIR"
            echo "HOST_LOG_DIR=$HOST_LOG_DIR"
        } > .env
        
        log "✅ FileMaker configuration saved"
        USE_FILEMAKER=true
    else
        log "Skipping FileMaker integration"
        {
            echo "# FileMaker Configuration"
            echo "FM_ENABLED=false"
            echo ""
            echo "# OCR Configuration"
            echo "OCR_LOG_LEVEL=INFO"
            echo "OLLAMA_HOST=http://ollama:11434"
            echo ""
            echo "# Directory Configuration"
            echo "HOST_INCOMING_DIR=$HOST_INCOMING_DIR"
            echo "HOST_PROCESSED_DIR=$HOST_PROCESSED_DIR"
            echo "HOST_LOG_DIR=$HOST_LOG_DIR"
        } > .env
        USE_FILEMAKER=false
    fi
}

# Function to choose AI enhancement
configure_ai_enhancement() {
    echo ""
    echo -e "${BLUE}🤖 AI Enhancement Setup${NC}"
    echo "========================="
    
    read -p "Enable AI-enhanced field extraction with Ollama? (y/n) [n]: " enable_ai
    enable_ai=${enable_ai:-n}
    
    if [[ $enable_ai =~ ^[Yy]$ ]]; then
        log "AI enhancement will be enabled"
        USE_AI=true
    else
        log "Using regex-only extraction (recommended for reliability)"
        USE_AI=false
    fi
}

# Function to choose deployment mode
choose_deployment_mode() {
    echo ""
    echo -e "${BLUE}🎯 Deployment Mode Selection${NC}"
    echo "============================="
    echo "1. Cron-based (Recommended for production)"
    echo "2. Continuous monitoring (Higher resource usage)"
    echo "3. One-shot processing (Test single run)"
    echo "4. Build only (Manual control)"
    
    read -p "Enter choice [1]: " DEPLOY_MODE
    DEPLOY_MODE=${DEPLOY_MODE:-1}
    
    case $DEPLOY_MODE in
        1)
            log "⏰ Cron-based processing selected"
            if [[ $USE_AI == true ]]; then
                COMPOSE_PROFILE="ai,cron"
            else
                COMPOSE_PROFILE="cron"
            fi
            ;;
        2)
            log "🔄 Continuous monitoring selected"
            if [[ $USE_AI == true ]]; then
                COMPOSE_PROFILE="ai,continuous"
            else
                COMPOSE_PROFILE="continuous"
            fi
            ;;
        3)
            log "🎯 One-shot processing selected"
            if [[ $USE_AI == true ]]; then
                COMPOSE_PROFILE="ai,oneshot"
            else
                COMPOSE_PROFILE="oneshot"
            fi
            ;;
        4)
            log "🛠️ Build-only mode selected"
            COMPOSE_PROFILE=""
            ;;
        *)
            warn "Invalid choice, using cron mode"
            COMPOSE_PROFILE="cron"
            ;;
    esac
}

# Function to build containers
build_containers() {
    log "🔨 Building enhanced OCR container..."
    
    # Build the main container
    docker build -f Dockerfile.unified -t ocr-unified:enhanced .
    
    if [[ $? -eq 0 ]]; then
        log "✅ Container built successfully"
    else
        error "❌ Container build failed"
        exit 1
    fi
}

# Function to start services
start_services() {
    if [[ -z "$COMPOSE_PROFILE" ]]; then
        log "✅ Build complete. Use docker-compose commands manually."
        return
    fi
    
    log "🚀 Starting services with profile: $COMPOSE_PROFILE"
    
    # Export environment variables for docker-compose
    export HOST_INCOMING_DIR HOST_PROCESSED_DIR HOST_LOG_DIR
    
    if [[ "$COMPOSE_PROFILE" == *"oneshot"* ]]; then
        docker-compose --profile $COMPOSE_PROFILE run --rm ocr_oneshot
    else
        docker-compose --profile $COMPOSE_PROFILE up -d
        
        # Wait a moment for services to start
        sleep 5
        
        # Check service status
        log "Checking service status..."
        docker-compose ps
    fi
    
    log "✅ Services started"
}

# Function to install monitoring models (if AI enabled)
setup_ai_models() {
    if [[ $USE_AI != true ]]; then
        return
    fi
    
    log "🤖 Setting up AI models..."
    
    # Wait for Ollama to be ready
    log "Waiting for Ollama service to be ready..."
    sleep 30
    
    # Install required models
    docker exec ocr_ollama ollama pull llama2:7b-chat
    
    if [[ $? -eq 0 ]]; then
        log "✅ AI models installed"
    else
        warn "⚠️  AI model installation failed. Will fallback to regex extraction."
    fi
}

# Function to run tests
run_tests() {
    echo ""
    read -p "Run test with sample PDF? (y/n) [y]: " run_test
    run_test=${run_test:-y}
    
    if [[ $run_test =~ ^[Yy]$ ]]; then
        log "🧪 Running test..."
        
        # Create a dummy PDF for testing
        cat > test_po.txt << 'EOF'
PURCHASE ORDER

PO Number: 4551234567
MJO NO: MJO-2024-001
QTY SHIP: 100
PART NUMBER: 12345*op06
Promise Delivery Date: 01/15/2024
DPAS Rating: A1
Payment Terms: Net 30 Days
Quality Clauses: Q8, Q10, Q43

Router Section Begins Here
Operation 10: Mill to dimension
Operation 20: Drill holes
EOF
        
        # Convert to PDF (if possible)
        if command -v enscript &> /dev/null && command -v ps2pdf &> /dev/null; then
            enscript -p test_po.ps test_po.txt 2>/dev/null
            ps2pdf test_po.ps OCR_INCOMING/test_po.pdf 2>/dev/null
            rm -f test_po.ps test_po.txt
            
            log "Test PDF created: OCR_INCOMING/test_po.pdf"
            log "Monitor OCR_PROCESSED/ directory for results"
            
            # If oneshot mode, the test already ran
            if [[ "$COMPOSE_PROFILE" != *"oneshot"* ]]; then
                log "Pipeline will process the test file automatically"
            fi
        else
            warn "Cannot create test PDF. Install enscript and ghostscript for testing."
            rm -f test_po.txt
        fi
    fi
}

# Function to show usage instructions
show_usage() {
    echo ""
    echo -e "${GREEN}🎉 Enhanced OCR Pipeline Setup Complete!${NC}"
    echo "=========================================="
    echo ""
    echo -e "${BLUE}📂 Directory Structure:${NC}"
    echo "   OCR_INCOMING/      ← Place your PDF files here"
    echo "   OCR_PROCESSED/      ← Processed files organized by PO number"
    echo "   ├── PO_4551234567/ ← Successful processing"
    echo "   │   ├── 4551234567_PO.pdf"
    echo "   │   ├── 4551234567_ROUTER.pdf"
    echo "   │   ├── extracted_data.json"
    echo "   │   └── extracted_text.txt"
    echo "   └── ERROR_*/       ← Failed processing attempts"
    echo "   logs/              ← System logs and debugging info"
    echo ""
    echo -e "${BLUE}🔧 Management Commands:${NC}"
    echo "   View logs:         docker-compose logs -f"
    echo "   Stop services:     docker-compose down"
    echo "   Restart:           docker-compose restart"
    echo "   Status:            docker-compose ps"
    echo "   Update:            docker-compose build && docker-compose up -d"
    echo ""
    echo -e "${BLUE}🔍 Monitoring:${NC}"
    echo "   Pipeline logs:     tail -f logs/pipeline.log"
    echo "   Cron logs:         tail -f logs/cron.log"
    if [[ $USE_AI == true ]]; then
        echo "   AI models:         docker exec ocr_ollama ollama list"
    fi
    echo ""
    echo -e "${BLUE}📖 Field Extraction:${NC}"
    echo "   • PO Number (10 digits starting with 45)"
    echo "   • MJO Number"
    echo "   • Quantity Shipped"
    echo "   • Part Number (*op## format)"
    echo "   • Delivery Date"
    echo "   • DPAS Rating"
    echo "   • Payment Terms (flags non-Net30)"
    echo "   • Quality Clauses (with descriptions)"
    echo "   • Planner Name (from reference list)"
    echo ""
    if [[ $USE_FILEMAKER == true ]]; then
        echo -e "${BLUE}📊 FileMaker Integration:${NC}"
        echo "   • Records created in PreInventory layout"
        echo "   • PDFs uploaded to container fields"
        echo "   • Check FileMaker for processed records"
        echo ""
    fi
    echo -e "${BLUE}🚨 Troubleshooting:${NC}"
    echo "   1. Check logs: docker-compose logs"
    echo "   2. Verify file permissions in OCR_INCOMING/"
    echo "   3. Ensure PDFs are not password-protected"
    echo "   4. Check FileMaker connectivity (if enabled)"
    echo ""
    echo -e "${GREEN}Ready to process PDFs! 🎯${NC}"
}

# Main execution function
main() {
    echo "Starting enhanced setup process..."
    
    check_prerequisites
    create_directories
    configure_environment
    configure_filemaker
    configure_ai_enhancement
    choose_deployment_mode
    build_containers
    start_services
    
    if [[ $USE_AI == true && "$COMPOSE_PROFILE" != *"oneshot"* ]]; then
        setup_ai_models
    fi
    
    run_tests
    show_usage
    
    log "🎯 Enhanced OCR Pipeline is ready!"
}

# Handle script interruption
trap 'echo -e "\n${RED}Setup interrupted by user${NC}"; exit 1' INT

# Run main function
main "$@"