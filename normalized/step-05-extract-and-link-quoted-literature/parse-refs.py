#!/usr/bin/env python3
"""
Step 05: Extract and Link Quoted Literature
Extracts literature references from the bibliography and replaces citations in text
with reference markers.

This script:
1. Parses literature entries from the bibliography markdown file
2. Extracts each entry as a separate JSON file
3. Processes markdown files to find and replace literature citations
4. Replaces citations like "М. Планка [1]" with {{literature:ID}}
"""

import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import shutil


class LiteratureExtractor:
    """Extracts and processes literature references"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.normalized_dir = self.base_dir.parent
        self.literature_dir = self.normalized_dir / 'literature'
        self.input_dir = self.normalized_dir / 'step-04-parse-missed-db-keys-and-src' / 'result'
        self.result_dir = self.base_dir / 'result'
        
        # Statistics
        self.stats = {
            'total_entries': 0,
            'files_processed': 0,
            'files_with_citations': 0,
            'total_citations': 0,
            'citations_replaced': 0
        }
        
        # Store literature entries: number -> entry data
        self.literature_map: Dict[int, dict] = {}
    
    def generate_literature_id(self, number: int, content: str) -> str:
        """Generate unique 12-character ID for literature entry"""
        unique_str = f"{number}|{content}"
        hash_obj = hashlib.md5(unique_str.encode('utf-8'))
        return hash_obj.hexdigest()[:12]
    
    def parse_bibliography(self, bib_file: Path) -> Dict[int, dict]:
        """Parse bibliography markdown file and extract entries"""
        print(f"\n📖 Parsing bibliography: {bib_file.name}")
        
        with open(bib_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match numbered entries
        # Matches: "1. Text here..."
        pattern = r'^(\d+)\.\s+(.+?)(?=^\d+\.|$)'
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
        
        entries = {}
        for match in matches:
            number = int(match.group(1))
            text = match.group(2).strip()
            
            # Generate unique ID
            lit_id = self.generate_literature_id(number, text)
            
            # Parse author and title (basic heuristic)
            author = ""
            title = ""
            publication = ""
            
            # Try to parse structure: "Author. Title. Publication info."
            parts = text.split('.')
            if len(parts) >= 2:
                author = parts[0].strip()
                # Rest is title and publication
                remaining = '.'.join(parts[1:]).strip()
                # Try to find publication markers
                pub_markers = ['М.,', 'M.,', 'Л.,', 'Киев,', 'Ann.', 'Phyl.']
                for marker in pub_markers:
                    if marker in remaining:
                        idx = remaining.index(marker)
                        title = remaining[:idx].strip()
                        publication = remaining[idx:].strip()
                        break
                else:
                    # No clear marker, take first sentence as title
                    sentences = remaining.split('.')
                    if sentences:
                        title = sentences[0].strip()
                        publication = '.'.join(sentences[1:]).strip()
            else:
                # Fallback: entire text
                author = text
            
            entry = {
                'id': lit_id,
                'number': number,
                'text': text,
                'author': author,
                'title': title,
                'publication': publication,
                'source': {
                    'file': str(bib_file.relative_to(self.normalized_dir.parent)),
                    'position': match.start()
                }
            }
            
            entries[number] = entry
            print(f"   {number}. {author[:50]}..." if len(author) > 50 else f"   {number}. {author}")
        
        self.stats['total_entries'] = len(entries)
        print(f"\n✓ Extracted {len(entries)} literature entries")
        
        return entries
    
    def save_literature_entries(self):
        """Save literature entries as individual JSON files"""
        print(f"\n💾 Saving literature entries to {self.literature_dir.name}/")
        
        # Create literature directory
        self.literature_dir.mkdir(parents=True, exist_ok=True)
        
        for number, entry in self.literature_map.items():
            filename = f"literature_{entry['id']}.json"
            filepath = self.literature_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Saved {len(self.literature_map)} JSON files")
    
    def find_citations(self, text: str) -> List[Tuple[str, int, int, int]]:
        """
        Find literature citations in text.
        Returns list of (match_text, start_pos, end_pos, ref_number)
        
        Patterns matched:
        - "М. Планка [1]" -> [1]
        - "в работе [2]" -> [2]
        - "[3, 4]" -> [3], [4]
        - "[5—7]" -> [5], [6], [7]
        """
        citations = []
        
        # Pattern 1: Simple [N]
        pattern1 = r'\[(\d+)\]'
        for match in re.finditer(pattern1, text):
            ref_num = int(match.group(1))
            citations.append((
                match.group(0),
                match.start(),
                match.end(),
                ref_num
            ))
        
        # Pattern 2: Ranges [N—M] or [N-M]
        pattern2 = r'\[(\d+)[—\-](\d+)\]'
        for match in re.finditer(pattern2, text):
            start_num = int(match.group(1))
            end_num = int(match.group(2))
            # For ranges, we'll replace with multiple references
            # Store the range as a special case
            for num in range(start_num, end_num + 1):
                citations.append((
                    match.group(0),
                    match.start(),
                    match.end(),
                    num
                ))
        
        # Pattern 3: Multiple refs [N, M]
        pattern3 = r'\[(\d+(?:\s*,\s*\d+)+)\]'
        for match in re.finditer(pattern3, text):
            nums_str = match.group(1)
            nums = [int(n.strip()) for n in nums_str.split(',')]
            for num in nums:
                citations.append((
                    match.group(0),
                    match.start(),
                    match.end(),
                    num
                ))
        
        return citations
    
    def replace_citations(self, text: str) -> Tuple[str, int]:
        """
        Replace citation patterns with {{literature:ID}} references.
        Returns (modified_text, replacement_count)
        """
        replacements_made = 0
        
        # Find all citations
        citations = self.find_citations(text)
        
        if not citations:
            return text, 0
        
        # Group citations by position (to handle ranges and multiples)
        position_groups = {}
        for match_text, start, end, ref_num in citations:
            key = (start, end)
            if key not in position_groups:
                position_groups[key] = {
                    'text': match_text,
                    'refs': []
                }
            position_groups[key]['refs'].append(ref_num)
        
        # Sort by position (reverse to replace from end to beginning)
        sorted_positions = sorted(position_groups.keys(), reverse=True)
        
        for start, end in sorted_positions:
            group = position_groups[(start, end)]
            ref_nums = sorted(set(group['refs']))  # Remove duplicates, sort
            
            # Build replacement string
            if len(ref_nums) == 1:
                # Single reference
                ref_num = ref_nums[0]
                if ref_num in self.literature_map:
                    lit_id = self.literature_map[ref_num]['id']
                    replacement = f"{{{{literature:{lit_id}}}}}"
                    text = text[:start] + replacement + text[end:]
                    replacements_made += 1
            else:
                # Multiple references - keep them together
                ref_parts = []
                for ref_num in ref_nums:
                    if ref_num in self.literature_map:
                        lit_id = self.literature_map[ref_num]['id']
                        ref_parts.append(f"{{{{literature:{lit_id}}}}}")
                
                if ref_parts:
                    # Join with commas: {{literature:ID1}}, {{literature:ID2}}
                    replacement = ', '.join(ref_parts)
                    text = text[:start] + replacement + text[end:]
                    replacements_made += len(ref_parts)
        
        return text, replacements_made
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single markdown file"""
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace citations
        new_content, count = self.replace_citations(content)
        
        if count > 0:
            # Write modified file
            output_path = self.result_dir / file_path.relative_to(self.input_dir)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True
        else:
            # No changes, just copy
            output_path = self.result_dir / file_path.relative_to(self.input_dir)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, output_path)
            
            return False
    
    def process_all_files(self):
        """Process all markdown files from previous step"""
        print(f"\n📝 Processing markdown files from {self.input_dir.name}/")
        
        # Remove existing result directory
        if self.result_dir.exists():
            shutil.rmtree(self.result_dir)
        
        # Find all markdown files
        md_files = sorted(self.input_dir.rglob('*.md'))
        
        print(f"Found {len(md_files)} markdown files")
        
        for md_file in md_files:
            rel_path = md_file.relative_to(self.input_dir)
            
            has_citations = self.process_file(md_file)
            
            self.stats['files_processed'] += 1
            if has_citations:
                self.stats['files_with_citations'] += 1
                print(f"   ✓ {rel_path}")
        
        print(f"\n✓ Processed {self.stats['files_processed']} files")
        print(f"   Files with citations: {self.stats['files_with_citations']}")
    
    def save_stats(self):
        """Save processing statistics"""
        stats_file = self.base_dir / 'extraction_stats.json'
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 Statistics saved to {stats_file.name}")
    
    def print_summary(self):
        """Print processing summary"""
        print("\n" + "=" * 80)
        print("PROCESSING SUMMARY")
        print("=" * 80)
        print(f"Literature entries extracted:  {self.stats['total_entries']}")
        print(f"Files processed:               {self.stats['files_processed']}")
        print(f"Files with citations:          {self.stats['files_with_citations']}")
        print(f"Total citation patterns found: {self.stats['total_citations']}")
        print(f"Citations replaced:            {self.stats['citations_replaced']}")
        print("\nOutput locations:")
        print(f"  - Literature JSON files: {self.literature_dir.relative_to(self.base_dir.parent)}")
        print(f"  - Modified markdown:     {self.result_dir.relative_to(self.base_dir.parent)}")
        print("=" * 80)
    
    def run(self):
        """Main processing workflow"""
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 15 + "STEP 05: EXTRACT AND LINK QUOTED LITERATURE" + " " * 20 + "║")
        print("╚" + "═" * 78 + "╝")
        
        # Find bibliography file
        bib_file = self.normalized_dir.parent / 'docs' / 'chapter_список-цитированной-литературы' / 'index.md'
        
        if not bib_file.exists():
            print(f"✗ Error: Bibliography file not found: {bib_file}")
            return 1
        
        # Parse bibliography
        self.literature_map = self.parse_bibliography(bib_file)
        
        # Save literature entries
        self.save_literature_entries()
        
        # Process all markdown files
        self.process_all_files()
        
        # Save statistics
        self.save_stats()
        
        # Print summary
        self.print_summary()
        
        return 0


def main():
    """Main entry point"""
    script_dir = Path(__file__).parent
    
    extractor = LiteratureExtractor(str(script_dir))
    exit_code = extractor.run()
    
    return exit_code


if __name__ == "__main__":
    import sys
    sys.exit(main())
