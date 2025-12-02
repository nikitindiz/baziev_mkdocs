#!/usr/bin/env python3
"""
Правильное связывание параграфов с подразделами.

Стратегия:
1. Читаем markdown файл секции
2. Парсим его чтобы найти где заканчивается каждый подраздел
3. Параграфы с order между subsection N и subsection N+1 принадлежат subsection N
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


def parse_markdown_structure(md_file):
    """
    Parse markdown to find subsection boundaries.
    Returns: dict mapping subsection number -> (first_para_order, last_para_order)
    """
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    subsections = []  # List of {number, first_para, last_para}
    current_subsection = None
    paragraph_order = 0
    in_paragraph = False
    blank_line_count = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip section header
        if stripped.startswith('## §'):
            continue
        
        # Detect subsection header: ### N. Title
        if re.match(r'^###\s+[\d.]+\s+.+', stripped):
            # Close previous subsection
            if current_subsection:
                current_subsection['last_para'] = paragraph_order
                subsections.append(current_subsection)
            
            # Extract number
            match = re.match(r'^###\s+([\d.]+)', stripped)
            number = match.group(1).rstrip('.')
            
            # Start new subsection
            current_subsection = {
                'number': number,
                'first_para': paragraph_order + 1  # Next paragraph starts this subsection
            }
            in_paragraph = False
            blank_line_count = 0
            continue
        
        # Skip if no current subsection
        if not current_subsection:
            continue
        
        # Detect paragraph boundaries
        if not stripped:
            # Blank line
            blank_line_count += 1
            if blank_line_count >= 1:  # One blank line ends paragraph
                in_paragraph = False
        else:
            blank_line_count = 0
            # Non-empty line
            if not in_paragraph:
                # Start new paragraph
                paragraph_order += 1
                in_paragraph = True
    
    # Close last subsection
    if current_subsection:
        current_subsection['last_para'] = paragraph_order + 100  # Large number for last section
        subsections.append(current_subsection)
    
    return {s['number']: (s['first_para'], s['last_para']) for s in subsections}


def find_markdown_file(section_id, normalized_dir):
    """Find markdown file for section"""
    if not section_id.startswith('chapter_'):
        return None
    
    rest = section_id[8:]  # Remove 'chapter_'
    parts = rest.rsplit('_', 1)
    if len(parts) != 2:
        return None
    
    chapter_part = parts[0]
    section_part = parts[1]
    
    pattern = f"**/chapter_{chapter_part}/{section_part}.md"
    matches = list(Path(normalized_dir).glob(pattern))
    
    return matches[0] if matches else None


def link_section(conn, section_id, normalized_dir, dry_run=False):
    """Link paragraphs to subsections for one section"""
    # Find markdown file
    md_file = find_markdown_file(section_id, normalized_dir)
    if not md_file:
        return 0, f"No markdown file found"
    
    # Parse markdown to get subsection boundaries
    try:
        boundaries = parse_markdown_structure(md_file)
    except Exception as e:
        return 0, f"Parse error: {e}"
    
    if not boundaries:
        return 0, "No subsections found in markdown"
    
    # Get subsections from database
    query = """
    MATCH (s:Section {id: $section_id})-[:HAS_SUBSECTION]->(sub:Subsection)
    RETURN sub.number as number, elementId(sub) as element_id
    ORDER BY toInteger(sub.number)
    """
    subsections = conn.execute_query(query, {'section_id': section_id})
    
    if not subsections:
        return 0, "No subsections in database"
    
    # Get paragraphs from database
    query = """
    MATCH (s:Section {id: $section_id})-[r:HAS_PARAGRAPH]->(p:Paragraph)
    RETURN elementId(p) as element_id, r.order as para_order
    ORDER BY r.order
    """
    paragraphs = conn.execute_query(query, {'section_id': section_id})
    
    if not paragraphs:
        return 0, "No paragraphs in database"
    
    # Create paragraph to subsection mapping
    linked = 0
    for sub in subsections:
        sub_number = sub['number']
        sub_element_id = sub['element_id']
        
        # Get boundary from markdown analysis
        if sub_number not in boundaries:
            # Try without decimal point
            sub_number_alt = sub_number.split('.')[0]
            if sub_number_alt in boundaries:
                first_para, last_para = boundaries[sub_number_alt]
            else:
                continue
        else:
            first_para, last_para = boundaries[sub_number]
        
        # Find paragraphs in this range
        for para in paragraphs:
            para_order = para['para_order']
            para_element_id = para['element_id']
            
            if first_para <= para_order <= last_para:
                # Create link
                if not dry_run:
                    link_query = """
                    MATCH (sub:Subsection), (p:Paragraph)
                    WHERE elementId(sub) = $sub_id AND elementId(p) = $para_id
                    MERGE (sub)-[:CONTAINS_PARAGRAPH {order: $order}]->(p)
                    """
                    conn.execute_query(link_query, {
                        'sub_id': sub_element_id,
                        'para_id': para_element_id,
                        'order': para_order
                    })
                
                linked += 1
    
    return linked, None


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
        # Get all sections with subsections
        query = """
        MATCH (s:Section)-[:HAS_SUBSECTION]->(:Subsection)
        WITH DISTINCT s
        RETURN s.id as section_id, s.title as section_title
        ORDER BY s.id
        """
        sections = conn.execute_query(query)
        
        print(f"{'[DRY RUN] ' if args.dry_run else ''}Processing {len(sections)} sections...\n")
        
        total_linked = 0
        errors = 0
        
        for section in sections:
            section_id = section['section_id']
            section_title = section['section_title']
            
            linked, error = link_section(conn, section_id, args.normalized, args.dry_run)
            
            if error:
                print(f"✗ {section_title}: {error}")
                errors += 1
            elif linked > 0:
                print(f"{'[DRY RUN] ' if args.dry_run else ''}✓ {section_title}: {linked} paragraphs")
                total_linked += linked
        
        print(f"\n{'='*60}")
        print(f"Summary:")
        print(f"  Sections: {len(sections) - errors}")
        print(f"  Paragraphs linked: {total_linked}")
        print(f"  Errors: {errors}")
        
    finally:
        conn.close()


if __name__ == '__main__':
    main()
