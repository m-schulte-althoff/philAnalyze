"""Proper check for tabs in ODT using text_recursive property."""
from odfdo import Document

doc = Document('data/Phil.odt')
body = doc.body

print("Checking for tabs using different methods...")
print("=" * 80)

# Method 1: Check serialize() for <text:tab>
tab_count = 0
for i, para in enumerate(body.paragraphs):
    xml = para.serialize()
    if '<text:tab' in xml or 'text:tab' in xml:
        tab_count += 1
        if tab_count <= 10:
            # para.text doesn't include tabs, but we can count them in XML
            tab_elements = xml.count('<text:tab')
            print(f"\n[{i}] Has {tab_elements} tab(s)")
            print(f"  .text: {repr(para.text[:100])}")
            print(f"  XML snippet: {xml[:250]}")

print(f"\nTotal paragraphs with <text:tab> elements: {tab_count}")

# Method 2: Look for paragraphs that should have quotes based on markers
print("\n" + "=" * 80)
print("Looking for quote markers in text content:")
marker_paras = []
for i, para in enumerate(body.paragraphs):
    text = para.text
    if text:
        stripped = text.strip()
        # Check if starts with marker
        if stripped and len(stripped) > 2:
            first_char = stripped[0]
            second_char = stripped[1] if len(stripped) > 1 else ''
            
            # Marker followed by space
            if first_char in ['°', '~', '^', '+', '-'] and second_char == ' ':
                marker_paras.append((i, text, para.serialize()))
                if len(marker_paras) <= 10:
                    print(f"\n[{i}] Marker: {first_char}")
                    print(f"  Text: {repr(text[:100])}")

print(f"\nTotal paragraphs with quote markers: {len(marker_paras)}")
