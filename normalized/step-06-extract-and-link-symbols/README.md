# Step 06: Extract Symbols and Link to Formulas

## Quick Start

```bash
cd normalized/step-06-extract-and-link-symbols
python3 extract-symbols.py
```

## What This Step Does

1. **Extracts** symbol definitions from "Условные обозначения" chapter (~300 symbols)
2. **Creates** JSON files for each symbol with metadata
3. **Updates** all formulas with references to symbols they use
4. **Generates** statistics about symbol usage

## Input

- `docs/chapter_условные-обозначения/index.md` - Symbol definitions
- `normalized/formulas/*.json` - Formulas to update

## Output

- `normalized/symbols/symbol_*.json` - Symbol definitions (~300 files)
- `normalized/formulas/*.json` - Updated with `symbols` field
- `extraction_stats.json` - Processing statistics

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

## Updated Formula Structure

Formulas get a new `symbols` field with IDs of symbols they use:

```json
{
  "id": "c6fed30764ee",
  "latex": "E_0 = m_э v^2",
  "symbols": ["abc123", "def456", "ghi789"],
  ...
}
```

## Expected Results

- **Symbols extracted**: ~300
- **Formulas processed**: ~4500
- **Formulas with symbols**: ~3000-4000 (60-80%)
- **Average symbols per formula**: 3-5

## Validation

```bash
# Count symbol files
ls -1 ../symbols/symbol_*.json | wc -l

# Check all formulas have symbols field
grep -L '"symbols"' ../formulas/formula_*.json | wc -l
# Should be 0

# View statistics
cat extraction_stats.json | jq
```

## Documentation

- `AI-INSTRUCTIONS.md` - Detailed implementation guide
- `step-result-context.md` - Complete result documentation
- `extraction_stats.json` - Processing statistics

## Dependencies

- Python 3.6+
- Standard library only (json, re, hashlib, pathlib)

## Notes

- Processes all formulas (~4500 files) - may take 1-2 minutes
- Updates formulas in-place (adds `symbols` field)
- Symbol IDs are deterministic (same latex+description → same ID)
- Preserves all existing formula data
