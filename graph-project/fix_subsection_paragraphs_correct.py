#!/usr/bin/env python3
"""
Правильное связывание параграфов с подразделами на основе анализа markdown файлов.

Логика:
1. Читаем markdown файл
2. Находим позиции заголовков ### (подразделы)
3. Считаем параграфы между заголовками
4. Параграфы между заголовком N и N+1 принадлежат подразделу N
"""

import yaml
import re
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


class SubsectionParagraphFixer:
    def __init__(self, connection, normalized_dir, dry_run=False):
        self.conn = connection
        self.normalized_dir = Path(normalized_dir)
        self.dry_run = dry_run
        self.stats = {'sections': 0, 'paragraphs_linked': 0, 'errors': 0}

    def find_markdown_file(self, section_id):
        """Find markdown file for section"""
        # section_id format: chapter_глава-...или-...
        # Extract chapter and section parts
        # Example: chapter_глава-i-система-новейших-фундаментальных-открытий_1-гиперчастотная-механика-или-механика-микромира
        if not section_id.startswith('chapter_'):
            return None
        
        # Remove 'chapter_' prefix
        rest = section_id[8:]  # Remove 'chapter_'
        
        # Find last underscore before section number
        # Section starts with digit: _1-название, _10-название, etc.
        parts = rest.rsplit('_', 1)
        if len(parts) != 2:
            return None
        
        chapter_part = parts[0]  # глава-i-система-...
        section_part = parts[1]  # 1-гиперчастотная-...
        
        # Build pattern
        pattern = f"**/chapter_{chapter_part}/{section_part}.md"
        matches = list(self.normalized_dir.glob(pattern))
        
        if matches:
            return matches[0]
        
        return None

    def extract_subsection_positions(self, content):
        """Extract subsection positions from markdown content"""
        lines = content.split('\n')
        subsections = []
        paragraph_count = 0
        
        for i, line in enumerate(lines):
            # Subsection header: ### N. Title
            if re.match(r'^###\s+\d+\.', line):
                match = re.match(r'^###\s+(\d+)\.\s*(.+)', line)
                if match:
                    number = match.group(1)
                    title = match.group(2).strip()
                    subsections.append({
                        'number': number,
                        'title': title,
                        'line': i,
                        'paragraph_before': paragraph_count
                    })
            # Count paragraphs (non-empty lines that are not headers, formulas, etc.)
            elif line.strip() and not line.startswith('#') and not line.startswith('{{'):
                # This is a simplification - actual paragraph counting is complex
                pass
        
        return subsections

    def get_paragraph_ranges(self, content):
        """
        Analyze markdown to determine which paragraphs belong to which subsection.
        Returns: list of (subsection_number, first_para_order, last_para_order)
        """
        lines = content.split('\n')
        subsections = []
        current_subsection = None
        paragraph_order = 0
        
        for line in lines:
            # Skip section header
            if line.startswith('## §'):
                continue
            
            # Subsection header
            if re.match(r'^###\s+\d+\.', line):
                # Save previous subsection if exists
                if current_subsection:
                    current_subsection['last_para'] = paragraph_order
                    subsections.append(current_subsection)
                
                # Start new subsection
                match = re.match(r'^###\s+(\d+)\.\s*(.+)', line)
                if match:
                    number = match.group(1)
                    current_subsection = {
                        'number': number,
                        'first_para': paragraph_order + 1  # Next paragraph starts this subsection
                    }
                continue
            
            # Count paragraphs (simple heuristic: non-empty line that looks like text)
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith('{{') and current_subsection:
                # This line might be part of a paragraph
                # For now, assume each non-empty text line could start a paragraph
                # (This is simplified - real counting needs paragraph block detection)
                pass
        
        # Save last subsection
        if current_subsection:
            current_subsection['last_para'] = paragraph_order + 100  # Assume many paragraphs after last header
            subsections.append(current_subsection)
        
        return subsections

    def link_section_paragraphs(self, section_id):
        """Link paragraphs to subsections for one section"""
        # Find markdown file
        md_file = self.find_markdown_file(section_id)
        if not md_file:
            print(f"✗ No markdown file found for {section_id}")
            self.stats['errors'] += 1
            return
        
        # Read content
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get subsections from database
        query = """
        MATCH (s:Section {id: $section_id})-[:HAS_SUBSECTION]->(sub:Subsection)
        RETURN sub.number as number, elementId(sub) as element_id, sub.title as title
        ORDER BY toInteger(sub.number)
        """
        subsections_db = self.conn.execute_query(query, {'section_id': section_id})
        
        if not subsections_db:
            return
        
        # Get paragraphs from database
        query = """
        MATCH (s:Section {id: $section_id})-[r:HAS_PARAGRAPH]->(p:Paragraph)
        RETURN elementId(p) as element_id, r.order as para_order, p.id as para_id
        ORDER BY r.order
        """
        paragraphs_db = self.conn.execute_query(query, {'section_id': section_id})
        
        if not paragraphs_db:
            return
        
        # Analyze markdown to find paragraph distribution
        # Strategy: count paragraphs between each ### header
        paragraph_counts = self._count_paragraphs_per_subsection(content)
        
        # Assign paragraphs to subsections
        para_index = 0
        linked_count = 0
        
        for i, sub in enumerate(subsections_db):
            sub_number = sub['number']
            sub_element_id = sub['element_id']
            
            # How many paragraphs for this subsection?
            para_count = paragraph_counts.get(sub_number, 0)
            
            # Link paragraphs
            for j in range(para_count):
                if para_index >= len(paragraphs_db):
                    break
                
                para = paragraphs_db[para_index]
                para_element_id = para['element_id']
                para_order = para['para_order']
                
                # Create link
                if not self.dry_run:
                    link_query = """
                    MATCH (sub:Subsection), (p:Paragraph)
                    WHERE elementId(sub) = $sub_id AND elementId(p) = $para_id
                    MERGE (sub)-[:CONTAINS_PARAGRAPH {order: $order}]->(p)
                    """
                    self.conn.execute_query(link_query, {
                        'sub_id': sub_element_id,
                        'para_id': para_element_id,
                        'order': para_order
                    })
                
                para_index += 1
                linked_count += 1
        
        self.stats['sections'] += 1
        self.stats['paragraphs_linked'] += linked_count
        
        if linked_count > 0:
            print(f"{'[DRY RUN] ' if self.dry_run else ''}✓ {section_id}: {linked_count} paragraphs linked")

    def _count_paragraphs_per_subsection(self, content):
        """
        Count how many paragraphs belong to each subsection in markdown.
        Returns dict: {subsection_number: paragraph_count}
        """
        lines = content.split('\n')
        counts = {}
        current_subsection = None
        current_count = 0
        in_paragraph = False
        
        for line in lines:
            # Section header - skip
            if line.startswith('## §'):
                continue
            
            # Subsection header
            if re.match(r'^###\s+\d+\.', line):
                # Save previous count
                if current_subsection:
                    counts[current_subsection] = current_count
                
                # Start new subsection
                match = re.match(r'^###\s+(\d+)\.', line)
                if match:
                    current_subsection = match.group(1)
                    current_count = 0
                    in_paragraph = False
                continue
            
            # Skip if no subsection started yet
            if not current_subsection:
                continue
            
            # Detect paragraph breaks
            line_stripped = line.strip()
            
            if not line_stripped:
                # Empty line - end of paragraph
                in_paragraph = False
            elif not line_stripped.startswith('{{'):
                # Non-empty, non-formula line
                if not in_paragraph:
                    # Start of new paragraph
                    current_count += 1
                    in_paragraph = True
        
        # Save last subsection count
        if current_subsection:
            counts[current_subsection] = current_count
        
        return counts

    def process_all(self):
        """Process all sections with subsections"""
        # First, delete all existing CONTAINS_PARAGRAPH relationships
        if not self.dry_run:
            print("Deleting existing CONTAINS_PARAGRAPH relationships...")
            delete_query = """
            MATCH (:Subsection)-[r:CONTAINS_PARAGRAPH]->(:Paragraph)
            DELETE r
            """
            self.conn.execute_query(delete_query)
            print("✓ Deleted\n")
        
        # Get all sections with subsections
        query = """
        MATCH (s:Section)-[:HAS_SUBSECTION]->(:Subsection)
        WITH DISTINCT s
        RETURN s.id as section_id, s.title as section_title
        ORDER BY s.id
        """
        sections = self.conn.execute_query(query)
        
        print(f"{'[DRY RUN] ' if self.dry_run else ''}Processing {len(sections)} sections...\n")
        
        for section in sections:
            section_id = section['section_id']
            try:
                self.link_section_paragraphs(section_id)
            except Exception as e:
                self.stats['errors'] += 1
                print(f"✗ {section_id}: ERROR - {e}")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"Summary:")
        print(f"  Sections processed: {self.stats['sections']}")
        print(f"  Paragraphs linked: {self.stats['paragraphs_linked']}")
        print(f"  Errors: {self.stats['errors']}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='graph-project/config/config.yml')
    parser.add_argument('--normalized', default='normalized/step-05-extract-and-link-quoted-literature/result')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    
    config_path = Path(args.config)
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
        fixer = SubsectionParagraphFixer(conn, args.normalized, dry_run=args.dry_run)
        fixer.process_all()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
