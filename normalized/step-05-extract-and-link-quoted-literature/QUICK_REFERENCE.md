# Step 05 Quick Reference

## What This Step Does

Extracts literature references from bibliography and replaces citation markers with structured references.

## Quick Start

```bash
cd normalized/step-05-extract-and-link-quoted-literature
python3 parse-refs.py
```

## Input → Output

| Input | Output |
|-------|--------|
| `М. Планка [1]` | `М. Планка {{literature:abc123def456}}` |
| `работах [3—5]` | `работах {{literature:abc}}, {{literature:def}}, {{literature:ghi}}` |
| `источникам [10, 11]` | `источникам {{literature:xxx}}, {{literature:yyy}}` |

## Files Generated

```
normalized/
├── literature/                    # 48 literature entries
│   ├── literature_abc123.json
│   ├── literature_def456.json
│   └── ...
└── step-05-extract-and-link-quoted-literature/
    ├── result/                    # Modified markdown files
    │   └── chapter_*/
    └── extraction_stats.json      # Processing statistics
```

## Validation Commands

```bash
# Count literature files (should be 48)
ls -1 ../../literature/literature_*.json | wc -l

# Check no citations remain
grep -r '\[\d\]' result/

# Count references
grep -r '{{literature:' result/ | wc -l
```

## Citation Patterns Supported

| Pattern | Example | Result |
|---------|---------|--------|
| Simple | `[1]` | `{{literature:ID}}` |
| Range | `[3—5]` | `{{literature:ID1}}, {{literature:ID2}}, {{literature:ID3}}` |
| Multiple | `[10, 11]` | `{{literature:ID1}}, {{literature:ID2}}` |

## Expected Statistics

- **Total entries**: 48
- **Files processed**: ~59
- **Files with citations**: ~15
- **Citations replaced**: ~87

## Troubleshooting

### No literature files generated

Check bibliography file exists:
```bash
ls -l ../../docs/chapter_список-цитированной-литературы/index.md
```

### Citations not replaced

Check input directory:
```bash
ls -l ../step-04-parse-missed-db-keys-and-src/result/
```

### Script errors

Run with Python 3.8+:
```bash
python3 --version
python3 parse-refs.py
```

## Testing

Test pattern matching:
```bash
python3 test_patterns.py
```

## Next Steps

After completion:
1. ✅ All 48 literature entries extracted
2. ✅ All citations replaced with references
3. ✅ Content ready for database integration
4. ✅ Ready for final rendering pipeline

## Integration

This completes the normalization pipeline:

```
Step 01: Formulas       → {{formula:ID}}
Step 02: Tables         → {{table:ID}}
Step 03: Illustrations  → {{illustration:ID}}
Step 04: Metadata       → Update formulas
Step 05: Literature     → {{literature:ID}}
```

All content is now in structured JSON format!
