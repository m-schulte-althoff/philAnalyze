"""Quick check for category structure."""
import data_model

# Load limited data first
data = data_model.load_odt_data('data/Phil.odt', max_pages=500)

print("Data types:")
print(data['type'].value_counts())

print("\n\nSearching for 'Ethik' category...")
ethik = data[data['text'].str.contains('Ethik', case=False, na=False)]
print(f"Found {len(ethik)} paragraphs with 'Ethik'")
print("\nFirst 10:")
for _, row in ethik.head(10).iterrows():
    print(f"[{row['paragraph_num']}] Type: {row['type']:12s} | {row['text'][:60]}")

print("\n\nSearching for 'Amoralismus' subcategory...")
amoral = data[data['text'].str.contains('Amoralismus', case=False, na=False)]
print(f"Found {len(amoral)} paragraphs with 'Amoralismus'")
for _, row in amoral.head(5).iterrows():
    print(f"[{row['paragraph_num']}] Type: {row['type']:12s} | Cat: {row['category']} | {row['text'][:60]}")

print("\n\nQuotes in Amoralismus subcategory:")
amoral_quotes = data[(data['subcategory'].str.contains('Amoralismus', case=False, na=False)) & 
                     (data['type'] == 'quote')]
print(f"Total: {len(amoral_quotes)}")
for _, row in amoral_quotes.head(5).iterrows():
    print(f"Level {row['quote_level']}: {row['quote_text'][:70]}...")
