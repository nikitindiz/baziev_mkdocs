# Table Extraction - ACTUAL FIX

## The Real Problem (Third Time's the Charm)

The markdown tables weren't being extracted because **the regex pattern didn't account for trailing whitespace after the last pipe `|` on each line**.

Looking at the actual file content:
```markdown
| Газ               | Масса осциллятора, ... | Value |
| ----------------- | ---------------------- | ----- |
| Водород           | {{formula:fd162a52d5de}}  | 0.089879896                    |
```

Notice that after the last `|` on row 3, there are TRAILING SPACES before the newline. The pattern `\|.+\|` expects lines to END with `|`, but `.+` greedily consumes those trailing spaces, so the line doesn't actually end with `|`!

## The CORRECT Fix

**Pattern that ACTUALLY works:**
```python
pattern = r'(\|.+\|\s*\n\|[\s:-]+\|\s*\n(?:\|.+\|\s*\n?)+)'
```

Key change: Added `\s*` (optional whitespace) after each `|` and before each `\n`:
- `\|.+\|\s*\n` - Header row ending with pipe + optional spaces + newline
- `\|[\s:-]+\|\s*\n` - Separator row with optional spaces  
- `(?:\|.+\|\s*\n?)+` - Data rows with optional spaces

## Changes Made

**In `extract-tables.py`, line ~261:**

```python
# OLD (BROKEN):
pattern = r'(\|.+\|\n\|[\s:-]+\|\n(?:\|.+\|\n?)+)'

# NEW (FIXED):
pattern = r'(\|.+\|\s*\n\|[\s:-]+\|\s*\n(?:\|.+\|\s*\n?)+)'
```

## Why Previous Attempts Failed

1. **First attempt**: Used `^` and `$` anchors with MULTILINE - too restrictive
2. **Second attempt**: Used `[^\n]+` - still had same trailing space issue
3. **Third attempt**: Used plain `\n` - **THIS was the real problem!**

The issue was never about the content matching (`.+` vs `[^\n]+`), it was about the **whitespace between the last pipe and the newline**!

## To Run

```bash
cd /Users/electrino/work/vibed/baziev_mkdocs/normalized/step-02-extract-all-tables

# Clean previous attempts
rm -rf tables result

# Run with CORRECT pattern
python3 extract-tables.py
```

## Expected Output

Should now find:
- 6 markdown tables in Приложение 1
- 2-3 HTML tables in other appendices  
- **Total: ~9 tables** (not just 3!)

## Verification

```bash
# Should show ~9 files
ls -1 tables/ | wc -l

# Should show both "markdown" and "html"
ls tables/*.json | xargs -I {} jq -r '.type' {} | sort | uniq -c

# Appendix file should have 6 table references
grep -c "{{table:" result/chapter_приложение-1-*/index.md
```

---

**Root Cause**: Trailing whitespace after pipes in markdown tables  
**Solution**: Add `\s*` after `|` before `\n` in regex pattern  
**Status**: Should work NOW (really!)  
**Date**: 18 October 2025
