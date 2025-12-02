#!/usr/bin/env python3
"""
Исправление связей параграфов с подразделами (версия 2).

Проблема v1: Скрипт оставлял параграфы в последнем (наибольшем) подразделе,
но реально параграфы должны быть связаны с ПРЕДЫДУЩИМ подразделом
(тем, после которого они идут в тексте).

Решение: Параграфы принадлежат подразделу, который начинается ПЕРЕД ними.
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


class SubsectionParagraphFixerV2:
    """Fix paragraph-subsection relationships based on actual order."""

    def __init__(self, connection, dry_run=False):
        self.conn = connection
        self.dry_run = dry_run

    def get_sections_with_subsections(self):
        """Get all sections that have subsections."""
        query = """
        MATCH (s:Section)-[:HAS_SUBSECTION]->(sub:Subsection)
        WITH s, count(DISTINCT sub) as sub_count
        WHERE sub_count > 0
        RETURN DISTINCT s.id as section_id, s.title as section_title, sub_count
        ORDER BY s.id
        """
        return self.conn.execute_query(query)

    def reassign_paragraphs_for_section(self, section_id):
        """
        Reassign paragraphs to correct subsections based on order.
        
        Logic: 
        - Paragraphs with order < first subsection order → no subsection
        - Paragraphs between subsection N and N+1 → belong to subsection N
        - Paragraphs after last subsection → belong to last subsection
        """
        # Get all subsections and paragraphs for this section, ordered
        query = """
        MATCH (s:Section {id: $section_id})
        OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(sub:Subsection)
        OPTIONAL MATCH (s)-[:CONTAINS_PARAGRAPH]->(p:Paragraph)
        WITH s, 
             collect(DISTINCT {
                 id: sub.id, 
                 number: sub.number, 
                 title: sub.title,
                 order: sub.order,
                 element_id: elementId(sub)
             }) as subsections,
             collect(DISTINCT {
                 id: p.id,
                 order: p.order,
                 element_id: elementId(p)
             }) as paragraphs
        RETURN subsections, paragraphs
        """
        result = self.conn.execute_query(query, {'section_id': section_id})
        if not result:
            return
        
        data = result[0]
        subsections = sorted([s for s in data['subsections'] if s['id']], 
                           key=lambda x: x['order'])
        paragraphs = sorted([p for p in data['paragraphs'] if p['id']], 
                          key=lambda x: x['order'])
        
        if not subsections or not paragraphs:
            return
        
        # Build assignment map: paragraph -> subsection
        assignments = {}
        
        for para in paragraphs:
            para_order = para['order']
            
            # Find the subsection this paragraph belongs to
            # It's the last subsection that starts at or before this paragraph
            target_sub = None
            for sub in subsections:
                if sub['order'] <= para_order:
                    target_sub = sub
                else:
                    break  # subsections are sorted, so we can break
            
            if target_sub:
                assignments[para['element_id']] = target_sub['element_id']
        
        # Now update the database
        for para_id, sub_id in assignments.items():
            self.update_paragraph_subsection(para_id, sub_id, section_id)
        
        return len(assignments)

    def update_paragraph_subsection(self, paragraph_element_id, subsection_element_id, section_id):
        """Remove all subsection links and add the correct one."""
        
        if self.dry_run:
            # Just show what would happen
            query_current = """
            MATCH (p:Paragraph)<-[r:CONTAINS_PARAGRAPH]-(sub:Subsection)
            WHERE elementId(p) = $para_id
            RETURN sub.number as current_sub_number, sub.title as current_sub_title
            """
            current = self.conn.execute_query(query_current, {'para_id': paragraph_element_id})
            
            query_target = """
            MATCH (sub:Subsection)
            WHERE elementId(sub) = $sub_id
            RETURN sub.number as target_sub_number, sub.title as target_sub_title
            """
            target = self.conn.execute_query(query_target, {'sub_id': subsection_element_id})
            
            if current and target:
                print(f"  Would move paragraph from subsection {current[0]['current_sub_number']} "
                      f"to {target[0]['target_sub_number']}")
            return
        
        # Remove all existing subsection relationships for this paragraph
        query_remove = """
        MATCH (p:Paragraph)<-[r:CONTAINS_PARAGRAPH]-(sub:Subsection)
        WHERE elementId(p) = $para_id
        DELETE r
        """
        self.conn.execute_query(query_remove, {'para_id': paragraph_element_id})
        
        # Add the correct relationship
        query_add = """
        MATCH (p:Paragraph), (sub:Subsection)
        WHERE elementId(p) = $para_id AND elementId(sub) = $sub_id
        CREATE (sub)-[:CONTAINS_PARAGRAPH {order: p.order}]->(p)
        """
        self.conn.execute_query(query_add, {
            'para_id': paragraph_element_id,
            'sub_id': subsection_element_id
        })

    def fix_all_sections(self):
        """Fix paragraph assignments for all sections with subsections."""
        sections = self.get_sections_with_subsections()
        
        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Found {len(sections)} sections with subsections")
        
        total_reassigned = 0
        for section in sections:
            section_id = section['section_id']
            print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Processing: {section['section_title']}")
            
            count = self.reassign_paragraphs_for_section(section_id)
            if count:
                total_reassigned += count
                print(f"  Reassigned {count} paragraphs")
        
        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Total: {total_reassigned} paragraphs reassigned")
        
        if not self.dry_run:
            # Verify - check for empty subsections
            query_verify = """
            MATCH (sub:Subsection)
            WHERE NOT (sub)-[:CONTAINS_PARAGRAPH]->()
            RETURN count(sub) as empty_subsections
            """
            result = self.conn.execute_query(query_verify)
            empty = result[0]['empty_subsections'] if result else 0
            
            if empty > 0:
                print(f"\n⚠️  Warning: {empty} subsections still have no paragraphs")
            else:
                print("\n✅ All subsections have paragraphs assigned!")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fix paragraph-subsection relationships v2 (correct order logic)'
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
        fixer = SubsectionParagraphFixerV2(conn, dry_run=args.dry_run)
        fixer.fix_all_sections()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
