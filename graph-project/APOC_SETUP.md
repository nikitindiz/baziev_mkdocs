# APOC Setup Guide

## What is APOC?

APOC (Awesome Procedures On Cypher) is a library of procedures and functions for Neo4j that adds hundreds of useful utilities for:
- Graph algorithms
- Data import/export
- Text processing
- Date/time handling
- Graph refactoring
- And much more!

## Why You Need APOC for This Project

The graph schema operations (like `apoc.meta.schema()`) mentioned in the error messages require APOC to be installed. This is essential for:
- Visualizing the complete graph structure
- Analyzing relationships between nodes
- Getting metadata about the graph

## Installation Methods

### Method 1: Homebrew Installation (Recommended for macOS)

If you installed Neo4j via Homebrew:

```bash
# Install APOC plugin
brew install neo4j-apoc

# Or manually download and install
NEO4J_VERSION=$(neo4j version | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
echo "Neo4j version: $NEO4J_VERSION"

# Download APOC (adjust version to match your Neo4j version)
cd ~/Library/Application\ Support/Neo4j/relate-data/dbmss/dbms-*/plugins/
# or for standalone installation:
# cd /usr/local/Cellar/neo4j/*/libexec/plugins/

# Download the latest APOC version compatible with your Neo4j
curl -L -O https://github.com/neo4j/apoc/releases/download/5.14.0/apoc-5.14.0-core.jar
```

### Method 2: Manual Installation

1. **Find your Neo4j plugins directory:**

```bash
# For Homebrew installation:
ls -la /usr/local/Cellar/neo4j/*/libexec/plugins/

# For Neo4j Desktop:
ls -la ~/Library/Application\ Support/Neo4j/relate-data/dbmss/*/plugins/

# For standalone installation:
ls -la /path/to/neo4j/plugins/
```

2. **Download APOC:**

Visit: https://github.com/neo4j/apoc/releases

Download the version matching your Neo4j version. For Neo4j 5.14.x:
```bash
wget https://github.com/neo4j/apoc/releases/download/5.14.0/apoc-5.14.0-core.jar
```

3. **Copy to plugins directory:**

```bash
cp apoc-5.14.0-core.jar /path/to/neo4j/plugins/
```

### Method 3: Docker Installation

If you're using Docker (add this to your docker-compose.yml or run command):

```bash
docker run -d \
  --name neo4j-baziev \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc"]' \
  -e NEO4J_apoc_export_file_enabled=true \
  -e NEO4J_apoc_import_file_enabled=true \
  -e NEO4J_apoc_import_file_use__neo4j__config=true \
  -v $PWD/neo4j-data:/data \
  -v $PWD/neo4j-plugins:/plugins \
  neo4j:5.14
```

## Configuration

After installing APOC, you need to configure Neo4j to allow it:

1. **Find your Neo4j configuration file:**

```bash
# For Homebrew:
ls -la /usr/local/etc/neo4j/neo4j.conf

# For Neo4j Desktop:
ls -la ~/Library/Application\ Support/Neo4j/relate-data/dbmss/*/conf/neo4j.conf
```

2. **Edit neo4j.conf and add/uncomment these lines:**

```properties
# APOC Configuration
dbms.security.procedures.unrestricted=apoc.*
dbms.security.procedures.allowlist=apoc.*

# Enable APOC features
apoc.export.file.enabled=true
apoc.import.file.enabled=true
apoc.import.file.use_neo4j_config=true
```

3. **Restart Neo4j:**

```bash
# For Homebrew:
neo4j restart

# For Neo4j Desktop:
# Stop and start the database from the UI

# For Docker:
docker restart neo4j-baziev
```

## Verification

Run the verification script to check if APOC is installed correctly:

```bash
cd graph-project
python verify_apoc.py
```

Or manually check in Neo4j Browser (http://localhost:7474):

```cypher
// Check if APOC is loaded
CALL apoc.help("apoc")

// Test apoc.meta.schema
CALL apoc.meta.schema()

// List all APOC procedures
CALL dbms.procedures() 
YIELD name 
WHERE name STARTS WITH 'apoc' 
RETURN name 
LIMIT 10
```

## Common Issues

### Issue 1: "Procedure not found"
**Solution:** APOC jar file is not in the plugins directory or Neo4j wasn't restarted.

### Issue 2: "Permission denied"
**Solution:** Add APOC to allowlist in neo4j.conf:
```properties
dbms.security.procedures.allowlist=apoc.*
```

### Issue 3: Wrong APOC version
**Solution:** Ensure APOC version matches Neo4j version (e.g., Neo4j 5.14 needs APOC 5.14.x)

### Issue 4: Multiple Neo4j installations
**Solution:** Make sure you're adding APOC to the correct Neo4j instance:
```bash
# Find running Neo4j process
ps aux | grep neo4j

# Check which config is being used
lsof -p <neo4j-pid> | grep neo4j.conf
```

## Quick Installation Script

Save and run this script for automated installation:

```bash
./install_apoc.sh
```

## Resources

- [APOC Documentation](https://neo4j.com/labs/apoc/)
- [APOC GitHub](https://github.com/neo4j/apoc)
- [APOC User Guide](https://neo4j.com/labs/apoc/5/)
- [Installation Guide](https://neo4j.com/labs/apoc/5/installation/)

## Next Steps

After installing APOC, you can use enhanced features in this project:

```bash
# Get graph schema
python main.py query graph-schema

# Use APOC for advanced exports
python main.py export --format apoc-json

# Run APOC-based analysis
python main.py analyze --use-apoc
```
