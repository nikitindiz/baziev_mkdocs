# Step 02: Table Extraction - AI Implementation Instructions

## Objective

Create a Python script that extracts all tables from the Baziev Physics book markdown files and stores them as individual JSON files, similar to the formula extraction in Step 01. Tables should be replaced with references in the modified content files.

## Input/Output Structure

### Input
- Source files from Step 01: `../step-01-extract-all-formulas/result/`
- Read formula references as plain text (don't expand them)

### Output
- `extract-tables.py` - Main extraction script
- `tables/` - Individual table JSON files
- `result/` - Modified chapter files with table references
- `extraction_stats.json` - Processing statistics
- `step-result-context.md` - Documentation (to be written after implementation)

## Table Types to Extract

Based on the project context, there are **two types** of tables:

### 1. Markdown Tables

Simple tables using Markdown pipe syntax:

```markdown
| Column 1 | Column 2 | Column 3 |
| -------- | -------- | -------- |
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |
```

**Characteristics**:
- Uses `|` delimiters
- Has header separator line with `---`
- May span multiple lines
- May contain formula references: `{{formula:abc123def456}}`
- Text content in Russian

### 2. HTML Tables

Complex tables using HTML `<table>` tags:

```html
<table>
<thead>
  <tr>
    <th>Header 1</th>
    <th>Header 2</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>Data 1</td>
    <td>Data 2</td>
  </tr>
  <tr>
    <td>Data 3</td>
    <td>Data 4</td>
  </tr>
</tbody>
</table>
```

**Characteristics**:
- Full HTML structure with `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>`
- May have attributes: `class`, `style`, `colspan`, `rowspan`
- May contain formula references
- May span many lines
- Russian text content

## Reference Format

### Table References in Modified Content

**Format**: `{{table:HASH_ID}}`

**Example**:
```markdown
Before:
| Газ | Масса | Плотность |
| --- | ----- | --------- |
| N₂  | 28.0  | 1.25      |

After:
{{table:abc123def456}}
```

### Hash ID Generation

Generate hash-based unique ID using MD5 of:
- Table content (raw markdown or HTML)
- Table type
- Position in file

```python
unique_str = f"{table_content}|{table_type}|{source_file}"
hash_id = hashlib.md5(unique_str.encode('utf-8')).hexdigest()[:12]
```

## JSON Structure for Tables

Each table stored as `tables/table_{hash_id}.json`:

```json
{
  "id": "abc123def456",
  "type": "markdown|html",
  "content": {
    "raw": "| Col1 | Col2 |\n|------|------|\n| A | B |",
    "headers": ["Col1", "Col2"],
    "rows": [
      ["A", "B"]
    ]
  },
  "metadata": {
    "row_count": 1,
    "column_count": 2,
    "has_formulas": true,
    "formula_refs": ["{{formula:xyz789}}"]
  },
  "source": {
    "file": "chapter_глава-i.../section.md",
    "position": 12345
  },
  "html_attributes": {
    "class": "data-table",
    "style": "width: 100%"
  }
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique hash ID (12 chars) |
| `type` | string | `"markdown"` or `"html"` |
| `content.raw` | string | Original table content (markdown or HTML) |
| `content.headers` | array | Extracted header cells |
| `content.rows` | array | Array of row arrays (parsed data) |
| `metadata.row_count` | number | Number of data rows (excluding header) |
| `metadata.column_count` | number | Number of columns |
| `metadata.has_formulas` | boolean | Contains formula references |
| `metadata.formula_refs` | array | List of all formula references in table |
| `source.file` | string | Source markdown file path |
| `source.position` | number | Character position in file |
| `html_attributes` | object\|null | HTML attributes (for HTML tables only) |

## Implementation Requirements

### Script Structure

```python
#!/usr/bin/env python3
"""
Table Extraction Script for Baziev Physics Book
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Table:
    id: str
    type: str  # 'markdown' or 'html'
    content: Dict
    metadata: Dict
    source: Dict
    html_attributes: Optional[Dict] = None


class TableExtractor:
    def __init__(self, input_dir: str, output_dir: str):
        # Initialize paths and stats
        pass
    
    def generate_table_id(self, content: str, table_type: str, source: str) -> str:
        # Generate hash-based ID
        pass
    
    def extract_markdown_tables(self, content: str, file_path: str) -> Tuple[str, List[Table]]:
        # Extract markdown tables
        # Pattern: | ... | ... |
        # Must handle multi-line tables
        pass
    
    def extract_html_tables(self, content: str, file_path: str) -> Tuple[str, List[Table]]:
        # Extract HTML <table>...</table>
        # Must handle nested tags and attributes
        pass
    
    def parse_markdown_table(self, table_str: str) -> Dict:
        # Parse markdown table into headers and rows
        pass
    
    def parse_html_table(self, table_str: str) -> Dict:
        # Parse HTML table into headers and rows
        # Extract attributes
        pass
    
    def find_formula_refs(self, text: str) -> List[str]:
        # Find all {{formula:*}} references
        pass
    
    def save_table(self, table: Table):
        # Save to JSON file
        pass
    
    def process_file(self, file_path: Path):
        # Process single file
        pass
    
    def process_all(self):
        # Process all files
        pass


def main():
    # Entry point
    pass
```

### Processing Order

1. **Extract HTML tables first** (more specific)
2. **Extract Markdown tables second**

This avoids conflicts where HTML tables might contain markdown-like content.

### Extraction Logic

#### For Markdown Tables

1. Find table pattern:
   ```python
   # Pattern to match markdown tables
   pattern = r'(\|.+\|[\r\n]+\|[-:\s|]+\|[\r\n]+(?:\|.+\|[\r\n]*)+)'
   ```

2. Parse structure:
   - Split by newlines
   - First line: headers
   - Second line: separator (validate `---`)
   - Remaining lines: data rows
   - Handle alignment indicators (`:---`, `:---:`, `---:`)

3. Extract data:
   - Split each row by `|`
   - Strip whitespace
   - Preserve formula references
   - Count rows and columns

#### For HTML Tables

1. Find table pattern:
   ```python
   pattern = r'<table[^>]*>.*?</table>'
   ```

2. Parse structure:
   - Extract `<table>` attributes
   - Find `<thead>` and `<tbody>` sections
   - Parse `<tr>` rows
   - Extract `<th>` headers and `<td>` data
   - Handle `colspan`, `rowspan` if present

3. Extract data:
   - Build header array from `<th>` elements
   - Build row arrays from `<td>` elements
   - Preserve inner HTML (formula refs, formatting)
   - Store attributes separately

### Formula Reference Handling

Tables may contain formula references from Step 01:
- **DO NOT** expand or modify formula references
- **DO** track them in `metadata.formula_refs`
- **DO** preserve them exactly as: `{{formula:abc123def456}}`

Example:
```markdown
| Variable | Formula |
| -------- | ------- |
| Energy   | {{formula:xyz789abc123}} |
```

Should extract as:
```json
{
  "content": {
    "headers": ["Variable", "Formula"],
    "rows": [["Energy", "{{formula:xyz789abc123}}"]]
  },
  "metadata": {
    "has_formulas": true,
    "formula_refs": ["{{formula:xyz789abc123}}"]
  }
}
```

### Edge Cases to Handle

1. **Empty cells**: Preserve as empty strings
2. **Multiline cells**: Preserve newlines in HTML tables
3. **Special characters**: Handle Russian Cyrillic, Greek letters, Unicode
4. **Nested tables**: Skip or handle as single unit (rare)
5. **Malformed tables**: Log warning and skip
6. **Tables in code blocks**: Skip (check for ``` markers)

## Statistics to Track

```json
{
  "total_tables": 123,
  "markdown_tables": 67,
  "html_tables": 56,
  "files_processed": 59,
  "tables_with_formulas": 45,
  "average_rows_per_table": 8.5,
  "average_columns_per_table": 4.2
}
```

## Testing Strategy

### Test Cases

1. **Simple markdown table** (3x3)
2. **Complex HTML table** with `colspan`/`rowspan`
3. **Table with formula references**
4. **Table with Russian text**
5. **Multi-line HTML table** with formatting
6. **Edge case**: Single-row table
7. **Edge case**: Table with empty cells

### Validation

After extraction:
1. Count JSON files matches `total_tables`
2. All references `{{table:*}}` have corresponding JSON files
3. All JSON files are valid
4. No tables were missed (manual spot check)
5. Formula references preserved exactly

## Expected Output Structure

```
step-02-extract-all-tables/
├── extract-tables.py
├── extraction_stats.json
├── tables/
│   ├── table_abc123def456.json
│   ├── table_def456ghi789.json
│   └── ... (one per table)
└── result/
    ├── index.md
    └── chapter_*/
        └── *.md (with {{table:*}} references)
```

## Implementation Notes

### Dependencies

- Standard library only: `re`, `json`, `hashlib`, `pathlib`
- No external packages needed

### Encoding

- Use UTF-8 for all file operations
- Handle Russian Cyrillic properly

### Performance

- Process files sequentially (no parallel processing needed)
- Use `reversed()` when replacing to preserve positions
- Expected runtime: < 1 minute for full book

## After Implementation

Once the script is complete and tested:

1. Run extraction: `python3 extract-tables.py`
2. Verify statistics
3. Spot-check several tables
4. Create `step-result-context.md` (similar to step-01)
5. Document any issues or limitations found

## Example Workflow

```bash
cd normalized/step-02-extract-all-tables
python3 extract-tables.py

# Output should show:
# ================================================================================
# Table Extraction Script
# ================================================================================
# 
# Found 59 markdown files to process
# 
# Processing: chapter_глава-i.../1-section.md
#   → Extracted 3 tables
# ...
# 
# ================================================================================
# Extraction Complete!
# ================================================================================
# Files processed:          59
# Total tables extracted:   123
#   - Markdown tables:      67
#   - HTML tables:          56
# Tables with formulas:     45
# 
# Tables saved to:          .../tables
# Modified chapters in:     .../result
# ================================================================================
```

## Reference Implementation

Refer to `../step-01-extract-all-formulas/extract-formulas.py` for:
- Overall script structure
- Hash ID generation approach
- File processing logic
- Statistics tracking
- Output formatting

Adapt the patterns for table extraction while maintaining consistency with Step 01's approach.

---

**Priority**: High  
**Complexity**: Medium  
**Estimated Time**: 2-4 hours  
**Next Step After This**: Step 03 - SVG Extraction
