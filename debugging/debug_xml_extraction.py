#!/usr/bin/env python
"""Debug XML extraction."""

from odfdo import Document
import re

doc = Document('data/Phil.odt')
body = doc.body
paragraphs = body.get_paragraphs()

# Get paragraph 4192
para = paragraphs[4192]
xml = para.serialize()

print(f"XML length: {len(xml)}")
print(f"\nRaw XML (first 500 chars):")
print(xml[:500])
print(f"\n... (middle) ...\n")
print(f"Raw XML (last 500 chars):")
print(xml[-500:])

# Try the extraction steps
print("\n=== EXTRACTION STEPS ===")

# Step 1: Replace tabs
content = re.sub(r'<text:tab[^/>]*/?>', '\t', xml)
print(f"After tab replacement: {len(content)} chars")

# Step 2: Strip tags
content = re.sub(r'<[^>]+>', '', content)
print(f"After tag stripping: {len(content)} chars")
print(f"Content (last 200 chars): {content[-200:]}")

# Step 3: Unescape
content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
print(f"After unescape: {len(content)} chars")
