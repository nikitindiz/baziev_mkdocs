#!/usr/bin/env python3
"""
Связывание параграфов с подразделами на основе их порядка.

Логика: Параграф принадлежит тому подразделу, который начинается
последним перед этим параграфом (или на той же позиции).
"""

import yaml
from pathlib import Path
from neo4j import GraphDatabase
import sys


class Neo4jConnection:
    def __init__(self, uri, user, password, database=None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        if self.driver:
            self.driver.close()

    def execute_query(self, query, parameters=None):
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]


class ParagraphSubsectionLinker:
    def __init__(self, connection, dry_run=False):
        self.conn = connection
        self.dry_run = dry_run
        self.stats = {'sections': 0, 'linked': 0, 'errors': 0}

    def link_section(self, section_id):
        """Link paragraphs to subsections for one section."""
        # Get subsections and paragraphs
        query = """
        MATCH (s:Section {id: $section_id})
        OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(sub:Subsection)
        OPTIONAL MATCH (s)-[r:HAS_PARAGRAPH]->(p:Paragraph)
        WITH s,
             collect(DISTINCT {
                 id: sub.id,
                 element_id: elementId(sub),
                 number: sub.number,
                 order: sub.order
             }) as subsections,
             collect(DISTINCT {
                 id: p.id,
                 element_id: elementId(p),
                 order: r.order
             }) as paragraphs
        RETURN subsections, paragraphs
        """
        result = self.conn.execute_query(query, {'section_id': section_id})
        if not result or not result[0]['subsections'] or not result[0]['paragraphs']:
            return 0
        
        subsections = [s for s in result[0]['subsections'] if s['id']]
        paragraphs = [p for p in result[0]['paragraphs'] if p['id']]
        
        if not subsections or not paragraphs:
            return 0
        
        # Sort by order
        subsections.sort(key=lambda x: x['order'])
        paragraphs.sort(key=lambda x: x['order'])
        
        # Build mapping: each paragraph → subsection
        links = []
        for para in paragraphs:
            para_order = para['order']
            
            # Find the last subsection that starts at or before this paragraph
            target_sub = None
            for sub in subsections:
                if sub['order'] <= para_order:
                    target_sub = sub
                else:
                    break
            
            if target_sub:
                links.append({
                    'para_id': para['element_id'],
                    'sub_id': target_sub['element_id'],
                    'para_order': para_order,
                    'sub_number': target_sub['number']
                })
        
        # Create links in database
        if not self.dry_run:
            for link in links:
                query = """
                MATCH (p:Paragraph), (sub:Subsection)
                WHERE elementId(p) = $para_id AND elementId(sub) = $sub_id
                CREATE (sub)-[:CONTAINS_PARAGRAPH {order: $para_order}]->(p)
                """
                self.conn.execute_query(query, link)
        
        return len(links)

    def process_all(self):
        """Process all sections with subsections."""
        # Get all sections with subsections
        query = """
        MATCH (s:Section)-[:HAS_SUBSECTION]->(:Subsection)
        WITH DISTINCT s
        RETURN s.id as section_id, s.title as section_title
        ORDER BY s.id
        """
        sections = self.conn.execute_query(query)
        
        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Found {len(sections)} sections with subsections\n")
        
        for section in sections:
            section_id = section['section_id']
            section_title = section['section_title']
            
            try:
                linked = self.link_section(section_id)
                self.stats['sections'] += 1
                self.stats['linked'] += linked
                
                if linked > 0:
                    print(f"{'[DRY RUN] ' if self.dry_run else ''}✓ {section_title}: {linked} paragraphs")
            except Exception as e:
                self.stats['errors'] += 1
                print(f"✗ {section_title}: ERROR - {e}")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"{'[DRY RUN] ' if self.dry_run else ''}Summary:")
        print(f"  Sections processed: {self.stats['sections']}")
        print(f"  Paragraphs linked: {self.stats['linked']}")
        print(f"  Errors: {self.stats['errors']}")
        
        if not self.dry_run:
            # Verify
            query = """
            MATCH (sub:Subsection)
            WHERE NOT (sub)-[:CONTAINS_PARAGRAPH]->()
            RETURN count(sub) as empty_subsections
            """
            result = self.conn.execute_query(query)
            empty = result[0]['empty_subsections'] if result else 0
            
            if empty > 0:
                print(f"\n⚠️  {empty} subsections have no paragraphs (may be correct if markdown has no content)")
            else:
                print(f"\n✅ All subsections have paragraphs!")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Link paragraphs to subsections')
    parser.add_argument('--config', default='graph-project/config/config.yml')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Config not found: {config_path}")
        sys.exit(1)
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    neo4j_config = config.get('neo4j', {})
    conn = Neo4jConnection(
        uri=neo4j_config.get('uri', 'bolt://localhost:7687'),
        user=neo4j_config.get('user', 'neo4j'),
        password=neo4j_config.get('password', ''),
        database=neo4j_config.get('database')
    )
    
    try:
        linker = ParagraphSubsectionLinker(conn, dry_run=args.dry_run)
        linker.process_all()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
