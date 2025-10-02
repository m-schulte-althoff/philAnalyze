"""Debug script to explore ODT paragraph structure."""
from odfdo import Document

doc = Document('data/Phil.odt')
body = doc.body
paragraphs = body.paragraphs

print("Exploring first 30 paragraphs:")
print("=" * 80)

for i, para in enumerate(paragraphs[:30]):
    text = para.text
    if not text or text.strip() == '':
        continue
    
    # Check paragraph style
    style = para.style
    
    # Check for text spans with formatting
    spans = para.get_spans()
    
    # Check text properties
    has_bold = False
    has_underline = False
    for span in spans:
        if span.style:
            # Check if span has bold or underline
            style_obj = doc.get_style('text', span.style)
            if style_obj:
                props = style_obj.serialize()
                if 'bold' in props.lower():
                    has_bold = True
                if 'underline' in props.lower():
                    has_underline = True
    
    # Get links
    links = para.get_links()
    
    text_preview = text[:80].replace('\n', ' ')
    
    print(f"\n[{i}] Style: {style}")
    print(f"    Bold: {has_bold}, Underline: {has_underline}, Links: {len(links)}")
    print(f"    Text: {text_preview}...")
    
    if i >= 20 and text_preview:  # Stop after showing some meaningful content
        break

print("\n" + "=" * 80)
print("Looking for paragraphs with specific styles or markers:")

for i, para in enumerate(paragraphs[:100]):
    text = para.text
    if not text or text.strip() == '':
        continue
    
    # Check if text starts with special markers
    text_stripped = text.strip()
    if text_stripped and text_stripped[0] in ['°', '^', '~', '+', '-']:
        print(f"\n[{i}] MARKER FOUND: {text_stripped[0]}")
        print(f"    Style: {para.style}")
        print(f"    Text: {text_stripped[:100]}")
