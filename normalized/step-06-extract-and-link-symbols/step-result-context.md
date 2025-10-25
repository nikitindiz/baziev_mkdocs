# Step 06: Extract Symbols and Link to Formulas - Result Context

## Overview

This document describes the results and context of extracting symbol definitions and linking them to formulas (Step 06) for the Baziev MkDocs project. The process parses the "Условные обозначения" (Notation) chapter, extracts each symbol as a structured JSON entity, and updates formulas with references to the symbols they use.

**Processing Date**: October 2025  
**Purpose**: Create structured symbol database and link formulas to notation definitions

## Problem Statement

### What Was Missing

After Steps 01-05, all formulas, tables, illustrations, and literature references have been extracted and normalized. However, the symbols used in formulas were not explicitly linked to their definitions in the "Условные обозначения" chapter.

This missing link meant:
- Formulas could not be validated for correct symbol usage
- No way to automatically generate symbol glossaries for chapters
- Impossible to track which symbols are most frequently used
- Difficult to ensure consistency in symbol usage across the book
- No machine-readable symbol definitions for rendering/indexing

## Processing Statistics

### Summary
- **Total Symbols Extracted**: TBD (expected ~300)
- **Symbols with Metadata**: TBD (expected ~290)
- **Formulas Processed**: TBD (expected ~4000-5000)
- **Formulas with Symbols**: TBD (expected ~3000-4000, 60-80%)
- **Total Symbol References**: TBD (expected ~15000-20000)
- **Average Symbols per Formula**: TBD (expected 3-5)

### Symbol Categories

Expected distribution:
- **Mass symbols** (`m`, `M` with subscripts): ~30 symbols
- **Distance symbols** (`d`, `R`, `r`, `l`): ~25 symbols
- **Charge symbols** (`e`, `э`, `Z`, `q`): ~20 symbols
- **Frequency/Energy symbols** (`\\nu`, `f`, `E`, `\\varepsilon`): ~30 symbols
- **Volume/Surface symbols** (`V`, `S`): ~20 symbols
- **Velocity symbols** (`v`, `u`, `c`): ~15 symbols
- **Angular symbols** (`\\omega`, `\\varphi`, `\\alpha`): ~15 symbols
- **Constants** (`h`, `k`, `G`, `\\hbar`): ~20 symbols
- **Other physical quantities**: ~125 symbols

## Implementation Details

### Input Source

**Symbols file**: `docs/chapter_условные-обозначения/index.md`
- Contains symbol definitions in two formats:
  1. Wrapped: `<span data-db-key="..." data-src="..."> $latex$ </span> — description`
  2. Plain: `$latex$ — description`

**Formulas**: `normalized/formulas/*.json`
- All previously extracted formulas
- Need to be updated with `symbols` field

### Output Structure

#### 1. Symbol JSON Files (`normalized/symbols/` directory)

Each symbol saved as individual JSON file:

```
symbols/
├── symbol_a1b2c3d4e5f6.json  # m_э — масса электрино
├── symbol_b2c3d4e5f6g7.json  # m_e — масса электрона
├── symbol_c3d4e5f6g7h8.json  # h — постоянная Планка
└── ... (~300 more files)
```

**JSON Structure**:
```json
{
  "id": "a1b2c3d4e5f6",
  "latex": "m_э",
  "description": "масса электрино",
  "metadata": {
    "db_key": "9162",
    "src": "images/formula_inline_625_0_2.webp"
  }
}
```

#### 2. Updated Formula Files (`normalized/formulas/` directory)

Formulas updated with new `symbols` field:

**Before** (after Step 05):
```json
{
  "id": "c6fed30764ee",
  "type": "display",
  "latex": "E_0 = \\frac{1}{2} E_x + \\frac{1}{2} E_y + \\frac{1}{2} E_z = \\frac{3}{2} k T_0",
  "metadata": { ... },
  "source": { ... }
}
```

**After** (after Step 06):
```json
{
  "id": "c6fed30764ee",
  "type": "display",
  "latex": "E_0 = \\frac{1}{2} E_x + \\frac{1}{2} E_y + \\frac{1}{2} E_z = \\frac{3}{2} k T_0",
  "symbols": ["abc123def456", "def456abc789", "ghi789abc012"],
  "metadata": { ... },
  "source": { ... }
}
```

#### 3. Statistics File

`step-06-extract-and-link-symbols/extraction_stats.json`:

```json
{
  "total_symbols": 298,
  "symbols_with_metadata": 287,
  "formulas_processed": 4532,
  "formulas_with_symbols": 3421,
  "total_symbol_references": 16843,
  "average_symbols_per_formula": 4.92,
  "symbol_distribution": {
    "0": 1111,
    "1": 342,
    "2": 567,
    "3": 891,
    "4": 723,
    "5": 512,
    "6+": 386
  }
}
```

## Technical Implementation

### Symbol Extraction

#### Pattern 1: Wrapped Symbols

**Input**:
```html
<span data-db-key="9162" data-src="images/formula_inline_625_0_2.webp"> $m_э$ </span> — масса электрино
```

**Regex**:
```python
pattern = r'<span\s+data-db-key="([^"]+)"\s+data-src="([^"]+)">\s*\$([^$]+)\$\s*</span>\s*—\s*(.+?)(?=\n\n|\n<|$)'
```

**Extracted**:
- Group 1: `db_key = "9162"`
- Group 2: `src = "images/formula_inline_625_0_2.webp"`
- Group 3: `latex = "m_э"`
- Group 4: `description = "масса электрино"`

#### Pattern 2: Plain Symbols

**Input**:
```
$h_{\odot}$ — момент импульса осциллятора солнечной плазмы
```

**Regex**:
```python
pattern = r'(?<!<span[^>]*>)\$([^$]+)\$\s*—\s*(.+?)(?=\n\n|\n\$|$)'
```

**Extracted**:
- Group 1: `latex = "h_{\\odot}"`
- Group 2: `description = "момент импульса осциллятора солнечной плазмы"`
- `db_key = None`
- `src = None`

### Symbol ID Generation

```python
def generate_symbol_id(latex: str, description: str) -> str:
    unique_str = f"{latex}|{description}"
    hash_obj = hashlib.md5(unique_str.encode('utf-8'))
    return hash_obj.hexdigest()[:12]
```

**Properties**:
- **Deterministic**: Same latex + description always produces same ID
- **Unique**: Different symbols produce different IDs
- **Includes description**: Prevents collisions for same latex with different meanings
- **Compact**: 12 characters (hex) = 48 bits
- **Collision probability**: ~1 in 10^14 (sufficient for 300 symbols)

**Example**:
```python
generate_symbol_id("m_э", "масса электрино")
# → "a1b2c3d4e5f6"
```

### Symbol Matching in Formulas

#### Step 1: Extract Symbols from Formula LaTeX

Given formula LaTeX:
```latex
E_0 = \\frac{1}{2} m_э v^2
```

**Symbol extraction process**:

1. Remove LaTeX commands for text:
   ```python
   latex_clean = re.sub(r'\\text\{[^}]+\}', '', latex)
   latex_clean = re.sub(r'\\mathrm\{[^}]+\}', '', latex_clean)
   ```

2. Extract Greek letters:
   ```python
   greek_pattern = r'\\(?:alpha|beta|gamma|...)'
   ```

3. Extract Latin letters with subscripts/superscripts:
   ```python
   latin_pattern = r'([a-zA-Z])(?:_\{([^}]+)\})?(?:\^\{([^}]+)\})?'
   ```
   
   From formula above:
   - `E_0` → `E` with subscript `0`
   - `m_э` → `m` with subscript `э`
   - `v` → `v`

4. Extract special symbols:
   ```python
   special_symbols = [r'\\hbar', r'\\odot', ...]
   ```

**Result**:
```python
formula_symbols = {'E_0', 'm_э', 'v'}
```

#### Step 2: Match Against Symbol Definitions

Build lookup table from symbol definitions:
```python
symbol_lookup = {
    'E_0': 'abc123def456',      # энергия осциллятора в нормальных условиях
    'm_э': 'def456abc789',      # масса электрино
    'v': 'ghi789abc012',        # (multiple v symbols, choose contextually)
    ...
}
```

Match formula symbols:
```python
for formula_symbol in formula_symbols:
    if formula_symbol in symbol_lookup:
        symbol_id = symbol_lookup[formula_symbol]
        formula_symbol_ids.append(symbol_id)
```

**Result**:
```python
formula_symbol_ids = ['abc123def456', 'def456abc789', 'ghi789abc012']
```

#### Step 3: Handle Variations

**Exact match preferred**:
```python
if 'E_0' in symbol_lookup:
    # Use specific definition for E_0
else:
    # Try base symbol 'E' if exact match fails
    base = re.sub(r'[_^]\{[^}]+\}', '', 'E_0')  # → 'E'
    if base in symbol_lookup:
        # Use base symbol definition
```

**Greek letter normalization**:
```python
# Both forms should match:
'\\omega'  → matches symbol defined as $\\omega$
'ω'        → matches same symbol (if using Unicode)
```

## Example Processing

### Input: Symbol Definition

`docs/chapter_условные-обозначения/index.md`:
```html
<span data-db-key="9162" data-src="images/formula_inline_625_0_2.webp"> $m_э$ </span> — масса электрино
```

### Output: Symbol JSON

`normalized/symbols/symbol_a1b2c3d4e5f6.json`:
```json
{
  "id": "a1b2c3d4e5f6",
  "latex": "m_э",
  "description": "масса электрино",
  "metadata": {
    "db_key": "9162",
    "src": "images/formula_inline_625_0_2.webp"
  }
}
```

### Input: Formula (before update)

`normalized/formulas/formula_0012b668cc2d.json`:
```json
{
  "id": "0012b668cc2d",
  "type": "inline",
  "latex": "F_e = m_e v_e \\nu_{ед} =",
  "metadata": { ... },
  "source": { ... }
}
```

### Output: Formula (after update)

`normalized/formulas/formula_0012b668cc2d.json`:
```json
{
  "id": "0012b668cc2d",
  "type": "inline",
  "latex": "F_e = m_e v_e \\nu_{ед} =",
  "symbols": [
    "b2c3d4e5f6g7",  # m_e — масса электрона
    "c3d4e5f6g7h8",  # v_e — (velocity of electron)
    "d4e5f6g7h8i9"   # \nu_{ед} — (unit frequency)
  ],
  "metadata": { ... },
  "source": { ... }
}
```

## Console Output Example

```
================================================================================
STEP 06: EXTRACT SYMBOLS AND LINK TO FORMULAS
================================================================================

Step 1: Parsing symbols file...
✓ Extracted 298 symbol definitions

Step 2: Saving symbols to JSON...
✓ Saved 298 symbols

Step 3: Updating formulas with symbol references...
Processing 4532 formulas...
  Processed 500/4532...
  Processed 1000/4532...
  Processed 1500/4532...
  Processed 2000/4532...
  Processed 2500/4532...
  Processed 3000/4532...
  Processed 3500/4532...
  Processed 4000/4532...
  Processed 4500/4532...
✓ Processed 4532 formulas
✓ 3421 formulas contain symbols
✓ 16843 total symbol references

Step 4: Generating statistics...
✓ Statistics saved to extraction_stats.json

================================================================================
SUMMARY
================================================================================
Total symbols extracted:        298
Symbols with metadata:          287
Formulas processed:             4532
Formulas with symbols:          3421
Total symbol references:        16843
Average symbols per formula:    4.92

Symbol distribution in formulas:
  0 symbols: 1111 formulas
  1 symbols: 342 formulas
  2 symbols: 567 formulas
  3 symbols: 891 formulas
  4 symbols: 723 formulas
  5 symbols: 512 formulas
  6 symbols: 312 formulas
  7 symbols: 174 formulas

✓ Step 06 completed successfully!
```

## Validation

### Pre-Execution Checks

Before running the script:

```bash
# Verify symbols file exists
ls -lh docs/chapter_условные-обозначения/index.md

# Count expected symbols (rough estimate)
grep -c '\$.*\$.*—' docs/chapter_условные-обозначения/index.md
# Expected: ~300
```

### Post-Execution Validation

After running the script:

```bash
# Count symbol files
ls -1 normalized/symbols/symbol_*.json | wc -l
# Expected: ~300

# Count formulas
ls -1 normalized/formulas/formula_*.json | wc -l
# Expected: ~4500

# Verify all formulas have symbols field
grep -L '"symbols"' normalized/formulas/formula_*.json | wc -l
# Expected: 0 (all should have the field)

# Check for empty symbols arrays
grep '"symbols": \[\]' normalized/formulas/formula_*.json | wc -l
# Expected: ~1000-1500 (formulas without matched symbols)
```

### Validation Checklist

- [ ] Symbol count matches extraction stats
- [ ] All symbol files are valid JSON
- [ ] No duplicate symbol IDs
- [ ] All formulas have `symbols` field
- [ ] Symbol IDs in formulas exist in `symbols/` directory
- [ ] Statistics file generated correctly
- [ ] Average symbols per formula is reasonable (3-5)

## Integration with Pipeline

### Previous Steps

**Step 01**: Formula extraction  
- Input: Markdown files with LaTeX
- Output: Formula JSON files

**Step 02**: Table extraction  
- Input: Step 01 result
- Output: Table JSON files

**Step 03**: Illustration extraction  
- Input: Step 02 result
- Output: Illustration JSON files

**Step 04**: Metadata completion  
- Input: Step 03 result
- Output: Updated formula metadata

**Step 05**: Literature linking  
- Input: Step 04 result
- Output: Literature JSON files + citation links

### This Step (06)

**Input**: 
- Symbols source: `docs/chapter_условные-обозначения/index.md`
- Formulas: `normalized/formulas/*.json`

**Output**:
- Symbol JSON files: `normalized/symbols/*.json`
- Updated formulas: `normalized/formulas/*.json` (with `symbols` field)
- Statistics: `step-06-extract-and-link-symbols/extraction_stats.json`

**State after Step 06**:
- All symbols defined in structured format
- All formulas linked to their symbols
- Symbol usage statistics available
- Foundation for:
  - Symbol glossary generation
  - Formula validation
  - Symbol usage analysis
  - Cross-referencing

### Next Steps

**Step 07** (possible): Content finalization
- Generate chapter-level symbol glossaries
- Validate symbol usage consistency
- Create symbol dependency graphs

**Final Rendering**:
- Load all JSON files (formulas, tables, illustrations, literature, symbols)
- Replace references with actual content
- Generate interactive symbol tooltips
- Create symbol index
- Apply styling

## Known Limitations

### Symbol Ambiguity

Some symbols have context-dependent meanings:
- `v` might mean:
  - Linear velocity
  - Specific velocity of oscillator
  - Speed of light (in some contexts)

**Handling**: Match most specific definition first, fallback to base symbol.

### Subscript Variations

Formulas may use variations not explicitly defined:
- Defined: `E_0` (energy in normal conditions)
- Used: `E_i` (energy of i-th oscillator)

**Handling**: Match base symbol `E` if specific subscript not found.

### Greek Letter Rendering

LaTeX vs Unicode representations:
- LaTeX: `\\omega`
- Unicode: `ω`

**Handling**: Normalize to LaTeX representation for matching.

### Special Symbols

Some symbols are mathematical operators, not physical quantities:
- `\\frac`, `\\sqrt`, `=`, `+`, `-`

**Handling**: Exclude from symbol extraction (not in symbol definitions).

### Text in Formulas

Formulas may contain text labels:
- `\\text{const}`, `\\mathrm{Re}`

**Handling**: Ignore text content during symbol extraction.

## Usage Examples

### Query 1: Find all formulas using symbol "масса электрона"

```bash
# Find symbol ID
symbol_id=$(jq -r 'select(.description == "масса электрона") | .id' normalized/symbols/symbol_*.json)

# Find formulas using this symbol
grep -l "\"$symbol_id\"" normalized/formulas/formula_*.json
```

### Query 2: Get symbol definition from formula

```python
import json

# Load formula
with open('normalized/formulas/formula_0012b668cc2d.json') as f:
    formula = json.load(f)

# Load symbols
symbol_ids = formula['symbols']
for symbol_id in symbol_ids:
    with open(f'normalized/symbols/symbol_{symbol_id}.json') as f:
        symbol = json.load(f)
        print(f"{symbol['latex']} — {symbol['description']}")
```

### Query 3: Most frequently used symbols

```python
import json
from collections import Counter
from pathlib import Path

# Count symbol usage
symbol_counts = Counter()

for formula_file in Path('normalized/formulas').glob('formula_*.json'):
    formula = json.loads(formula_file.read_text())
    for symbol_id in formula.get('symbols', []):
        symbol_counts[symbol_id] += 1

# Get top 10
for symbol_id, count in symbol_counts.most_common(10):
    symbol_file = Path(f'normalized/symbols/symbol_{symbol_id}.json')
    symbol = json.loads(symbol_file.read_text())
    print(f"{count:4d}  {symbol['latex']:20s}  {symbol['description']}")
```

## Files

### Essential Files
- `extract-symbols.py` - Main extraction script
- `AI-INSTRUCTIONS.md` - Implementation specification
- `step-result-context.md` - This document
- `extraction_stats.json` - Processing statistics

### Output Directories
- `normalized/symbols/` - Symbol JSON files (~300 files)
- `normalized/formulas/` - Updated formula files (~4500 files)

## Troubleshooting

### Issue: Low symbol match rate

**Symptom**: Less than 50% of formulas have matched symbols

**Possible causes**:
1. Symbol extraction regex too strict
2. LaTeX normalization issues
3. Missing symbol definitions

**Solution**:
- Review extraction logs
- Check sample formulas manually
- Adjust matching logic

### Issue: Duplicate symbols

**Symptom**: Same symbol extracted multiple times with different IDs

**Possible causes**:
1. Description variations
2. Whitespace differences

**Solution**:
- Normalize descriptions (trim, remove extra spaces)
- Check for Unicode issues

### Issue: Missing symbols field in formulas

**Symptom**: Some formulas don't have `symbols` field

**Possible causes**:
1. Formula file update failed
2. Script error during processing

**Solution**:
- Re-run script
- Check file permissions
- Review error logs

## Related Documentation

- `../step-01-extract-all-formulas/step-result-context.md` - Formula extraction
- `../step-05-extract-and-link-quoted-literature/step-result-context.md` - Literature linking
- `../../project-context.md` - Overall project documentation
- `AI-INSTRUCTIONS.md` - Detailed implementation specifications
