# Step 05: Literature Extraction - Visual Guide

## Complete Transformation Example

### Source Document (Original)

```markdown
## § 1. Гиперчастотная механика или механика микромира

### 1. Состояние термодинамики газов.

Постоянные Больцмана (в неявном виде) и Планка были выведены одновременно, 
в одной статье М. Планка [1] от 1900 г. Первая из этих констант широко 
применяется в термодинамике газов в то время как постоянная Планка не 
используется совершенно. Всем казалось и кажется теперь, что постоянная 
Планка не имеет никакого отношения к состоянию реальных газов.
```

### After Step 05

```markdown
## § 1. Гиперчастотная механика или механика микромира

### 1. Состояние термодинамики газов.

Постоянные Больцмана (в неявном виде) и Планка были выведены одновременно, 
в одной статье М. Планка {{literature:abc123def456}} от 1900 г. Первая из 
этих констант широко применяется в термодинамике газов в то время как 
постоянная Планка не используется совершенно. Всем казалось и кажется 
теперь, что постоянная Планка не имеет никакого отношения к состоянию 
реальных газов.
```

### Generated Literature JSON

`normalized/literature/literature_abc123def456.json`:
```json
{
  "id": "abc123def456",
  "number": 1,
  "text": "М. Планк. О необратимых процессах излучения. Ann. Phys., 1, 69—122, 1900. А также в кн. Х.—Г. Шёпф. От Кирхгофа до Планка. M., Мир, 1981, 158—163.",
  "author": "М. Планк",
  "title": "О необратимых процессах излучения",
  "publication": "Ann. Phys., 1, 69—122, 1900. А также в кн. Х.—Г. Шёпф. От Кирхгофа до Планка. M., Мир, 1981, 158—163.",
  "source": {
    "file": "docs/chapter_список-цитированной-литературы/index.md",
    "position": 35
  }
}
```

## Bibliography Parsing

### Source Bibliography

```markdown
# СПИСОК ЦИТИРОВАННОЙ ЛИТЕРАТУРЫ

1. М. Планк. О необратимых процессах излучения. Ann. Phys., 1, 69—122, 1900. А также в кн. Х.—Г. Шёпф. От Кирхгофа до Планка. M., Мир, 1981, 158—163. 

2. М. Планк. О законе распределения энергии в нормальном спектре излучения. Ann. Phys., 4, 553—563, 1901. Х.—Г. ШЕпф. От Кирхгофа до Планка. M., Мир, 1981, 170—181. 

3. Физика микромира. М., Советская энциклопедия, 1980.
```

### Extracted Entries

**Entry 1**:
```json
{
  "id": "abc123def456",
  "number": 1,
  "author": "М. Планк",
  "title": "О необратимых процессах излучения",
  "publication": "Ann. Phys., 1, 69—122, 1900..."
}
```

**Entry 2**:
```json
{
  "id": "def456ghi789",
  "number": 2,
  "author": "М. Планк",
  "title": "О законе распределения энергии...",
  "publication": "Ann. Phys., 4, 553—563, 1901..."
}
```

**Entry 3**:
```json
{
  "id": "ghi789jkl012",
  "number": 3,
  "author": "Физика микромира",
  "title": "",
  "publication": "М., Советская энциклопедия, 1980."
}
```

## Citation Pattern Examples

### Example 1: Simple Citation

**Before**:
```markdown
согласно работе [10]
```

**After**:
```markdown
согласно работе {{literature:xyz789abc123}}
```

### Example 2: Range Citation (Em-dash)

**Before**:
```markdown
как показано в источниках [3—5]
```

**After**:
```markdown
как показано в источниках {{literature:abc123}}, {{literature:def456}}, {{literature:ghi789}}
```

**Expansion**:
- `[3—5]` → References 3, 4, 5
- Each number gets its own `{{literature:ID}}`
- Joined with commas

### Example 3: Range Citation (Hyphen)

**Before**:
```markdown
в работах [7-9]
```

**After**:
```markdown
в работах {{literature:jkl012}}, {{literature:mno345}}, {{literature:pqr678}}
```

### Example 4: Multiple Citations

**Before**:
```markdown
согласно [10, 11, 23]
```

**After**:
```markdown
согласно {{literature:aaa111}}, {{literature:bbb222}}, {{literature:ccc333}}
```

**Parsing**:
- Split by comma: `[10, 11, 23]` → `10`, `11`, `23`
- Look up each in literature map
- Generate references

## Complete Pipeline Visualization

### Original Document (before any processing)

```markdown
## § 1. Заголовок

Формула: $$E = mc^2$$

| Column 1 | Column 2 |
|----------|----------|
| Data     | More     |

<svg>...</svg>

Ссылка на работу [1].
```

### After Step 01: Formulas Extracted

```markdown
## § 1. Заголовок

Формула: {{formula:abc123def456}}

| Column 1 | Column 2 |
|----------|----------|
| Data     | More     |

<svg>...</svg>

Ссылка на работу [1].
```

### After Step 02: Tables Extracted

```markdown
## § 1. Заголовок

Формула: {{formula:abc123def456}}

{{table:def456ghi789}}

<svg>...</svg>

Ссылка на работу [1].
```

### After Step 03: Illustrations Extracted

```markdown
## § 1. Заголовок

Формула: {{formula:abc123def456}}

{{table:def456ghi789}}

{{illustration:ghi789jkl012}}

Ссылка на работу [1].
```

### After Step 04: Metadata Updated

```markdown
## § 1. Заголовок

Формула: {{formula:abc123def456}}

{{table:def456ghi789}}

{{illustration:ghi789jkl012}}

Ссылка на работу [1].
```

(Step 04 updates formula JSON files but doesn't change markdown)

### After Step 05: Literature Linked

```markdown
## § 1. Заголовок

Формула: {{formula:abc123def456}}

{{table:def456ghi789}}

{{illustration:ghi789jkl012}}

Ссылка на работу {{literature:jkl012mno345}}.
```

## Database Structure

All content is now stored in JSON format:

```
normalized/
├── formulas/
│   ├── formula_abc123def456.json
│   ├── formula_def456ghi789.json
│   └── ...
├── tables/
│   ├── table_abc123def456.json
│   ├── table_def456ghi789.json
│   └── ...
├── illustrations/
│   ├── illustration_abc123def456.json
│   ├── illustration_def456ghi789.json
│   └── ...
└── literature/
    ├── literature_abc123def456.json
    ├── literature_def456ghi789.json
    └── ...
```

## Rendering Example

### Reference Markup

```markdown
{{literature:abc123def456}}
```

### Rendered Output (HTML)

```html
<a href="#ref-1" class="citation" data-literature-id="abc123def456">
  [1]
</a>
```

### Rendered Output (with hover preview)

```html
<a href="#ref-1" class="citation" 
   data-literature-id="abc123def456"
   title="М. Планк. О необратимых процессах излучения. Ann. Phys., 1, 69—122, 1900.">
  [1]
</a>
```

### Full Citation in Bibliography

```html
<div class="bibliography-entry" id="ref-1">
  <span class="entry-number">1.</span>
  <span class="entry-author">М. Планк.</span>
  <span class="entry-title">О необратимых процессах излучения.</span>
  <span class="entry-publication">Ann. Phys., 1, 69—122, 1900.</span>
</div>
```

## File Organization

### Before Processing

```
docs/
├── chapter_глава-i-система-новейших-фундаментальных-открытий/
│   └── 1-гиперчастотная-механика-или-механика-микромира.md
└── chapter_список-цитированной-литературы/
    └── index.md
```

### After Processing

```
normalized/
├── literature/
│   ├── literature_abc123def456.json  # Entry 1
│   ├── literature_def456ghi789.json  # Entry 2
│   └── ... (46 more)
└── step-05-extract-and-link-quoted-literature/
    ├── result/
    │   └── chapter_глава-i-система-новейших-фундаментальных-открытий/
    │       └── 1-гиперчастотная-механика-или-механика-микромира.md
    └── extraction_stats.json
```

## Statistics Example

```json
{
  "total_entries": 48,
  "files_processed": 59,
  "files_with_citations": 15,
  "total_citations": 87,
  "citations_replaced": 87
}
```

### Interpretation

- **48 literature entries**: All references from bibliography extracted
- **59 files processed**: All markdown files from Step 04
- **15 files with citations**: Only some files contain references
- **87 citations found**: Total citation markers in all files
- **87 replaced**: All citations successfully linked

## Cross-Reference Network

Literature references can link to:

### Formulas
```markdown
{{literature:abc123}} → "М. Планк. О необратимых процессах излучения."
                        (Introduced formula {{formula:def456}})
```

### Tables
```markdown
{{literature:ghi789}} → "Справочник химика"
                        (Data in {{table:jkl012}})
```

### Illustrations
```markdown
{{literature:mno345}} → "Физика Солнца"
                        (Diagram {{illustration:pqr678}})
```

This enables building a complete knowledge graph of the document!
