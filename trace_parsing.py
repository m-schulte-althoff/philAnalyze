#!/usr/bin/env python
"""Trace the exact parsing of G. West citation."""
import data_model
import re

# Load raw data
raw_data = data_model.load_odt_data('data/Phil.odt', max_pages=250)

# Find paragraph 4192
para_data = raw_data[raw_data['paragraph_num'] == 4192].iloc[0]
text = para_data['text']

print("=== RAW TEXT ===")
print(text[-200:])
print()

# Extract citation manually
match = re.search(r'\[([^\]]+)\]$', text.strip())
if match:
    citation_raw = match.group(1)
    print(f"=== CITATION RAW ===")
    print(citation_raw)
    print()
    
    # Now parse it
    quote_text, citation = data_model.parse_citation(text)
    
    print("=== PARSED ===")
    if citation:
        print(f"Author: {citation.get('author')}")
        print(f"Title: {citation.get('title')}")
        print(f"Source: {citation.get('source')}")
        
        # Check title
        title = citation.get('title', '')
        if title:
            print(f"\nTitle first char: {repr(title[0])} ord={ord(title[0])}")
            print(f"Title last char: {repr(title[-1])} ord={ord(title[-1])}")
