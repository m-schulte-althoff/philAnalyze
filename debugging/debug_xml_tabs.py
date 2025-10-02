"""Check how tabs are represented in ODT XML structure."""
from odfdo import Document

doc = Document('data/Phil.odt')
body = doc.body

# Get raw XML to see how tabs are actually stored
print("Checking ODT internal XML structure for tabs...")
print("=" * 80)

# ODT uses <text:tab/> elements for tabs, not \t characters
# Let's check if paragraphs have tab elements

count = 0
for i, para in enumerate(body.paragraphs):
    # Get the XML element
    element = para._element if hasattr(para, '_element') else para
    
    # Check for tab children
    # In ODT XML, tabs are stored as <text:tab> elements
    xml_str = element.serialize()
    
    if 'text:tab' in xml_str or '<text:tab' in xml_str:
        count += 1
        if count <= 5:
            print(f"\n[Paragraph {i}]")
            print(f"Text: {repr(para.text[:80])}")
            print(f"XML (first 200 chars): {xml_str[:200]}")
            
            # Try to get children
            children = list(element)
            print(f"Children: {len(children)}")
            for child in children[:5]:
                print(f"  - {child.tag}: {repr(child.text[:40] if child.text else 'None')}")

print(f"\nTotal paragraphs with <text:tab> elements: {count}")

# Let's also check for specific markers
print("\n" + "=" * 80)
print("Searching for paragraphs containing markers (°~^+-):")
marker_count = 0
for i, para in enumerate(body.paragraphs):
    text = para.text
    if text:
        stripped = text.strip()
        if stripped and stripped[0] in ['°', '~', '^', '+', '-']:
            marker_count += 1
            if marker_count <= 10:
                print(f"[{i}] {repr(text[:80])}")

print(f"\nTotal with markers: {marker_count}")
