#!/usr/bin/env python
"""Test citation parsing with curly quotes."""

import data_model

# Test with actual curly quotes from the document
text_with_curly = 'Test [G. West, "Scale - The Universal Laws of Growth, Innovation, Sustainability, and the Pace of Life"]'

quote, citation = data_model.parse_citation(text_with_curly)

print('=== TESTING CITATION PARSER ===')
print(f'Input: {text_with_curly}')
print()
print('Parsed citation:')
print(f'  Author: {citation.get("author") if citation else None}')
print(f'  Title: {citation.get("title") if citation else None}')
print(f'  Source: {citation.get("source") if citation else None}')
print()

# Check if commas in quotes are handled correctly
if citation and citation.get('title'):
    title = citation.get('title')
    print(f'Title contains "Innovation": {"Innovation" in title}')
    print(f'Title length: {len(title)}')
    
    # Count commas in title
    comma_count = title.count(',')
    print(f'Commas in title: {comma_count}')
