#!/usr/bin/env python3
import re

# Read test file
with open('../step-01-extract-all-formulas/result/chapter_приложение-1-гиперчастотные-параметры-некоторых-газов-в-нормальных-условиях/index.md', 'r') as f:
    content = f.read()

# Test the pattern
pattern = r'(^\|.+\|\s*$\n^\s*\|[\s:-]+\|\s*$(?:\n^\s*\|.+\|\s*$)+)'
matches = list(re.finditer(pattern, content, flags=re.MULTILINE))

print(f"Found {len(matches)} markdown tables")

for i, match in enumerate(matches):
    lines = match.group(0).count('\n')
    print(f"Table {i+1}: starts at {match.start()}, {lines} lines")
