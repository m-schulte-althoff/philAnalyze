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

### Updating an existing vault

Choose the mode with `REBUILD_OBSIDIAN` in `main.py`:

- `False` (default): update the existing `output/obsidian` vault incrementally.
- `True`: build from scratch in a new `output/obsidian-fresh-*` folder on each
  run, leaving the existing vault intact. The log prints the new vault's absolute
  path. Open that folder in Obsidian; it will need initial indexing and has no
  copied Obsidian settings or personal notes.

With `USE_TEST_PHIL = True`, these folders are under `output/test` instead.
Switching back to `False` updates `output/obsidian` again, not the fresh copy.

Run `uv run python main.py` as usual and keep using the same `output/obsidian`
vault in Obsidian. Export is incremental by default: identical Markdown files
keep their contents and modification times. Only new or changed notes and MOCs
are written. Creation dates are preserved; timestamps alone never trigger writes.
The log reports created, updated, unchanged, deleted, and conflicted file counts.

The hidden `.philanalyze-manifest.json` records generated files and their hashes.
On subsequent full exports, obsolete tracked files are removed when entries are
deleted, renamed, or moved. Untracked files and `.obsidian` settings are left
alone. Locally edited tracked files are preserved and reported as conflicts;
resolve these manually (back up your annotations, then remove the conflicting
generated file to allow its regeneration). Do not delete the manifest routinely.

The first run against an older vault establishes this tracking baseline. Matching
files are adopted without rewriting. Existing files at generated destinations
are still updated from Phil.odt on this first run, so back up any annotations
made in those files beforehand. Historical stale files that are not part of the
current export are not adopted or removed.

Phil.odt is still fully parsed and Markdown is compared on every run. IDs,
paragraph numbers, and page metadata come from document order: insertions or
reordering can therefore change many later notes. This is file-level incremental
export, not persistent source-entry identity. Partial exports never delete
excluded files, but their MOCs describe only the selected entries; use a separate
test vault when sampling a document.

Obsidian [automatically refreshes external file changes and maintains its metadata
cache](https://obsidian.md/help/data-storage). Keep the existing vault open, or
reopen that same vault after export; no cache rebuild or Python indexing step is
needed. The pipeline does not write Obsidian's internal index. A new vault still
needs its initial indexing pass.

### Basic Export

```python
from data_model import load_odt_data, preprocess_philosophical_data
from obsidian_export import export_to_markdown

# Keep bookmark metadata and link positions through the in-memory pipeline.
df = preprocess_philosophical_data(load_odt_data('data/Phil.odt'))

# Export to Obsidian vault
stats = export_to_markdown(df, 'output/obsidian_vault')

# View statistics
print(f"Files created: {stats['files_created']}")
print(f"MOCs created: {stats['mocs_created']}")
print(f"Resolved internal links: {stats['resolved_internal_links']}")
print(f"Unresolved internal links: {stats['unresolved_internal_links']}")
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
- `links`: Native list of link dictionaries (`text`, `url`, `type`, `start`, `end`); JSON arrays are also accepted
- `has_citation`: Boolean flag
- `has_links`: Boolean flag

## Internal ODT links

Actual ODT hyperlinks are preserved inline, regardless of whether they follow
`(vgl.)`, `(Vgl.)`, `Vgl.`, or other wording. Unlinked mentions stay unlinked.
Nested spans contribute their complete visible text; source font styling is not
translated to Markdown. Link positions distinguish linked words from identical
unlinked words, including in merged continuation paragraphs.

Bookmarks on subcategory headings resolve to the actual exported MOC path:
`[[Wirtschaft/Analogien/_MOC - Analogien|Analogien]]`. The same destination mapping
is used in each entry's Links section and in MOC related-category lists. External
hyperlinks remain Markdown links. Categories without entries also get MOCs.
Filename collisions stop the export before files are written.

The loader retains heading/bookmark metadata in `DataFrame.attrs['sections']`,
non-heading bookmarks in `other_bookmarks`, and the sampling flag in
`partial_export`. Preprocessing preserves these attributes. Use the in-memory
ODT pipeline above: plain CSV round-trips do **not** preserve these attributes.
Existing JSON link arrays can still be rendered, but internal targets require
bookmark metadata and inline placement requires offsets relative to `text`.
The exporter does not guess targets from labels or category names.

Missing, ambiguous, non-category, or unavailable targets remain visible text.
`stats['warnings']` identifies each source entry and original target. Sampling
can leave forward targets outside the export; these are reported as missing or
excluded from the partial export. `resolved_internal_links` and
`unresolved_internal_links` count source link occurrences in exported entries,
not duplicated renderings in Links/MOC sections. `total_links` is the resolved
internal-link count. Navigation links in the source table of contents are not
included in these counts. Entries without a category/subcategory cannot be placed
in the existing folder structure; `skipped_entries` and a warning with their IDs
make this existing export limitation explicit.

To check the conversion without touching an existing vault, export into a
`tempfile.TemporaryDirectory()`. The integration tests construct a small real
ODT fixture and exercise extraction through final Markdown output:

```bash
.venv/bin/python -m pytest tests/test_internal_links.py
```

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
    'mocs_created': 7,        # Newly created MOCs (included in files_created)
    'files_updated': 2,      # Existing Markdown files rewritten
    'files_unchanged': 100,  # Files whose modification times were preserved
    'files_deleted': 1,     # Obsolete tracked files removed
    'files_conflicted': 0,  # Locally edited tracked files preserved
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
