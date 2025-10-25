#!/usr/bin/env python3
"""
Step 06: Extract Symbols and Link to Formulas

This script:
1. Parses the "Условные обозначения" (Notation) chapter
2. Extracts each symbol as a separate entity
3. Creates JSON files for each symbol
4. Updates formula JSON files with references to symbols they use
5. Generates statistics

Input:  docs/chapter_условные-обозначения/index.md
        normalized/formulas/*.json
Output: normalized/symbols/*.json (symbol definitions)
        normalized/formulas/*.json (updated with symbol references)
        step-06-extract-and-link-symbols/extraction_stats.json
"""

import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


def generate_symbol_id(latex: str, description: str) -> str:
    """Generate unique 12-character MD5-based ID for a symbol"""
    unique_str = f"{latex}|{description}"
    hash_obj = hashlib.md5(unique_str.encode('utf-8'))
    return hash_obj.hexdigest()[:12]


def parse_symbols_file(file_path: Path) -> List[Dict]:
    """
    Parse the symbols file and extract symbol definitions.
    
    Returns list of dicts with:
    - latex: LaTeX representation (without $ delimiters)
    - description: Russian description
    - db_key: Original db key (if present)
    - src: Original image source (if present)
    """
    content = file_path.read_text(encoding='utf-8')
    symbols = []
    
    # Pattern to match symbol definitions:
    # <span data-db-key="..." data-src="..."> $latex$ </span> — description
    pattern = r'<span\s+data-db-key="([^"]+)"\s+data-src="([^"]+)">\s*\$([^$]+)\$\s*</span>\s*—\s*(.+?)(?=\n\n|\n<|$)'
    
    matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        db_key = match.group(1)
        src = match.group(2)
        latex = match.group(3).strip()
        description = match.group(4).strip()
        
        # Clean up description (remove trailing whitespace, normalize spaces)
        description = re.sub(r'\s+', ' ', description).strip()
        
        symbols.append({
            'latex': latex,
            'description': description,
            'db_key': db_key,
            'src': src
        })
    
    # Also catch plain symbols without span wrappers (like at the end of file)
    # Pattern: $latex$ — description
    # First, remove already matched spans to avoid duplicates
    content_without_spans = re.sub(
        r'<span[^>]*>\s*\$[^$]+\$\s*</span>\s*—[^\n]+',
        '',
        content
    )
    
    # Now match plain symbols (no negative lookbehind needed)
    plain_pattern = r'\$([^$]+)\$\s*—\s*(.+?)(?=\n\n|\n\$|$)'
    plain_matches = re.finditer(plain_pattern, content_without_spans, re.MULTILINE)
    
    for match in plain_matches:
        latex = match.group(1).strip()
        description = match.group(2).strip()
        
        # Clean up description
        description = re.sub(r'\s+', ' ', description).strip()
        
        # Skip if latex is empty or description is too short
        if not latex or len(description) < 3:
            continue
        
        symbols.append({
            'latex': latex,
            'description': description,
            'db_key': None,
            'src': None
        })
    
    return symbols


def extract_latex_symbols(latex: str) -> Set[str]:
    """
    Extract individual symbols from LaTeX expression.
    
    Returns set of base symbols (variables, not operators or numbers).
    """
    symbols = set()
    
    # Remove common LaTeX commands and keep only their arguments
    latex_clean = latex
    
    # Extract text content from \text{...}, \mathrm{...}, etc.
    # But don't treat them as symbols
    latex_clean = re.sub(r'\\text\{[^}]+\}', '', latex_clean)
    latex_clean = re.sub(r'\\mathrm\{[^}]+\}', '', latex_clean)
    latex_clean = re.sub(r'\\mathscr\{[^}]+\}', '', latex_clean)
    latex_clean = re.sub(r'\\mathcal\{[^}]+\}', '', latex_clean)
    
    # Pattern for symbols:
    # - Single letters (a-z, A-Z, Greek letters)
    # - Letters with subscripts/superscripts
    # - Special symbols
    
    # Greek letters
    greek_pattern = r'\\(?:alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|omicron|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega|Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega|varepsilon|varphi|vartheta|varsigma)'
    
    # Find Greek letters
    for match in re.finditer(greek_pattern, latex_clean):
        symbols.add(match.group(0))
    
    # Find single Latin letters (possibly with decorations)
    # Pattern: letter possibly followed by _{subscript} or ^{superscript}
    latin_pattern = r'([a-zA-Z])(?:_\{([^}]+)\})?(?:\^\{([^}]+)\})?'
    
    for match in re.finditer(latin_pattern, latex_clean):
        base_letter = match.group(1)
        subscript = match.group(2)
        superscript = match.group(3)
        
        # Build full symbol representation
        symbol = base_letter
        if subscript:
            symbol += f'_{{{subscript}}}'
        if superscript:
            symbol += f'^{{{superscript}}}'
        
        symbols.add(symbol)
    
    # Special symbols
    special_symbols = [
        r'\\hbar', r'\\odot', r'\\oplus', r'\\otimes',
        r'\\infty', r'\\partial', r'\\nabla', r'\\Delta',
        r'\\sum', r'\\prod', r'\\int'
    ]
    
    for special in special_symbols:
        if special in latex_clean:
            symbols.add(special)
    
    return symbols


def save_symbol(symbol_data: Dict, symbols_dir: Path) -> str:
    """
    Save symbol as JSON file.
    
    Returns the symbol ID.
    """
    latex = symbol_data['latex']
    description = symbol_data['description']
    
    symbol_id = generate_symbol_id(latex, description)
    
    symbol_json = {
        'id': symbol_id,
        'latex': latex,
        'description': description,
        'metadata': {
            'db_key': symbol_data.get('db_key'),
            'src': symbol_data.get('src')
        }
    }
    
    output_file = symbols_dir / f"symbol_{symbol_id}.json"
    output_file.write_text(json.dumps(symbol_json, ensure_ascii=False, indent=2), encoding='utf-8')
    
    return symbol_id


def build_symbol_lookup(symbols: List[Dict], symbols_dir: Path) -> Dict[str, str]:
    """
    Build lookup table from LaTeX representation to symbol ID.
    
    Saves symbols to JSON files and returns mapping.
    """
    lookup = {}
    
    for symbol_data in symbols:
        symbol_id = save_symbol(symbol_data, symbols_dir)
        latex = symbol_data['latex']
        lookup[latex] = symbol_id
    
    return lookup


def find_symbols_in_formula(formula_latex: str, symbol_lookup: Dict[str, str]) -> List[str]:
    """
    Find which symbols from the lookup table are used in the formula.
    
    Returns list of symbol IDs.
    """
    # Extract symbols from formula
    formula_symbols = extract_latex_symbols(formula_latex)
    
    # Match against symbol lookup
    found_symbol_ids = []
    
    for formula_symbol in formula_symbols:
        # Try exact match first
        if formula_symbol in symbol_lookup:
            symbol_id = symbol_lookup[formula_symbol]
            if symbol_id not in found_symbol_ids:
                found_symbol_ids.append(symbol_id)
            continue
        
        # Try matching base letter without subscript/superscript
        base_symbol = re.sub(r'[_^]\{[^}]+\}', '', formula_symbol)
        if base_symbol in symbol_lookup:
            symbol_id = symbol_lookup[base_symbol]
            if symbol_id not in found_symbol_ids:
                found_symbol_ids.append(symbol_id)
    
    return found_symbol_ids


def update_formulas_with_symbols(formulas_dir: Path, symbol_lookup: Dict[str, str]) -> Dict:
    """
    Update all formula JSON files with symbol references.
    
    Returns statistics.
    """
    stats = {
        'formulas_processed': 0,
        'formulas_with_symbols': 0,
        'total_symbol_references': 0,
        'symbols_per_formula': defaultdict(int)
    }
    
    formula_files = sorted(formulas_dir.glob('formula_*.json'))
    
    print(f"Processing {len(formula_files)} formulas...")
    
    for i, formula_file in enumerate(formula_files, 1):
        if i % 500 == 0:
            print(f"  Processed {i}/{len(formula_files)}...")
        
        # Load formula
        formula_data = json.loads(formula_file.read_text(encoding='utf-8'))
        
        # Find symbols
        symbol_ids = find_symbols_in_formula(formula_data['latex'], symbol_lookup)
        
        # Update formula data
        if 'symbols' not in formula_data:
            formula_data['symbols'] = []
        
        formula_data['symbols'] = symbol_ids
        
        # Save updated formula
        formula_file.write_text(
            json.dumps(formula_data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        
        # Update stats
        stats['formulas_processed'] += 1
        if symbol_ids:
            stats['formulas_with_symbols'] += 1
            stats['total_symbol_references'] += len(symbol_ids)
            stats['symbols_per_formula'][len(symbol_ids)] += 1
    
    return stats


def main():
    # Paths
    base_dir = Path(__file__).parent.parent
    symbols_file = base_dir.parent / 'docs' / 'chapter_условные-обозначения' / 'index.md'
    symbols_dir = base_dir / 'symbols'
    formulas_dir = base_dir / 'formulas'
    output_dir = Path(__file__).parent
    
    print("=" * 80)
    print("STEP 06: EXTRACT SYMBOLS AND LINK TO FORMULAS")
    print("=" * 80)
    print()
    
    # Step 1: Parse symbols file
    print("Step 1: Parsing symbols file...")
    symbols = parse_symbols_file(symbols_file)
    print(f"✓ Extracted {len(symbols)} symbol definitions")
    print()
    
    # Step 2: Save symbols and build lookup
    print("Step 2: Saving symbols to JSON...")
    symbol_lookup = build_symbol_lookup(symbols, symbols_dir)
    print(f"✓ Saved {len(symbol_lookup)} symbols")
    print()
    
    # Step 3: Update formulas with symbol references
    print("Step 3: Updating formulas with symbol references...")
    stats = update_formulas_with_symbols(formulas_dir, symbol_lookup)
    print(f"✓ Processed {stats['formulas_processed']} formulas")
    print(f"✓ {stats['formulas_with_symbols']} formulas contain symbols")
    print(f"✓ {stats['total_symbol_references']} total symbol references")
    print()
    
    # Step 4: Generate statistics
    print("Step 4: Generating statistics...")
    
    extraction_stats = {
        'total_symbols': len(symbols),
        'symbols_with_metadata': sum(1 for s in symbols if s.get('db_key')),
        'formulas_processed': stats['formulas_processed'],
        'formulas_with_symbols': stats['formulas_with_symbols'],
        'total_symbol_references': stats['total_symbol_references'],
        'average_symbols_per_formula': (
            stats['total_symbol_references'] / stats['formulas_with_symbols']
            if stats['formulas_with_symbols'] > 0 else 0
        ),
        'symbol_distribution': dict(stats['symbols_per_formula'])
    }
    
    stats_file = output_dir / 'extraction_stats.json'
    stats_file.write_text(
        json.dumps(extraction_stats, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    print(f"✓ Statistics saved to {stats_file.name}")
    print()
    
    # Display summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total symbols extracted:        {extraction_stats['total_symbols']}")
    print(f"Symbols with metadata:          {extraction_stats['symbols_with_metadata']}")
    print(f"Formulas processed:             {extraction_stats['formulas_processed']}")
    print(f"Formulas with symbols:          {extraction_stats['formulas_with_symbols']}")
    print(f"Total symbol references:        {extraction_stats['total_symbol_references']}")
    print(f"Average symbols per formula:    {extraction_stats['average_symbols_per_formula']:.2f}")
    print()
    
    # Show distribution
    print("Symbol distribution in formulas:")
    for count in sorted(extraction_stats['symbol_distribution'].keys(), key=int):
        formulas = extraction_stats['symbol_distribution'][count]
        print(f"  {count} symbols: {formulas} formulas")
    print()
    
    print("✓ Step 06 completed successfully!")
    print()


if __name__ == '__main__':
    main()
