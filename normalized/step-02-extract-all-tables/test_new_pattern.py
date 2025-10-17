#!/usr/bin/env python3
import re

# Test the NEW pattern
pattern = r'(\|[^\n]+\n\|[\s:-]+\|[^\n]*\n(?:\|[^\n]+\n?)+)'

# Simple test
test = """# Title

| A | B |
| - | - |
| 1 | 2 |
| 3 | 4 |

Text after.
"""

matches = re.findall(pattern, test)
print(f"Simple test: Found {len(matches)} tables")
if matches:
    print(f"Match: {repr(matches[0][:80])}")

# Real file test
with open('../step-01-extract-all-formulas/result/chapter_приложение-1-гиперчастотные-параметры-некоторых-газов-в-нормальных-условиях/index.md', 'r') as f:
    content = f.read()

matches = re.findall(pattern, content)
print(f"\nReal file: Found {len(matches)} tables")
for i, m in enumerate(matches):
    rows = m.count('\n')
    print(f"  Table {i+1}: {rows} rows")
