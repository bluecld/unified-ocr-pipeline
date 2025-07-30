#!/bin/bash

# Unified OCR Pipeline Setup Script
set -e

echo "🚀 Setting up Unified OCR Pipeline System..."
echo "=============================================="

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p OCR_INCOMING
mkdir -p OCR_PROCESSED  
mkdir -p logs

# Set permissions
chmod +x run_pipeline.sh

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
    echo "✅ Docker is running"
}

# Function to build the unified container
build_container() {
    echo "🔨 Building unified OCR container..."
    docker build -f Dockerfile.unified -t ocr-unified:latest .
    echo "✅ Container built successfully"
}

# Function to configure FileMaker
configure_filemaker() {
    read -p "📊 Do you want to enable FileMaker integration? (y/n): " enable_fm
    
    if [[ $enable_fm =~ ^[Yy]$ ]]; then
        echo "📊 Configuring FileMaker integration..."
        
        read -p "Enter FileMaker server IP [192.168.0.39]: " FM_HOST
        FM_HOST=${FM_HOST:-192.168.0.39}
        
        read -p "Enter database name [PreInventory]: " FM_DB
        FM_DB=${FM_DB:-PreInventory}
        
        read -p "Enter layout name [PreInventory]: " FM_LAYOUT
        FM_LAYOUT=${FM_LAYOUT:-PreInventory}
        
        read -p "Enter username [Anthony]: " FM_USERNAME
        FM_USERNAME=${FM_USERNAME:-Anthony}
        
        read -s -p "Enter password: " FM_PASSWORD
        echo
        
        # Create environment file
        cat > .env << ENVEOF
FM_ENABLED=true
FM_HOST=$FM_HOST
FM_DB=$FM_DB
FM_LAYOUT=$FM_LAYOUT
FM_USERNAME=$FM_USERNAME
FM_PASSWORD=$FM_PASSWORD
ENVEOF
        
        echo "✅ FileMaker configuration saved to .env"
        USE_FILEMAKER=true
    else
        echo "⏭️  Skipping FileMaker integration"
        cat > .env << ENVEOF
FM_ENABLED=false
ENVEOF
        USE_FILEMAKER=false
    fi
}

# Function to choose deployment mode
choose_deployment_mode() {
    echo ""
    echo "🎯 Choose deployment mode:"
    echo "1. Cron-based (Recommended for production)"
    echo "2. One-shot processing (test mode)"
    echo "3. Manual control (build only)"
    
    read -p "Enter choice [1]: " DEPLOY_MODE
    DEPLOY_MODE=${DEPLOY_MODE:-1}
    
    case $DEPLOY_MODE in
        1)
            echo "⏰ Setting up cron-based processing..."
            COMPOSE_PROFILE="cron"
            ;;
        2)
            echo "🎯 Setting up one-shot processing..."
            COMPOSE_PROFILE="oneshot"
            ;;
        3)
            echo "🛠️  Build-only mode selected"
            COMPOSE_PROFILE=""
            ;;
        *)
            echo "❌ Invalid choice, using cron mode"
            COMPOSE_PROFILE="cron"
            ;;
    esac
}

# Function to start services
start_services() {
    if [ -z "$COMPOSE_PROFILE" ]; then
        echo "✅ Build complete. Use docker-compose commands manually."
        return
    fi
    
    echo "🚀 Starting services..."
    
    if [ "$COMPOSE_PROFILE" = "oneshot" ]; then
        docker-compose --profile $COMPOSE_PROFILE run --rm ocr_oneshot
    else
        docker-compose --profile $COMPOSE_PROFILE up -d
    fi
    
    echo "✅ Services started"
}

# Function to show usage instructions
show_usage() {
    echo ""
    echo "🎉 Setup Complete!"
    echo "=================="
    echo ""
    echo "📂 Directory Structure:"
    echo "   OCR_INCOMING/     ← Place your PDF files here"  
    echo "   OCR_PROCESSED/     ← Processed files appear here"
    echo "   logs/             ← System logs"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs:        docker-compose logs -f"
    echo "   Stop services:    docker-compose down"
    echo "   Restart:          docker-compose restart"
    echo "   Status:           docker-compose ps"
    echo ""
    echo "📖 Quick Test:"
    echo "   1. Copy a PDF to OCR_INCOMING/"
    echo "   2. Check OCR_PROCESSED/ for results"
    echo "   3. View logs for details"
    echo ""
}

# Main execution
main() {
    echo "Starting setup process..."
    
    check_docker
    build_container
    configure_filemaker
    choose_deployment_mode
    start_services
    show_usage
    
    echo "🎯 Ready to process PDFs!"
}

# Run main function
main "$@"
