#!/usr/bin/env python3
"""
Illustration Extraction Script for Baziev Physics Book
Extracts SVG illustrations from markdown files.

Features:
- Extracts SVG illustrations wrapped in div layouts (both full and simple wrappers)
- Handles metadata attributes (data-db-key, data-src)
- Preserves figure captions (including formulas)
- Generates hash-based unique IDs
- Stores illustrations as individual JSON files
- Creates modified chapters with illustration references
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Illustration:
    """Represents an extracted illustration"""
    id: str
    type: str  # 'svg' (future: 'png', 'jpg', etc.)
    svg_content: str
    caption: Optional[str]
    metadata: Dict
    source: Dict
    wrapper_html: Optional[str] = None


class IllustrationExtractor:
    """Extracts illustrations from markdown files"""
    
    def __init__(self, input_dir: str, output_dir: str, illustrations_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.illustrations_dir = Path(illustrations_dir)
        self.result_dir = self.output_dir / "result"
        
        # Ensure directories exist
        self.illustrations_dir.mkdir(parents=True, exist_ok=True)
        self.result_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_illustrations': 0,
            'svg_illustrations': 0,
            'files_processed': 0,
            'illustrations_with_metadata': 0,
            'illustrations_with_captions': 0,
            'captions_with_formulas': 0,
            'full_wrapper': 0,
            'simple_wrapper': 0
        }
    
    def generate_illustration_id(self, svg_content: str, metadata: Dict, source: str, position: int) -> str:
        """Generate hash-based unique ID for illustration"""
        # Use SVG viewBox and first 500 chars for uniqueness
        viewbox_match = re.search(r'viewBox="([^"]+)"', svg_content)
        viewbox = viewbox_match.group(1) if viewbox_match else ""
        
        svg_preview = svg_content[:500]
        unique_str = f"{viewbox}|{svg_preview}|{metadata.get('db_key')}|{metadata.get('src')}|{source}|{position}"
        hash_obj = hashlib.md5(unique_str.encode('utf-8'))
        return hash_obj.hexdigest()[:12]
    
    def extract_metadata_from_tag(self, tag_str: str) -> Dict:
        """Extract metadata attributes from HTML tag"""
        metadata = {}
        
        # Extract data-db-key
        db_key_match = re.search(r'data-db-key="([^"]+)"', tag_str)
        if db_key_match:
            metadata['db_key'] = db_key_match.group(1)
        
        # Extract data-src
        src_match = re.search(r'data-src="([^"]+)"', tag_str)
        if src_match:
            metadata['src'] = src_match.group(1)
        
        return metadata
    
    def find_formula_refs(self, text: str) -> List[str]:
        """Find all {{formula:*}} references in text"""
        pattern = r'\{\{formula:[a-f0-9]+(?::\([^)]+\))?\}\}'
        return re.findall(pattern, text)
    
    def extract_svg_id(self, svg_content: str) -> Optional[str]:
        """Extract SVG id attribute if present"""
        id_match = re.search(r'<svg[^>]*\s+id="([^"]+)"', svg_content)
        if id_match:
            return id_match.group(1)
        return None
    
    def extract_svg_viewbox(self, svg_content: str) -> Optional[str]:
        """Extract SVG viewBox attribute if present"""
        viewbox_match = re.search(r'viewBox="([^"]+)"', svg_content)
        if viewbox_match:
            return viewbox_match.group(1)
        return None
    
    def count_svg_elements(self, svg_content: str) -> Dict[str, int]:
        """Count different SVG element types"""
        counts = {
            'path': len(re.findall(r'<path', svg_content)),
            'text': len(re.findall(r'<text', svg_content)),
            'line': len(re.findall(r'<line', svg_content)),
            'circle': len(re.findall(r'<circle', svg_content)),
            'rect': len(re.findall(r'<rect', svg_content)),
            'g': len(re.findall(r'<g', svg_content)),
            'polygon': len(re.findall(r'<polygon', svg_content)),
            'polyline': len(re.findall(r'<polyline', svg_content)),
        }
        return counts
    
    def extract_svg_illustrations(self, content: str, file_path: str) -> Tuple[str, List[Illustration]]:
        """Extract SVG illustrations with both full and simple wrappers"""
        illustrations = []
        modified_content = content
        
        # Pattern 1: Full wrapper with flex div
        # Structure: 
        # <div style="display: flex; ...">
        #   <div ...>
        #     <div data-db-key="..." data-src="...">
        #       <svg>...</svg>
        #     </div>
        #   </div>
        #   <div style="font-style: italic; ...">Caption</div>
        # </div>
        
        pattern_full = r'<div\s+style="[^"]*display:\s*flex[^"]*"[^>]*>\s*<div[^>]*>\s*<div([^>]*)>\s*(<svg[^>]*>.*?</svg>)\s*</div>\s*</div>\s*(?:<div\s+style="[^"]*font-style:\s*italic[^"]*"[^>]*>(.*?)</div>\s*)?</div>'
        
        # Pattern 2: Simple wrapper (just data-db-key div with SVG, no flex wrapper)
        # Structure:
        # <div data-db-key="..." data-src="...">
        # <svg>...</svg>
        # </div>
        # Optional caption below
        
        pattern_simple = r'<div([^>]*data-db-key[^>]*)>\s*(<svg[^>]*>.*?</svg>)\s*</div>(?:\s*<div[^>]*>([^<]*(?:{{[^}]+}}[^<]*)*)</div>)?'
        
        # First, extract full wrappers
        matches_full = list(re.finditer(pattern_full, content, flags=re.DOTALL | re.IGNORECASE))
        
        # Track positions to avoid double-extraction
        extracted_positions = set()
        
        # Process full wrappers in reverse to preserve positions
        for match in reversed(matches_full):
            wrapper_start = match.start()
            wrapper_end = match.end()
            extracted_positions.add((wrapper_start, wrapper_end))
            wrapper_html = match.group(0)
            inner_div_attrs = match.group(1)
            svg_content = match.group(2)
            caption = match.group(3) if match.group(3) else None
            
            # Clean up caption
            if caption:
                caption = caption.strip()
                caption = re.sub(r'\s+', ' ', caption)
            
            # Extract metadata from inner div
            metadata = self.extract_metadata_from_tag(inner_div_attrs)
            
            # Extract SVG properties
            svg_id = self.extract_svg_id(svg_content)
            svg_viewbox = self.extract_svg_viewbox(svg_content)
            element_counts = self.count_svg_elements(svg_content)
            
            # Find formula references in caption
            formula_refs = []
            has_formulas_in_caption = False
            if caption:
                formula_refs = self.find_formula_refs(caption)
                has_formulas_in_caption = len(formula_refs) > 0
            
            # Generate illustration ID
            illustration_id = self.generate_illustration_id(
                svg_content,
                metadata,
                str(file_path),
                wrapper_start
            )
            
            # Create illustration object
            illustration = Illustration(
                id=illustration_id,
                type='svg',
                svg_content=svg_content,
                caption=caption,
                metadata={
                    'db_key': metadata.get('db_key'),
                    'src': metadata.get('src'),
                    'svg_id': svg_id,
                    'svg_viewbox': svg_viewbox,
                    'element_counts': element_counts,
                    'has_caption': caption is not None,
                    'caption_has_formulas': has_formulas_in_caption,
                    'caption_formula_refs': formula_refs,
                    'wrapper_type': 'full'
                },
                source={
                    'file': str(file_path),
                    'position': wrapper_start
                },
                wrapper_html=wrapper_html
            )
            
            illustrations.append(illustration)
            self.stats['svg_illustrations'] += 1
            self.stats['full_wrapper'] += 1
            
            if metadata.get('db_key') or metadata.get('src'):
                self.stats['illustrations_with_metadata'] += 1
            
            if caption:
                self.stats['illustrations_with_captions'] += 1
            
            if has_formulas_in_caption:
                self.stats['captions_with_formulas'] += 1
            
            # Replace with reference
            ref = f"{{{{illustration:{illustration_id}}}}}"
            modified_content = modified_content[:wrapper_start] + ref + modified_content[wrapper_end:]
        
        # Now extract simple wrappers (not already extracted)
        matches_simple = list(re.finditer(pattern_simple, modified_content, flags=re.DOTALL | re.IGNORECASE))
        
        for match in reversed(matches_simple):
            wrapper_start = match.start()
            wrapper_end = match.end()
            
            # Skip if already extracted or if it's not really a data-db-key div
            inner_div_attrs = match.group(1)
            if 'data-db-key' not in inner_div_attrs:
                continue
            
            # Check if this position overlaps with already extracted
            overlap = False
            for start, end in extracted_positions:
                if not (wrapper_end <= start or wrapper_start >= end):
                    overlap = True
                    break
            
            if overlap:
                continue
            
            wrapper_html = match.group(0)
            svg_content = match.group(2)
            caption = match.group(3) if match.group(3) else None
            
            # Clean up caption
            if caption:
                caption = caption.strip()
                caption = re.sub(r'\s+', ' ', caption)
                # Simple wrapper captions are often just text on next line
                # Check if it looks like a real caption (has "Рис" or formulas)
                if not ('Рис' in caption or 'рис' in caption or '{{formula:' in caption or '{{table:' in caption):
                    caption = None
            
            # Extract metadata
            metadata = self.extract_metadata_from_tag(inner_div_attrs)
            
            # Extract SVG properties
            svg_id = self.extract_svg_id(svg_content)
            svg_viewbox = self.extract_svg_viewbox(svg_content)
            element_counts = self.count_svg_elements(svg_content)
            
            # Find formula references in caption
            formula_refs = []
            has_formulas_in_caption = False
            if caption:
                formula_refs = self.find_formula_refs(caption)
                has_formulas_in_caption = len(formula_refs) > 0
            
            # Generate illustration ID
            illustration_id = self.generate_illustration_id(
                svg_content,
                metadata,
                str(file_path),
                wrapper_start
            )
            
            # Create illustration object
            illustration = Illustration(
                id=illustration_id,
                type='svg',
                svg_content=svg_content,
                caption=caption,
                metadata={
                    'db_key': metadata.get('db_key'),
                    'src': metadata.get('src'),
                    'svg_id': svg_id,
                    'svg_viewbox': svg_viewbox,
                    'element_counts': element_counts,
                    'has_caption': caption is not None,
                    'caption_has_formulas': has_formulas_in_caption,
                    'caption_formula_refs': formula_refs,
                    'wrapper_type': 'simple'
                },
                source={
                    'file': str(file_path),
                    'position': wrapper_start
                },
                wrapper_html=wrapper_html
            )
            
            illustrations.append(illustration)
            self.stats['svg_illustrations'] += 1
            self.stats['simple_wrapper'] += 1
            
            if metadata.get('db_key') or metadata.get('src'):
                self.stats['illustrations_with_metadata'] += 1
            
            if caption:
                self.stats['illustrations_with_captions'] += 1
            
            if has_formulas_in_caption:
                self.stats['captions_with_formulas'] += 1
            
            # Replace with reference
            ref = f"{{{{illustration:{illustration_id}}}}}"
            modified_content = modified_content[:wrapper_start] + ref + modified_content[wrapper_end:]
        
        # Reverse to maintain original order
        illustrations.reverse()
        
        return modified_content, illustrations
    
    def save_illustration(self, illustration: Illustration):
        """Save illustration to JSON file"""
        illustration_file = self.illustrations_dir / f"illustration_{illustration.id}.json"
        
        # Convert to dict
        illustration_dict = {
            'id': illustration.id,
            'type': illustration.type,
            'svg_content': illustration.svg_content,
            'caption': illustration.caption,
            'metadata': illustration.metadata,
            'source': illustration.source,
            'wrapper_html': illustration.wrapper_html
        }
        
        with open(illustration_file, 'w', encoding='utf-8') as f:
            json.dump(illustration_dict, f, ensure_ascii=False, indent=2)
    
    def process_file(self, file_path: Path):
        """Process a single markdown file"""
        print(f"Processing: {file_path.relative_to(self.input_dir)}")
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        all_illustrations = []
        
        # Extract SVG illustrations
        content, illustrations = self.extract_svg_illustrations(content, file_path.relative_to(self.input_dir))
        all_illustrations.extend(illustrations)
        
        # Save all illustrations
        for illustration in all_illustrations:
            self.save_illustration(illustration)
        
        # Create output file path
        relative_path = file_path.relative_to(self.input_dir)
        output_file = self.result_dir / relative_path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write modified content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.stats['files_processed'] += 1
        self.stats['total_illustrations'] += len(all_illustrations)
        
        if all_illustrations:
            print(f"  → Extracted {len(all_illustrations)} illustrations")
    
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
        print("Illustration Extraction Script (FIXED - handles both wrapper types)")
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
        print(f"Files processed:                 {self.stats['files_processed']}")
        print(f"Total illustrations extracted:   {self.stats['total_illustrations']}")
        print(f"  - SVG illustrations:           {self.stats['svg_illustrations']}")
        print(f"  - Full wrapper (flex div):     {self.stats['full_wrapper']}")
        print(f"  - Simple wrapper (no flex):    {self.stats['simple_wrapper']}")
        print(f"Illustrations with metadata:     {self.stats['illustrations_with_metadata']}")
        print(f"Illustrations with captions:     {self.stats['illustrations_with_captions']}")
        print(f"Captions with formula refs:      {self.stats['captions_with_formulas']}")
        print()
        print(f"Illustrations saved to:          {self.illustrations_dir}")
        print(f"Modified chapters in:            {self.result_dir}")
        print("=" * 80)
        
        # Save statistics to JSON
        stats_file = self.output_dir / "extraction_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        print(f"Statistics saved to:             {stats_file}")


def main():
    """Main entry point"""
    # Get script directory
    script_dir = Path(__file__).parent
    normalized_dir = script_dir.parent
    
    # Input: result from step-02
    input_dir = script_dir.parent / "step-02-extract-all-tables" / "result"
    
    # Output: current directory
    output_dir = script_dir
    
    # Illustrations: normalized directory
    illustrations_dir = normalized_dir / "illustrations"
    
    # Validate input directory exists
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        print("Please run step-02 first.")
        return 1
    
    # Create extractor and run
    extractor = IllustrationExtractor(str(input_dir), str(output_dir), str(illustrations_dir))
    extractor.process_all()
    
    return 0


if __name__ == "__main__":
    exit(main())
