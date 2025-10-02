"""Test script to verify tab and marker detection works correctly."""
from data_model import detect_quote_level

# Test cases matching your example: (text, expected_level, expected_marker)
test_cases = [
    ("Ökologie & Klima", None, None),  # Subcategory header, no tabs
    ("\t° Vgl. Kapital, class action lawsuit", 1, "°"),  # 1 tab, ° marker
    ("\t~ Andrew Bryant can still remember when he thought...", 1, "~"),  # 1 tab, ~ marker
    ("\t\t~ Now lots of Bryant's clients wanted to talk...", 2, "~"),  # 2 tabs, ~ marker
    ("    ° Text with 4 spaces instead of 1 tab", 1, "°"),  # 4 spaces = 1 tab
    ("        ~ Text with 8 spaces (2 tabs worth)", 2, "~"),  # 8 spaces = 2 tabs
]

print("Testing quote level detection:")
print("=" * 80)

for text, expected_level, expected_marker in test_cases:
    level, marker, content = detect_quote_level(text)
    status = "✓" if (level == expected_level and marker == expected_marker) else "✗"
    
    # Display tabs and spaces clearly
    display_text = text.replace('\t', '[TAB]').replace('    ', '[4SP]')
    
    print(f"\n{status} Input: {display_text[:60]}")
    print(f"  Expected: level={expected_level}, marker={expected_marker}")
    print(f"  Got:      level={level}, marker={marker}")

print("\n" + "=" * 80)
print("\nConclusion:")
print("If all tests show ✓, the detection logic is working correctly.")
print("The issue is that the Phil.odt file in data/ doesn't contain the")
print("hierarchical structure yet, or we're analyzing a different file.")
