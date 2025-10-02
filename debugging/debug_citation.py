#!/usr/bin/env python
"""Debug script to test citation parsing independently."""

import sys
import importlib

# Force fresh import
if 'data_model' in sys.modules:
    del sys.modules['data_model']

import data_model

# Test parsing
citation_text = '[G. West, "Scale - The Universal Laws of Growth, Innovation, Sustainability, and the Pace of Life in Organisms, Cities, Economies, and Companies"]'

# Extract citation from full text
import re
match = re.search(r'\[([^\]]+)\]$', citation_text.strip())
if match:
    citation_raw = match.group(1)
    
    # Debug: show the parsing process
    parts = []
    current_part = []
    in_quotes = False
    
    for i, char in enumerate(citation_raw):
        if char in ['"', '"', '"']:
            in_quotes = not in_quotes
            if i < 15 or i > len(citation_raw) - 15:
                print(f'Pos {i}: quote char (ord={ord(char)}) -> in_quotes={in_quotes}')
        elif char == ',' and not in_quotes:
            part = ''.join(current_part).strip()
            parts.append(part)
            print(f'Pos {i}: comma (not in quotes) -> split, part="{part[:30]}..."')
            current_part = []
            continue
        current_part.append(char)
    
    if current_part:
        part = ''.join(current_part).strip()
        parts.append(part)
        print(f'Final part: "{part[:50]}..."')
    
    print(f'\nTotal parts: {len(parts)}')
    for i, part in enumerate(parts):
        print(f'  Part {i}: {part[:60]}...')
