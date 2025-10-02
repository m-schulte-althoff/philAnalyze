"""Debug script to check what's happening with page 13 content."""
from odfdo import Document

doc = Document('data/Phil.odt')
body = doc.body
paragraphs = body.paragraphs

# Page 13 is approximately paragraph 13 * 40 = 520
# But we need to account for ToC, so let's search for "Philosophie" followed by quotes

print("Searching for 'Philosophie' paragraph and following content...")
print("=" * 80)

philosophie_found = False
for i, para in enumerate(paragraphs):
    text = para.text
    if not text:
        continue
    
    # Find the "Philosophie" heading
    if text.strip() == "Philosophie" or ("Philosophie" in text and len(text.strip()) < 30):
        philosophie_found = True
        print(f"\n[{i}] FOUND Philosophie heading: {repr(text)}")
        print("\nFollowing 10 paragraphs:")
        
        # Show next 10 non-empty paragraphs
        count = 0
        for j in range(i+1, min(i+50, len(paragraphs))):
            next_para = paragraphs[j]
            next_text = next_para.text
            if next_text and next_text.strip():
                count += 1
                # Show tabs, spaces, and first char clearly
                display = repr(next_text)
                print(f"\n  [{j}] {display[:150]}...")
                
                # Check if it starts with tab
                if next_text.startswith('\t'):
                    print(f"       -> STARTS WITH TAB!")
                elif next_text.startswith('    '):
                    print(f"       -> STARTS WITH 4 SPACES!")
                else:
                    first_char = next_text[0] if next_text else ''
                    print(f"       -> First char: {repr(first_char)}")
                
                if count >= 10:
                    break
        break

if not philosophie_found:
    print("'Philosophie' heading not found. Searching for content with markers...")
    for i, para in enumerate(paragraphs[1000:2000]):
        text = para.text
        if text and text.strip() and text.strip()[0] in ['°', '~', '^', '+', '-']:
            print(f"\n[{i+1000}] {repr(text[:100])}")
