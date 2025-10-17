#!/usr/bin/env python3
import re

# Simple test content with one table
test_content = """# Test

| Газ | Value |
| --- | ----- |
| H2  | 1.0   |
| He  | 2.0   |

Some text after.
"""

# Test different patterns
patterns = [
    (r'(^\|.+\|\s*$\n^\s*\|[\s:-]+\|\s*$(?:\n^\s*\|.+\|\s*$)+)', 'Current pattern'),
    (r'(\|.+\|[\r\n]+\|[\s:-]+\|[\r\n]+(?:\|.+\|[\r\n]*)+)', 'Original simple pattern'),
    (r'(\|[^\n]+\|\n\|[\s:-]+\|\n(?:\|[^\n]+\|\n?)+)', 'No whitespace pattern'),
]

for pattern, name in patterns:
    matches = list(re.finditer(pattern, test_content, flags=re.MULTILINE))
    print(f"{name}: Found {len(matches)} tables")
    if matches:
        print(f"  Match: {repr(matches[0].group(0)[:80])}")
    print()
