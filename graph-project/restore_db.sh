#!/bin/bash

# Neo4j Database Restore Script for Baziev Physics Graph
# Supports both local (Homebrew) and Docker deployments
# Usage: ./restore_db.sh [OPTIONS] <backup_file>

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
DEPLOYMENT_TYPE=""
BACKUP_FILE=""
FORCE=false
VERBOSE=false

print_usage() {
    cat << EOF
Usage: $0 [OPTIONS] <backup_file>

Options:
    -t, --type TYPE         Deployment type: 'local' or 'docker' (auto-detected if not specified)
    -f, --force             Force restore without confirmation
    -v, --verbose           Verbose output
    -l, --list              List available backups and exit
    -h, --help              Show this help message

Arguments:
    backup_file             Path to backup file or backup name (without .tar.gz)

Examples:
    ./restore_db.sh -l                                  # List available backups
    ./restore_db.sh neo4j_backup_20250126_120000        # Restore specific backup
    ./restore_db.sh -t docker backups/custom_backup.tar.gz
    ./restore_db.sh -f neo4j_backup_20250126_120000     # Force restore without confirmation
EOF
}

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

# List available backups
list_backups() {
    log_info "Available backups in $BACKUP_DIR:"
    echo ""
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_warning "Backup directory not found: $BACKUP_DIR"
        return
    fi
    
    local backups=$(find "$BACKUP_DIR" -maxdepth 1 \( -name "neo4j_backup_*.tar.gz" -o -type d -name "neo4j_backup_*" \) | sort -r)
    
    if [ -z "$backups" ]; then
        log_warning "No backups found"
        return
    fi
    
    echo -e "${BLUE}Name${NC}\t\t\t${BLUE}Size${NC}\t${BLUE}Date${NC}"
    echo "------------------------------------------------------------"
    
    echo "$backups" | while read backup; do
        local name=$(basename "$backup" | sed 's/\.tar\.gz$//')
        local size=$(du -h "$backup" 2>/dev/null | cut -f1)
        local date=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$backup" 2>/dev/null || stat -c "%y" "$backup" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)
        echo -e "$name\t$size\t$date"
    done
    
    echo ""
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -l|--list)
            list_backups
            exit 0
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            if [ -z "$BACKUP_FILE" ]; then
                BACKUP_FILE="$1"
                shift
            else
                log_error "Unknown option: $1"
                print_usage
                exit 1
            fi
            ;;
    esac
done

# Check if backup file is specified
if [ -z "$BACKUP_FILE" ]; then
    log_error "No backup file specified"
    print_usage
    exit 1
fi

# Detect deployment type if not specified
detect_deployment_type() {
    if [ -n "$DEPLOYMENT_TYPE" ]; then
        log_verbose "Using specified deployment type: $DEPLOYMENT_TYPE"
        return
    fi

    log_info "Auto-detecting deployment type..."
    
    # Check if Docker container exists
    if command -v docker &> /dev/null; then
        if docker ps -a --format '{{.Names}}' | grep -q "neo4j-baziev"; then
            DEPLOYMENT_TYPE="docker"
            log_info "Detected Docker deployment"
            return
        fi
    fi
    
    # Check if local Neo4j exists
    if command -v neo4j &> /dev/null; then
        DEPLOYMENT_TYPE="local"
        log_info "Detected local Neo4j (Homebrew) deployment"
        return
    fi
    
    log_error "Could not detect Neo4j deployment. Please specify with -t flag."
    exit 1
}

# Find backup file
find_backup_file() {
    # If it's a full path and exists, use it
    if [ -f "$BACKUP_FILE" ]; then
        log_verbose "Using backup file: $BACKUP_FILE"
        return
    fi
    
    # Try adding .tar.gz extension
    if [ -f "${BACKUP_FILE}.tar.gz" ]; then
        BACKUP_FILE="${BACKUP_FILE}.tar.gz"
        log_verbose "Using backup file: $BACKUP_FILE"
        return
    fi
    
    # Try in backup directory
    if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
        log_verbose "Using backup file: $BACKUP_FILE"
        return
    fi
    
    if [ -f "$BACKUP_DIR/${BACKUP_FILE}.tar.gz" ]; then
        BACKUP_FILE="$BACKUP_DIR/${BACKUP_FILE}.tar.gz"
        log_verbose "Using backup file: $BACKUP_FILE"
        return
    fi
    
    # Try as directory
    if [ -d "$BACKUP_DIR/$BACKUP_FILE" ]; then
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
        log_verbose "Using backup directory: $BACKUP_FILE"
        return
    fi
    
    log_error "Backup file not found: $BACKUP_FILE"
    log_info "Available backups:"
    list_backups
    exit 1
}

# Confirm restore
confirm_restore() {
    if [ "$FORCE" = true ]; then
        log_warning "Force mode enabled, skipping confirmation"
        return
    fi
    
    log_warning "This will REPLACE the current database with the backup!"
    log_warning "All current data will be lost."
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "Restore cancelled"
        exit 0
    fi
}

# Restore Docker deployment
restore_docker() {
    local container_name="neo4j-baziev"
    local temp_dir="$SCRIPT_DIR/temp_restore_$$"
    
    log_info "Starting Docker restore..."
    
    # Stop container
    log_info "Stopping Neo4j container..."
    docker stop "$container_name" || {
        log_error "Failed to stop container"
        exit 1
    }
    
    # Create temp directory and extract backup
    mkdir -p "$temp_dir"
    
    if [ -f "$BACKUP_FILE" ]; then
        log_info "Extracting backup..."
        tar -xzf "$BACKUP_FILE" -C "$temp_dir" || {
            log_error "Failed to extract backup"
            rm -rf "$temp_dir"
            docker start "$container_name"
            exit 1
        }
    else
        log_info "Copying backup directory..."
        cp -R "$BACKUP_FILE"/* "$temp_dir/" || {
            log_error "Failed to copy backup"
            rm -rf "$temp_dir"
            docker start "$container_name"
            exit 1
        }
    fi
    
    # Remove old data
    log_info "Removing old data from container..."
    docker exec "$container_name" rm -rf /data/* || log_warning "Could not remove old data"
    
    # Copy backup to container
    log_info "Copying backup to container..."
    if [ -d "$temp_dir/data" ]; then
        docker cp "$temp_dir/data/." "$container_name:/data/" || {
            log_error "Failed to copy backup to container"
            rm -rf "$temp_dir"
            docker start "$container_name"
            exit 1
        }
    else
        docker cp "$temp_dir/." "$container_name:/data/" || {
            log_error "Failed to copy backup to container"
            rm -rf "$temp_dir"
            docker start "$container_name"
            exit 1
        }
    fi
    
    # Fix permissions
    log_info "Fixing permissions..."
    docker exec "$container_name" chown -R neo4j:neo4j /data || log_warning "Could not fix permissions"
    
    # Cleanup temp directory
    rm -rf "$temp_dir"
    
    # Start container
    log_info "Starting Neo4j container..."
    docker start "$container_name" || {
        log_error "Failed to start container"
        exit 1
    }
    
    # Wait for Neo4j to be ready
    log_info "Waiting for Neo4j to start..."
    sleep 10
    
    local retries=30
    while [ $retries -gt 0 ]; do
        if docker exec "$container_name" cypher-shell -u neo4j -p 20021030 "RETURN 1" &>/dev/null; then
            break
        fi
        sleep 2
        retries=$((retries - 1))
    done
    
    if [ $retries -eq 0 ]; then
        log_warning "Neo4j may not be fully started yet"
    else
        log_success "Neo4j is ready"
    fi
}

# Restore local deployment (Homebrew)
restore_local() {
    local temp_dir="$SCRIPT_DIR/temp_restore_$$"
    
    log_info "Starting local Neo4j restore..."
    
    # Find Neo4j home directory
    local neo4j_home=$(neo4j console 2>&1 | grep -o 'NEO4J_HOME=.*' | cut -d'=' -f2 | head -n1)
    if [ -z "$neo4j_home" ]; then
        neo4j_home="/usr/local/var/neo4j"
        log_warning "Could not detect NEO4J_HOME, using default: $neo4j_home"
    fi
    
    local data_dir="$neo4j_home/data"
    
    log_verbose "Neo4j data directory: $data_dir"
    
    # Stop Neo4j
    log_info "Stopping Neo4j..."
    neo4j stop || log_warning "Neo4j may already be stopped"
    sleep 2
    
    # Backup current data (just in case)
    if [ -d "$data_dir" ]; then
        local safety_backup="$data_dir.pre_restore_$(date +%Y%m%d_%H%M%S)"
        log_info "Creating safety backup of current data..."
        mv "$data_dir" "$safety_backup"
        log_verbose "Safety backup: $safety_backup"
    fi
    
    # Create temp directory and extract backup
    mkdir -p "$temp_dir"
    mkdir -p "$data_dir"
    
    if [ -f "$BACKUP_FILE" ]; then
        log_info "Extracting backup..."
        tar -xzf "$BACKUP_FILE" -C "$temp_dir" || {
            log_error "Failed to extract backup"
            rm -rf "$temp_dir"
            [ -d "$safety_backup" ] && mv "$safety_backup" "$data_dir"
            neo4j start
            exit 1
        }
    else
        log_info "Copying backup directory..."
        cp -R "$BACKUP_FILE"/* "$temp_dir/" || {
            log_error "Failed to copy backup"
            rm -rf "$temp_dir"
            [ -d "$safety_backup" ] && mv "$safety_backup" "$data_dir"
            neo4j start
            exit 1
        }
    fi
    
    # Copy data
    log_info "Restoring data..."
    if [ -d "$temp_dir/data" ]; then
        cp -R "$temp_dir/data"/* "$data_dir/" || {
            log_error "Failed to restore data"
            rm -rf "$temp_dir"
            [ -d "$safety_backup" ] && mv "$safety_backup" "$data_dir"
            neo4j start
            exit 1
        }
    else
        cp -R "$temp_dir"/* "$data_dir/" || {
            log_error "Failed to restore data"
            rm -rf "$temp_dir"
            [ -d "$safety_backup" ] && mv "$safety_backup" "$data_dir"
            neo4j start
            exit 1
        }
    fi
    
    # Cleanup temp directory
    rm -rf "$temp_dir"
    
    # Start Neo4j
    log_info "Starting Neo4j..."
    neo4j start
    sleep 5
    
    log_success "Restore completed"
    log_info "Safety backup kept at: $safety_backup"
}

# Main restore function
main() {
    log_info "=== Neo4j Restore Script ==="
    log_info "Timestamp: $(date)"
    
    # Detect deployment type
    detect_deployment_type
    
    # Find backup file
    find_backup_file
    
    log_info "Backup file: $BACKUP_FILE"
    
    # Confirm restore
    confirm_restore
    
    # Perform restore based on deployment type
    case "$DEPLOYMENT_TYPE" in
        docker)
            restore_docker
            ;;
        local)
            restore_local
            ;;
        *)
            log_error "Invalid deployment type: $DEPLOYMENT_TYPE"
            exit 1
            ;;
    esac
    
    log_success "=== Restore completed successfully ==="
    log_info "You can now access Neo4j at http://localhost:7474"
}

# Run main function
main
