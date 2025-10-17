#!/usr/bin/env python3
import re

# Test with actual table content that has trailing spaces
test_table = """| Газ | Value |
| --- | ----- |
| H2  | 1.0   |
| He  | 2.0   |
"""

pattern = r'(\|.+\|\s*\n\|[\s:-]+\|\s*\n(?:\|.+\|\s*\n?)+)'
matches = re.findall(pattern, test_table, re.DOTALL)
print(f"Test 1 - Simple table: {len(matches)} matches")

# Now test with file
with open('../step-01-extract-all-formulas/result/chapter_приложение-1-гиперчастотные-параметры-некоторых-газов-в-нормальных-условиях/index.md', 'r', encoding='utf-8') as f:
    content = f.read()

matches = re.findall(pattern, content, re.DOTALL)
print(f"Test 2 - Appendix file: {len(matches)} matches")

if matches:
    print(f"First match has {matches[0].count(chr(10))} newlines (rows)")
    print(f"Last match has {matches[-1].count(chr(10))} newlines (rows)")
