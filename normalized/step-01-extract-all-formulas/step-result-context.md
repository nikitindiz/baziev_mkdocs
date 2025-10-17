# Step 01: Formula Extraction - Result Context

## Overview

This directory contains the results of **Step 01: Formula Extraction**, which processes the Baziev Physics book markdown files to separate LaTeX formulas from content text. All mathematical formulas are extracted into individual JSON files, and the original content is modified to reference these formulas using a standardized format.

**Processing Date**: October 2025  
**Purpose**: Normalize formula storage for database integration and content management

## Directory Structure

```
step-01-extract-all-formulas/
├── extract-formulas.py           # Extraction script
├── step-result-context.md         # This file
├── extraction_stats.json          # Processing statistics
├── formulas/                      # Individual formula JSON files
│   ├── formula_abc123def456.json
│   ├── formula_def456abc789.json
│   └── ... (one file per formula)
└── result/                        # Modified chapter files
    ├── index.md
    └── chapter_*/
        └── *.md
```

## Formula Storage Format

### Individual Formula Files

Each formula is stored as a separate JSON file in the `formulas/` directory.

**File naming**: `formula_{hash_id}.json`

**JSON Structure**:
```json
{
  "id": "abc123def456",
  "type": "inline|display",
  "latex": "E = mc^2",
  "metadata": {
    "db_key": "123",
    "src": "images/formula_inline_1_2_3.webp",
    "equation_number": "(1.15)"
  },
  "source": {
    "file": "chapter_глава-i.../1-гиперчастотная-механика.md",
    "position": 12345
  },
  "wrapper_html": "<original HTML wrapper if present>"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique hash-based identifier (12 chars, MD5-based) |
| `type` | string | Formula type: `"inline"` or `"display"` |
| `latex` | string | Pure LaTeX content (without `$` or `$$` delimiters) |
| `metadata.db_key` | string\|null | Original `data-db-key` attribute from source |
| `metadata.src` | string\|null | Original `data-src` attribute (image path) |
| `metadata.equation_number` | string\|null | Equation number like `"(1.15)"` for display formulas |
| `source.file` | string | Relative path to source markdown file |
| `source.position` | number | Character position in source file |
| `wrapper_html` | string\|null | Original HTML wrapper (for complex structures) |

## Formula Reference Format

In the modified markdown files (`result/` directory), formulas are replaced with references:

### Inline Formula References

**Format**: `{{formula:HASH_ID}}`

**Example**:
```markdown
Before: The energy equation $E = mc^2$ is fundamental.
After:  The energy equation {{formula:abc123def456}} is fundamental.
```

### Display Formula References

**Format**: `{{formula:HASH_ID:(EQ_NUM)}}` or `{{formula:HASH_ID}}` (if no equation number)

**Example with equation number**:
```markdown
Before:
<div style="display: flex; width: 100%;">
<div style="width: 100%;">
$$E_0 = h f_0$$
</div>
<div style="width: 80px;">
(1.15)
</div>
</div>

After:
{{formula:def456abc789:(1.15)}}
```

**Example without equation number**:
```markdown
Before:
$$F = ma$$

After:
{{formula:xyz789abc123}}
```

## Formula Types Extracted

### 1. Display Formulas in Div Wrappers

**Original Format**:
```html
<div style="display: flex; width: 100%;" data-db-key="50" data-src="images/formula_full_4_2_0.webp">
<div style="width: 100%;">

$$E_0 = P_0 \cdot V_{g0}$$

</div>
<div style="width: 80px;">
(1.2)
</div>
</div>
```

**Extracted Data**:
- LaTeX: `E_0 = P_0 \cdot V_{g0}`
- Type: `display`
- Metadata: `db_key="50"`, `src="images/formula_full_4_2_0.webp"`, `equation_number="(1.2)"`
- Wrapper HTML preserved for reconstruction

### 2. Inline Formulas in Span Wrappers

**Original Format**:
```html
<span data-db-key="8" data-src="images/formula_inline_1_1_24.webp">$E = mv^2/2$</span>
```

**Extracted Data**:
- LaTeX: `E = mv^2/2`
- Type: `inline`
- Metadata: `db_key="8"`, `src="images/formula_inline_1_1_24.webp"`
- Wrapper HTML preserved

### 3. Standalone Display Formulas

**Original Format**:
```markdown
$$\frac{E_0}{h} = \frac{v_0}{2A_0}$$
```

**Extracted Data**:
- LaTeX: `\frac{E_0}{h} = \frac{v_0}{2A_0}`
- Type: `display`
- Metadata: All null (no wrapper)

### 4. Standalone Inline Formulas

**Original Format**:
```markdown
The variable $x$ represents position.
```

**Extracted Data**:
- LaTeX: `x`
- Type: `inline`
- Metadata: All null (no wrapper)

## Hash ID Generation

Formula IDs are generated using MD5 hash of:
```
latex_content|db_key|src|equation_number
```

**Properties**:
- **Deterministic**: Same formula with same metadata always produces same ID
- **Unique**: Different formulas produce different IDs
- **Collision-resistant**: MD5 provides sufficient uniqueness for this dataset
- **Length**: 12 characters (first 12 chars of MD5 hex digest)

**Example**:
```python
unique_str = "E = mc^2|123|images/formula_inline_1_2_3.webp|None"
hash_id = hashlib.md5(unique_str.encode('utf-8')).hexdigest()[:12]
# Result: "abc123def456"
```

## Processing Statistics

The `extraction_stats.json` file contains:

```json
{
  "total_formulas": 1234,
  "inline_formulas": 567,
  "display_formulas": 667,
  "files_processed": 59,
  "formulas_with_metadata": 890
}
```

| Metric | Description |
|--------|-------------|
| `total_formulas` | Total number of formulas extracted |
| `inline_formulas` | Count of inline formulas (`$...$`) |
| `display_formulas` | Count of display formulas (`$$...$$`) |
| `files_processed` | Number of markdown files processed |
| `formulas_with_metadata` | Formulas with `data-db-key` or `data-src` attributes |

## Modified Chapter Files

### Structure Preservation

The modified files in `result/` directory:
- **Maintain directory structure**: Same hierarchy as `docs/`
- **Preserve all non-formula content**: Text, headings, tables, SVG, etc.
- **Replace only formulas**: Only LaTeX expressions are replaced with references
- **Keep formatting**: Markdown structure and HTML elements unchanged

### Example Transformation

**Original** (`docs/chapter_глава-i.../1-гиперчастотная-механика.md`):
```markdown
## § 1. Гиперчастотная механика

Уравнение состояния идеального газа:

<div style="display: flex; width: 100%;" data-db-key="1" data-src="images/formula_full_0_7.webp">
<div style="width: 100%;">

$$PV = nRT = \frac{m}{\mu} \cdot RT$$

</div>
<div style="width: 80px;">
(1.1)
</div>
</div>

где <span data-db-key="10" data-src="images/formula_inline_1_2_11.webp">$m$</span> — масса молекулы.
```

**Modified** (`result/chapter_глава-i.../1-гиперчастотная-механика.md`):
```markdown
## § 1. Гиперчастотная механика

Уравнение состояния идеального газа:

{{formula:a1b2c3d4e5f6:(1.1)}}

где {{formula:x7y8z9a0b1c2}} — масса молекулы.
```

## What Was NOT Extracted

The following elements are intentionally **not extracted** in this step:

1. **SVG Illustrations**: Vector graphics remain in place (processed in later steps)
2. **Table Content**: Tables preserved as-is, including formulas within cells
3. **Code Blocks**: Any LaTeX in code/pre blocks untouched
4. **Escaped Characters**: `\$` sequences left unchanged
5. **Links and References**: Markdown links and citations preserved

## Usage Notes

### Reconstructing Original Content

To reconstruct original formulas:

1. Parse formula reference: `{{formula:abc123def456:(1.15)}}`
2. Extract hash ID: `abc123def456`
3. Load JSON: `formulas/formula_abc123def456.json`
4. Retrieve LaTeX: `"E_0 = h f_0"`
5. Apply format:
   - Inline: `$E_0 = h f_0$`
   - Display: `$$E_0 = h f_0$$`
6. Optionally restore wrapper HTML from `wrapper_html` field

### Database Integration

The JSON structure is designed for direct database import:

**Recommended schema**:
```sql
CREATE TABLE formulas (
  id VARCHAR(12) PRIMARY KEY,
  type ENUM('inline', 'display'),
  latex TEXT NOT NULL,
  db_key VARCHAR(50),
  src VARCHAR(255),
  equation_number VARCHAR(20),
  source_file VARCHAR(255),
  source_position INT,
  wrapper_html TEXT
);
```

### Querying Formulas

**Find all formulas with metadata**:
```bash
jq 'select(.metadata.db_key != null)' formulas/*.json
```

**Find formulas by type**:
```bash
jq 'select(.type == "display")' formulas/*.json
```

**Search LaTeX content**:
```bash
jq 'select(.latex | contains("mc^2"))' formulas/*.json
```

## Next Steps

This extraction is **Step 01** in the normalization pipeline. Subsequent steps will:

- **Step 02**: Extract and normalize SVG illustrations
- **Step 03**: Extract and normalize tables
- **Step 04**: Process text content and metadata
- **Step 05**: Database integration and validation

## Validation

To verify extraction integrity:

1. **Count formulas**: Match `total_formulas` with file count in `formulas/`
2. **Check references**: Ensure all `{{formula:*}}` references have corresponding JSON files
3. **Validate JSON**: All files should parse as valid JSON
4. **Compare metadata**: Original `data-db-key` values should match extracted metadata

### Validation Script (example)

```python
import json
from pathlib import Path

formulas_dir = Path("formulas")
json_files = list(formulas_dir.glob("formula_*.json"))

print(f"Total formula files: {len(json_files)}")

# Validate each file
for f in json_files:
    with open(f) as file:
        data = json.load(file)
        assert 'id' in data
        assert 'type' in data in ['inline', 'display']
        assert 'latex' in data
        
print("✓ All formula files validated")
```

## Known Limitations

1. **Nested formulas**: Formulas within formulas are not handled (rare case)
2. **Malformed LaTeX**: Invalid LaTeX is extracted as-is without validation
3. **Unicode math**: Unicode mathematical characters are not converted to LaTeX
4. **Table formulas**: Formulas inside table cells are not tracked separately
5. **Caption formulas**: Formulas in SVG captions remain in place (for Step 02)

## Technical Notes

### Extraction Order

Formulas are extracted in specific order to avoid conflicts:

1. **Div-wrapped display formulas** (most specific)
2. **Span-wrapped inline formulas**
3. **Standalone display formulas**
4. **Standalone inline formulas** (least specific)

This ordering ensures wrapped formulas are processed before attempting to match their inner content.

### Position Tracking

The `source.position` field tracks character offset in the **original** file, not the modified file. This allows correlation with source material.

### Encoding

All files use **UTF-8 encoding** to properly handle:
- Russian Cyrillic text
- Greek letters in formulas
- Mathematical symbols
- Special characters

---

**Script**: `extract-formulas.py`  
**Input**: `../../docs/chapter_*/`  
**Output**: `formulas/` + `result/`  
**Last Updated**: October 2025
