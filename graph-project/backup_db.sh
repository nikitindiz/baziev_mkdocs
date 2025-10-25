#!/bin/bash

# Neo4j Database Backup Script for Baziev Physics Graph
# Supports both local (Homebrew) and Docker deployments
# Usage: ./backup_db.sh [OPTIONS]

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config/config.yml"
BACKUP_DIR="$SCRIPT_DIR/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
KEEP_BACKUPS=7  # Number of backups to retain

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
DEPLOYMENT_TYPE=""
COMPRESS=true
VERBOSE=false

print_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    -t, --type TYPE         Deployment type: 'local' or 'docker' (auto-detected if not specified)
    -d, --dir DIRECTORY     Custom backup directory (default: ./backups)
    -n, --no-compress       Don't compress backup
    -k, --keep N            Number of backups to keep (default: 7)
    -v, --verbose           Verbose output
    -h, --help              Show this help message

Examples:
    ./backup_db.sh                          # Auto-detect and backup
    ./backup_db.sh -t docker                # Force Docker mode
    ./backup_db.sh -d /path/to/backups      # Custom backup directory
    ./backup_db.sh -k 30                    # Keep 30 backups
EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        -d|--dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -n|--no-compress)
            COMPRESS=false
            shift
            ;;
        -k|--keep)
            KEEP_BACKUPS="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

# Detect deployment type if not specified
detect_deployment_type() {
    if [ -n "$DEPLOYMENT_TYPE" ]; then
        log_verbose "Using specified deployment type: $DEPLOYMENT_TYPE"
        return
    fi

    log_info "Auto-detecting deployment type..."
    
    # Check if Docker container is running
    if command -v docker &> /dev/null; then
        if docker ps --format '{{.Names}}' | grep -q "neo4j-baziev"; then
            DEPLOYMENT_TYPE="docker"
            log_info "Detected Docker deployment"
            return
        fi
    fi
    
    # Check if local Neo4j is running (Homebrew)
    if command -v neo4j &> /dev/null; then
        if neo4j status &> /dev/null; then
            DEPLOYMENT_TYPE="local"
            log_info "Detected local Neo4j (Homebrew) deployment"
            return
        fi
    fi
    
    log_error "Could not detect Neo4j deployment. Please specify with -t flag."
    exit 1
}

# Create backup directory
create_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    log_verbose "Backup directory: $BACKUP_DIR"
}

# Backup using Python (Cypher export)
backup_cypher_export() {
    local backup_name="$1"
    local export_file="$BACKUP_DIR/${backup_name}_cypher.cypher"
    
    log_info "Exporting database using Cypher..."
    
    python3 << EOF
import sys
sys.path.insert(0, "$SCRIPT_DIR")

from src.utils.neo4j_connection import Neo4jConnection
from src.utils.config import load_config

config = load_config("$CONFIG_FILE")
neo4j_config = config['neo4j']
neo4j_conn = Neo4jConnection(
    uri=neo4j_config['uri'],
    user=neo4j_config['username'],
    password=neo4j_config['password'],
    database=neo4j_config['database']
)

try:
    with neo4j_conn.driver.session() as session:
        # Export all nodes and relationships
        result = session.run("""
            CALL apoc.export.cypher.all('$export_file', {
                format: 'cypher-shell',
                useOptimizations: {type: 'UNWIND_BATCH', unwindBatchSize: 20}
            })
            YIELD file, batches, source, format, nodes, relationships, properties, time
            RETURN file, nodes, relationships, properties, time
        """)
        
        record = result.single()
        if record:
            print(f"Exported {record['nodes']} nodes and {record['relationships']} relationships")
            print(f"Export file: {record['file']}")
            print(f"Time: {record['time']} ms")
        else:
            print("Export completed (no statistics available)")
except Exception as e:
    print(f"Error during Cypher export: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    neo4j_conn.close()
EOF
    
    if [ $? -eq 0 ]; then
        log_success "Cypher export completed"
        return 0
    else
        log_error "Cypher export failed"
        return 1
    fi
}

# Backup Docker deployment
backup_docker() {
    local backup_name="neo4j_backup_${TIMESTAMP}"
    local container_name="neo4j-baziev"
    
    log_info "Starting Docker backup: $backup_name"
    
    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "$container_name"; then
        log_error "Docker container '$container_name' is not running"
        exit 1
    fi
    
    # Create temporary directory for backup
    local temp_dir="$BACKUP_DIR/temp_$TIMESTAMP"
    mkdir -p "$temp_dir"
    
    # Method 1: Copy data directory from Docker volume
    log_info "Copying data from Docker volume..."
    docker cp "$container_name:/data" "$temp_dir/" || {
        log_error "Failed to copy data from Docker container"
        rm -rf "$temp_dir"
        exit 1
    }
    
    # Method 2: Export using Cypher (if APOC is available)
    if backup_cypher_export "$backup_name"; then
        log_success "Cypher export completed"
    else
        log_warning "Cypher export failed, continuing with volume backup only"
    fi
    
    # Compress if requested
    if [ "$COMPRESS" = true ]; then
        log_info "Compressing backup..."
        tar -czf "$BACKUP_DIR/${backup_name}.tar.gz" -C "$temp_dir" . || {
            log_error "Compression failed"
            rm -rf "$temp_dir"
            exit 1
        }
        log_success "Backup compressed: ${backup_name}.tar.gz"
        
        # Calculate size
        local size=$(du -h "$BACKUP_DIR/${backup_name}.tar.gz" | cut -f1)
        log_info "Backup size: $size"
    else
        mv "$temp_dir" "$BACKUP_DIR/${backup_name}"
        log_success "Backup saved: ${backup_name}"
    fi
    
    # Cleanup
    [ -d "$temp_dir" ] && rm -rf "$temp_dir"
    
    echo "$BACKUP_DIR/${backup_name}"
}

# Backup local deployment (Homebrew)
backup_local() {
    local backup_name="neo4j_backup_${TIMESTAMP}"
    
    log_info "Starting local Neo4j backup: $backup_name"
    
    # Find Neo4j home directory
    local neo4j_home=$(neo4j console 2>&1 | grep -o 'NEO4J_HOME=.*' | cut -d'=' -f2 | head -n1)
    if [ -z "$neo4j_home" ]; then
        # Try Homebrew paths (Apple Silicon first, then Intel)
        if [ -d "/opt/homebrew/var/neo4j" ]; then
            neo4j_home="/opt/homebrew/var/neo4j"
        elif [ -d "/usr/local/var/neo4j" ]; then
            neo4j_home="/usr/local/var/neo4j"
        else
            neo4j_home="/usr/local/var/neo4j"
        fi
        log_warning "Could not detect NEO4J_HOME, using default: $neo4j_home"
    fi
    
    local data_dir="$neo4j_home/data"
    
    if [ ! -d "$data_dir" ]; then
        log_error "Neo4j data directory not found: $data_dir"
        exit 1
    fi
    
    log_verbose "Neo4j data directory: $data_dir"
    
    # Stop Neo4j for consistent backup
    log_info "Stopping Neo4j..."
    neo4j stop || log_warning "Neo4j may already be stopped"
    sleep 2
    
    # Create temporary directory for backup
    local temp_dir="$BACKUP_DIR/temp_$TIMESTAMP"
    mkdir -p "$temp_dir"
    
    # Copy data directory
    log_info "Copying Neo4j data directory..."
    cp -R "$data_dir" "$temp_dir/" || {
        log_error "Failed to copy data directory"
        rm -rf "$temp_dir"
        neo4j start
        exit 1
    }
    
    # Restart Neo4j
    log_info "Restarting Neo4j..."
    neo4j start
    sleep 3
    
    # Export using Cypher (if APOC is available)
    if backup_cypher_export "$backup_name"; then
        log_success "Cypher export completed"
    else
        log_warning "Cypher export failed, continuing with data directory backup only"
    fi
    
    # Compress if requested
    if [ "$COMPRESS" = true ]; then
        log_info "Compressing backup..."
        tar -czf "$BACKUP_DIR/${backup_name}.tar.gz" -C "$temp_dir" . || {
            log_error "Compression failed"
            rm -rf "$temp_dir"
            exit 1
        }
        log_success "Backup compressed: ${backup_name}.tar.gz"
        
        # Calculate size
        local size=$(du -h "$BACKUP_DIR/${backup_name}.tar.gz" | cut -f1)
        log_info "Backup size: $size"
    else
        mv "$temp_dir" "$BACKUP_DIR/${backup_name}"
        log_success "Backup saved: ${backup_name}"
    fi
    
    # Cleanup
    [ -d "$temp_dir" ] && rm -rf "$temp_dir"
    
    echo "$BACKUP_DIR/${backup_name}"
}

# Clean old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (keeping last $KEEP_BACKUPS)..."
    
    # Count backups
    local backup_count=$(find "$BACKUP_DIR" -maxdepth 1 -name "neo4j_backup_*" | wc -l | tr -d ' ')
    
    if [ "$backup_count" -le "$KEEP_BACKUPS" ]; then
        log_info "No cleanup needed ($backup_count backups)"
        return
    fi
    
    # Remove old backups
    find "$BACKUP_DIR" -maxdepth 1 -name "neo4j_backup_*" -type f -o -type d | \
        sort | \
        head -n -"$KEEP_BACKUPS" | \
        while read backup; do
            log_verbose "Removing old backup: $(basename "$backup")"
            rm -rf "$backup"
        done
    
    local removed=$((backup_count - KEEP_BACKUPS))
    log_success "Removed $removed old backup(s)"
}

# Create backup metadata
create_metadata() {
    local backup_name="$1"
    local metadata_file="$BACKUP_DIR/${backup_name}_metadata.json"
    
    cat > "$metadata_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "deployment_type": "$DEPLOYMENT_TYPE",
    "compressed": $COMPRESS,
    "backup_dir": "$BACKUP_DIR",
    "hostname": "$(hostname)",
    "neo4j_version": "$(get_neo4j_version)"
}
EOF
    
    log_verbose "Metadata saved: $metadata_file"
}

# Get Neo4j version
get_neo4j_version() {
    if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
        docker exec neo4j-baziev neo4j --version 2>/dev/null || echo "unknown"
    else
        neo4j --version 2>/dev/null || echo "unknown"
    fi
}

# Main backup function
main() {
    log_info "=== Neo4j Backup Script ==="
    log_info "Timestamp: $(date)"
    
    # Detect deployment type
    detect_deployment_type
    
    # Create backup directory
    create_backup_dir
    
    # Perform backup based on deployment type
    local backup_path=""
    case "$DEPLOYMENT_TYPE" in
        docker)
            backup_path=$(backup_docker)
            ;;
        local)
            backup_path=$(backup_local)
            ;;
        *)
            log_error "Invalid deployment type: $DEPLOYMENT_TYPE"
            exit 1
            ;;
    esac
    
    # Create metadata
    local backup_name=$(basename "$backup_path" | sed 's/\.tar\.gz$//')
    create_metadata "$backup_name"
    
    # Cleanup old backups
    cleanup_old_backups
    
    log_success "=== Backup completed successfully ==="
    log_info "Backup location: $backup_path"
    
    # List recent backups
    log_info "Recent backups:"
    ls -lht "$BACKUP_DIR" | grep "neo4j_backup_" | head -n 5
}

# Run main function
main
