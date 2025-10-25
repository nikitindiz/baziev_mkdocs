# Database Backup and Restore Guide

This guide explains how to backup and restore your Neo4j database for the Baziev Physics Knowledge Graph project.

## 📦 Backup Script

The `backup_db.sh` script creates backups of your Neo4j database. It supports both local (Homebrew) and Docker deployments.

### Features

- ✅ **Auto-detection** - Automatically detects whether you're using Docker or local Neo4j
- ✅ **Multiple backup methods** - Volume backup + Cypher export (APOC)
- ✅ **Compression** - Automatically compresses backups to save space
- ✅ **Retention policy** - Keeps last N backups, removes old ones
- ✅ **Metadata** - Stores backup metadata (timestamp, version, etc.)
- ✅ **Safe backups** - For local deployments, stops/starts Neo4j safely

### Usage

#### Basic backup
```bash
cd graph-project
chmod +x backup_db.sh
./backup_db.sh
```

#### Advanced options
```bash
# Force Docker mode
./backup_db.sh -t docker

# Custom backup directory
./backup_db.sh -d /path/to/backups

# Keep 30 backups instead of 7
./backup_db.sh -k 30

# Don't compress (faster, but larger)
./backup_db.sh -n

# Verbose output
./backup_db.sh -v

# All options combined
./backup_db.sh -t docker -d /custom/backup -k 30 -v
```

#### Help
```bash
./backup_db.sh -h
```

### What gets backed up?

1. **Complete data directory** - All nodes, relationships, indexes, constraints
2. **Cypher export** (if APOC is available) - Portable Cypher script for easy restore
3. **Metadata** - Timestamp, Neo4j version, deployment type

### Backup location

By default, backups are stored in `graph-project/backups/` with the naming pattern:
- `neo4j_backup_YYYYMMDD_HHMMSS.tar.gz` (compressed)
- `neo4j_backup_YYYYMMDD_HHMMSS/` (uncompressed)

### Backup size

Typical backup sizes:
- **Compressed**: ~20-50 MB (depending on data)
- **Uncompressed**: ~100-200 MB

## 🔄 Restore Script

The `restore_db.sh` script restores your Neo4j database from a backup.

### Features

- ✅ **Auto-detection** - Automatically detects deployment type
- ✅ **List backups** - Shows all available backups
- ✅ **Safety backup** - Creates a safety backup before restoring (local mode)
- ✅ **Confirmation prompt** - Prevents accidental data loss
- ✅ **Force mode** - Skip confirmation for automated scripts

### Usage

#### List available backups
```bash
cd graph-project
chmod +x restore_db.sh
./restore_db.sh -l
```

#### Restore a backup
```bash
# Restore by backup name
./restore_db.sh neo4j_backup_20250126_120000

# Restore with full path
./restore_db.sh backups/neo4j_backup_20250126_120000.tar.gz

# Force restore without confirmation
./restore_db.sh -f neo4j_backup_20250126_120000

# Verbose output
./restore_db.sh -v neo4j_backup_20250126_120000
```

#### Help
```bash
./restore_db.sh -h
```

### ⚠️ Important Notes

1. **Data loss warning**: Restoring will **REPLACE ALL CURRENT DATA**
2. **Safety backup**: Local mode creates a safety backup (`.pre_restore_TIMESTAMP`)
3. **Downtime**: Neo4j will be stopped during restore (a few seconds to minutes)
4. **Confirmation**: You'll be asked to confirm unless using `-f` flag

## 🔧 Scheduled Backups

### Using cron (macOS/Linux)

Edit your crontab:
```bash
crontab -e
```

Add one of these lines:

```bash
# Daily backup at 2 AM
0 2 * * * cd /Users/electrino/work/vibed/baziev_mkdocs/graph-project && ./backup_db.sh >> logs/backup.log 2>&1

# Backup every 6 hours
0 */6 * * * cd /Users/electrino/work/vibed/baziev_mkdocs/graph-project && ./backup_db.sh >> logs/backup.log 2>&1

# Weekly backup on Sunday at 3 AM
0 3 * * 0 cd /Users/electrino/work/vibed/baziev_mkdocs/graph-project && ./backup_db.sh >> logs/backup.log 2>&1
```

Create logs directory:
```bash
mkdir -p graph-project/logs
```

### Using launchd (macOS)

Create a plist file at `~/Library/LaunchAgents/com.baziev.neo4j.backup.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.baziev.neo4j.backup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/electrino/work/vibed/baziev_mkdocs/graph-project/backup_db.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/electrino/work/vibed/baziev_mkdocs/graph-project/logs/backup.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/electrino/work/vibed/baziev_mkdocs/graph-project/logs/backup_error.log</string>
</dict>
</plist>
```

Load the job:
```bash
launchctl load ~/Library/LaunchAgents/com.baziev.neo4j.backup.plist
```

## 📊 Backup Best Practices

### Frequency

- **Development**: Weekly or before major changes
- **Production**: Daily or multiple times per day
- **Before imports**: Always backup before running `import all`

### Retention

- **Short-term**: Keep last 7 days (default)
- **Medium-term**: Keep weekly backups for 1 month
- **Long-term**: Keep monthly backups for 1 year

### Storage

- **Local backups**: Good for quick recovery
- **Remote backups**: Copy to cloud storage (Google Drive, Dropbox, S3)
- **Multiple locations**: Store backups in at least 2 different locations

### Verification

Test restore process periodically:
```bash
# List backups
./restore_db.sh -l

# Restore to test database
# (modify config to use different database)
./restore_db.sh -f latest_backup
```

## 🐛 Troubleshooting

### Backup fails with "APOC not found"

This is OK! The script will still create a volume backup. To enable Cypher export:
```bash
./install_apoc.sh
```

### "Permission denied" error

Make scripts executable:
```bash
chmod +x backup_db.sh restore_db.sh
```

### Docker container not found

Make sure container is running:
```bash
docker ps | grep neo4j-baziev
```

Start if needed:
```bash
docker-compose up -d
```

### Local Neo4j not detected

Check if Neo4j is installed:
```bash
which neo4j
neo4j status
```

Install if needed:
```bash
brew install neo4j
```

### Backup too large

Use compression (enabled by default):
```bash
./backup_db.sh  # Creates .tar.gz file
```

Or clean up old backups:
```bash
./backup_db.sh -k 3  # Keep only last 3 backups
```

### Restore takes too long

This is normal for large databases. Typical times:
- Small (< 100 MB): 10-30 seconds
- Medium (100-500 MB): 1-3 minutes
- Large (> 500 MB): 5-10 minutes

## 🔐 Security

### Backup encryption

For sensitive data, encrypt backups:
```bash
# Encrypt backup
openssl enc -aes-256-cbc -salt -in backup.tar.gz -out backup.tar.gz.enc

# Decrypt backup
openssl enc -aes-256-cbc -d -in backup.tar.gz.enc -out backup.tar.gz
```

### Backup passwords

Store passwords securely:
```bash
# Use environment variables instead of hardcoding
export NEO4J_PASSWORD="your_password"
```

## 📋 Quick Reference

### Backup
```bash
./backup_db.sh              # Auto-detect and backup
./backup_db.sh -v           # Verbose
./backup_db.sh -k 30        # Keep 30 backups
```

### Restore
```bash
./restore_db.sh -l          # List backups
./restore_db.sh NAME        # Restore backup
./restore_db.sh -f NAME     # Force restore
```

### Scheduling
```bash
# Add to crontab
0 2 * * * cd /path/to/graph-project && ./backup_db.sh
```

## 🆘 Emergency Recovery

If something goes wrong:

1. **Check logs**: Look at script output and Neo4j logs
2. **Safety backup**: Local mode creates `.pre_restore_*` backups
3. **Manual restore**: Copy data directory manually if needed
4. **Re-import**: Worst case, re-run `python main.py import all`

## 📞 Support

For issues or questions:
1. Check this guide
2. Check script help: `./backup_db.sh -h`
3. Review Neo4j logs
4. Create an issue in the project repository
