"""Debug script to check if tabs are in the raw text."""
from odfdo import Document

doc = Document('data/Phil.odt')
body = doc.body
paragraphs = body.paragraphs

print("Searching for paragraphs with tabs or markers...")
print("=" * 80)

found_count = 0
for i, para in enumerate(paragraphs):
    text = para.text
    if not text:
        continue
    
    # Check for markers
    stripped = text.strip()
    if stripped and stripped[0] in ['°', '~', '^', '+', '-']:
        found_count += 1
        if found_count <= 20:
            # Show tabs as [TAB]
            display_text = text.replace('\t', '[TAB]')[:120]
            print(f"[{i:5d}] Marker '{stripped[0]}': {display_text}...")
    
    # Also check for "Ökologie" specifically
    if 'Ökologie' in text:
        print(f"\n[{i:5d}] FOUND Ökologie: {text.replace(chr(9), '[TAB]')[:150]}...")

print(f"\nTotal paragraphs with markers found: {found_count}")

# Also check the raw XML
print("\n" + "=" * 80)
print("Checking a sample paragraph's internal structure:")
for i, para in enumerate(paragraphs[2000:2100]):
    text = para.text
    if text and ('°' in text or '~' in text):
        print(f"\nParagraph {i+2000}:")
        print(f"  Text: {text[:100]}")
        print(f"  Text repr: {repr(text[:50])}")
        
        # Check children
        children = list(para.children)
        print(f"  Children count: {len(children)}")
        for child in children[:3]:
            print(f"    Child type: {child.tag}, text: {repr(child.text[:30] if child.text else 'None')}")
        break
