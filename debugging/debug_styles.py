"""Analyze paragraph styles to understand document structure."""
from odfdo import Document
from collections import Counter

doc = Document('data/Phil.odt')
body = doc.body
paragraphs = body.paragraphs

# Count styles
style_counter = Counter()
style_samples = {}

for para in paragraphs:
    text = para.text
    if text and text.strip():
        style = para.style if para.style else "None"
        style_counter[style] += 1
        
        if style not in style_samples:
            style_samples[style] = text[:150]

print("Top 20 paragraph styles:")
print("=" * 80)
for style, count in style_counter.most_common(20):
    sample = style_samples.get(style, "")[:80]
    print(f"{style:15s} ({count:4d}): {sample}...")

print("\n" + "=" * 80)
print("\nChecking for citations (text with [ ] brackets):")
citation_count = 0
for i, para in enumerate(paragraphs):
    text = para.text
    if text and '[' in text and ']' in text:
        citation_count += 1
        if citation_count <= 10:
            text_preview = text[:120].replace('\n', ' ')
            print(f"[{i:4d}] {text_preview}...")

print(f"\nTotal paragraphs with brackets: {citation_count}")
