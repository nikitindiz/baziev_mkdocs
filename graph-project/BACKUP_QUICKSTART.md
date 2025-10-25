# Backup & Restore Quick Start

## 🚀 Quick Examples

### Create a backup
```bash
# Simple backup (auto-detects Docker or local)
./backup_db.sh

# With verbose output
./backup_db.sh -v

# Keep more backups (default is 7)
./backup_db.sh -k 30
```

### List backups
```bash
# Using bash script
ls -lht backups/

# Using Python utility
python backup_utility.py list
```

### Restore a backup
```bash
# List available backups first
./restore_db.sh -l

# Restore specific backup
./restore_db.sh neo4j_backup_20250126_120000

# Force restore (no confirmation prompt)
./restore_db.sh -f neo4j_backup_20250126_120000
```

## 📊 Python Utility Examples

### Create backup programmatically
```python
from backup_utility import Neo4jBackup

# Initialize
backup = Neo4jBackup()

# Create backup
backup_path = backup.create_backup(
    name="my_custom_backup",
    compress=True,
    include_cypher=True
)
print(f"Backup created: {backup_path}")
```

### List and manage backups
```python
from backup_utility import Neo4jBackup

backup = Neo4jBackup()

# List all backups
backups = backup.list_backups()
for b in backups:
    print(f"{b['name']} - {b['size']} - {b['date']}")

# Cleanup old backups
backup.cleanup_old_backups(keep=10)
```

## ⏰ Automated Backups

### Daily backup at 2 AM
```bash
# Add to crontab
crontab -e

# Add this line:
0 2 * * * cd /Users/electrino/work/vibed/baziev_mkdocs/graph-project && ./backup_db.sh >> logs/backup.log 2>&1
```

### Before every import
Add to your import script:
```bash
#!/bin/bash
# backup_and_import.sh

cd /Users/electrino/work/vibed/baziev_mkdocs/graph-project

# Create backup before import
echo "Creating backup before import..."
./backup_db.sh -v

# Run import
echo "Running import..."
python main.py import all

echo "Done!"
```

## 📁 Backup Structure

Each backup contains:
- **Data export** - Complete Neo4j data directory
- **Cypher export** - Portable Cypher script (if APOC available)
- **Statistics** - Node and relationship counts
- **Metadata** - Timestamp, version, configuration

Example:
```
backups/
├── neo4j_backup_20250126_120000.tar.gz    # Compressed backup
├── neo4j_backup_20250126_120000_metadata.json
└── neo4j_backup_20250126_120000_cypher.cypher
```

## 🔄 Common Workflows

### Before Major Changes
```bash
# Create named backup
./backup_db.sh
# or with custom name
python backup_utility.py create --name before_v2_import
```

### Disaster Recovery
```bash
# List backups
./restore_db.sh -l

# Restore most recent
./restore_db.sh -f neo4j_backup_20250126_120000

# Verify restoration
python graph_stats.py
```

### Weekly Cleanup
```bash
# Keep only last 30 days
./backup_db.sh -k 30

# Or using Python
python backup_utility.py cleanup --keep 30
```

## 🐛 Troubleshooting

### "APOC not found"
```bash
# Install APOC
./install_apoc.sh

# Verify
python verify_apoc.py
```

### "Permission denied"
```bash
# Make scripts executable
chmod +x backup_db.sh restore_db.sh backup_utility.py
```

### Check backup integrity
```bash
# List backup contents
tar -tzf backups/neo4j_backup_20250126_120000.tar.gz

# View metadata
cat backups/neo4j_backup_20250126_120000_metadata.json
```

## 📖 Full Documentation

See [BACKUP_GUIDE.md](BACKUP_GUIDE.md) for complete documentation.
