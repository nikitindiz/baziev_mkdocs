# Step 05: Extract and Link Quoted Literature - AI Instructions

## Overview

This step extracts literature references from the bibliography chapter and replaces citation markers in the text with structured references.

## Objectives

1. **Parse bibliography** - Extract numbered literature entries from the bibliography markdown file
2. **Create literature database** - Save each entry as a separate JSON file with metadata
3. **Find citations** - Locate citation patterns in text (e.g., `[1]`, `[2—5]`, `[3, 4]`)
4. **Replace citations** - Replace citation markers with `{{literature:ID}}` references

## Input

- **Source**: `step-04-parse-missed-db-keys-and-src/result/` - Markdown files from previous step
- **Bibliography**: `docs/chapter_список-цитированной-литературы/index.md` - Source literature list

## Output

1. **Literature JSON files** - `normalized/literature/literature_{ID}.json`
2. **Modified markdown files** - `step-05-extract-and-link-quoted-literature/result/`
3. **Statistics** - `extraction_stats.json`

## Citation Patterns

### Patterns to Match

1. **Simple reference**: `[1]`
   - Replace with: `{{literature:abc123def456}}`

2. **Range reference**: `[2—5]` or `[2-5]`
   - Replace with: `{{literature:def456}}, {{literature:ghi789}}, {{literature:jkl012}}, {{literature:mno345}}`

3. **Multiple references**: `[3, 4, 5]`
   - Replace with: `{{literature:abc123}}, {{literature:def456}}, {{literature:ghi789}}`

### Context Examples

**Example 1**: Simple citation
```markdown
Before: в одной статье М. Планка [1] от 1900 г.
After:  в одной статье М. Планка {{literature:abc123def456}} от 1900 г.
```

**Example 2**: Range citation
```markdown
Before: как показано в работах [3—5]
After:  как показано в работах {{literature:abc123}}, {{literature:def456}}, {{literature:ghi789}}
```

**Example 3**: Multiple citations
```markdown
Before: согласно источникам [10, 11, 23]
After:  согласно источникам {{literature:aaa111}}, {{literature:bbb222}}, {{literature:ccc333}}
```

## Literature JSON Structure

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

### Field Descriptions

- **id** - 12-character MD5-based unique identifier
- **number** - Original reference number (1-48)
- **text** - Complete citation text
- **author** - Extracted author name(s)
- **title** - Extracted title (if parseable)
- **publication** - Extracted publication info (if parseable)
- **source.file** - Source bibliography file
- **source.position** - Character position in source file

## Implementation Details

### ID Generation

```python
unique_str = f"{number}|{full_text}"
hash_id = hashlib.md5(unique_str.encode('utf-8')).hexdigest()[:12]
```

### Bibliography Parsing

Pattern to match numbered entries:
```regex
^(\d+)\.\s+(.+?)(?=^\d+\.|$)
```

Flags: `re.MULTILINE | re.DOTALL`

### Citation Detection

**Pattern 1**: Simple references
```regex
\[(\d+)\]
```

**Pattern 2**: Range references
```regex
\[(\d+)[—\-](\d+)\]
```

**Pattern 3**: Multiple references
```regex
\[(\d+(?:\s*,\s*\d+)+)\]
```

### Text Parsing Heuristics

Author-Title-Publication parsing:
1. Split by `.` (period)
2. First part = Author
3. Find publication markers: `М.,`, `M.,`, `Л.,`, `Ann.`, etc.
4. Before marker = Title
5. After marker = Publication info

## Processing Algorithm

```
1. Parse bibliography file
   - Extract numbered entries (1-48)
   - Generate unique IDs
   - Parse author, title, publication
   - Save as JSON files

2. For each markdown file:
   - Find all citation patterns
   - Group by position (handle ranges/multiples)
   - Replace with {{literature:ID}} references
   - Save to result directory

3. Generate statistics
   - Total entries extracted
   - Files processed
   - Files with citations
   - Total citations replaced
```

## Edge Cases

### Overlapping Citations

When multiple citation formats overlap at the same position:
```markdown
[1—3]  -> matches as range, generates 3 separate references
```

### Missing References

If citation `[99]` is found but entry #99 doesn't exist:
- Log warning
- Skip replacement
- Keep original text

### Special Characters

Handle various dash types in ranges:
- Em dash: `—` (U+2014)
- En dash: `–` (U+2013)
- Hyphen: `-` (U+002D)

### Escaped Brackets

Don't match citations in code blocks or escaped contexts:
```markdown
\[1\]  -> ignore
`[1]`  -> ignore
```

## Validation

### Pre-execution
- Verify bibliography file exists
- Check Step 04 result directory exists

### Post-execution
- Verify all literature JSON files created (48 expected)
- Check no original `[N]` patterns remain in result files
- Validate all `{{literature:ID}}` references have corresponding JSON files

## Statistics File

`extraction_stats.json`:
```json
{
  "total_entries": 48,
  "files_processed": 59,
  "files_with_citations": 15,
  "total_citations": 87,
  "citations_replaced": 87
}
```

## Integration with Pipeline

### Previous Steps

**Step 04**: Parse missed DB keys and src
- Output: Cleaned markdown files with all formula metadata complete

### This Step (05)

**Input**: Step 04 result
**Output**: 
- Literature JSON files in `normalized/literature/`
- Modified markdown in `step-05/result/`
- Citations replaced with `{{literature:ID}}`

### Next Steps

**Final rendering**:
- Load literature JSON files
- Replace `{{literature:ID}}` with formatted citations
- Generate bibliography section
- Create citation links

## Known Limitations

1. **Author parsing** - Heuristic-based, may not perfectly split author/title/publication
2. **Citation context** - Doesn't validate if citation makes sense in context
3. **Duplicate numbers** - Assumes bibliography has unique numbers 1-48
4. **Language-specific** - Optimized for Russian/English mixed text

## Success Criteria

- [ ] All 48 literature entries extracted
- [ ] JSON files created with valid structure
- [ ] All citation patterns replaced
- [ ] No broken references in output
- [ ] Statistics file generated
- [ ] All markdown files copied to result directory
