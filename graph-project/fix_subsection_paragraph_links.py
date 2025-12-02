#!/usr/bin/env python3
"""
Исправление дублирующихся связей параграфов с подразделами.

Проблема: один параграф связан с несколькими подразделами из-за ошибки
в логике импорта.

Решение: каждый параграф должен принадлежать только одному подразделу -
тому, который начинается последним перед этим параграфом.
"""

import yaml
from pathlib import Path
from neo4j import GraphDatabase
import sys


class Neo4jConnection:
    """Neo4j database connection handler."""

    def __init__(self, uri, user, password, database=None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        if self.driver:
            self.driver.close()

    def execute_query(self, query, parameters=None):
        """Execute a Cypher query."""
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]


class SubsectionParagraphFixer:
    """Fix duplicate paragraph-subsection relationships."""

    def __init__(self, connection, dry_run=False):
        self.conn = connection
        self.dry_run = dry_run

    def find_duplicate_links(self):
        """Find paragraphs linked to multiple subsections."""
        query = """
        MATCH (p:Paragraph)<-[r:CONTAINS_PARAGRAPH]-(sub:Subsection)
        WITH p, count(DISTINCT sub) as subsection_count, 
             collect(DISTINCT {
                 id: sub.id, 
                 title: sub.title,
                 number: sub.number,
                 order: r.order
             }) as subsections
        WHERE subsection_count > 1
        RETURN elementId(p) as paragraph_element_id,
               p.id as paragraph_id, 
               subsection_count,
               subsections
        ORDER BY subsection_count DESC, p.id
        """
        results = self.conn.execute_query(query)
        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Found {len(results)} paragraphs with duplicate links")
        return results

    def fix_paragraph_links(self, paragraph_element_id, subsections):
        """
        Fix paragraph links: keep only the last subsection
        (the one with highest number that should contain this paragraph).
        """
        # Sort subsections by number (descending) to find the correct one
        sorted_subs = sorted(subsections, key=lambda x: int(x['number']), reverse=True)
        
        # The paragraph should belong to the LAST subsection before it
        # Since we sorted descending, we need to find the right one based on order
        # Actually, we need the subsection with the LOWEST number that still contains this paragraph
        sorted_subs = sorted(subsections, key=lambda x: int(x['number']))
        
        correct_subsection = sorted_subs[-1]  # The last (highest numbered) subsection
        subsections_to_remove = [s for s in subsections if s['id'] != correct_subsection['id']]

        if self.dry_run:
            print(f"\n  Paragraph: {paragraph_element_id}")
            print(f"  Would keep: {correct_subsection['number']}. {correct_subsection['title']}")
            print(f"  Would remove from:")
            for sub in subsections_to_remove:
                print(f"    - {sub['number']}. {sub['title']}")
            return

        # Remove incorrect relationships
        for sub in subsections_to_remove:
            query = """
            MATCH (p:Paragraph)<-[r:CONTAINS_PARAGRAPH]-(sub:Subsection)
            WHERE elementId(p) = $paragraph_id AND sub.id = $subsection_id
            DELETE r
            """
            self.conn.execute_query(query, {
                'paragraph_id': paragraph_element_id,
                'subsection_id': sub['id']
            })
            print(f"  Removed link from paragraph to subsection {sub['number']}")

    def fix_all_duplicates(self):
        """Find and fix all duplicate links."""
        duplicates = self.find_duplicate_links()
        
        if not duplicates:
            print("\nNo duplicate links found!")
            return

        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Fixing {len(duplicates)} paragraphs...")
        
        for dup in duplicates:
            self.fix_paragraph_links(
                dup['paragraph_element_id'],
                dup['subsections']
            )

        if not self.dry_run:
            print(f"\nFixed {len(duplicates)} paragraphs")
            
            # Verify
            remaining = self.find_duplicate_links()
            if not remaining:
                print("✅ All duplicates fixed!")
            else:
                print(f"⚠️  Still {len(remaining)} duplicates remaining")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fix duplicate paragraph-subsection relationships'
    )
    parser.add_argument(
        '--config',
        default='graph-project/config/config.yml',
        help='Path to config file (default: graph-project/config/config.yml)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    args = parser.parse_args()
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    neo4j_config = config.get('neo4j', {})
    
    # Connect to Neo4j
    conn = Neo4jConnection(
        uri=neo4j_config.get('uri', 'bolt://localhost:7687'),
        user=neo4j_config.get('user', 'neo4j'),
        password=neo4j_config.get('password', ''),
        database=neo4j_config.get('database')
    )
    
    try:
        fixer = SubsectionParagraphFixer(conn, dry_run=args.dry_run)
        fixer.fix_all_duplicates()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
