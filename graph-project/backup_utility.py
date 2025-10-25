#!/usr/bin/env python3
"""
Python Database Backup Utility for Neo4j Baziev Physics Graph
Provides programmatic backup and restore capabilities
"""

import os
import sys
import json
import shutil
import tarfile
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.utils.neo4j_connection import Neo4jConnection
from src.utils.config import load_config


class Neo4jBackup:
    """Neo4j backup and restore utility"""
    
    def __init__(self, config_path: str = "config/config.yml"):
        """Initialize backup utility
        
        Args:
            config_path: Path to config file
        """
        self.config = load_config(config_path)
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self, 
                     name: Optional[str] = None,
                     compress: bool = True,
                     include_cypher: bool = True) -> Path:
        """Create a backup of the Neo4j database
        
        Args:
            name: Backup name (default: auto-generated with timestamp)
            compress: Compress backup to .tar.gz
            include_cypher: Include Cypher export (requires APOC)
            
        Returns:
            Path to backup file/directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"neo4j_backup_{timestamp}"
        
        print(f"Creating backup: {backup_name}")
        
        # Create temp directory for backup
        temp_dir = self.backup_dir / f"temp_{timestamp}"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Export using Cypher (if APOC available)
            if include_cypher:
                cypher_file = self._export_cypher(backup_name, temp_dir)
                if cypher_file:
                    print(f"✓ Cypher export completed: {cypher_file.name}")
            
            # Export graph statistics
            stats_file = self._export_statistics(backup_name, temp_dir)
            print(f"✓ Statistics exported: {stats_file.name}")
            
            # Create metadata
            metadata_file = self._create_metadata(backup_name, temp_dir)
            print(f"✓ Metadata created: {metadata_file.name}")
            
            # Compress or move
            if compress:
                backup_path = self.backup_dir / f"{backup_name}.tar.gz"
                self._compress_backup(temp_dir, backup_path)
                print(f"✓ Backup compressed: {backup_path}")
            else:
                backup_path = self.backup_dir / backup_name
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                shutil.move(str(temp_dir), str(backup_path))
                print(f"✓ Backup created: {backup_path}")
                
            # Cleanup temp directory if it still exists
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                
            print(f"\n✓ Backup completed: {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"✗ Backup failed: {e}", file=sys.stderr)
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise
            
    def _export_cypher(self, backup_name: str, output_dir: Path) -> Optional[Path]:
        """Export database to Cypher file using APOC
        
        Args:
            backup_name: Backup name
            output_dir: Output directory
            
        Returns:
            Path to Cypher file or None if export failed
        """
        try:
            neo4j_config = self.config['neo4j']
            conn = Neo4jConnection(
                uri=neo4j_config['uri'],
                user=neo4j_config['username'],
                password=neo4j_config['password'],
                database=neo4j_config['database']
            )
            cypher_file = output_dir / f"{backup_name}.cypher"
            
            with conn.driver.session() as session:
                # Check if APOC is available
                result = session.run("""
                    CALL dbms.procedures() 
                    YIELD name 
                    WHERE name = 'apoc.export.cypher.all'
                    RETURN count(*) as count
                """)
                
                if result.single()['count'] == 0:
                    print("! APOC not available, skipping Cypher export")
                    conn.close()
                    return None
                
                # Export to Cypher
                result = session.run(f"""
                    CALL apoc.export.cypher.all('{cypher_file}', {{
                        format: 'cypher-shell',
                        useOptimizations: {{type: 'UNWIND_BATCH', unwindBatchSize: 20}}
                    }})
                    YIELD file, nodes, relationships, properties, time
                    RETURN file, nodes, relationships, properties, time
                """)
                
                record = result.single()
                if record:
                    print(f"  Exported {record['nodes']} nodes, "
                          f"{record['relationships']} relationships")
                          
            conn.close()
            return cypher_file
            
        except Exception as e:
            print(f"! Cypher export failed: {e}")
            return None
            
    def _export_statistics(self, backup_name: str, output_dir: Path) -> Path:
        """Export graph statistics
        
        Args:
            backup_name: Backup name
            output_dir: Output directory
            
        Returns:
            Path to statistics file
        """
        neo4j_config = self.config['neo4j']
        conn = Neo4jConnection(
            uri=neo4j_config['uri'],
            user=neo4j_config['username'],
            password=neo4j_config['password'],
            database=neo4j_config['database']
        )
        stats_file = output_dir / f"{backup_name}_stats.json"
        
        stats = {}
        
        with conn.driver.session() as session:
            # Node counts by label
            result = session.run("""
                CALL db.labels() YIELD label
                CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {})
                YIELD value
                RETURN label, value.count as count
                ORDER BY label
            """)
            stats['nodes_by_label'] = {record['label']: record['count'] 
                                       for record in result}
            
            # Relationship counts by type
            result = session.run("""
                CALL db.relationshipTypes() YIELD relationshipType
                CALL apoc.cypher.run('MATCH ()-[r:' + relationshipType + ']->() RETURN count(r) as count', {})
                YIELD value
                RETURN relationshipType, value.count as count
                ORDER BY relationshipType
            """)
            stats['relationships_by_type'] = {record['relationshipType']: record['count'] 
                                              for record in result}
            
            # Total counts
            result = session.run("""
                MATCH (n) RETURN count(n) as total_nodes
            """)
            stats['total_nodes'] = result.single()['total_nodes']
            
            result = session.run("""
                MATCH ()-[r]->() RETURN count(r) as total_relationships
            """)
            stats['total_relationships'] = result.single()['total_relationships']
            
        conn.close()
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
            
        return stats_file
        
    def _create_metadata(self, backup_name: str, output_dir: Path) -> Path:
        """Create backup metadata
        
        Args:
            backup_name: Backup name
            output_dir: Output directory
            
        Returns:
            Path to metadata file
        """
        metadata_file = output_dir / f"{backup_name}_metadata.json"
        
        neo4j_config = self.config['neo4j']
        conn = Neo4jConnection(
            uri=neo4j_config['uri'],
            user=neo4j_config['username'],
            password=neo4j_config['password'],
            database=neo4j_config['database']
        )
        
        # Get Neo4j version
        with conn.driver.session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions WHERE name = 'Neo4j Kernel' RETURN versions[0] as version LIMIT 1")
            record = result.single()
            neo4j_version = record['version'] if record else "unknown"
            
        conn.close()
        
        metadata = {
            'backup_name': backup_name,
            'timestamp': datetime.now().isoformat(),
            'neo4j_version': neo4j_version,
            'config': {
                'uri': self.config['neo4j']['uri'],
                'database': self.config['neo4j']['database']
            },
            'book': self.config['book']
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        return metadata_file
        
    def _compress_backup(self, source_dir: Path, output_file: Path):
        """Compress backup directory to tar.gz
        
        Args:
            source_dir: Source directory to compress
            output_file: Output tar.gz file
        """
        with tarfile.open(output_file, 'w:gz') as tar:
            tar.add(source_dir, arcname=source_dir.name)
            
    def list_backups(self) -> list:
        """List all available backups
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        for item in sorted(self.backup_dir.iterdir(), reverse=True):
            # Skip hidden files, temp directories, and non-backup files
            if item.name.startswith('.') or item.name.startswith('temp_'):
                continue
            
            # Check if it's a backup file or directory
            is_backup = (
                (item.is_file() and item.suffix == '.gz') or
                (item.is_dir() and not item.name.startswith('temp_'))
            )
            
            if is_backup:
                backup_info = {
                    'name': item.name.replace('.tar.gz', ''),
                    'path': str(item),
                    'compressed': item.suffix == '.gz',
                    'size': self._format_size(self._get_size(item)),
                    'date': datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Try to read metadata
                metadata_file = None
                if item.is_dir():
                    metadata_file = item / f"{item.name}_metadata.json"
                    
                if metadata_file and metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                        backup_info['metadata'] = metadata
                        
                backups.append(backup_info)
                
        return backups
        
    def _get_size(self, path: Path) -> int:
        """Get size of file or directory
        
        Args:
            path: Path to file or directory
            
        Returns:
            Size in bytes
        """
        if path.is_file():
            return path.stat().st_size
        else:
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            
    def _format_size(self, size: int) -> str:
        """Format size in human-readable format
        
        Args:
            size: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
        
    def cleanup_old_backups(self, keep: int = 7):
        """Remove old backups, keeping only the most recent ones
        
        Args:
            keep: Number of backups to keep
        """
        backups = self.list_backups()
        
        if len(backups) <= keep:
            print(f"No cleanup needed ({len(backups)} backups, keeping {keep})")
            return
            
        to_remove = backups[keep:]
        
        print(f"Removing {len(to_remove)} old backup(s)...")
        
        for backup in to_remove:
            path = Path(backup['path'])
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                print(f"  Removed: {backup['name']}")
                
        print(f"✓ Cleanup completed")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Neo4j Database Backup Utility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create                    # Create new backup
  %(prog)s create --name my_backup   # Create named backup
  %(prog)s list                      # List all backups
  %(prog)s cleanup --keep 30         # Keep only last 30 backups
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Create backup command
    create_parser = subparsers.add_parser('create', help='Create a new backup')
    create_parser.add_argument('--name', help='Backup name (default: auto-generated)')
    create_parser.add_argument('--no-compress', action='store_true', help='Do not compress backup')
    create_parser.add_argument('--no-cypher', action='store_true', help='Skip Cypher export')
    
    # List backups command
    list_parser = subparsers.add_parser('list', help='List all backups')
    list_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Remove old backups')
    cleanup_parser.add_argument('--keep', type=int, default=7, help='Number of backups to keep (default: 7)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    backup = Neo4jBackup()
    
    if args.command == 'create':
        backup.create_backup(
            name=args.name,
            compress=not args.no_compress,
            include_cypher=not args.no_cypher
        )
        
    elif args.command == 'list':
        backups = backup.list_backups()
        
        if args.json:
            print(json.dumps(backups, indent=2))
        else:
            print(f"\nAvailable backups ({len(backups)}):\n")
            print(f"{'Name':<40} {'Size':<10} {'Date':<20}")
            print("-" * 70)
            for b in backups:
                print(f"{b['name']:<40} {b['size']:<10} {b['date']:<20}")
            print()
            
    elif args.command == 'cleanup':
        backup.cleanup_old_backups(keep=args.keep)


if __name__ == '__main__':
    main()
