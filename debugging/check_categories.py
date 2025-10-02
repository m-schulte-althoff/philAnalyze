"""Check if category and subcategory structure is working correctly."""
import data_model
import pandas as pd

# Load more data to ensure we get the Ethik category
data = data_model.load_odt_data('data/Phil.odt', max_pages=None)  # Load full file

print("=" * 80)
print("CHECKING CATEGORY AND SUBCATEGORY STRUCTURE")
print("=" * 80)

# Check what types we have
print("\nData types detected:")
type_counts = data['type'].value_counts()
print(type_counts)

# Find all categories
categories = data[data['type'] == 'category']['text'].unique()
print(f"\n\nCategories found: {len(categories)}")
for i, cat in enumerate(categories[:20], 1):
    print(f"{i:2d}. {cat}")

# Check if "Ethik" category exists
ethik_category = data[data['text'].str.contains('Ethik', case=False, na=False) & 
                      (data['type'] == 'category')]
print(f"\n\n'Ethik' as category: {len(ethik_category)} found")
if len(ethik_category) > 0:
    print(ethik_category[['paragraph_num', 'text', 'type']].to_string())

# Find "Amoralismus & moralischer Nihilismus" subcategory
print("\n" + "=" * 80)
print("CHECKING 'Amoralismus & moralischer Nihilismus' SUBCATEGORY")
print("=" * 80)

# Look for this subcategory
amoralism_subcat = data[data['text'].str.contains('Amoralismus.*moralischer.*Nihilismus', 
                                                   case=False, na=False, regex=True)]
print(f"\nFound {len(amoralism_subcat)} paragraphs with 'Amoralismus & moralischer Nihilismus'")
print("\nFirst few matches:")
print(amoralism_subcat[['paragraph_num', 'type', 'category', 'subcategory', 'text']].head().to_string())

# Find quotes under this subcategory
amoralism_quotes = data[(data['subcategory'].str.contains('Amoralismus', case=False, na=False)) & 
                        (data['type'] == 'quote')]
print(f"\n\nQuotes under Amoralismus subcategory: {len(amoralism_quotes)}")

if len(amoralism_quotes) > 0:
    print("\nFirst 5 quotes:")
    for idx, row in amoralism_quotes.head(5).iterrows():
        level = int(row['quote_level']) if pd.notna(row['quote_level']) else 0
        indent = "  " * (level - 1) if level > 0 else ""
        marker = row['quote_marker'] if pd.notna(row['quote_marker']) else '?'
        text_preview = row['quote_text'][:80] if pd.notna(row['quote_text']) else ''
        print(f"\n{indent}Level {level}, Marker: {marker}")
        print(f"{indent}Text: {text_preview}...")
        if row['has_citation']:
            print(f"{indent}Citation: [{row['citation_author']}, \"{row['citation_title']}\"]")

# Check quote hierarchy
print("\n" + "=" * 80)
print("QUOTE HIERARCHY CHECK")
print("=" * 80)
if len(amoralism_quotes) > 0:
    level_counts = amoralism_quotes['quote_level'].value_counts().sort_index()
    print("\nQuote levels in Amoralismus subcategory:")
    for level, count in level_counts.items():
        print(f"  Level {int(level)}: {count} quotes")

# Check if we can find the specific quotes mentioned
print("\n" + "=" * 80)
print("LOOKING FOR SPECIFIC QUOTES MENTIONED")
print("=" * 80)

specific_text = "Moral nihilism, or amoralism, is the view"
found_quote = data[data['quote_text'].str.contains(specific_text, case=False, na=False)]
if len(found_quote) > 0:
    print(f"\nFound the first quote: 'Moral nihilism, or amoralism...'")
    row = found_quote.iloc[0]
    print(f"  Category: {row['category']}")
    print(f"  Subcategory: {row['subcategory']}")
    print(f"  Level: {row['quote_level']}")
    print(f"  Has citation: {row['has_citation']}")
else:
    print(f"\nFirst quote NOT FOUND in data")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total paragraphs loaded: {len(data)}")
print(f"Categories: {len(categories)}")
print(f"Subcategories: {len(data[data['type'] == 'subcategory'])}")
print(f"Quotes: {len(data[data['type'] == 'quote'])}")
print(f"ToC entries: {len(data[data['type'] == 'toc'])}")
