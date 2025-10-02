"""Debug script to analyze ToC structure with categories and subcategories."""
from odfdo import Document
from data_model import get_text_with_tabs

doc = Document('data/Phil.odt')
body = doc.body
paragraphs = body.paragraphs

print("Analyzing ToC structure (first 600 paragraphs):")
print("=" * 80)

# Look for ToC pattern
toc_items = []
for i, para in enumerate(paragraphs[:600]):
    text = get_text_with_tabs(para)
    if not text or not text.strip():
        continue
    
    # Check if it's bold (category) or has links (subcategory)
    links = para.get_links()
    
    # Try to detect bold by checking style
    style_name = para.style if para.style else "None"
    
    # Get text spans to check for bold
    xml = para.serialize()
    has_bold = 'bold' in xml.lower() or 'text:style-name="T1"' in xml or 'text:style-name="T2"' in xml
    
    # Detect tabs
    has_tab = '\t' in text
    
    if has_tab or len(links) > 0 or (len(text.strip()) < 80 and i < 500):
        toc_items.append({
            'index': i,
            'text': text.strip()[:70],
            'has_tab': has_tab,
            'has_links': len(links) > 0,
            'links': len(links),
            'style': style_name,
            'has_bold_marker': has_bold
        })

print(f"\nFound {len(toc_items)} potential ToC items\n")

# Show first 30
for item in toc_items[:30]:
    bold_marker = "**" if item['has_bold_marker'] else "  "
    tab_marker = "[TAB]" if item['has_tab'] else "     "
    link_marker = f"({item['links']} links)" if item['has_links'] else "          "
    
    print(f"[{item['index']:3d}] {bold_marker} {tab_marker} {link_marker} | {item['text'][:60]}")

print("\n" + "=" * 80)
print("\nLooking for category/subcategory pattern:")
print("(Bold items = categories, items with links = subcategories)")

# Find the pattern
category = None
for item in toc_items[:50]:
    if item['has_bold_marker'] and not item['has_tab']:
        category = item['text']
        print(f"\nCATEGORY: {category}")
    elif item['has_links'] and item['has_tab']:
        print(f"  → Subcategory: {item['text']}")
