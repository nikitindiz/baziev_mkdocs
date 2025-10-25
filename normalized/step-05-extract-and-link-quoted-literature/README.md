# Step 05: Extract and Link Quoted Literature

This step extracts literature references from the bibliography and replaces citation markers in the text with structured references.

## Purpose

- Parse numbered bibliography entries from the literature chapter
- Create a structured database of literature references
- Find and replace citation markers `[N]` with `{{literature:ID}}` references
- Enable database integration and automated citation rendering

## Input

- `step-04-parse-missed-db-keys-and-src/result/` - Markdown files from previous step
- `docs/chapter_список-цитированной-литературы/index.md` - Bibliography source

## Output

1. **Literature database**: `normalized/literature/literature_{ID}.json` (48 files)
2. **Modified markdown**: `step-05-extract-and-link-quoted-literature/result/`
3. **Statistics**: `extraction_stats.json`

## Usage

### Run Step 05 Only

```bash
cd normalized/step-05-extract-and-link-quoted-literature
python3 parse-refs.py
```

### Run Complete Pipeline

```bash
cd normalized
python3 normalize.py
```

## Citation Patterns

### Simple Reference

```markdown
# Before
в одной статье М. Планка [1] от 1900 г.

# After
в одной статье М. Планка {{literature:abc123def456}} от 1900 г.
```

### Range Reference

```markdown
# Before
как показано в работах [3—5]

# After
как показано в работах {{literature:abc123}}, {{literature:def456}}, {{literature:ghi789}}
```

### Multiple References

```markdown
# Before
согласно источникам [10, 11, 23]

# After
согласно источникам {{literature:aaa111}}, {{literature:bbb222}}, {{literature:ccc333}}
```

## Literature JSON Structure

Each literature entry is stored as:

```json
{
  "id": "abc123def456",
  "number": 1,
  "text": "М. Планк. О необратимых процессах излучения. Ann. Phys., 1, 69—122, 1900.",
  "author": "М. Планк",
  "title": "О необратимых процессах излучения",
  "publication": "Ann. Phys., 1, 69—122, 1900.",
  "source": {
    "file": "docs/chapter_список-цитированной-литературы/index.md",
    "position": 123
  }
}
```

## Features

### Automatic Parsing

- Extracts 48 numbered bibliography entries
- Parses author, title, and publication info
- Generates unique MD5-based IDs

### Citation Detection

- Simple references: `[1]`
- Range references: `[2—5]` or `[2-5]`
- Multiple references: `[3, 4, 5]`

### Smart Replacement

- Handles overlapping citation patterns
- Preserves citation order
- Groups multiple references with commas

## Expected Statistics

```json
{
  "total_entries": 48,
  "files_processed": ~59,
  "files_with_citations": ~15,
  "total_citations": ~87,
  "citations_replaced": ~87
}
```

## Validation

### Check extraction

```bash
# Count literature JSON files (should be 48)
ls -1 ../../literature/literature_*.json | wc -l

# Verify no citation markers remain
grep -r '\[\d\]' result/
```

### Check references

```bash
# Find all literature references
grep -r '{{literature:' result/ | wc -l
```

## Integration

This step completes the normalization pipeline:

```
Step 01: Formulas    → {{formula:ID}}
Step 02: Tables      → {{table:ID}}
Step 03: Illustrations → {{illustration:ID}}
Step 04: Metadata    → Update formula JSONs
Step 05: Literature  → {{literature:ID}}
```

All content is now stored in structured JSON format with references in markdown.

## Documentation

- `AI-INSTRUCTIONS.md` - Detailed implementation specification
- `step-result-context.md` - Processing results and analysis (generated after run)
- `extraction_stats.json` - Processing statistics (generated after run)

## Next Steps

After completing all normalization steps, the content is ready for:

1. Database import (MongoDB, PostgreSQL, etc.)
2. Custom rendering pipeline
3. Interactive features (clickable citations, hover previews)
4. Search and cross-reference functionality
5. Export to other formats (LaTeX, DOCX, etc.)
