#!/usr/bin/env python3
"""
Formula Extraction Script for Baziev Physics Book
Extracts inline and display LaTeX formulas from markdown files.

Features:
- Extracts both inline ($...$) and display ($$...$$) formulas
- Handles HTML-wrapped formulas with metadata
- Generates hash-based unique IDs
- Preserves equation numbers
- Stores formulas as individual JSON files
- Creates modified chapters with formula references
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class FormulaMetadata:
    """Metadata for a formula"""
    db_key: Optional[str] = None
    src: Optional[str] = None
    equation_number: Optional[str] = None


@dataclass
class Formula:
    """Represents an extracted formula"""
    id: str
    type: str  # 'inline' or 'display'
    latex: str
    metadata: FormulaMetadata
    source: Dict[str, any]
    wrapper_html: Optional[str] = None


class FormulaExtractor:
    """Extracts formulas from markdown files"""
    
    def __init__(self, docs_dir: str, output_dir: str):
        self.docs_dir = Path(docs_dir)
        self.output_dir = Path(output_dir)
        self.formulas_dir = self.output_dir / "formulas"
        self.result_dir = self.output_dir / "result"
        
        # Ensure directories exist
        self.formulas_dir.mkdir(parents=True, exist_ok=True)
        self.result_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_formulas': 0,
            'inline_formulas': 0,
            'display_formulas': 0,
            'files_processed': 0,
            'formulas_with_metadata': 0
        }
    
    def generate_formula_id(self, latex: str, metadata: FormulaMetadata) -> str:
        """Generate hash-based unique ID for formula"""
        # Create a unique string from latex and metadata
        unique_str = f"{latex}|{metadata.db_key}|{metadata.src}|{metadata.equation_number}"
        hash_obj = hashlib.md5(unique_str.encode('utf-8'))
        return hash_obj.hexdigest()[:12]  # Use first 12 characters
    
    def extract_metadata_from_tag(self, tag_str: str) -> FormulaMetadata:
        """Extract metadata attributes from HTML tag"""
        metadata = FormulaMetadata()
        
        # Extract data-db-key
        db_key_match = re.search(r'data-db-key="([^"]+)"', tag_str)
        if db_key_match:
            metadata.db_key = db_key_match.group(1)
        
        # Extract data-src
        src_match = re.search(r'data-src="([^"]+)"', tag_str)
        if src_match:
            metadata.src = src_match.group(1)
        
        return metadata
    
    def extract_equation_number(self, text: str, start_pos: int) -> Optional[str]:
        """Extract equation number like (1.15) after display formula"""
        # Look for pattern like (1.15) within the next 200 characters
        search_text = text[start_pos:start_pos + 200]
        eq_num_match = re.search(r'\((\d+\.\d+)\)', search_text)
        if eq_num_match:
            return f"({eq_num_match.group(1)})"
        return None
    
    def extract_display_formulas_with_divs(self, content: str, file_path: str) -> Tuple[str, List[Formula]]:
        """Extract display formulas wrapped in div layouts"""
        formulas = []
        
        # Pattern for display formulas in div structure
        # Matches: <div ...>...<div ...>$$...$$</div><div ...>(X.Y)</div></div>
        pattern = r'<div[^>]*?(?:data-db-key="[^"]*")?(?:data-src="[^"]*")?[^>]*?>\s*<div[^>]*?>\s*\$\$(.*?)\$\$\s*</div>\s*<div[^>]*?>\s*(\([^)]+\))?\s*</div>\s*</div>'
        
        def replace_formula(match):
            wrapper_start = match.start()
            wrapper_end = match.end()
            wrapper_html = match.group(0)
            latex = match.group(1).strip()
            eq_number = match.group(2)  # This will be (X.Y) or None
            
            # Extract metadata from outer div
            outer_div_match = re.match(r'<div([^>]*)>', wrapper_html)
            metadata = FormulaMetadata()
            if outer_div_match:
                metadata = self.extract_metadata_from_tag(outer_div_match.group(1))
            
            if eq_number:
                metadata.equation_number = eq_number
            
            # Generate formula ID
            formula_id = self.generate_formula_id(latex, metadata)
            
            # Create formula object
            formula = Formula(
                id=formula_id,
                type='display',
                latex=latex,
                metadata=metadata,
                source={
                    'file': str(file_path),
                    'position': wrapper_start
                },
                wrapper_html=wrapper_html
            )
            
            formulas.append(formula)
            self.stats['display_formulas'] += 1
            if metadata.db_key or metadata.src:
                self.stats['formulas_with_metadata'] += 1
            
            # Create reference
            ref = f"{{{{formula:{formula_id}"
            if metadata.equation_number:
                ref += f":{metadata.equation_number}"
            ref += "}}"
            
            return ref
        
        # Replace all matches
        new_content = re.sub(pattern, replace_formula, content, flags=re.DOTALL)
        
        return new_content, formulas
    
    def extract_standalone_display_formulas(self, content: str, file_path: str) -> Tuple[str, List[Formula]]:
        """Extract standalone display formulas ($$...$$) not in div wrappers"""
        formulas = []
        modified_content = content
        
        # Find all $$ ... $$ patterns
        pattern = r'\$\$(.*?)\$\$'
        matches = list(re.finditer(pattern, content, flags=re.DOTALL))
        
        # Process matches in reverse to preserve positions
        for match in reversed(matches):
            wrapper_start = match.start()
            wrapper_end = match.end()
            latex = match.group(1).strip()
            
            # Check if this is inside a div wrapper (already processed)
            # Look backward for <div and forward for </div>
            before_text = content[max(0, wrapper_start - 100):wrapper_start]
            after_text = content[wrapper_end:min(len(content), wrapper_end + 100)]
            
            # Skip if we find div markers that are very close
            if '<div' in before_text and '</div>' in after_text:
                div_start = before_text.rfind('<div')
                # If div is within 50 chars before, it's likely a wrapper
                if wrapper_start - (wrapper_start - 100 + div_start) < 50:
                    continue
            
            metadata = FormulaMetadata()
            
            # Check if there's an equation number nearby
            eq_num = self.extract_equation_number(content, wrapper_end)
            if eq_num:
                metadata.equation_number = eq_num
            
            # Generate formula ID
            formula_id = self.generate_formula_id(latex, metadata)
            
            # Create formula object
            formula = Formula(
                id=formula_id,
                type='display',
                latex=latex,
                metadata=metadata,
                source={
                    'file': str(file_path),
                    'position': wrapper_start
                }
            )
            
            formulas.append(formula)
            self.stats['display_formulas'] += 1
            
            # Create reference
            ref = f"{{{{formula:{formula_id}"
            if metadata.equation_number:
                ref += f":{metadata.equation_number}"
            ref += "}}"
            
            # Replace in content
            modified_content = modified_content[:wrapper_start] + ref + modified_content[wrapper_end:]
        
        # Reverse formulas list to maintain original order
        formulas.reverse()
        
        return modified_content, formulas
    
    def extract_inline_formulas_with_spans(self, content: str, file_path: str) -> Tuple[str, List[Formula]]:
        """Extract inline formulas wrapped in span tags"""
        formulas = []
        
        # Pattern for inline formulas in span tags
        pattern = r'<span([^>]*?)>\s*\$(.*?)\$\s*</span>'
        
        def replace_formula(match):
            wrapper_start = match.start()
            wrapper_html = match.group(0)
            span_attrs = match.group(1)
            latex = match.group(2).strip()
            
            # Extract metadata
            metadata = self.extract_metadata_from_tag(span_attrs)
            
            # Generate formula ID
            formula_id = self.generate_formula_id(latex, metadata)
            
            # Create formula object
            formula = Formula(
                id=formula_id,
                type='inline',
                latex=latex,
                metadata=metadata,
                source={
                    'file': str(file_path),
                    'position': wrapper_start
                },
                wrapper_html=wrapper_html
            )
            
            formulas.append(formula)
            self.stats['inline_formulas'] += 1
            if metadata.db_key or metadata.src:
                self.stats['formulas_with_metadata'] += 1
            
            # Create reference (inline formulas don't have equation numbers)
            return f"{{{{formula:{formula_id}}}}}"
        
        new_content = re.sub(pattern, replace_formula, content, flags=re.DOTALL)
        
        return new_content, formulas
    
    def extract_standalone_inline_formulas(self, content: str, file_path: str) -> Tuple[str, List[Formula]]:
        """Extract standalone inline formulas ($...$) not in span wrappers"""
        formulas = []
        modified_content = content
        
        # Find all $ ... $ patterns (but not $$)
        pattern = r'(?<!\$)\$(?!\$)(.*?)\$(?!\$)'
        matches = list(re.finditer(pattern, content))
        
        # Process matches in reverse to preserve positions
        for match in reversed(matches):
            wrapper_start = match.start()
            wrapper_end = match.end()
            latex = match.group(1).strip()
            
            # Check if this is inside a span wrapper (already processed)
            before_text = content[max(0, wrapper_start - 100):wrapper_start]
            after_text = content[wrapper_end:min(len(content), wrapper_end + 20)]
            
            # Skip if we find span markers that are very close
            if '<span' in before_text and '</span>' in after_text:
                span_start = before_text.rfind('<span')
                # If span is within 50 chars before, it's likely a wrapper
                if wrapper_start - (wrapper_start - 100 + span_start) < 50:
                    continue
            
            metadata = FormulaMetadata()
            
            # Generate formula ID
            formula_id = self.generate_formula_id(latex, metadata)
            
            # Create formula object
            formula = Formula(
                id=formula_id,
                type='inline',
                latex=latex,
                metadata=metadata,
                source={
                    'file': str(file_path),
                    'position': wrapper_start
                }
            )
            
            formulas.append(formula)
            self.stats['inline_formulas'] += 1
            
            # Replace in content
            ref = f"{{{{formula:{formula_id}}}}}"
            modified_content = modified_content[:wrapper_start] + ref + modified_content[wrapper_end:]
        
        # Reverse formulas list to maintain original order
        formulas.reverse()
        
        return modified_content, formulas
    
    def save_formula(self, formula: Formula):
        """Save formula to JSON file"""
        formula_file = self.formulas_dir / f"formula_{formula.id}.json"
        
        # Convert to dict
        formula_dict = {
            'id': formula.id,
            'type': formula.type,
            'latex': formula.latex,
            'metadata': {
                'db_key': formula.metadata.db_key,
                'src': formula.metadata.src,
                'equation_number': formula.metadata.equation_number
            },
            'source': formula.source,
            'wrapper_html': formula.wrapper_html
        }
        
        with open(formula_file, 'w', encoding='utf-8') as f:
            json.dump(formula_dict, f, ensure_ascii=False, indent=2)
    
    def process_file(self, file_path: Path):
        """Process a single markdown file"""
        print(f"Processing: {file_path.relative_to(self.docs_dir)}")
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        all_formulas = []
        
        # Extract formulas in order (most specific to least specific)
        # 1. Display formulas in div structures
        content, formulas = self.extract_display_formulas_with_divs(content, file_path.relative_to(self.docs_dir))
        all_formulas.extend(formulas)
        
        # 2. Inline formulas in span tags
        content, formulas = self.extract_inline_formulas_with_spans(content, file_path.relative_to(self.docs_dir))
        all_formulas.extend(formulas)
        
        # 3. Standalone display formulas
        content, formulas = self.extract_standalone_display_formulas(content, file_path.relative_to(self.docs_dir))
        all_formulas.extend(formulas)
        
        # 4. Standalone inline formulas
        content, formulas = self.extract_standalone_inline_formulas(content, file_path.relative_to(self.docs_dir))
        all_formulas.extend(formulas)
        
        # Save all formulas
        for formula in all_formulas:
            self.save_formula(formula)
        
        # Create output file path
        relative_path = file_path.relative_to(self.docs_dir)
        output_file = self.result_dir / relative_path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write modified content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.stats['files_processed'] += 1
        self.stats['total_formulas'] += len(all_formulas)
        
        print(f"  → Extracted {len(all_formulas)} formulas")
    
    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in chapter directories"""
        md_files = []
        
        # Look for chapter directories
        for item in self.docs_dir.iterdir():
            if item.is_dir() and item.name.startswith('chapter_'):
                # Find all .md files in this chapter
                for md_file in item.rglob('*.md'):
                    md_files.append(md_file)
        
        # Also process index.md if exists
        index_file = self.docs_dir / 'index.md'
        if index_file.exists():
            md_files.append(index_file)
        
        return sorted(md_files)
    
    def process_all(self):
        """Process all markdown files"""
        print("=" * 80)
        print("Formula Extraction Script")
        print("=" * 80)
        print()
        
        md_files = self.find_markdown_files()
        print(f"Found {len(md_files)} markdown files to process\n")
        
        for md_file in md_files:
            self.process_file(md_file)
        
        # Print statistics
        print()
        print("=" * 80)
        print("Extraction Complete!")
        print("=" * 80)
        print(f"Files processed:          {self.stats['files_processed']}")
        print(f"Total formulas extracted: {self.stats['total_formulas']}")
        print(f"  - Inline formulas:      {self.stats['inline_formulas']}")
        print(f"  - Display formulas:     {self.stats['display_formulas']}")
        print(f"Formulas with metadata:   {self.stats['formulas_with_metadata']}")
        print()
        print(f"Formulas saved to:        {self.formulas_dir}")
        print(f"Modified chapters in:     {self.result_dir}")
        print("=" * 80)
        
        # Save statistics to JSON
        stats_file = self.output_dir / "extraction_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        print(f"Statistics saved to:      {stats_file}")


def main():
    """Main entry point"""
    # Get script directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # Set paths
    docs_dir = project_root / "docs"
    output_dir = script_dir
    
    # Create extractor and run
    extractor = FormulaExtractor(str(docs_dir), str(output_dir))
    extractor.process_all()


if __name__ == "__main__":
    main()
