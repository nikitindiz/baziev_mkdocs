# Project Context: Baziev Physics MkDocs Book

## Project Overview

This repository contains a scientific book about Baziev's physics ("Физика Базиева: Система новейших фундаментальных открытий") formatted as an MkDocs documentation site. The book presents a unified theory of physics with fundamental discoveries across multiple domains.

## Technology Stack

- **Framework**: MkDocs with Material theme
- **Rendering**: KaTeX for mathematical formulas
- **Language**: Russian (primary content language)
- **Markup**: Markdown with HTML elements and LaTeX mathematics

## Project Structure

### Directory Layout

```
baziev_mkdocs/
├── docs/                              # Main content directory
│   ├── index.md                       # Table of contents (main entry)
│   ├── chapter_*/                     # Chapter directories
│   │   ├── index.md                   # Chapter overview
│   │   └── *.md                       # Individual sections/paragraphs
│   └── javascripts/                   # Custom JavaScript (KaTeX config)
├── site/                              # Built/generated site
├── normalized/                        # Normalized content (if applicable)
├── mkdocs.yml                        # MkDocs configuration
├── requirements.txt                   # Python dependencies
├── package.json                      # Node.js dependencies (if any)
├── deploy_ghpages.sh                 # Deployment script
├── split_book.py                     # Book processing script
└── split_only.sh                     # Content splitting script
```

### Chapter Organization

The book is organized into chapters (Глава/Главa/ГЛАВА) and appendices (Приложение), with each chapter containing:
- An `index.md` file (chapter overview)
- Individual section files named with pattern: `{number}-{title-in-russian}.md`

**Chapter naming pattern**: `chapter_{chapter-title-in-russian}/`

## Content Structure

### Document Components

#### 1. **Headings**
- Multiple levels of Markdown headings (`#`, `##`, `###`, etc.)
- Used for chapters, sections, and subsections
- May contain numbered paragraphs (§ 1, § 2, etc.)

#### 2. **Text Content**
- Paragraphs of Russian text
- May contain inline LaTeX formulas
- May include inline references and citations
- Sometimes includes Unicode superscript/subscript characters (e.g., `²`, `³`)

#### 3. **Inline LaTeX Formulas**
Mathematical expressions within text paragraphs.

**Variants**:
- **Plain LaTeX**: `$E = mc^2$`
- **Wrapped in `<span>` tag with metadata**:
  ```html
  <span data-db-key="123" data-src="images/formula_inline_1_2_3.webp">$E = mc^2$</span>
  ```

**Attributes**:
- `data-db-key`: Unique identifier from external recognition system
- `data-src`: Path to scanned image of the formula

#### 4. **Display LaTeX Formulas**
Block-level mathematical equations, typically centered and may include equation numbers.

**Variants**:

a) **Plain display formula**:
```markdown
$$E = mc^2$$
```

b) **Wrapped in `<div>` with layout**:
```html
<div style="display: flex; width: 100%;">
<div style="width: 100%;">

$$E = mc^2$$

</div>
<div style="width: 80px;">
(1.1)
</div>
</div>
```

c) **With metadata attributes**:
```html
<div style="display: flex; width: 100%;" data-db-key="50" data-src="images/formula_full_4_2_0.webp">
<div style="width: 100%;">

$$E_0 = h f_0$$

</div>
<div style="width: 80px;">
(1.15)
</div>
</div>
```

**Features**:
- Two-column layout: formula on left, equation number on right (80px width)
- Equation numbers in format: `(chapter.number)`
- Optional metadata attributes (`data-db-key`, `data-src`)

#### 5. **SVG Illustrations**
Vector graphics embedded directly in Markdown files as inline SVG.

**Structure**:
```html
<div style="display: flex; width: 100%; flex-direction: column; margin-bottom: 1em;">
<div style="width: 100%;">
<div data-db-key="2308" data-src="images/formula_full_151_1.webp">

<svg id="uuid-..." xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1034 359.4">
  <!-- SVG content with paths, text elements, etc. -->
</svg>

</div>
</div>
<div style="font-style: italic; padding: 10px">
<!-- Caption with inline formulas -->
Puc. 4. Траектория фотона...
</div>
</div>
```

**Features**:
- Wrapped in multi-level `<div>` structure
- May have metadata attributes on wrapper div
- SVG contains `<path>`, `<text>`, `<line>`, `<g>` elements
- Text in SVG may include mathematical symbols and formulas
- Followed by italic caption (figure description)

#### 6. **Tables**

**Markdown format** (simple tables):
```markdown
| Column 1 | Column 2 |
| -------- | -------- |
| Data 1   | Data 2   |
```

**HTML format** (complex tables):
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
</tbody>
</table>
```

**Content**:
- May contain inline LaTeX formulas in cells
- Headers and data in Russian
- Scientific data with units and measurements
- LaTeX expressions with `$...$` notation

### Special Attributes

#### Metadata Attributes

Many formulas and illustrations have tracking attributes from external system:

- **`data-db-key`**: Unique identifier (integer) from formula recognition database
- **`data-src`**: Path to original scanned image (e.g., `images/formula_inline_1_2_3.webp`)

**Usage patterns**:
- Both attributes usually appear together
- Present on `<div>` or `<span>` wrapper elements
- Help track correspondence between recognized and original content
- Path format: `images/{type}_{page}_{formula_number}.webp`
  - `type`: `formula_inline`, `formula_full`
  - Numbers indicate position in source document

#### Unicode Mathematical Characters

Text may contain Unicode superscript/subscript symbols:
- Superscripts: `²`, `³`, `⁰`, `¹`, `⁴`-`⁹`
- Subscripts: `₀`, `₁`, `₂`, etc.
- Greek letters: `α`, `β`, `γ`, `λ`, `π`, etc.
- Special symbols: `×`, `÷`, `±`, `∞`, `∫`, `∂`

These may appear in:
- Regular text
- Table cells
- Headings
- Before proper LaTeX conversion

## MkDocs Configuration

### Key Settings (mkdocs.yml)

```yaml
site_name: Физика Базиева
theme:
  name: material
  language: ru
  
markdown_extensions:
  - pymdownx.arithmatex:
      generic: true
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.details
  - pymdownx.tabbed
  - admonition
  - attr_list
  - md_in_html

extra_javascript:
  - javascripts/katex.js
  - KaTeX library files

extra_css:
  - KaTeX CSS
```

### Navigation Structure

Hierarchical navigation defined in `mkdocs.yml`:
- Main page: `index.md`
- Chapters with overview pages
- Individual sections/paragraphs
- Appendices
- References and notations

## Content Patterns

### Common Section Structure

```markdown
## § N. Section Title

### 1. Subsection Title

Paragraph text with inline formula $E = mc^2$ and more text.

<div style="display: flex; width: 100%;">
<div style="width: 100%;">

$$E_0 = P_0 \cdot V_{g0}$$

</div>
<div style="width: 80px;">
(N.M)
</div>
</div>

More text continues...
```

### Typical Formula Patterns

1. **Energy equations**: `$E = ...$`, `$E_0 = ...$`
2. **Physical quantities**: Mass `$m$`, volume `$V$`, pressure `$P$`, temperature `$T$`
3. **Subscripts/superscripts**: `$x_0$`, `$x^2$`, `$x_i$`
4. **Greek letters**: `$\lambda$`, `$\nu$`, `$\beta$`, `$\rho$`
5. **Fractions**: `$\frac{a}{b}$`
6. **Roots**: `$\sqrt{x}$`, `$\sqrt[3]{x}$`
7. **Units**: `$\text{м}$`, `$\text{кг}$`, `$\text{с}^{-1}$`
8. **Scientific notation**: `$1.23 \cdot 10^{-5}$`

## Processing Notes

### For AI/ML Systems Working with This Content

1. **Preserve metadata**: Keep `data-db-key` and `data-src` attributes when present
2. **Maintain structure**: Respect nested `<div>` hierarchies for formulas and figures
3. **LaTeX handling**: 
   - Inline formulas: single `$` delimiters
   - Display formulas: double `$$` delimiters
   - May be wrapped in HTML tags
4. **Language context**: Primary language is Russian; variable names are often Latin/Greek
5. **Mathematical rigor**: Content contains precise scientific formulas—maintain accuracy
6. **SVG preservation**: Keep SVG structure intact; contains both graphics and text
7. **Table complexity**: Both simple Markdown and complex HTML tables exist
8. **Unicode normalization**: Handle Unicode math characters appropriately
9. **File naming**: Russian Cyrillic in directory and file names
10. **Equation numbering**: Format `(chapter.equation)` in right column of display formulas

## Special Considerations

### Chapter Navigation

- Some chapters use Roman numerals (Ⅷ, Ⅸ, X)
- Some use Cyrillic variations ("Глава" vs "ГЛАВА")
- Index files contain chapter overviews and section lists
- Internal links use relative paths

### Formula Recognition System

The `data-db-key` and `data-src` attributes indicate this content was:
- Scanned from original source
- Processed through OCR/recognition system
- Formulas matched to database entries
- Original images preserved as reference

### Content Consistency

When processing or generating content:
- Match existing style patterns
- Preserve formula numbering sequences
- Maintain consistent heading levels
- Keep Russian text conventions
- Respect scientific notation standards

## References and Citations

- Bibliography section: `chapter_список-цитированной-литературы/`
- Notation guide: `chapter_условные-обозначения/`
- Citations in format: `[1]`, `[2]`, etc.
- References to equations: "(1.1)", "(13.4)", etc.
- Links may use `{:target="_blank"}` for external opens

## Build and Deployment

- Build command: `mkdocs build`
- Deployment: GitHub Pages (via `deploy_ghpages.sh`)
- Output directory: `site/`
- Python requirements in `requirements.txt`

---

**Last Updated**: October 2025  
**Document Purpose**: Context for AI/ML systems working with Baziev Physics MkDocs project
