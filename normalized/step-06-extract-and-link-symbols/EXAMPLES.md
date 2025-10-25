# Usage Examples

## Finding Symbols

### Example 1: Find symbol by LaTeX

```python
import json
from pathlib import Path

def find_symbol_by_latex(latex: str):
    symbols_dir = Path('../symbols')
    for symbol_file in symbols_dir.glob('symbol_*.json'):
        symbol = json.loads(symbol_file.read_text(encoding='utf-8'))
        if symbol['latex'] == latex:
            return symbol
    return None

# Find mass of electron
symbol = find_symbol_by_latex('m_e')
print(f"{symbol['latex']} — {symbol['description']}")
# Output: m_e — масса электрона
```

### Example 2: Find symbol by description

```python
def find_symbol_by_description(description: str):
    symbols_dir = Path('../symbols')
    for symbol_file in symbols_dir.glob('symbol_*.json'):
        symbol = json.loads(symbol_file.read_text(encoding='utf-8'))
        if description.lower() in symbol['description'].lower():
            return symbol
    return None

# Find Planck constant
symbol = find_symbol_by_description('планка')
print(f"{symbol['latex']} — {symbol['description']}")
# Output: h — постоянная Планка
```

## Analyzing Formulas

### Example 3: Get all symbols used in a formula

```python
def get_formula_symbols(formula_id: str):
    formula_file = Path(f'../formulas/formula_{formula_id}.json')
    formula = json.loads(formula_file.read_text(encoding='utf-8'))
    
    symbols = []
    for symbol_id in formula.get('symbols', []):
        symbol_file = Path(f'../symbols/symbol_{symbol_id}.json')
        symbol = json.loads(symbol_file.read_text(encoding='utf-8'))
        symbols.append(symbol)
    
    return symbols

# Get symbols from a specific formula
symbols = get_formula_symbols('c6fed30764ee')
for symbol in symbols:
    print(f"  {symbol['latex']:20s} — {symbol['description']}")
```

### Example 4: Find formulas using a specific symbol

```python
def find_formulas_with_symbol(symbol_id: str):
    formulas_dir = Path('../formulas')
    matching_formulas = []
    
    for formula_file in formulas_dir.glob('formula_*.json'):
        formula = json.loads(formula_file.read_text(encoding='utf-8'))
        if symbol_id in formula.get('symbols', []):
            matching_formulas.append(formula)
    
    return matching_formulas

# Find all formulas using "масса электрона"
# First, find the symbol
symbol = find_symbol_by_description('масса электрона')
symbol_id = symbol['id']

# Then find formulas
formulas = find_formulas_with_symbol(symbol_id)
print(f"Found {len(formulas)} formulas using m_e")
```

## Statistics and Analysis

### Example 5: Most frequently used symbols

```python
from collections import Counter

def get_symbol_usage_stats():
    formulas_dir = Path('../formulas')
    symbol_counter = Counter()
    
    for formula_file in formulas_dir.glob('formula_*.json'):
        formula = json.loads(formula_file.read_text(encoding='utf-8'))
        for symbol_id in formula.get('symbols', []):
            symbol_counter[symbol_id] += 1
    
    return symbol_counter

# Get top 20 most used symbols
symbol_counter = get_symbol_usage_stats()
symbols_dir = Path('../symbols')

print("Top 20 most used symbols:\n")
print(f"{'Count':>6}  {'LaTeX':20s}  Description")
print("-" * 80)

for symbol_id, count in symbol_counter.most_common(20):
    symbol_file = symbols_dir / f"symbol_{symbol_id}.json"
    symbol = json.loads(symbol_file.read_text(encoding='utf-8'))
    print(f"{count:6d}  {symbol['latex']:20s}  {symbol['description']}")
```

### Example 6: Symbols distribution by chapter

```python
from collections import defaultdict

def get_symbols_by_chapter():
    formulas_dir = Path('../formulas')
    chapter_symbols = defaultdict(set)
    
    for formula_file in formulas_dir.glob('formula_*.json'):
        formula = json.loads(formula_file.read_text(encoding='utf-8'))
        
        # Extract chapter from source file path
        source_file = formula['source']['file']
        chapter = source_file.split('/')[0] if '/' in source_file else 'unknown'
        
        # Add symbols
        for symbol_id in formula.get('symbols', []):
            chapter_symbols[chapter].add(symbol_id)
    
    return chapter_symbols

# Analyze symbol usage by chapter
chapter_symbols = get_symbols_by_chapter()

print("Symbol usage by chapter:\n")
for chapter in sorted(chapter_symbols.keys()):
    count = len(chapter_symbols[chapter])
    print(f"{chapter:60s}  {count:3d} unique symbols")
```

### Example 7: Find unused symbols

```python
def find_unused_symbols():
    # Get all symbol IDs
    symbols_dir = Path('../symbols')
    all_symbols = set()
    for symbol_file in symbols_dir.glob('symbol_*.json'):
        symbol = json.loads(symbol_file.read_text(encoding='utf-8'))
        all_symbols.add(symbol['id'])
    
    # Get used symbols
    formulas_dir = Path('../formulas')
    used_symbols = set()
    for formula_file in formulas_dir.glob('formula_*.json'):
        formula = json.loads(formula_file.read_text(encoding='utf-8'))
        used_symbols.update(formula.get('symbols', []))
    
    # Find unused
    unused = all_symbols - used_symbols
    
    return unused

# Find symbols defined but not used in any formula
unused_symbol_ids = find_unused_symbols()

print(f"Found {len(unused_symbol_ids)} unused symbols:\n")
for symbol_id in sorted(unused_symbol_ids):
    symbol_file = Path(f'../symbols/symbol_{symbol_id}.json')
    symbol = json.loads(symbol_file.read_text(encoding='utf-8'))
    print(f"  {symbol['latex']:20s} — {symbol['description']}")
```

## Generating Reports

### Example 8: Symbol glossary for a chapter

```python
def generate_chapter_glossary(chapter_name: str):
    """Generate a symbol glossary for a specific chapter"""
    formulas_dir = Path('../formulas')
    symbols_dir = Path('../symbols')
    
    # Collect symbols used in chapter
    chapter_symbol_ids = set()
    for formula_file in formulas_dir.glob('formula_*.json'):
        formula = json.loads(formula_file.read_text(encoding='utf-8'))
        
        source_file = formula['source']['file']
        if chapter_name in source_file:
            chapter_symbol_ids.update(formula.get('symbols', []))
    
    # Load symbol details
    symbols = []
    for symbol_id in chapter_symbol_ids:
        symbol_file = symbols_dir / f"symbol_{symbol_id}.json"
        symbol = json.loads(symbol_file.read_text(encoding='utf-8'))
        symbols.append(symbol)
    
    # Sort by LaTeX
    symbols.sort(key=lambda s: s['latex'])
    
    # Generate markdown
    glossary = f"# Условные обозначения — {chapter_name}\n\n"
    
    for symbol in symbols:
        glossary += f"- ${symbol['latex']}$ — {symbol['description']}\n"
    
    return glossary

# Generate glossary for Chapter I
glossary = generate_chapter_glossary('глава-i')
print(glossary)
```

### Example 9: Export symbols to CSV

```python
import csv

def export_symbols_to_csv(output_file: str):
    """Export all symbols to CSV file"""
    symbols_dir = Path('../symbols')
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'latex', 'description', 'db_key', 'src']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for symbol_file in sorted(symbols_dir.glob('symbol_*.json')):
            symbol = json.loads(symbol_file.read_text(encoding='utf-8'))
            writer.writerow({
                'id': symbol['id'],
                'latex': symbol['latex'],
                'description': symbol['description'],
                'db_key': symbol['metadata'].get('db_key', ''),
                'src': symbol['metadata'].get('src', '')
            })

# Export to CSV
export_symbols_to_csv('symbols.csv')
print("Symbols exported to symbols.csv")
```

## Validation

### Example 10: Validate symbol references

```python
def validate_symbol_references():
    """Check that all symbol IDs in formulas exist"""
    formulas_dir = Path('../formulas')
    symbols_dir = Path('../symbols')
    
    # Get all symbol IDs
    symbol_ids = set()
    for symbol_file in symbols_dir.glob('symbol_*.json'):
        symbol = json.loads(symbol_file.read_text(encoding='utf-8'))
        symbol_ids.add(symbol['id'])
    
    # Check formula references
    errors = []
    for formula_file in formulas_dir.glob('formula_*.json'):
        formula = json.loads(formula_file.read_text(encoding='utf-8'))
        
        for symbol_id in formula.get('symbols', []):
            if symbol_id not in symbol_ids:
                errors.append({
                    'formula_id': formula['id'],
                    'missing_symbol_id': symbol_id
                })
    
    return errors

# Validate
errors = validate_symbol_references()
if errors:
    print(f"Found {len(errors)} invalid symbol references:")
    for error in errors[:10]:  # Show first 10
        print(f"  Formula {error['formula_id']} references missing symbol {error['missing_symbol_id']}")
else:
    print("✓ All symbol references are valid")
```

## Integration with MkDocs

### Example 11: Generate symbol tooltips for formulas

```python
def generate_formula_with_tooltips(formula_id: str):
    """Generate HTML with symbol tooltips for a formula"""
    formulas_dir = Path('../formulas')
    symbols_dir = Path('../symbols')
    
    # Load formula
    formula_file = formulas_dir / f"formula_{formula_id}.json"
    formula = json.loads(formula_file.read_text(encoding='utf-8'))
    
    # Load symbols
    symbol_details = {}
    for symbol_id in formula.get('symbols', []):
        symbol_file = symbols_dir / f"symbol_{symbol_id}.json"
        symbol = json.loads(symbol_file.read_text(encoding='utf-8'))
        symbol_details[symbol['latex']] = symbol['description']
    
    # Generate HTML with tooltips
    latex = formula['latex']
    
    # Wrap each symbol in a tooltip span
    for symbol_latex, description in symbol_details.items():
        tooltip_html = f'<span class="symbol-tooltip" title="{description}">{symbol_latex}</span>'
        # This is simplified - real implementation would need proper LaTeX parsing
        latex = latex.replace(symbol_latex, tooltip_html)
    
    return f"<div class=\"formula-with-tooltips\">${latex}$</div>"

# Example usage
html = generate_formula_with_tooltips('c6fed30764ee')
print(html)
```

## Command Line Tools

### Example 12: Quick lookup script

Save as `symbol_lookup.py`:

```python
#!/usr/bin/env python3
import sys
import json
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: symbol_lookup.py <latex>")
    sys.exit(1)

latex = sys.argv[1]
symbols_dir = Path(__file__).parent.parent / 'symbols'

for symbol_file in symbols_dir.glob('symbol_*.json'):
    symbol = json.loads(symbol_file.read_text(encoding='utf-8'))
    if symbol['latex'] == latex:
        print(f"ID:          {symbol['id']}")
        print(f"LaTeX:       {symbol['latex']}")
        print(f"Description: {symbol['description']}")
        if symbol['metadata'].get('db_key'):
            print(f"DB Key:      {symbol['metadata']['db_key']}")
        sys.exit(0)

print(f"Symbol '{latex}' not found")
sys.exit(1)
```

Usage:
```bash
chmod +x symbol_lookup.py
./symbol_lookup.py "m_e"
```
