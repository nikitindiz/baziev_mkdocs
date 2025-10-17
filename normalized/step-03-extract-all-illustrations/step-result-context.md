# Step 03: Extract All Illustrations - Result Context

## Overview

This document describes the results and context of the illustration extraction process (Step 03) for the Baziev MkDocs project. The process extracts SVG illustrations from processed markdown files and replaces them with unique references.

**Processing Date**: October 2025  
**Purpose**: Normalize SVG illustration storage for database integration and content management

## Extraction Statistics

### Summary
- **Total Illustrations Extracted**: TBD (estimated 100-300)
- **SVG Illustrations**: TBD (100%)
- **Files Processed**: 59
- **Illustrations with Metadata**: TBD (estimated ~85%)
- **Illustrations with Captions**: TBD (estimated ~90%)
- **Captions with Formula References**: TBD (estimated ~25%)

### Illustration Characteristics
- **Average SVG Elements per Illustration**: TBD
- **Most Common Element Types**: `path`, `text`, `line`, `g`
- **Illustrations with UUID IDs**: TBD

## Implementation Details

### Input Source
- **Directory**: `step-02-extract-all-tables/result/`
- **Format**: Markdown files with formulas and tables already extracted and referenced

### Output Structure

#### 1. Extracted Illustrations (`illustrations/` directory)
Each illustration is saved as a JSON file with a 12-character MD5-based unique identifier:
```
illustrations/
├── a1b2c3d4e5f6.json
├── b2c3d4e5f6g7.json
└── ...
```

#### 2. Modified Markdown Files (`result/` directory)
Original markdown files with illustrations replaced by references:
```markdown
Some text before the illustration.

{{illustration:a1b2c3d4e5f6}}

Some text after the illustration.
```

### JSON Structure

Each illustration JSON file contains:

```json
{
  "id": "a1b2c3d4e5f6",
  "type": "svg",
  "svg_content": "<svg id=\"uuid-...\" xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 1034 359.4\">...</svg>",
  "caption": "Рис. 4. Траектория фотона при рассеянии {{formula:abc123def456}}",
  "metadata": {
    "db_key": "2308",
    "src": "images/formula_full_151_1.webp",
    "svg_id": "uuid-12345678-abcd-1234-abcd-123456789abc",
    "svg_viewbox": "0 0 1034 359.4",
    "element_counts": {
      "path": 45,
      "text": 12,
      "line": 8,
      "circle": 3,
      "rect": 0,
      "g": 5,
      "polygon": 0,
      "polyline": 2
    },
    "has_caption": true,
    "caption_has_formulas": true,
    "caption_formula_refs": ["{{formula:abc123def456}}"]
  },
  "source": {
    "file": "chapter_глава-vii-физика-солнца/section.md",
    "position": 12345
  },
  "wrapper_html": "<div style=\"display: flex; width: 100%; flex-direction: column; margin-bottom: 1em;\">...</div>"
}
```

### Key Fields

- **id**: 12-character unique identifier (MD5 hash)
- **type**: Illustration type (currently always `"svg"`)
- **svg_content**: Complete SVG markup including `<svg>` tags
- **caption**: Figure caption text (may contain formula/table references)
- **metadata.db_key**: Original tracking database key
- **metadata.src**: Path to original scanned image
- **metadata.svg_id**: SVG element's id attribute (typically UUID)
- **metadata.svg_viewbox**: SVG viewBox attribute value
- **metadata.element_counts**: Count of different SVG element types
- **metadata.has_caption**: Boolean indicating presence of caption
- **metadata.caption_has_formulas**: Boolean indicating formulas in caption
- **metadata.caption_formula_refs**: Array of formula reference strings
- **source.file**: Relative path to source markdown file
- **source.position**: Character position in source file
- **wrapper_html**: Original complete HTML wrapper for reconstruction

## Technical Implementation

### Regex Pattern

```regex
<div\s+style="[^"]*display:\s*flex[^"]*"[^>]*>\s*<div[^>]*>\s*<div([^>]*)>\s*(<svg[^>]*>.*?</svg>)\s*</div>\s*</div>\s*(?:<div\s+style="[^"]*font-style:\s*italic[^"]*"[^>]*>(.*?)</div>\s*)?</div>
```

**Pattern Breakdown**:
- `<div\s+style="[^"]*display:\s*flex[^"]*"[^>]*>` - Outer flex container
- `\s*<div[^>]*>` - Middle wrapper div
- `\s*<div([^>]*)>` - Inner div with metadata (capture group 1)
- `\s*(<svg[^>]*>.*?</svg>)` - SVG content (capture group 2)
- `\s*</div>\s*</div>` - Close inner and middle divs
- `\s*(?:<div\s+style="[^"]*font-style:\s*italic[^"]*"[^>]*>(.*?)</div>\s*)?` - Optional caption (capture group 3)
- `</div>` - Close outer div

**Flags**: `re.DOTALL | re.IGNORECASE`

**Key Design Decisions**:
- Uses non-greedy match (`.*?`) for SVG content to avoid over-matching
- Optional caption group handles illustrations without captions
- Captures inner div attributes separately to extract metadata
- Handles whitespace variations between divs

### SVG Illustration Structure

#### Typical SVG Wrapper

```html
<div style="display: flex; width: 100%; flex-direction: column; margin-bottom: 1em;">
<div style="width: 100%;">
<div data-db-key="2308" data-src="images/formula_full_151_1.webp">

<svg id="uuid-12345678-abcd-1234-abcd-123456789abc" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1034 359.4">
  <defs>
    <style>.cls-1{fill:none;stroke:#000;stroke-miterlimit:10;}</style>
  </defs>
  <path class="cls-1" d="M100,200 L400,200"/>
  <text transform="translate(250 150)">E</text>
  <g id="layer-1">
    <line x1="0" y1="0" x2="100" y2="100"/>
  </g>
</svg>

</div>
</div>
<div style="font-style: italic; padding: 10px">
Рис. 4. Траектория фотона при рассеянии {{formula:abc123def456}}
</div>
</div>
```

#### SVG Element Types

Common SVG elements found in illustrations:

| Element | Purpose | Frequency |
|---------|---------|-----------|
| `<path>` | Vector paths for lines, curves, shapes | Very High |
| `<text>` | Text labels and annotations | High |
| `<g>` | Groups of elements | High |
| `<line>` | Straight lines | Medium |
| `<circle>` | Circles and dots | Medium |
| `<rect>` | Rectangles | Low |
| `<polygon>` | Polygons | Low |
| `<polyline>` | Multi-segment lines | Low |
| `<defs>` | Reusable definitions (styles, gradients) | Medium |

### Metadata Extraction

#### From Inner Div Attributes

```python
metadata = {}

# Extract data-db-key
db_key_match = re.search(r'data-db-key="([^"]+)"', inner_div_attrs)
if db_key_match:
    metadata['db_key'] = db_key_match.group(1)

# Extract data-src
src_match = re.search(r'data-src="([^"]+)"', inner_div_attrs)
if src_match:
    metadata['src'] = src_match.group(1)
```

#### From SVG Element

```python
# Extract SVG id attribute
svg_id_match = re.search(r'<svg[^>]*\s+id="([^"]+)"', svg_content)
svg_id = svg_id_match.group(1) if svg_id_match else None

# Extract viewBox attribute
viewbox_match = re.search(r'viewBox="([^"]+)"', svg_content)
svg_viewbox = viewbox_match.group(1) if viewbox_match else None

# Count element types
element_counts = {
    'path': len(re.findall(r'<path', svg_content)),
    'text': len(re.findall(r'<text', svg_content)),
    'line': len(re.findall(r'<line', svg_content)),
    'circle': len(re.findall(r'<circle', svg_content)),
    'rect': len(re.findall(r'<rect', svg_content)),
    'g': len(re.findall(r'<g', svg_content)),
    'polygon': len(re.findall(r'<polygon', svg_content)),
    'polyline': len(re.findall(r'<polyline', svg_content))
}
```

### Caption Processing

#### Extract and Clean Caption

```python
if caption:
    # Clean up whitespace
    caption = caption.strip()
    caption = re.sub(r'\s+', ' ', caption)
```

#### Find Formula References

```python
# Pattern matches {{formula:ID}} or {{formula:ID:(X.Y)}}
formula_refs = re.findall(r'\{\{formula:[a-f0-9]+(?::\([^)]+\))?\}\}', caption)
has_formulas = len(formula_refs) > 0
```

**Caption formats**:
- `Рис. 4. Траектория фотона` - Simple caption
- `Рис. 4. График зависимости {{formula:abc123}}` - Caption with formula
- `Puc. 15. Диаграмма для {{formula:def456}} и {{table:ghi789}}` - Caption with formula and table

### Hash ID Generation

#### Algorithm

```python
def generate_illustration_id(svg_content, metadata, source, position):
    # Extract viewBox for uniqueness
    viewbox_match = re.search(r'viewBox="([^"]+)"', svg_content)
    viewbox = viewbox_match.group(1) if viewbox_match else ""
    
    # Use first 500 characters of SVG as preview
    svg_preview = svg_content[:500]
    
    # Combine unique identifiers
    unique_str = f"{viewbox}|{svg_preview}|{metadata['db_key']}|{metadata['src']}|{source}|{position}"
    
    # Generate MD5 hash
    hash_obj = hashlib.md5(unique_str.encode('utf-8'))
    
    # Return first 12 characters
    return hash_obj.hexdigest()[:12]
```

#### Uniqueness Factors

1. **SVG viewBox** - Viewport dimensions (e.g., "0 0 1034 359.4")
2. **SVG content preview** - First 500 characters of SVG markup
3. **Database key** - Original tracking ID from `data-db-key`
4. **Source path** - Image reference from `data-src`
5. **File path** - Source markdown file
6. **Position** - Character offset in file

This ensures:
- Different illustrations get different IDs
- Same illustration in different locations gets different IDs
- Deterministic IDs for the same illustration
- Collision probability ~1 in 10^14 (sufficient for this dataset)

## Distribution by Chapter

Illustrations are expected to be distributed across:
- **Глава I**: Mechanics diagrams (oscillators, trajectories)
- **Глава VI**: Gravity field diagrams
- **Глава VII**: Solar physics diagrams (photon trajectories, magnetic fields)
- **Глава VIII**: Solar system formation diagrams
- **Глава IX**: Planetary system diagrams
- **Глава X**: Experimental setup diagrams

## Formula and Table Integration

### Formula References in Captions

Captions may contain formula references from Step 01:
```
Рис. 4. График зависимости {{formula:abc123def456}} от температуры
```

These references:
- Link to formulas extracted in Step 01
- Are preserved in the `caption` field
- Are tracked in `metadata.caption_formula_refs` array
- Enable cross-referencing between illustrations and formulas
- Will be restored during final rendering

### Table References in Captions (rare)

Occasionally, captions may reference tables:
```
Рис. 7. Данные из {{table:xyz789abc123}}
```

These are handled similarly to formula references.

## Processing Notes

### File Processing Order

Files are processed alphabetically within chapter directories:
1. `index.md` (if exists)
2. Chapter directories (alphabetically)
3. Files within each chapter (alphabetically)

This matches the processing order from Steps 01 and 02.

### Illustration ID Generation

MD5 hash input combines:
- SVG viewBox attribute
- First 500 characters of SVG content
- Metadata (db_key, src)
- Source file path
- Position in file

This ensures:
- Identical SVGs in different locations get different IDs
- Deterministic IDs for the same illustration
- 12-character IDs are sufficiently unique

### Preservation Strategy

- **Original SVG preserved** in `svg_content` field
- **Complete wrapper HTML** preserved in `wrapper_html` field
- **Caption with references** preserved as-is
- **Metadata enables** filtering and analysis
- **Source information enables** traceability and regeneration

## Usage in Next Steps

### Step 04: Content Analysis (planned)

Future step may:
- Analyze remaining text content
- Build content graph (formulas → tables → illustrations)
- Extract metadata and cross-references
- Validate structure and completeness

### Final Rendering

During site generation:
- Replace `{{illustration:ID}}` references with actual SVG
- Restore wrapper HTML structure
- Process formula references in captions
- Apply styling and formatting
- Enable interactive features (zoom, pan)

## Key Learnings

### Regex Pattern Design

1. **Multi-level nesting**: SVG illustrations have complex 3-level div nesting
2. **Optional groups**: Caption div is optional, requiring `(?:...)?` pattern
3. **Non-greedy matching**: `.*?` prevents over-matching across multiple SVGs
4. **Whitespace handling**: `\s*` handles variations in whitespace between tags
5. **Attribute extraction**: Separate capture group for inner div attributes

### Data Structure Design

1. **SVG preservation**: Complete SVG markup stored as string
2. **Dual caption tracking**: Raw caption + parsed formula references
3. **Element counting**: Statistics on SVG complexity
4. **Metadata separation**: Tracking metadata vs. SVG properties
5. **Source tracking**: File path + position enables debugging

### Processing Pipeline

1. **Sequential dependencies**: Step 03 builds on Steps 01 and 02
2. **Reference preservation**: Formula/table refs in captions maintained
3. **Consistent format**: `{{illustration:ID}}` matches `{{formula:ID}}` and `{{table:ID}}`
4. **Statistics tracking**: Parallel to previous steps
5. **Directory structure**: Mirrors Step 01 and 02 patterns

## Files

### Essential Files
- `extract-illustrations.py` - Main extraction script
- `AI-INSTRUCTIONS.md` - Implementation specification
- `step-result-context.md` - This document
- `extraction_stats.json` - Processing statistics

### Output Directories
- `illustrations/` - JSON files containing extracted illustrations
- `result/` - Markdown files with illustration references

## Validation

### Post-Extraction Checks

1. **Count illustrations**: Match `total_illustrations` with file count in `illustrations/`
2. **Check references**: Ensure all `{{illustration:*}}` references have corresponding JSON files
3. **Validate JSON**: All files should parse as valid JSON
4. **Validate SVG**: Each SVG should have opening and closing `<svg>` tags
5. **Check viewBox**: Most illustrations should have viewBox attribute
6. **Verify formulas**: Formula refs in captions should exist in Step 01 output
7. **Element counts**: Verify element counts are non-negative integers

### Validation Script Example

```python
import json
from pathlib import Path

illustrations_dir = Path("illustrations")
json_files = list(illustrations_dir.glob("illustration_*.json"))

print(f"Total illustration files: {len(json_files)}")

# Validate each file
for f in json_files:
    with open(f) as file:
        data = json.load(file)
        assert 'id' in data
        assert 'type' in data
        assert data['type'] == 'svg'
        assert 'svg_content' in data
        assert data['svg_content'].startswith('<svg')
        assert data['svg_content'].endswith('</svg>')
        assert 'metadata' in data
        assert 'element_counts' in data['metadata']

print("✓ All illustration files validated")
```

### Cross-Reference Validation

```python
import json
import re
from pathlib import Path

# Load all illustrations
illustrations_dir = Path("illustrations")
formulas_dir = Path("../step-01-extract-all-formulas/formulas")

# Get all formula IDs
formula_ids = set()
for f in formulas_dir.glob("formula_*.json"):
    formula_id = f.stem.replace("formula_", "")
    formula_ids.add(formula_id)

# Check formula references in captions
invalid_refs = []
for f in illustrations_dir.glob("illustration_*.json"):
    with open(f) as file:
        data = json.load(file)
        caption = data.get('caption')
        if caption:
            refs = re.findall(r'\{\{formula:([a-f0-9]+)(?::\([^)]+\))?\}\}', caption)
            for ref_id in refs:
                if ref_id not in formula_ids:
                    invalid_refs.append((f.name, ref_id))

if invalid_refs:
    print(f"Warning: {len(invalid_refs)} invalid formula references found")
else:
    print("✓ All formula references in captions are valid")
```

## Edge Cases

### Missing Caption

Some illustrations may not have captions:
- `caption` field: `null`
- `has_caption`: `false`
- `caption_has_formulas`: `false`
- `caption_formula_refs`: `[]`

### Missing Metadata

Some illustrations may not have tracking attributes:
- `db_key`: `null`
- `src`: `null`
- Hash ID still generated using SVG content

### Complex SVG Structure

Some SVGs may have:
- Nested `<g>` groups with transforms
- `<defs>` with gradients, patterns, masks
- `<clipPath>` elements
- Embedded `<style>` sections
- Text with `<tspan>` elements
- Animation elements (rare)

All SVG content is preserved exactly as-is.

### Caption Variations

Captions may use different formats:
- `Рис. 4.` - Standard figure prefix
- `Puc. 4.` - Alternative spelling
- `Схема 1.` - Diagram
- `Диаграмма 2.` - Chart/Diagram

All are preserved in the caption field.

## Known Limitations

1. **SVG-only**: Currently only extracts SVG illustrations (no raster images)
2. **Structure dependency**: Requires specific div wrapper structure
3. **No validation**: SVG content is not validated for correctness
4. **Text preservation**: SVG text elements preserved as-is (no extraction)
5. **No optimization**: SVG is not minified or optimized

## Technical Notes

### Extraction Order

Illustrations are extracted in single pass:
1. Find all SVG illustration wrappers
2. Process in **reverse order** to preserve character positions
3. Extract metadata, SVG content, and caption
4. Generate hash ID
5. Save to JSON
6. Replace with reference

### Position Tracking

The `source.position` field tracks character offset in the **original** file (from Step 02 result), not the modified file.

### Encoding

All files use **UTF-8 encoding** to properly handle:
- Russian Cyrillic text in captions
- Greek letters in SVG text elements
- Mathematical symbols in SVG
- Special characters in captions
- UUID identifiers

### SVG Preservation

SVG content is preserved **exactly** as found:
- No whitespace normalization
- No attribute reordering
- No path optimization
- No style extraction
- No text conversion

This ensures perfect reconstruction capability.

## Expected Results

### Volume Estimates

Based on typical physics textbook structure:
- **Total illustrations**: 100-300 SVG diagrams
- **Illustrations with captions**: ~90% (most diagrams are captioned)
- **Illustrations with metadata**: ~85% (most tracked in original system)
- **Captions with formulas**: ~25% (many reference equations)
- **Average elements per SVG**: 20-50 (varies by complexity)

### File Size

- **JSON files**: ~5-50 KB each (depending on SVG complexity)
- **Total illustrations directory**: ~5-15 MB
- **Modified markdown files**: Significantly smaller (SVG replaced with references)

### Processing Time

- **Per file**: <1 second
- **Total**: ~1-2 minutes for all files

## Integration with Pipeline

### Previous Steps

**Step 01**: Formula extraction
- Input: Original markdown with LaTeX formulas
- Output: Formula JSON files + markdown with `{{formula:ID}}`

**Step 02**: Table extraction
- Input: Step 01 result
- Output: Table JSON files + markdown with `{{table:ID}}`

### This Step (03)

**Input**: Step 02 result (markdown with formula and table references)
**Output**: Illustration JSON files + markdown with all three reference types

**State after Step 03**:
- Formulas: `{{formula:ID}}`
- Tables: `{{table:ID}}`
- Illustrations: `{{illustration:ID}}`
- Remaining: Plain text, headings, links, basic markdown

### Next Steps

**Step 04** (planned): Content and metadata analysis
- Extract remaining structure
- Build dependency graph
- Validate cross-references
- Generate content index

**Final Rendering**:
- Load all JSON files (formulas, tables, illustrations)
- Replace references with actual content
- Apply formatting and styling
- Generate final MkDocs site

## Statistics Tracking

The `extraction_stats.json` file will contain:

```json
{
  "total_illustrations": 234,
  "svg_illustrations": 234,
  "files_processed": 59,
  "illustrations_with_metadata": 210,
  "illustrations_with_captions": 220,
  "captions_with_formulas": 45
}
```

| Metric | Description |
|--------|-------------|
| `total_illustrations` | Total number of illustrations extracted |
| `svg_illustrations` | Count of SVG illustrations (all currently) |
| `files_processed` | Number of markdown files processed |
| `illustrations_with_metadata` | Illustrations with `data-db-key` or `data-src` |
| `illustrations_with_captions` | Illustrations with caption divs |
| `captions_with_formulas` | Captions containing formula references |

## Related Documentation

- `../step-01-extract-all-formulas/step-result-context.md` - Formula extraction context
- `../step-02-extract-all-tables/step-result-context.md` - Table extraction context
- `../../project-context.md` - Overall project documentation
- `AI-INSTRUCTIONS.md` - Detailed implementation specifications

---

**Script**: `extract-illustrations.py`  
**Input**: `../step-02-extract-all-tables/result/`  
**Output**: `illustrations/` + `result/`  
**Last Updated**: October 2025  
**Status**: Ready for execution
