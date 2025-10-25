# Step 06: Implementation Summary

## Overview

Step 06 extracts symbol definitions from the "Условные обозначения" (Notation) chapter and links them to formulas. This creates a bidirectional relationship between symbols and their usage in mathematical expressions.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT SOURCES                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Symbol Definitions                                        │
│     docs/chapter_условные-обозначения/index.md              │
│     Format: $latex$ — description                            │
│     Count: ~300 symbols                                       │
│                                                               │
│  2. Existing Formulas                                         │
│     normalized/formulas/formula_*.json                       │
│     Count: ~4500 formulas                                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 PROCESSING PIPELINE                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Step 1: Parse Symbol Definitions                            │
│  ├─ Extract LaTeX representations                            │
│  ├─ Extract descriptions (Russian)                           │
│  ├─ Extract metadata (db_key, src)                           │
│  └─ Generate symbol IDs (MD5-based)                          │
│                                                               │
│  Step 2: Save Symbol JSON Files                              │
│  ├─ Create symbol_{id}.json for each                         │
│  └─ Build lookup table: latex → symbol_id                    │
│                                                               │
│  Step 3: Match Symbols in Formulas                           │
│  ├─ Extract symbols from formula LaTeX                       │
│  ├─ Match against symbol lookup table                        │
│  ├─ Build symbol reference list                              │
│  └─ Update formula JSON with "symbols" field                 │
│                                                               │
│  Step 4: Generate Statistics                                 │
│  ├─ Count total symbols and formulas                         │
│  ├─ Calculate usage metrics                                  │
│  └─ Generate distribution data                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      OUTPUT                                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Symbol Database                                           │
│     normalized/symbols/symbol_*.json                         │
│     Structure:                                                │
│     {                                                         │
│       "id": "abc123",                                         │
│       "latex": "m_э",                                         │
│       "description": "масса электрино",                       │
│       "metadata": { "db_key": "9162", "src": "..." }         │
│     }                                                         │
│                                                               │
│  2. Updated Formulas                                          │
│     normalized/formulas/formula_*.json                       │
│     Added field:                                              │
│     "symbols": ["id1", "id2", "id3"]                         │
│                                                               │
│  3. Statistics                                                │
│     step-06-.../extraction_stats.json                        │
│     Metrics: counts, averages, distribution                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Symbol Extraction

```
Symbols File (MD)
        ↓
   [Parse Regex]
        ↓
   Symbol Data
        ↓
  [Generate ID]
        ↓
   Symbol JSON ─────→ symbols/symbol_{id}.json
        │
        └───→ Lookup Table (latex → id)
```

### Formula Update

```
Formula JSON
        ↓
  [Load LaTeX]
        ↓
[Extract Symbols] ←── Lookup Table
        ↓
  Symbol IDs
        ↓
[Update Formula]
        ↓
Formula JSON (updated) ─→ formulas/formula_{id}.json
```

## Key Algorithms

### 1. Symbol Extraction from Text

```python
def parse_symbols_file(file_path):
    # Pattern 1: Wrapped symbols
    pattern1 = r'<span data-db-key="([^"]+)" data-src="([^"]+)">\s*\$([^$]+)\$\s*</span>\s*—\s*(.+?)(?=\n\n|\n<|$)'
    
    # Pattern 2: Plain symbols
    pattern2 = r'(?<!<span[^>]*>)\$([^$]+)\$\s*—\s*(.+?)(?=\n\n|\n\$|$)'
    
    # Extract and structure
    for match in re.finditer(pattern1, content):
        symbol = {
            'latex': match.group(3),
            'description': match.group(4),
            'db_key': match.group(1),
            'src': match.group(2)
        }
        yield symbol
```

### 2. Symbol Matching in LaTeX

```python
def extract_latex_symbols(latex):
    symbols = set()
    
    # Remove text commands
    latex = re.sub(r'\\text\{[^}]+\}', '', latex)
    
    # Extract Greek letters
    greek = r'\\(?:alpha|beta|gamma|...)'
    symbols.update(re.findall(greek, latex))
    
    # Extract Latin with subscripts
    latin = r'([a-zA-Z])(?:_\{([^}]+)\})?(?:\^\{([^}]+)\})?'
    for match in re.finditer(latin, latex):
        symbol = build_symbol(match)
        symbols.add(symbol)
    
    return symbols
```

### 3. Symbol ID Generation

```python
def generate_symbol_id(latex, description):
    # Combine latex and description for uniqueness
    unique_str = f"{latex}|{description}"
    
    # MD5 hash (first 12 characters)
    hash_obj = hashlib.md5(unique_str.encode('utf-8'))
    return hash_obj.hexdigest()[:12]
```

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Count | Time (est.) |
|-----------|------------|-------|-------------|
| Parse symbols file | O(n) | 1 file | < 1s |
| Save symbol JSONs | O(s) | ~300 | < 1s |
| Load formula JSON | O(1) | ~4500 | ~10s |
| Extract symbols from LaTeX | O(m) | ~4500 | ~20s |
| Match symbols | O(k·log s) | ~4500×5 | ~30s |
| Save formula JSON | O(1) | ~4500 | ~10s |
| **Total** | | | **~60s** |

Where:
- n = size of symbols file (~50KB)
- s = number of symbols (~300)
- m = average formula length (~50 chars)
- k = average symbols per formula (~5)

### Space Complexity

| Data Structure | Size (est.) |
|----------------|-------------|
| Symbol JSON files | ~300 × 500B = 150KB |
| Updated formula files | ~4500 × 1KB = 4.5MB |
| Statistics | ~5KB |
| Runtime memory | < 50MB |

## Design Decisions

### Why MD5 for Symbol IDs?

**Alternatives considered:**
1. Sequential numbering (1, 2, 3, ...)
2. LaTeX as key (m_э, m_e, ...)
3. Description-based hash
4. UUID v4

**Chosen: MD5(latex + description)**

**Rationale:**
- ✓ Deterministic (same input → same ID)
- ✓ Unique (different symbols → different IDs)
- ✓ Compact (12 chars vs 36 for UUID)
- ✓ Content-based (changes with symbol definition)
- ✗ Not cryptographically secure (not needed)

### Why Separate Symbol Files?

**Alternatives considered:**
1. Single `symbols.json` file
2. Symbols embedded in formulas
3. Database table

**Chosen: Individual JSON files**

**Rationale:**
- ✓ Consistent with Step 01 (formulas) pattern
- ✓ Easy to add/update individual symbols
- ✓ Parallel processing possible
- ✓ Git-friendly (individual file changes)
- ✗ More files (~300 vs 1)

### Why Update Formulas In-Place?

**Alternatives considered:**
1. Create new formula files
2. Separate symbol-formula mapping file
3. Keep symbols in separate database

**Chosen: Update existing formula files**

**Rationale:**
- ✓ Single source of truth (formula JSON has all data)
- ✓ No need to join data during rendering
- ✓ Preserves existing formula structure
- ✓ Backward compatible (adds field, doesn't remove)
- ✗ Modifies existing files (backup recommended)

## Error Handling

### Missing Symbol Definitions

**Scenario**: Formula uses symbol not in definitions
**Handling**: Log warning, skip symbol, continue processing
**Impact**: Formula has incomplete symbol list

### Malformed Symbol Entries

**Scenario**: Symbol definition doesn't match expected format
**Handling**: Skip entry, log error, continue
**Impact**: Symbol not extracted

### Formula File Read Errors

**Scenario**: Cannot read/parse formula JSON
**Handling**: Log error, skip file, continue
**Impact**: Formula not updated with symbols

### File Write Errors

**Scenario**: Cannot write symbol/formula JSON
**Handling**: Raise exception, stop processing
**Impact**: Partial data, requires re-run

## Integration Points

### With Step 01 (Formulas)

- **Input**: Uses formula JSON files from Step 01
- **Output**: Updates formulas with symbol references
- **Dependency**: Requires Step 01 to be completed first

### With Step 05 (Literature)

- **Similar pattern**: Both link entities (symbols/literature) to text
- **Complementary**: Symbols explain notation, literature provides sources
- **Difference**: Symbols are technical, literature is bibliographic

### With Future Rendering

```python
# Pseudocode for rendering with symbols
def render_formula(formula_json):
    latex = formula_json['latex']
    symbols = load_symbols(formula_json['symbols'])
    
    # Render LaTeX
    html = katex.render(latex)
    
    # Add symbol tooltips
    for symbol in symbols:
        html = add_tooltip(html, symbol['latex'], symbol['description'])
    
    return html
```

## Testing Strategy

### Unit Tests

```python
def test_symbol_extraction():
    text = '<span data-db-key="9162" data-src="..."> $m_э$ </span> — масса'
    symbols = parse_symbols_file(text)
    assert symbols[0]['latex'] == 'm_э'
    assert symbols[0]['description'] == 'масса'

def test_latex_symbol_matching():
    latex = 'E = m v^2'
    symbols = extract_latex_symbols(latex)
    assert 'E' in symbols
    assert 'm' in symbols
    assert 'v' in symbols

def test_symbol_id_generation():
    id1 = generate_symbol_id('m_э', 'масса электрино')
    id2 = generate_symbol_id('m_э', 'масса электрино')
    assert id1 == id2  # Deterministic
```

### Integration Tests

```bash
# Run full pipeline
python3 extract-symbols.py

# Verify outputs
assert_file_count symbols/symbol_*.json 300
assert_all_formulas_have_symbols_field
assert_no_broken_symbol_references
assert_statistics_match_actual_counts
```

## Future Enhancements

### 1. Symbol Variants

Track symbol variations:
```json
{
  "id": "abc123",
  "latex": "E",
  "variants": ["E_0", "E_i", "E_k"],
  "description": "энергия"
}
```

### 2. Symbol Categories

Group related symbols:
```json
{
  "id": "abc123",
  "latex": "m_э",
  "category": "mass",
  "subcategory": "elementary_particles"
}
```

### 3. Symbol Dependencies

Track relationships:
```json
{
  "id": "abc123",
  "latex": "E_0",
  "depends_on": ["h", "f_0"],  // E_0 = h·f_0
  "used_in": ["E", "E_k"]
}
```

### 4. Multi-language Descriptions

Support multiple languages:
```json
{
  "id": "abc123",
  "latex": "m_э",
  "descriptions": {
    "ru": "масса электрино",
    "en": "mass of electrino"
  }
}
```

## Maintenance

### Adding New Symbols

1. Edit `docs/chapter_условные-обозначения/index.md`
2. Add entry: `$new_symbol$ — description`
3. Re-run Step 06
4. New symbol JSON created automatically
5. Formulas updated with new symbol reference

### Updating Symbol Descriptions

1. Edit symbol description in source file
2. Re-run Step 06
3. New symbol ID generated (hash changes)
4. Old symbol file can be removed
5. Formulas updated with new ID

### Removing Symbols

1. Remove from source file
2. Re-run Step 06
3. Symbol JSON file not created
4. Formulas no longer reference removed symbol
5. Check for orphaned symbol files

## Known Issues

### Issue #1: Subscript Ambiguity

**Problem**: `E_0` and `E_i` both match base symbol `E`

**Workaround**: Define specific subscript variants explicitly

**Future**: Implement symbol variant matching

### Issue #2: Greek Letter Rendering

**Problem**: `\\omega` vs `ω` (LaTeX vs Unicode)

**Workaround**: Normalize to LaTeX representation

**Future**: Support both formats

### Issue #3: Context-Dependent Symbols

**Problem**: Same symbol has different meanings in different chapters

**Workaround**: Use most common definition

**Future**: Chapter-specific symbol definitions

## References

- **Step 01 Formula Extraction**: Similar pattern, formula extraction
- **Step 05 Literature Linking**: Similar pattern, citation linking
- **LaTeX Symbol Guide**: https://www.overleaf.com/learn/latex/List_of_Greek_letters_and_math_symbols
- **MD5 Hash Algorithm**: https://en.wikipedia.org/wiki/MD5
