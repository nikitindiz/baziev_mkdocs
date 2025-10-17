#!/usr/bin/env python3
import re

# Read the actual file
with open('../step-01-extract-all-formulas/result/chapter_приложение-1-гиперчастотные-параметры-некоторых-газов-в-нормальных-условиях/index.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Get the first table manually
lines = content.split('\n')

# Find first separator
sep_idx = None
for i, line in enumerate(lines):
    if '---' in line and '|' in line:
        sep_idx = i
        break

print(f"First separator at line {sep_idx}")
print(f"\nLines around first table:")
for i in range(max(0, sep_idx-2), min(len(lines), sep_idx+5)):
    line = lines[i]
    print(f"Line {i}: {repr(line[:80])}")
    print(f"  Length: {len(line)}, Ends with |: {line.endswith('|')}, Ends with | space: {line.endswith('| ')}")

# Build a small sample table
sample_lines = lines[sep_idx-1:sep_idx+3]
sample = '\n'.join(sample_lines)
print(f"\n\nSample table ({len(sample_lines)} lines):")
print(repr(sample[:200]))

# Test various patterns on this sample
patterns = [
    (r'(\|.+\|\s*\n\|[\s:-]+\|\s*\n(?:\|.+\|\s*\n?)+)', 'Current'),
    (r'(\|[^\n]+\n\|[\s:-]+\n(?:\|[^\n]+\n?)+)', 'Without pipe at end'),
    (r'(\|.*\|\s*\n\|[\s:-]+\|\s*\n(?:\|.*\|\s*\n)+)', 'Using .* instead of .+'),
]

print("\n\nPattern tests on sample:")
for pattern, name in patterns:
    matches = re.findall(pattern, sample, re.DOTALL)
    print(f"{name}: {len(matches)} matches")
    if matches:
        print(f"  Length: {len(matches[0])}")
