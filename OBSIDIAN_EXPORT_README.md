# Obsidian Export Module - Documentation

## Overview

The Obsidian Export module transforms preprocessed philosophical notes from a DataFrame into an Obsidian-compatible markdown vault with hierarchical folder structure, Map of Content (MOC) notes, and proper interlinking.

## Features

- ✅ **Hierarchical Folder Structure**: Organizes notes by Category/Subcategory/
- ✅ **YAML Frontmatter**: Rich metadata for each note including type, citations, tags
- ✅ **Quote Notes**: Formatted with citations, quote levels, and parent references
- ✅ **Reference Notes**: External work references with links
- ✅ **Personal Notes**: Own observations and thoughts
- ✅ **Map of Content (MOC)**: Auto-generated index notes for each subcategory
- ✅ **Link Conversion**: Internal wikilinks and external markdown links
- ✅ **Quote Hierarchy**: Preserves nested quote relationships
- ✅ **Data Validation**: Comprehensive error checking and reporting
- ✅ **Safe Filenames**: Sanitizes names for cross-platform compatibility

## Usage

### Basic Export

```python
import pandas as pd
from obsidian_export import export_to_markdown

# Load preprocessed data
df = pd.read_csv('output/test/preprocessed_data.csv')

# Export to Obsidian vault
stats = export_to_markdown(df, 'output/obsidian_vault')

# View statistics
print(f"Files created: {stats['files_created']}")
print(f"MOCs created: {stats['mocs_created']}")
print(f"Total links: {stats['total_links']}")
```

### Using the Class Directly

```python
from obsidian_export import ObsidianExporter

exporter = ObsidianExporter('output/obsidian_vault')
stats = exporter.export_to_markdown(df)

# Check for errors
if stats['errors']:
    for error in stats['errors']:
        print(f"Error: {error}")

# Check for warnings
if stats['warnings']:
    for warning in stats['warnings']:
        print(f"Warning: {warning}")
```

## Input Data Schema

The module expects a pandas DataFrame with the following columns:

### Required Columns
- `id`: Unique identifier for each entry
- `category`: Top-level category name
- `subcategory`: Second-level category name
- `type`: Entry type ('quote', 'reference', or null/other for notes)
- `text`: Main content text

### Optional Columns
- `paragraph_num`: Original paragraph number
- `page`: Source page number
- `word_count`: Word count
- `quote_level`: Nesting depth for quotes (1.0, 2.0, etc.)
- `higherLevelQuoteRef`: ID of parent quote
- `quote_marker`: Quote marker symbol (~, °, etc.)
- `quote_text`: Extracted quote text
- `citation_author`: Author name
- `citation_title`: Work title
- `citation_source`: Publication source
- `citation_raw`: Full citation string
- `links`: JSON array of link objects
- `has_citation`: Boolean flag
- `has_links`: Boolean flag

## Output Structure

```
output/obsidian_vault/
├── Category 1/
│   ├── Subcategory A/
│   │   ├── _MOC - Subcategory A.md
│   │   ├── Quote - Author - Title (id-13).md
│   │   ├── Quote - Author - Title (id-14).md
│   │   └── Reference - Topic (id-52).md
│   └── Subcategory B/
│       └── _MOC - Subcategory B.md
└── Category 2/
    └── ...
```

## File Formats

### Quote Note Example

```markdown
---
type: quote
category: Psychology
subcategory: Psychoanalysis
id: 11
quote_level: 1.0
citation:
  author: Carl Jung
  title: Psychology and Religion
tags:
  - psychoanalysis
  - carl jung
created: 2025-10-13
---

# Quote: Carl Jung - Psychology and Religion

> The shadow is a moral problem that challenges the whole ego-personality...

## Citation

**Author:** [[Carl Jung]]
**Title:** *Psychology and Religion*
**Full Citation:** Carl Jung, "Psychology and Religion"

## Context

- **Category:** [[Psychology]]
- **Subcategory:** [[Psychoanalysis]]
- **Quote Level:** 1.0
```

### MOC Note Example

```markdown
---
type: moc
category: Psychology
subcategory: Psychoanalysis
entry_count: 15
---

# Map of Content: Psychoanalysis

**Category:** [[Psychology]]
**Total Entries:** 15

## Quotes (12)

- [[Quote - Jung - Psychology (id-11)]] — The shadow is a moral problem...
- [[Quote - Freud - The Unconscious (id-12)]] — The unconscious is the...

## References (2)

- [[Reference - Modern psychoanalytic theory (id-50)]]

## Notes (1)

- [[Note - Thoughts on shadow work (id-99)]]
```

## Validation

The module performs comprehensive validation:

1. **DataFrame Structure**: Checks for required columns
2. **ID Uniqueness**: Ensures no duplicate IDs
3. **Internal Links**: Validates that linked subcategories exist
4. **Data Types**: Handles missing values and type conversions

Validation results are included in the statistics output.

## Testing

Run the comprehensive test suite:

```bash
conda run -n llmStuff python -m pytest tests/test_obsidian_export.py -v
```

Test coverage includes:
- 42 unit tests covering all methods
- Edge case handling (empty data, special characters, Unicode)
- Integration tests with complete workflow
- File system operations
- Link conversion and validation

## Statistics Tracking

The export function returns detailed statistics:

```python
{
    'files_created': 57,      # Total markdown files created
    'mocs_created': 7,        # Number of MOC files
    'total_links': 23,        # Total internal links created
    'errors': [],             # List of error messages
    'warnings': []            # List of warning messages
}
```

## Implementation Details

### File Naming Convention

Files are named using a sanitized format:
- Quotes: `Quote - {Author} - {Title} (id-{id}).md`
- References: `Reference - {snippet} (id-{id}).md`
- Notes: `Note - {snippet} (id-{id}).md`
- MOCs: `_MOC - {Subcategory}.md`

The underscore prefix on MOC files ensures they appear first when sorted alphabetically.

### Link Handling

The module converts links from JSON format:

```python
# Internal link (wikilink format)
{"text": "Death", "url": "#Death", "type": "internal"}
→ [[Death]]

# External link (markdown format)
{"text": "Article", "url": "https://example.com", "type": "external"}
→ [Article](https://example.com)
```

### Quote Hierarchy

Nested quotes are tracked via:
1. `quote_level`: Depth level (1.0, 2.0, 3.0, etc.)
2. `higherLevelQuoteRef`: ID of parent quote

This creates a hierarchical structure in MOCs:
```
- Level 1 Quote
  - Level 2 Nested Quote
    - Level 3 Nested Quote
```

## Compatibility

- **Python**: 3.8+
- **Required Packages**: pandas, pathlib, json, logging
- **Obsidian**: Compatible with Obsidian v1.0+
- **Operating Systems**: Cross-platform (Windows, macOS, Linux)

## Error Handling

The module gracefully handles:
- Missing optional fields (uses defaults)
- Invalid JSON in links (reports warning)
- Invalid characters in filenames (sanitizes)
- Malformed citations (uses available data)
- Empty or null values (appropriate fallbacks)

## Future Enhancements

Potential improvements:
- Tag generation from content analysis
- Backlink graph optimization
- Export to Zotero/BibTeX format
- Batch processing for large datasets
- Custom templates for different note types
- Dataview query integration

## License

Part of the philAnalyze project.

## Support

For issues or questions, see the main project README or create an issue in the repository.
