"""Debug script to check what's being parsed."""
import data_model

# Load sample data
data = data_model.load_odt_data('data/Phil.odt', max_pages=100)

print("Type counts:")
print(data['type'].value_counts())
print(f"\nTotal records: {len(data)}")

print("\n\nSample paragraphs:")
for i in range(min(20, len(data))):
    row = data.iloc[i]
    text_preview = row['text'][:100].replace('\n', ' ')
    print(f"{i}: [{row['type']:12s}] Level={row['quote_level']} Marker={row['quote_marker']} | {text_preview}...")

print("\n\nLooking for quotes (checking for tab indentation):")
for i in range(len(data)):
    text = data.iloc[i]['text']
    if text.startswith('\t') or text.startswith('    '):
        print(f"{i}: Indented text: '{text[:80]}'")
        if i < 5:  # Show first 5
            break
