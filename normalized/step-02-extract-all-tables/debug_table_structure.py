#!/usr/bin/env python3
import re

with open('../step-01-extract-all-formulas/result/chapter_приложение-1-гиперчастотные-параметры-некоторых-газов-в-нормальных-условиях/index.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Get first table manually
lines = content.split('\n')
table_start = 2  # Line with "| Газ..."
table_lines = []
for i in range(table_start, min(table_start + 20, len(lines))):
    line = lines[i]
    if line.strip() == '':
        break
    table_lines.append(line)

print(f"Found {len(table_lines)} lines in first table")
print("\nFirst 5 lines:")
for i, line in enumerate(table_lines[:5]):
    print(f"{i}: {repr(line)}")

# Try to match just this table
table_text = '\n'.join(table_lines)
print(f"\nTable text length: {len(table_text)}")

# Test different patterns
patterns = [
    (r'(\|.+\|\n\|[\s:-]+\|\n(?:\|.+\|\n?)+)', 'Original'),
    (r'(\|.+\|\n\|[\s:-]+\|\n(?:\|.+\n?)+)', 'Without trailing |'),
    (r'(\|[^\n]+\n\|[\s:-]+\|\n(?:\|[^\n]+\n?)+)', 'Using [^\\n]'),
]

for pattern, name in patterns:
    matches = re.findall(pattern, table_text)
    print(f"\n{name}: {len(matches)} matches")
    if matches:
        print(f"  Match length: {len(matches[0])}")
