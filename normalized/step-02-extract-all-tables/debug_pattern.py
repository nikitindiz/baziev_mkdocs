#!/usr/bin/env python3
import re

# Read actual table from the file
with open('../step-01-extract-all-formulas/result/chapter_приложение-1-гиперчастотные-параметры-некоторых-газов-в-нормальных-условиях/index.md', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"File length: {len(content)} chars")
print(f"First 500 chars:\n{content[:500]}\n")

# Look for the pipe characters
pipes = content.count('|')
print(f"Total pipe characters: {pipes}")

# Look for separator lines
lines = content.split('\n')
sep_lines = [i for i, line in enumerate(lines) if re.match(r'\|[\s:-]+\|', line)]
print(f"\nFound {len(sep_lines)} separator lines at indices: {sep_lines[:5]}")

if sep_lines:
    idx = sep_lines[0]
    print(f"\nContext around first separator (lines {idx-1} to {idx+2}):")
    for i in range(max(0, idx-1), min(len(lines), idx+3)):
        print(f"  Line {i}: {repr(lines[i][:80])}")

# Test the pattern
pattern = r'(\|.+\|\n\|[\s:-]+\|\n(?:\|.+\|\n?)+)'
matches = list(re.finditer(pattern, content))
print(f"\nPattern matches: {len(matches)}")

if matches:
    print(f"First match at position {matches[0].start()}-{matches[0].end()}")
    print(f"Preview: {repr(matches[0].group(0)[:200])}")
else:
    # Try even simpler pattern
    simple = r'\|.+\|\n\|[- :]+\|'
    simple_matches = list(re.finditer(simple, content))
    print(f"\nSimple pattern matches (header+sep only): {len(simple_matches)}")
    if simple_matches:
        print(f"First simple match: {repr(simple_matches[0].group(0))}")
