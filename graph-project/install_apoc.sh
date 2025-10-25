#!/bin/bash

# APOC Installation Script for Neo4j
# This script automatically installs APOC for your Neo4j instance

set -e  # Exit on error

echo "=== APOC Installation Script ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info() { echo -e "ℹ $1"; }

# Detect Neo4j installation
detect_neo4j() {
    print_info "Detecting Neo4j installation..."
    
    # Check for Homebrew installation
    if [ -d "/usr/local/Cellar/neo4j" ] || [ -d "/opt/homebrew/Cellar/neo4j" ]; then
        NEO4J_HOME=$(find /usr/local/Cellar/neo4j /opt/homebrew/Cellar/neo4j -maxdepth 2 -type d -name "libexec" 2>/dev/null | head -1)
        if [ -n "$NEO4J_HOME" ]; then
            PLUGINS_DIR="$NEO4J_HOME/plugins"
            # Try libexec/conf first (newer Neo4j), then system etc
            if [ -d "$NEO4J_HOME/conf" ]; then
                CONF_DIR="$NEO4J_HOME/conf"
            elif [ -d "/usr/local/etc/neo4j" ]; then
                CONF_DIR="/usr/local/etc/neo4j"
            elif [ -d "/opt/homebrew/etc/neo4j" ]; then
                CONF_DIR="/opt/homebrew/etc/neo4j"
            else
                CONF_DIR="$NEO4J_HOME/conf"
            fi
            INSTALL_TYPE="homebrew"
            print_success "Found Homebrew Neo4j installation"
            return 0
        fi
    fi
    
    # Check for Neo4j Desktop
    DESKTOP_DIR="$HOME/Library/Application Support/Neo4j/relate-data/dbmss"
    if [ -d "$DESKTOP_DIR" ]; then
        DBMS_DIR=$(find "$DESKTOP_DIR" -maxdepth 1 -type d -name "dbms-*" 2>/dev/null | head -1)
        if [ -n "$DBMS_DIR" ]; then
            PLUGINS_DIR="$DBMS_DIR/plugins"
            CONF_DIR="$DBMS_DIR/conf"
            INSTALL_TYPE="desktop"
            print_success "Found Neo4j Desktop installation"
            return 0
        fi
    fi
    
    print_error "Could not detect Neo4j installation"
    print_info "Please specify Neo4j directory manually:"
    read -p "Enter Neo4j home directory: " NEO4J_HOME
    PLUGINS_DIR="$NEO4J_HOME/plugins"
    CONF_DIR="$NEO4J_HOME/conf"
    INSTALL_TYPE="custom"
    return 0
}

# Get Neo4j version
get_neo4j_version() {
    print_info "Detecting Neo4j version..."
    
    if command -v neo4j &> /dev/null; then
        NEO4J_VERSION=$(neo4j version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        if [ -n "$NEO4J_VERSION" ]; then
            print_success "Neo4j version: $NEO4J_VERSION"
            # Extract major.minor version
            APOC_VERSION=$(echo $NEO4J_VERSION | grep -oE '[0-9]+\.[0-9]+')
            return 0
        fi
    fi
    
    # Fallback: ask user
    print_warning "Could not auto-detect Neo4j version"
    read -p "Enter Neo4j version (e.g., 5.14): " APOC_VERSION
}

# Download APOC
download_apoc() {
    print_info "Downloading APOC $APOC_VERSION..."
    
    # Find latest patch version
    APOC_URL="https://github.com/neo4j/apoc/releases/download/${APOC_VERSION}.0/apoc-${APOC_VERSION}.0-core.jar"
    
    # Try extended version (e.g., 5.14.0)
    TMP_DIR=$(mktemp -d)
    APOC_JAR="$TMP_DIR/apoc-core.jar"
    
    if curl -L -f -o "$APOC_JAR" "$APOC_URL" 2>/dev/null; then
        print_success "Downloaded APOC ${APOC_VERSION}.0"
        return 0
    fi
    
    # Try to find the right version from releases page
    print_warning "Version ${APOC_VERSION}.0 not found, checking available versions..."
    
    # List available versions
    print_info "Available APOC versions:"
    curl -s https://api.github.com/repos/neo4j/apoc/releases | grep -o '"tag_name": "[^"]*"' | head -10
    
    read -p "Enter exact APOC version to download (e.g., 5.14.0): " EXACT_VERSION
    APOC_URL="https://github.com/neo4j/apoc/releases/download/${EXACT_VERSION}/apoc-${EXACT_VERSION}-core.jar"
    
    if curl -L -f -o "$APOC_JAR" "$APOC_URL"; then
        print_success "Downloaded APOC ${EXACT_VERSION}"
        return 0
    else
        print_error "Failed to download APOC"
        return 1
    fi
}

# Install APOC
install_apoc() {
    print_info "Installing APOC to $PLUGINS_DIR..."
    
    # Create plugins directory if it doesn't exist
    mkdir -p "$PLUGINS_DIR"
    
    # Remove old APOC versions
    rm -f "$PLUGINS_DIR"/apoc-*-core.jar
    
    # Copy new version
    cp "$APOC_JAR" "$PLUGINS_DIR/"
    
    print_success "APOC jar installed to plugins directory"
}

# Configure Neo4j
configure_neo4j() {
    print_info "Configuring Neo4j for APOC..."
    
    CONF_FILE="$CONF_DIR/neo4j.conf"
    
    if [ ! -f "$CONF_FILE" ]; then
        print_error "Configuration file not found: $CONF_FILE"
        return 1
    fi
    
    # Backup config
    cp "$CONF_FILE" "$CONF_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    print_success "Backed up configuration file"
    
    # Add APOC configuration if not present
    if ! grep -q "dbms.security.procedures.unrestricted=apoc.\*" "$CONF_FILE"; then
        echo "" >> "$CONF_FILE"
        echo "# APOC Configuration (added by install_apoc.sh)" >> "$CONF_FILE"
        echo "dbms.security.procedures.unrestricted=apoc.*" >> "$CONF_FILE"
        echo "dbms.security.procedures.allowlist=apoc.*" >> "$CONF_FILE"
        echo "apoc.export.file.enabled=true" >> "$CONF_FILE"
        echo "apoc.import.file.enabled=true" >> "$CONF_FILE"
        echo "apoc.import.file.use_neo4j_config=true" >> "$CONF_FILE"
        print_success "Added APOC configuration to neo4j.conf"
    else
        print_warning "APOC configuration already exists in neo4j.conf"
    fi
}

# Restart Neo4j
restart_neo4j() {
    print_info "Restarting Neo4j..."
    
    if [ "$INSTALL_TYPE" = "homebrew" ]; then
        if command -v neo4j &> /dev/null; then
            neo4j restart
            print_success "Neo4j restarted"
        else
            print_warning "Please restart Neo4j manually: brew services restart neo4j"
        fi
    elif [ "$INSTALL_TYPE" = "desktop" ]; then
        print_warning "Please restart your Neo4j database from Neo4j Desktop"
    else
        print_warning "Please restart Neo4j manually"
    fi
}

# Verify installation
verify_installation() {
    print_info "Verifying APOC installation..."
    
    # Wait for Neo4j to start
    sleep 5
    
    if command -v python3 &> /dev/null; then
        python3 verify_apoc.py 2>/dev/null && print_success "APOC verification successful!" || print_warning "Run 'python verify_apoc.py' to verify installation"
    else
        print_info "Run this in Neo4j Browser to verify:"
        echo "CALL apoc.help('apoc')"
    fi
}

# Main installation flow
main() {
    echo "This script will install APOC for Neo4j"
    echo ""
    
    detect_neo4j
    echo "Plugins directory: $PLUGINS_DIR"
    echo "Config directory: $CONF_DIR"
    echo ""
    
    get_neo4j_version
    echo ""
    
    download_apoc
    install_apoc
    configure_neo4j
    
    echo ""
    print_success "APOC installation completed!"
    echo ""
    
    read -p "Restart Neo4j now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        restart_neo4j
        verify_installation
    else
        print_warning "Please restart Neo4j manually to activate APOC"
    fi
    
    echo ""
    echo "=== Installation Summary ==="
    echo "APOC Version: $APOC_VERSION"
    echo "Installation Type: $INSTALL_TYPE"
    echo "Plugins Directory: $PLUGINS_DIR"
    echo "Config File: $CONF_DIR/neo4j.conf"
    echo ""
    echo "Next steps:"
    echo "1. Restart Neo4j if not done already"
    echo "2. Run: python verify_apoc.py"
    echo "3. Test in Neo4j Browser: CALL apoc.help('apoc')"
    echo ""
}

# Run main function
main
