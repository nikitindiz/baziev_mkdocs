#!/usr/bin/env python3
"""
Quick test for parse-refs.py
Tests the citation pattern matching and replacement logic
"""

import re
from pathlib import Path

# Test text with various citation patterns
test_text = """
# Test Document

Постоянные Больцмана (в неявном виде) и Планка были выведены одновременно, 
в одной статье М. Планка [1] от 1900 г. Первая из этих констант широко 
применяется в термодинамике газов.

Как показано в работах [3—5], эта теория имеет широкое применение.

Согласно источникам [10, 11, 23], результаты были подтверждены.

Простая ссылка [2] в тексте.

Диапазон с дефисом [7-9] также должен работать.
"""

def find_citations(text: str):
    """Test citation finding logic"""
    citations = []
    
    # Pattern 1: Simple [N]
    pattern1 = r'\[(\d+)\]'
    for match in re.finditer(pattern1, text):
        ref_num = int(match.group(1))
        citations.append((
            match.group(0),
            match.start(),
            match.end(),
            ref_num,
            'simple'
        ))
    
    # Pattern 2: Ranges [N—M] or [N-M]
    pattern2 = r'\[(\d+)[—\-](\d+)\]'
    for match in re.finditer(pattern2, text):
        start_num = int(match.group(1))
        end_num = int(match.group(2))
        for num in range(start_num, end_num + 1):
            citations.append((
                match.group(0),
                match.start(),
                match.end(),
                num,
                'range'
            ))
    
    # Pattern 3: Multiple refs [N, M]
    pattern3 = r'\[(\d+(?:\s*,\s*\d+)+)\]'
    for match in re.finditer(pattern3, text):
        nums_str = match.group(1)
        nums = [int(n.strip()) for n in nums_str.split(',')]
        for num in nums:
            citations.append((
                match.group(0),
                match.start(),
                match.end(),
                num,
                'multiple'
            ))
    
    return citations

# Run test
print("Testing citation pattern matching...\n")
print("=" * 60)
print("TEST TEXT:")
print("=" * 60)
print(test_text)
print("\n" + "=" * 60)
print("FOUND CITATIONS:")
print("=" * 60)

citations = find_citations(test_text)

# Group by position
position_groups = {}
for match_text, start, end, ref_num, pattern_type in citations:
    key = (start, end)
    if key not in position_groups:
        position_groups[key] = {
            'text': match_text,
            'refs': [],
            'type': pattern_type
        }
    position_groups[key]['refs'].append(ref_num)

# Print results
for (start, end), group in sorted(position_groups.items()):
    context_start = max(0, start - 20)
    context_end = min(len(test_text), end + 20)
    context = test_text[context_start:context_end].replace('\n', ' ')
    
    print(f"\nPattern: {group['text']}")
    print(f"Type:    {group['type']}")
    print(f"Refs:    {sorted(set(group['refs']))}")
    print(f"Context: ...{context}...")

print("\n" + "=" * 60)
print(f"Total citation groups found: {len(position_groups)}")
print(f"Total reference numbers: {sum(len(g['refs']) for g in position_groups.values())}")
print("=" * 60)
