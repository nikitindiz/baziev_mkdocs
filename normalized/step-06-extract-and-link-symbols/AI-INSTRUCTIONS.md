# AI Instructions: Step 06 - Extract Symbols and Link to Formulas

## Objective

Extract symbol definitions from the "Условные обозначения" (Notation) chapter and link them to formulas that use these symbols.

## Input

1. **Symbols source**: `docs/chapter_условные-обозначения/index.md`
   - Contains ~300 symbol definitions
   - Format: `$latex$ — description`
   - Some wrapped in `<span>` with metadata

2. **Formulas**: `normalized/formulas/*.json`
   - All previously extracted formulas
   - Need to be updated with symbol references

## Output

1. **Symbol JSON files**: `normalized/symbols/symbol_{ID}.json`
   - One file per symbol
   - Structure defined below

2. **Updated formula files**: `normalized/formulas/*.json`
   - Add `"symbols": [...]` field with symbol IDs

3. **Statistics**: `step-06-extract-and-link-symbols/extraction_stats.json`

## Symbol JSON Structure

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

### Fields

- **id**: 12-character MD5 hash of `latex|description`
- **latex**: LaTeX representation without `$` delimiters
- **description**: Russian description of the symbol
- **metadata.db_key**: Original tracking ID (if present)
- **metadata.src**: Original image path (if present)

## Updated Formula Structure

Formulas get a new `"symbols"` field:

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

## Symbol Extraction Pattern

### Pattern 1: Wrapped symbols

```html
<span data-db-key="9162" data-src="images/formula_inline_625_0_2.webp"> $m_э$ </span> — масса электрино
```

**Extract**:
- `latex`: `"m_э"`
- `description`: `"масса электрино"`
- `db_key`: `"9162"`
- `src`: `"images/formula_inline_625_0_2.webp"`

### Pattern 2: Plain symbols

```
$h_{\odot}$ — момент импульса осциллятора солнечной плазмы
```

**Extract**:
- `latex`: `"h_{\\odot}"`
- `description`: `"момент импульса осциллятора солнечной плазмы"`
- `db_key`: `null`
- `src`: `null`

## Symbol Matching Logic

### Step 1: Extract symbols from formula LaTeX

Given formula: `E_0 = m_э v^2`

Extract base symbols:
- `E_0` → `E` with subscript `0`
- `m_э` → `m` with subscript `э`
- `v` → `v`

### Step 2: Match against symbol definitions

Look up each symbol in the symbol definitions table:

1. Try exact match: `E_0` → found: `symbol_abc123def456`
2. Try exact match: `m_э` → found: `symbol_def456abc789`
3. Try exact match: `v` → found: `symbol_ghi789abc012`

### Step 3: Handle variations

- **Subscripts/Superscripts**: Match base letter if exact match fails
  - `E_0`, `E_i`, `E_k` → all match base symbol `E`
  - But prefer exact match if available
  
- **Greek letters**: Normalize LaTeX commands
  - `\\alpha` matches `α` symbol definition
  - `\\odot` matches `⊙` symbol definition

- **Text in formulas**: Ignore `\\text{...}`, `\\mathrm{...}` content
  - These are labels, not symbols

## Implementation Details

### Regex Patterns

**Wrapped symbol**:
```python
pattern = r'<span\s+data-db-key="([^"]+)"\s+data-src="([^"]+)">\s*\$([^$]+)\$\s*</span>\s*—\s*(.+?)(?=\n\n|\n<|$)'
```

**Plain symbol**:
```python
pattern = r'(?<!<span[^>]*>)\$([^$]+)\$\s*—\s*(.+?)(?=\n\n|\n\$|$)'
```

### Symbol Extraction from LaTeX

1. Remove LaTeX commands: `\\text{...}`, `\\mathrm{...}`, etc.
2. Extract Greek letters: `\\alpha`, `\\beta`, `\\gamma`, ...
3. Extract Latin letters with subscripts: `m_э`, `E_0`, ...
4. Extract special symbols: `\\hbar`, `\\odot`, ...

### Symbol ID Generation

```python
def generate_symbol_id(latex: str, description: str) -> str:
    unique_str = f"{latex}|{description}"
    hash_obj = hashlib.md5(unique_str.encode('utf-8'))
    return hash_obj.hexdigest()[:12]
```

## Expected Statistics

- **Total symbols**: ~300
- **Symbols with metadata**: ~290 (most have `data-db-key`)
- **Formulas processed**: ~4000-5000
- **Formulas with symbols**: ~3000-4000 (60-80%)
- **Average symbols per formula**: 3-5

## Edge Cases

### Multiple subscripts

```latex
m_{si}  → symbol with subscript "si"
```

### Superscripts and subscripts

```latex
E_0^2   → base symbol E with both subscript 0 and superscript 2
```

### Special characters in descriptions

```markdown
$V = \text{const}$ — (plain text, not a symbol)
```

### Duplicate symbols

Some symbols may appear multiple times with different contexts:
- Keep all occurrences
- Generate unique IDs based on latex + description
- If exact duplicates, same ID

## Validation

After processing, verify:

1. **Symbol count**: Should extract ~300 symbols
2. **Symbol files**: All valid JSON, no duplicates
3. **Formula updates**: All formulas have `symbols` field (even if empty `[]`)
4. **Reference integrity**: All symbol IDs in formulas exist in `symbols/`

## Running the Script

```bash
cd normalized/step-06-extract-and-link-symbols
python3 extract-symbols.py
```

## Output Example

### Symbol File: `symbols/symbol_a1b2c3d4e5f6.json`

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

### Updated Formula: `formulas/formula_c6fed30764ee.json`

```json
{
  "id": "c6fed30764ee",
  "type": "display",
  "latex": "E_0 = \\frac{1}{2} E_x + \\frac{1}{2} E_y + \\frac{1}{2} E_z = \\frac{3}{2} k T_0",
  "symbols": ["abc123", "def456", "ghi789"],
  "metadata": {
    "db_key": "30",
    "src": "images/formula_full_2_9.webp",
    "equation_number": null
  },
  "source": {
    "file": "chapter_глава-i.../1-гиперчастотная-механика-или-механика-микромира.md",
    "position": 6389
  },
  "wrapper_html": null
}
```

## Notes

- Symbols are mathematical notation definitions, not text labels
- Focus on variables, constants, and operators that have specific meanings
- Ignore pure numbers and standard mathematical operators (+, -, =, etc.)
- Greek letters are important symbols in physics
- Subscripts and superscripts are part of the symbol identity
