"""Debug script to find where content actually starts."""
from odfdo import Document

doc = Document('data/Phil.odt')
body = doc.body
paragraphs = body.paragraphs

print(f"Total paragraphs in document: {len(paragraphs)}")

non_empty_count = 0
for i, para in enumerate(paragraphs):
    text = para.text
    if text and text.strip():
        non_empty_count += 1
        if non_empty_count <= 30:
            text_preview = text[:100].replace('\n', ' ')
            style = para.style if para.style else "None"
            
            # Check for markers at start
            stripped = text.strip()
            marker = stripped[0] if stripped and stripped[0] in ['°', '^', '~', '+', '-'] else '-'
            
            print(f"[{i:4d}] [{marker}] Style:{style:20s} | {text_preview}...")

print(f"\nTotal non-empty paragraphs found: {non_empty_count}")
