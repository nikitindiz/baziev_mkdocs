#!/usr/bin/env python3
import re

# Simple minimal test
test1 = """| A | B |
| - | - |
| 1 | 2 |
"""

test2 = """| A | B |  
| - | - |  
| 1 | 2 |  
"""  # With trailing spaces

# Pattern
pattern = r'(\|.+\|\s*\n\|[\s:-]+\|\s*\n(?:\|.+\|\s*\n?)+)'

m1 = re.findall(pattern, test1)
m2 = re.findall(pattern, test2)

print(f"Test 1 (no trailing spaces): {len(m1)} matches")
print(f"Test 2 (with trailing spaces): {len(m2)} matches")

if m1:
    print(f"Match 1: {repr(m1[0])}")
if m2:
    print(f"Match 2: {repr(m2[0])}")

# Now let's try the ACTUAL simplest pattern that should work
simple_pattern = r'\|[^\n]+\n\|[- :]+\n(?:\|[^\n]+\n)+'

m1s = re.findall(simple_pattern, test1)
m2s = re.findall(simple_pattern, test2)

print(f"\nSimple pattern:")
print(f"Test 1: {len(m1s)} matches")
print(f"Test 2: {len(m2s)} matches")
