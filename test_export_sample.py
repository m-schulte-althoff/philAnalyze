#!/usr/bin/env python3
"""Test the Obsidian export with actual sample data."""

import pandas as pd
from obsidian_export import export_to_markdown
from pathlib import Path

# Load the sample preprocessed data
df = pd.read_csv('output/test/preprocessed_data.csv')

print(f"Loaded {len(df)} entries from preprocessed_data.csv")
print(f"\nData types breakdown:")
print(df['type'].value_counts())

print(f"\nCategories:")
print(df['category'].value_counts())

# Export to Obsidian format
output_dir = 'output/obsidian_test'
print(f"\nExporting to {output_dir}...")

stats = export_to_markdown(df, output_dir)

print("\n=== Export Statistics ===")
print(f"Files created: {stats['files_created']}")
print(f"MOCs created: {stats['mocs_created']}")
print(f"Total links: {stats['total_links']}")

if stats['errors']:
    print(f"\nErrors ({len(stats['errors'])}):")
    for error in stats['errors']:
        print(f"  - {error}")

if stats['warnings']:
    print(f"\nWarnings ({len(stats['warnings'])}):")
    for warning in stats['warnings'][:10]:  # Show first 10
        print(f"  - {warning}")
    if len(stats['warnings']) > 10:
        print(f"  ... and {len(stats['warnings']) - 10} more")

# Check the output structure
output_path = Path(output_dir)
if output_path.exists():
    print(f"\n=== Output Structure ===")
    categories = [d for d in output_path.iterdir() if d.is_dir()]
    print(f"Categories: {len(categories)}")
    
    for cat in sorted(categories)[:3]:  # Show first 3
        subcats = [d for d in cat.iterdir() if d.is_dir()]
        print(f"\n{cat.name}/ ({len(subcats)} subcategories)")
        for subcat in sorted(subcats)[:2]:  # Show first 2
            files = list(subcat.glob('*.md'))
            moc_files = [f for f in files if f.name.startswith('_MOC')]
            entry_files = [f for f in files if not f.name.startswith('_MOC')]
            print(f"  {subcat.name}/ ({len(files)} files: {len(moc_files)} MOC, {len(entry_files)} entries)")

print("\n✅ Export complete!")
