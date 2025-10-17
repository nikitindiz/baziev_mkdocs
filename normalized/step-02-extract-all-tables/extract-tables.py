#!/usr/bin/env python3
"""
Table Extraction Script for Baziev Physics Book
Extracts both Markdown and HTML tables from markdown files.

Features:
- Extracts Markdown tables (| ... | format)
- Extracts HTML tables (<table>...</table>)
- Generates hash-based unique IDs
- Preserves formula references
- Stores tables as individual JSON files
- Creates modified chapters with table references
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from html.parser import HTMLParser


@dataclass
class Table:
    """Represents an extracted table"""
    id: str
    type: str  # 'markdown' or 'html'
    content: Dict
    metadata: Dict
    source: Dict
    html_attributes: Optional[Dict] = None


class HTMLTableParser(HTMLParser):
    """Parse HTML table structure"""
    
    def __init__(self):
        super().__init__()
        self.table_attrs = {}
        self.headers = []
        self.rows = []
        self.current_row = []
        self.current_cell = []
        self.in_thead = False
        self.in_tbody = False
        self.in_tr = False
        self.in_th = False
        self.in_td = False
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'table':
            self.table_attrs = attrs_dict
        elif tag == 'thead':
            self.in_thead = True
        elif tag == 'tbody':
            self.in_tbody = True
        elif tag == 'tr':
            self.in_tr = True
            self.current_row = []
        elif tag == 'th':
            self.in_th = True
            self.current_cell = []
        elif tag == 'td':
            self.in_td = True
            self.current_cell = []
    
    def handle_endtag(self, tag):
        if tag == 'thead':
            self.in_thead = False
        elif tag == 'tbody':
            self.in_tbody = False
        elif tag == 'tr':
            self.in_tr = False
            if self.current_row:
                if self.in_thead or (not self.in_tbody and not self.rows):
                    self.headers.extend(self.current_row)
                else:
                    self.rows.append(self.current_row)
        elif tag == 'th':
            self.in_th = False
            self.headers.append(''.join(self.current_cell).strip())
            self.current_cell = []
        elif tag == 'td':
            self.in_td = False
            self.current_row.append(''.join(self.current_cell).strip())
            self.current_cell = []
    
    def handle_data(self, data):
        if self.in_th or self.in_td:
            self.current_cell.append(data)


class TableExtractor:
    """Extracts tables from markdown files"""
    
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.tables_dir = self.output_dir / "tables"
        self.result_dir = self.output_dir / "result"
        
        # Ensure directories exist
        self.tables_dir.mkdir(parents=True, exist_ok=True)
        self.result_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_tables': 0,
            'markdown_tables': 0,
            'html_tables': 0,
            'files_processed': 0,
            'tables_with_formulas': 0,
            'total_rows': 0,
            'total_columns': 0
        }
    
    def generate_table_id(self, content: str, table_type: str, source: str, position: int) -> str:
        """Generate hash-based unique ID for table"""
        unique_str = f"{content}|{table_type}|{source}|{position}"
        hash_obj = hashlib.md5(unique_str.encode('utf-8'))
        return hash_obj.hexdigest()[:12]
    
    def find_formula_refs(self, text: str) -> List[str]:
        """Find all {{formula:*}} references in text"""
        pattern = r'\{\{formula:[a-f0-9]+(?::\([^)]+\))?\}\}'
        return re.findall(pattern, text)
    
    def parse_markdown_table(self, table_str: str) -> Dict:
        """Parse markdown table into headers and rows"""
        lines = [line.strip() for line in table_str.strip().split('\n') if line.strip()]
        
        if len(lines) < 2:
            return None
        
        # First line: headers
        header_line = lines[0]
        headers = [cell.strip() for cell in header_line.split('|')]
        headers = [h for h in headers if h]  # Remove empty strings
        
        # Second line: separator (validate it's a separator)
        separator_line = lines[1]
        if not re.match(r'^\|?[\s:-]+\|', separator_line):
            return None
        
        # Remaining lines: data rows
        rows = []
        for line in lines[2:]:
            cells = [cell.strip() for cell in line.split('|')]
            cells = [c for c in cells if c or len([c for c in cells if c]) > 0]  # Keep structure
            if cells:
                # Pad with empty strings if needed to match header count
                while len(cells) < len(headers):
                    cells.append('')
                rows.append(cells[:len(headers)])  # Trim to header count
        
        return {
            'raw': table_str,
            'headers': headers,
            'rows': rows
        }
    
    def parse_html_table(self, table_str: str) -> Dict:
        """Parse HTML table into headers and rows"""
        parser = HTMLTableParser()
        try:
            parser.feed(table_str)
        except Exception as e:
            print(f"    Warning: Failed to parse HTML table: {e}")
            return None
        
        # If no headers found in thead, try to use first row
        if not parser.headers and parser.rows:
            parser.headers = parser.rows.pop(0)
        
        return {
            'raw': table_str,
            'headers': parser.headers,
            'rows': parser.rows,
            'attributes': parser.table_attrs
        }
    
    def extract_html_tables(self, content: str, file_path: str) -> Tuple[str, List[Table]]:
        """Extract HTML tables from content"""
        tables = []
        modified_content = content
        
        # Pattern to match <table>...</table> including nested tags
        pattern = r'<table[^>]*>.*?</table>'
        matches = list(re.finditer(pattern, content, flags=re.DOTALL | re.IGNORECASE))
        
        # Process in reverse to preserve positions
        for match in reversed(matches):
            table_html = match.group(0)
            start_pos = match.start()
            end_pos = match.end()
            
            # Parse the table
            parsed = self.parse_html_table(table_html)
            if not parsed:
                continue
            
            # Extract formula references
            formula_refs = self.find_formula_refs(table_html)
            has_formulas = len(formula_refs) > 0
            
            # Generate table ID
            table_id = self.generate_table_id(
                table_html, 
                'html', 
                str(file_path), 
                start_pos
            )
            
            # Calculate stats
            row_count = len(parsed['rows'])
            column_count = len(parsed['headers']) if parsed['headers'] else 0
            
            # Create table object
            table = Table(
                id=table_id,
                type='html',
                content=parsed,
                metadata={
                    'row_count': row_count,
                    'column_count': column_count,
                    'has_formulas': has_formulas,
                    'formula_refs': formula_refs
                },
                source={
                    'file': str(file_path),
                    'position': start_pos
                },
                html_attributes=parsed.get('attributes')
            )
            
            tables.append(table)
            self.stats['html_tables'] += 1
            self.stats['total_rows'] += row_count
            self.stats['total_columns'] += column_count
            
            if has_formulas:
                self.stats['tables_with_formulas'] += 1
            
            # Replace with reference
            ref = f"{{{{table:{table_id}}}}}"
            modified_content = modified_content[:start_pos] + ref + modified_content[end_pos:]
        
        # Reverse to maintain original order
        tables.reverse()
        
        return modified_content, tables
    
    def extract_markdown_tables(self, content: str, file_path: str) -> Tuple[str, List[Table]]:
        """Extract markdown tables from content"""
        tables = []
        modified_content = content
        
        # Pattern to match markdown tables
        # Simplified: match header row, separator, and data rows
        # Use [^\n]+ to match any content on a line (excluding newline)
        pattern = r'(\|[^\n]+\n\|[\s:-]+\|[^\n]*\n(?:\|[^\n]+\n?)+)'
        matches = list(re.finditer(pattern, content))
        
        # Process in reverse to preserve positions
        for match in reversed(matches):
            table_md = match.group(1).strip()
            start_pos = match.start()
            end_pos = match.end()
            
            # Skip if this table is inside a code block
            # Check for ``` markers before this position
            before_text = content[:start_pos]
            code_block_count = before_text.count('```')
            if code_block_count % 2 == 1:  # Inside code block
                continue
            
            # Parse the table
            parsed = self.parse_markdown_table(table_md)
            if not parsed:
                continue
            
            # Extract formula references
            formula_refs = self.find_formula_refs(table_md)
            has_formulas = len(formula_refs) > 0
            
            # Generate table ID
            table_id = self.generate_table_id(
                table_md, 
                'markdown', 
                str(file_path), 
                start_pos
            )
            
            # Calculate stats
            row_count = len(parsed['rows'])
            column_count = len(parsed['headers']) if parsed['headers'] else 0
            
            # Create table object
            table = Table(
                id=table_id,
                type='markdown',
                content=parsed,
                metadata={
                    'row_count': row_count,
                    'column_count': column_count,
                    'has_formulas': has_formulas,
                    'formula_refs': formula_refs
                },
                source={
                    'file': str(file_path),
                    'position': start_pos
                },
                html_attributes=None
            )
            
            tables.append(table)
            self.stats['markdown_tables'] += 1
            self.stats['total_rows'] += row_count
            self.stats['total_columns'] += column_count
            
            if has_formulas:
                self.stats['tables_with_formulas'] += 1
            
            # Replace with reference
            ref = f"{{{{table:{table_id}}}}}"
            modified_content = modified_content[:start_pos] + ref + modified_content[end_pos:]
        
        # Reverse to maintain original order
        tables.reverse()
        
        return modified_content, tables
    
    def save_table(self, table: Table):
        """Save table to JSON file"""
        table_file = self.tables_dir / f"table_{table.id}.json"
        
        # Convert to dict
        table_dict = {
            'id': table.id,
            'type': table.type,
            'content': table.content,
            'metadata': table.metadata,
            'source': table.source,
            'html_attributes': table.html_attributes
        }
        
        with open(table_file, 'w', encoding='utf-8') as f:
            json.dump(table_dict, f, ensure_ascii=False, indent=2)
    
    def process_file(self, file_path: Path):
        """Process a single markdown file"""
        print(f"Processing: {file_path.relative_to(self.input_dir)}")
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        all_tables = []
        
        # Extract tables in order (most specific first)
        # 1. HTML tables first (more specific)
        content, tables = self.extract_html_tables(content, file_path.relative_to(self.input_dir))
        all_tables.extend(tables)
        
        # 2. Markdown tables second
        content, tables = self.extract_markdown_tables(content, file_path.relative_to(self.input_dir))
        all_tables.extend(tables)
        
        # Save all tables
        for table in all_tables:
            self.save_table(table)
        
        # Create output file path
        relative_path = file_path.relative_to(self.input_dir)
        output_file = self.result_dir / relative_path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write modified content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.stats['files_processed'] += 1
        self.stats['total_tables'] += len(all_tables)
        
        if all_tables:
            print(f"  → Extracted {len(all_tables)} tables")
    
    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in the input directory"""
        md_files = []
        
        # Look for chapter directories
        for item in self.input_dir.iterdir():
            if item.is_dir() and item.name.startswith('chapter_'):
                # Find all .md files in this chapter
                for md_file in item.rglob('*.md'):
                    md_files.append(md_file)
        
        # Also process index.md if exists
        index_file = self.input_dir / 'index.md'
        if index_file.exists():
            md_files.append(index_file)
        
        return sorted(md_files)
    
    def process_all(self):
        """Process all markdown files"""
        print("=" * 80)
        print("Table Extraction Script")
        print("=" * 80)
        print()
        
        md_files = self.find_markdown_files()
        print(f"Found {len(md_files)} markdown files to process\n")
        
        for md_file in md_files:
            self.process_file(md_file)
        
        # Calculate averages
        avg_rows = 0
        avg_cols = 0
        if self.stats['total_tables'] > 0:
            avg_rows = self.stats['total_rows'] / self.stats['total_tables']
            avg_cols = self.stats['total_columns'] / self.stats['total_tables']
        
        # Print statistics
        print()
        print("=" * 80)
        print("Extraction Complete!")
        print("=" * 80)
        print(f"Files processed:          {self.stats['files_processed']}")
        print(f"Total tables extracted:   {self.stats['total_tables']}")
        print(f"  - Markdown tables:      {self.stats['markdown_tables']}")
        print(f"  - HTML tables:          {self.stats['html_tables']}")
        print(f"Tables with formulas:     {self.stats['tables_with_formulas']}")
        print(f"Average rows per table:   {avg_rows:.1f}")
        print(f"Average columns per table: {avg_cols:.1f}")
        print()
        print(f"Tables saved to:          {self.tables_dir}")
        print(f"Modified chapters in:     {self.result_dir}")
        print("=" * 80)
        
        # Save statistics to JSON
        stats_file = self.output_dir / "extraction_stats.json"
        stats_to_save = self.stats.copy()
        stats_to_save['average_rows_per_table'] = avg_rows
        stats_to_save['average_columns_per_table'] = avg_cols
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_to_save, f, ensure_ascii=False, indent=2)
        print(f"Statistics saved to:      {stats_file}")


def main():
    """Main entry point"""
    # Get script directory
    script_dir = Path(__file__).parent
    
    # Input: result from step-01
    input_dir = script_dir.parent / "step-01-extract-all-formulas" / "result"
    
    # Output: current directory
    output_dir = script_dir
    
    # Validate input directory exists
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        print("Please run step-01 first.")
        return 1
    
    # Create extractor and run
    extractor = TableExtractor(str(input_dir), str(output_dir))
    extractor.process_all()
    
    return 0


if __name__ == "__main__":
    exit(main())
