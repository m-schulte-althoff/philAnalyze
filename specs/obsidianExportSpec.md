# PhilAnalyze Obsidian Export: Comprehensive Implementation Specification

## 1. Executive Summary

Transform a 5000-page philosophical notebook from ODT format into a structured Obsidian vault with hierarchical folders, Map of Content (MOC) notes, and proper interlinking.

## 2. Project Requirements

### 2.1 Functional Requirements

**Must Have:**
- Export preprocessed DataFrame to Obsidian-compatible markdown files
- Create folder hierarchy: `Category/Subcategory/`
- Generate Map of Content (MOC) notes for each subcategory
- Preserve internal links between subcategories
- Include citation metadata in quote notes
- Support all entry types: quote, reference, own notes

**Should Have:**
- YAML frontmatter for metadata
- Citation formatting using markdown/dataview syntax
- Hierarchical quote levels (quote trees)
- Link validation and error reporting

**Nice to Have:**
- Tag generation from categories
- Backlink graph optimization
- Citation export for reference managers

### 2.2 Input Data Schema

From preprocessed_data.csv:

```
paragraph_num, text, type, category, subcategory, quote_level, 
higherLevelQuoteRef, quote_marker, quote_text, citation_author, 
citation_title, citation_source, citation_raw, links, page, 
length, id, word_count, has_citation, has_links
```

**Key Fields:**
- `type`: quote | reference | (null/other for own notes)
- `category`: Top-level folder name
- `subcategory`: Second-level folder name
- `quote_level`: Nesting depth for quotes
- `links`: JSON array of `{text, url, type: internal|external}`

## 3. Architecture Design

### 3.1 Output Directory Structure

```
output/obsidian/
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

### 3.2 File Naming Convention

```python
def generate_filename(row):
    """
    Quote: "Quote - {author} - {title} (id-{id}).md"
    Reference: "Reference - {text[:50]} (id-{id}).md"
    Note: "Note - {text[:50]} (id-{id}).md"
    MOC: "_MOC - {subcategory}.md"
    """
    pass
```

### 3.3 Component Architecture

```python
# obsidian_export.py structure

class ObsidianExporter:
    def __init__(self, output_dir: str)
    def export_to_markdown(self, df: pd.DataFrame) -> dict
    def _create_folder_structure(self, df: pd.DataFrame)
    def _export_entry(self, row: pd.Series) -> str
    def _create_moc(self, category: str, subcategory: str, entries: list) -> str
    def _format_frontmatter(self, row: pd.Series) -> str
    def _format_citation(self, row: pd.Series) -> str
    def _convert_links(self, links_json: str) -> str
    def _sanitize_filename(self, text: str) -> str
```

## 4. Detailed Implementation Specifications

### 4.1 YAML Frontmatter Template

```yaml
---
type: quote|reference|note
category: Menschlich- & Soziales
subcategory: Psychoanalytik
id: 11
paragraph_num: 13
page: 1
word_count: 92
has_citation: true
has_links: false
quote_level: 1.0
higher_level_quote_ref: 14
citation:
  author: Carl Jung
  title: Psychology and Religion
  source: ""
  raw: Carl Jung, "Psychology and Religion"
tags:
  - psychoanalytik
  - jung
  - shadow
created: 2025-10-13
---
```

### 4.2 Quote Note Template

````markdown
---
[frontmatter]
---

# Quote: [Author] - [Title]

> [quote_text]

## Citation

**Author:** [[{citation_author}]]  
**Title:** *{citation_title}*  
**Source:** {citation_source}  
**Full Citation:** {citation_raw}

## Metadata

- **Type:** Quote
- **Marker:** {quote_marker}
- **Original Page:** {page}
- **Word Count:** {word_count}

## Context

- **Category:** [[{category}]]
- **Subcategory:** [[{subcategory}]]
- **Quote Level:** {quote_level}
{if higher_level_quote_ref}
- **Parent Quote:** [[Quote id-{higherLevelQuoteRef}]]
{endif}

## Links

{formatted_links}

---
*Generated from philAnalyze id: {id}*
````

### 4.3 Reference Note Template

````markdown
---
[frontmatter]
---

# Reference: {text[:80]}

{text}

## Links

{formatted_links}

---
*Category: [[{category}]] > [[{subcategory}]]*
````

### 4.4 Map of Content (MOC) Template

````markdown
---
type: moc
category: {category}
subcategory: {subcategory}
entry_count: {count}
tags:
  - moc
  - {subcategory_tag}
---

# Map of Content: {subcategory}

**Category:** [[{category}]]  
**Total Entries:** {count}

## Overview

This MOC organizes {count} entries related to {subcategory}.

## Quotes ({quote_count})

### Primary Sources (Level 1)

{for each level-1 quote}
- [[Quote - {author} - {title} (id-{id})]] — {snippet}
{endfor}

### Nested Quotes (Level 2+)

{hierarchical_quote_tree}

## References ({reference_count})

{for each reference}
- [[Reference - {snippet} (id-{id})]]
{endfor}

## Notes ({note_count})

{for each note}
- [[Note - {snippet} (id-{id})]]
{endfor}

## Related Subcategories

{internal_links_to_other_subcategories}

---
*Generated: {timestamp}*
````

### 4.5 Link Conversion Logic

```python
def _convert_links(self, links_json: str) -> str:
    """
    Input: '[{"text": "Tod", "url": "#Tod", "type": "internal"}]'
    
    Output for internal: "- [[Tod]]"
    Output for external: "- [What Makes Us Happy?](https://...)"
    """
    if pd.isna(links_json) or links_json == '[]':
        return "*No links*"
    
    links = json.loads(links_json)
    formatted = []
    
    for link in links:
        if link['type'] == 'internal':
            # Remove '#' and create wikilink
            target = link['url'].replace('#', '')
            formatted.append(f"- [[{target}]]")
        else:
            text = link['text'] or link['url']
            formatted.append(f"- [{text}]({link['url']})")
    
    return '\n'.join(formatted)
```

### 4.6 Quote Hierarchy Construction

```python
def _build_quote_tree(self, df: pd.DataFrame, subcategory: str) -> str:
    """
    Build hierarchical structure for nested quotes using quote_level and higherLevelQuoteRef.
    
    Example output:
    - [[Quote id-14]] (Level 1)
      - [[Quote id-15]] (Level 2)
        - [[Quote id-16]] (Level 3)
    """
    subset = df[(df['subcategory'] == subcategory) & (df['type'] == 'quote')]
    
    # Group by quote_level
    tree = []
    for level in sorted(subset['quote_level'].unique()):
        quotes_at_level = subset[subset['quote_level'] == level]
        indent = '  ' * int(level - 1)
        
        for _, row in quotes_at_level.iterrows():
            author = row.get('citation_author', 'Unknown')
            title = row.get('citation_title', 'Untitled')
            tree.append(f"{indent}- [[Quote - {author} - {title} (id-{row['id']})]]")
    
    return '\n'.join(tree)
```

## 5. Error Handling & Validation

### 5.1 Input Validation

```python
def validate_dataframe(df: pd.DataFrame) -> list[str]:
    """Return list of validation errors."""
    errors = []
    
    required_cols = ['id', 'category', 'subcategory', 'type', 'text']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")
    
    # Check for duplicate IDs
    if df['id'].duplicated().any():
        errors.append("Duplicate IDs found")
    
    # Validate quote levels
    invalid_levels = df[df['quote_level'] < 1.0]
    if len(invalid_levels) > 0:
        errors.append(f"{len(invalid_levels)} entries with invalid quote_level < 1")
    
    return errors
```

### 5.2 File System Safety

```python
def _sanitize_filename(self, text: str, max_length: int = 100) -> str:
    """
    Remove invalid filename characters and limit length.
    
    Invalid: / \ : * ? " < > |
    """
    # Replace invalid chars with dash
    text = re.sub(r'[/\\:*?"<>|]', '-', text)
    
    # Remove multiple dashes
    text = re.sub(r'-+', '-', text)
    
    # Trim and limit length
    text = text.strip('-')[:max_length]
    
    return text
```

### 5.3 Link Validation

```python
def _validate_internal_links(self, df: pd.DataFrame) -> list[str]:
    """Check that all internal links point to existing subcategories."""
    warnings = []
    
    all_subcategories = set(df['subcategory'].dropna().unique())
    
    for idx, row in df.iterrows():
        if pd.notna(row['links']) and row['links'] != '[]':
            links = json.loads(row['links'])
            for link in links:
                if link['type'] == 'internal':
                    target = link['url'].replace('#', '')
                    if target not in all_subcategories:
                        warnings.append(
                            f"Row {idx} (id-{row['id']}): "
                            f"Link to non-existent subcategory '{target}'"
                        )
    
    return warnings
```

## 6. Implementation Code

### 6.1 Main Export Function

```python
"""
Obsidian Export Module for philAnalyze.

Transforms preprocessed philosophical notes DataFrame into 
Obsidian-compatible markdown vault with hierarchical structure.
"""

import os
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd


class ObsidianExporter:
    """Export philAnalyze data to Obsidian markdown vault."""
    
    def __init__(self, output_dir: str):
        """
        Initialize exporter.
        
        Args:
            output_dir: Base directory for Obsidian vault export
        """
        self.output_dir = Path(output_dir)
        self.stats = {
            'files_created': 0,
            'folders_created': 0,
            'mocs_created': 0,
            'errors': [],
            'warnings': []
        }
        
    def export_to_markdown(self, df: pd.DataFrame) -> Dict:
        """
        Main export orchestration function.
        
        Args:
            df: Preprocessed philAnalyze DataFrame
            
        Returns:
            dict: Export statistics
        """
        logging.info("Starting Obsidian export...")
        
        # Validate input
        errors = self._validate_dataframe(df)
        if errors:
            self.stats['errors'].extend(errors)
            logging.error(f"Validation failed: {errors}")
            return self.stats
        
        # Check for link issues (warnings only)
        warnings = self._validate_internal_links(df)
        if warnings:
            self.stats['warnings'].extend(warnings)
            logging.warning(f"Found {len(warnings)} link warnings")
        
        # Create folder structure
        self._create_folder_structure(df)
        
        # Group by subcategory for MOC creation
        grouped = df.groupby(['category', 'subcategory'])
        
        for (category, subcategory), group in grouped:
            # Create subcategory folder
            subcategory_path = self.output_dir / category / subcategory
            subcategory_path.mkdir(parents=True, exist_ok=True)
            self.stats['folders_created'] += 1
            
            # Export individual entries
            for _, row in group.iterrows():
                self._export_entry(row, subcategory_path)
            
            # Create MOC
            self._create_moc(category, subcategory, group, subcategory_path)
        
        logging.info(f"Export complete: {self.stats}")
        return self.stats
    
    def _validate_dataframe(self, df: pd.DataFrame) -> List[str]:
        """Validate input DataFrame structure."""
        errors = []
        
        required_cols = ['id', 'category', 'subcategory', 'type', 'text']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            errors.append(f"Missing required columns: {missing}")
        
        if 'id' in df.columns and df['id'].duplicated().any():
            errors.append("Duplicate IDs found in DataFrame")
        
        return errors
    
    def _validate_internal_links(self, df: pd.DataFrame) -> List[str]:
        """Check internal link validity."""
        warnings = []
        all_subcategories = set(df['subcategory'].dropna().unique())
        
        for idx, row in df.iterrows():
            if pd.notna(row.get('links')) and row['links'] != '[]':
                try:
                    links = json.loads(row['links'])
                    for link in links:
                        if link.get('type') == 'internal':
                            target = link['url'].replace('#', '')
                            if target not in all_subcategories:
                                warnings.append(
                                    f"ID {row['id']}: Link to non-existent '{target}'"
                                )
                except json.JSONDecodeError:
                    warnings.append(f"ID {row['id']}: Invalid JSON in links field")
        
        return warnings
    
    def _create_folder_structure(self, df: pd.DataFrame):
        """Create category and subcategory folders."""
        for category in df['category'].dropna().unique():
            category_path = self.output_dir / category
            category_path.mkdir(parents=True, exist_ok=True)
    
    def _export_entry(self, row: pd.Series, subcategory_path: Path):
        """Export individual entry to markdown file."""
        entry_type = row.get('type', 'note')
        
        # Generate filename
        if entry_type == 'quote':
            author = row.get('citation_author', 'Unknown')
            title = row.get('citation_title', 'Untitled')
            filename = f"Quote - {author} - {title} (id-{row['id']}).md"
        elif entry_type == 'reference':
            snippet = row['text'][:50] if pd.notna(row['text']) else 'Reference'
            filename = f"Reference - {snippet} (id-{row['id']}).md"
        else:
            snippet = row['text'][:50] if pd.notna(row['text']) else 'Note'
            filename = f"Note - {snippet} (id-{row['id']}).md"
        
        filename = self._sanitize_filename(filename)
        filepath = subcategory_path / filename
        
        # Generate content
        if entry_type == 'quote':
            content = self._create_quote_note(row)
        elif entry_type == 'reference':
            content = self._create_reference_note(row)
        else:
            content = self._create_note(row)
        
        # Write file
        filepath.write_text(content, encoding='utf-8')
        self.stats['files_created'] += 1
    
    def _create_quote_note(self, row: pd.Series) -> str:
        """Generate markdown for quote entry."""
        frontmatter = self._format_frontmatter(row)
        
        author = row.get('citation_author', 'Unknown')
        title = row.get('citation_title', 'Untitled')
        quote_text = row.get('quote_text', row.get('text', ''))
        
        # Citation block
        citation_block = self._format_citation(row)
        
        # Links
        links_block = self._convert_links(row.get('links', '[]'))
        
        # Parent quote reference
        parent_ref = ""
        if pd.notna(row.get('higherLevelQuoteRef')):
            parent_ref = f"\n- **Parent Quote:** [[Quote id-{int(row['higherLevelQuoteRef'])}]]"
        
        content = f"""{frontmatter}

# Quote: {author} - {title}

> {quote_text}

## Citation

{citation_block}

## Metadata

- **Type:** Quote
- **Marker:** {row.get('quote_marker', '')}
- **Original Page:** {row.get('page', 'N/A')}
- **Word Count:** {row.get('word_count', 0)}

## Context

- **Category:** [[{row.get('category', '')}]]
- **Subcategory:** [[{row.get('subcategory', '')}]]
- **Quote Level:** {row.get('quote_level', 1.0)}{parent_ref}

## Links

{links_block}

---
*Generated from philAnalyze id: {row['id']}*
"""
        return content
    
    def _create_reference_note(self, row: pd.Series) -> str:
        """Generate markdown for reference entry."""
        frontmatter = self._format_frontmatter(row)
        text = row.get('text', '')
        links_block = self._convert_links(row.get('links', '[]'))
        
        content = f"""{frontmatter}

# Reference: {text[:80]}

{text}

## Links

{links_block}

---
*Category: [[{row.get('category', '')}]] > [[{row.get('subcategory', '')}]]*
*ID: {row['id']}*
"""
        return content
    
    def _create_note(self, row: pd.Series) -> str:
        """Generate markdown for general note."""
        frontmatter = self._format_frontmatter(row)
        text = row.get('text', '')
        links_block = self._convert_links(row.get('links', '[]'))
        
        content = f"""{frontmatter}

# {text[:80]}

{text}

## Links

{links_block}

---
*Category: [[{row.get('category', '')}]] > [[{row.get('subcategory', '')}]]*
*ID: {row['id']}*
"""
        return content
    
    def _create_moc(self, category: str, subcategory: str, 
                    group: pd.DataFrame, subcategory_path: Path):
        """Create Map of Content for subcategory."""
        moc_filename = f"_MOC - {subcategory}.md"
        moc_path = subcategory_path / moc_filename
        
        # Count by type
        quote_count = len(group[group['type'] == 'quote'])
        ref_count = len(group[group['type'] == 'reference'])
        note_count = len(group) - quote_count - ref_count
        
        # Build quote tree
        quote_tree = self._build_quote_tree(group)
        
        # Build reference list
        ref_list = self._build_reference_list(group)
        
        # Build note list
        note_list = self._build_note_list(group)
        
        # Find related subcategories from internal links
        related = self._find_related_subcategories(group)
        
        # Frontmatter
        frontmatter = f"""---
type: moc
category: {category}
subcategory: {subcategory}
entry_count: {len(group)}
quote_count: {quote_count}
reference_count: {ref_count}
note_count: {note_count}
tags:
  - moc
  - {self._sanitize_filename(subcategory.lower())}
created: {datetime.now().strftime('%Y-%m-%d')}
---"""
        
        content = f"""{frontmatter}

# Map of Content: {subcategory}

**Category:** [[{category}]]  
**Total Entries:** {len(group)}

## Overview

This MOC organizes {len(group)} entries related to {subcategory}.

## Quotes ({quote_count})

{quote_tree}

## References ({ref_count})

{ref_list}

## Notes ({note_count})

{note_list}

## Related Subcategories

{related}

---
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        moc_path.write_text(content, encoding='utf-8')
        self.stats['mocs_created'] += 1
    
    def _build_quote_tree(self, group: pd.DataFrame) -> str:
        """Build hierarchical quote structure."""
        quotes = group[group['type'] == 'quote'].copy()
        
        if len(quotes) == 0:
            return "*No quotes in this subcategory*"
        
        # Sort by quote_level, then id
        quotes = quotes.sort_values(['quote_level', 'id'])
        
        lines = []
        for _, row in quotes.iterrows():
            level = int(row.get('quote_level', 1)) - 1
            indent = '  ' * level
            
            author = row.get('citation_author', 'Unknown')
            title = row.get('citation_title', 'Untitled')[:40]
            snippet = row.get('quote_text', row.get('text', ''))[:60]
            
            lines.append(
                f"{indent}- [[Quote - {author} - {title} (id-{row['id']})]] "
                f"— {snippet}..."
            )
        
        return '\n'.join(lines)
    
    def _build_reference_list(self, group: pd.DataFrame) -> str:
        """Build reference entry list."""
        refs = group[group['type'] == 'reference']
        
        if len(refs) == 0:
            return "*No references in this subcategory*"
        
        lines = []
        for _, row in refs.iterrows():
            snippet = row.get('text', 'Reference')[:60]
            lines.append(f"- [[Reference - {snippet} (id-{row['id']})]]")
        
        return '\n'.join(lines)
    
    def _build_note_list(self, group: pd.DataFrame) -> str:
        """Build note entry list."""
        notes = group[~group['type'].isin(['quote', 'reference'])]
        
        if len(notes) == 0:
            return "*No notes in this subcategory*"
        
        lines = []
        for _, row in notes.iterrows():
            snippet = row.get('text', 'Note')[:60]
            lines.append(f"- [[Note - {snippet} (id-{row['id']})]]")
        
        return '\n'.join(lines)
    
    def _find_related_subcategories(self, group: pd.DataFrame) -> str:
        """Extract related subcategories from internal links."""
        related = set()
        
        for _, row in group.iterrows():
            if pd.notna(row.get('links')) and row['links'] != '[]':
                try:
                    links = json.loads(row['links'])
                    for link in links:
                        if link.get('type') == 'internal':
                            target = link['url'].replace('#', '')
                            related.add(target)
                except json.JSONDecodeError:
                    continue
        
        if not related:
            return "*No related subcategories found*"
        
        return '\n'.join([f"- [[{sub}]]" for sub in sorted(related)])
    
    def _format_frontmatter(self, row: pd.Series) -> str:
        """Generate YAML frontmatter."""
        entry_type = row.get('type', 'note')
        
        # Base fields
        yaml = {
            'type': entry_type,
            'category': row.get('category', ''),
            'subcategory': row.get('subcategory', ''),
            'id': int(row['id']),
            'paragraph_num': int(row.get('paragraph_num', 0)),
            'page': int(row.get('page', 0)),
            'word_count': int(row.get('word_count', 0)),
            'has_citation': bool(row.get('has_citation', False)),
            'has_links': bool(row.get('has_links', False))
        }
        
        # Quote-specific fields
        if entry_type == 'quote':
            yaml['quote_level'] = float(row.get('quote_level', 1.0))
            if pd.notna(row.get('higherLevelQuoteRef')):
                yaml['higher_level_quote_ref'] = int(row['higherLevelQuoteRef'])
        
        # Citation
        if pd.notna(row.get('citation_author')):
            yaml['citation'] = {
                'author': row.get('citation_author', ''),
                'title': row.get('citation_title', ''),
                'source': row.get('citation_source', ''),
                'raw': row.get('citation_raw', '')
            }
        
        # Tags
        tags = ['philanalyze']
        if pd.notna(row.get('subcategory')):
            tags.append(self._sanitize_filename(row['subcategory'].lower()))
        yaml['tags'] = tags
        
        yaml['created'] = datetime.now().strftime('%Y-%m-%d')
        
        # Convert to YAML string
        lines = ['---']
        for key, value in yaml.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for subkey, subval in value.items():
                    lines.append(f"  {subkey}: {subval}")
            elif isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {value}")
        lines.append('---')
        
        return '\n'.join(lines)
    
    def _format_citation(self, row: pd.Series) -> str:
        """Format citation block."""
        author = row.get('citation_author', '')
        title = row.get('citation_title', '')
        source = row.get('citation_source', '')
        raw = row.get('citation_raw', '')
        
        lines = []
        if author:
            lines.append(f"**Author:** [[{author}]]")
        if title:
            lines.append(f"**Title:** *{title}*")
        if source:
            lines.append(f"**Source:** {source}")
        if raw:
            lines.append(f"**Full Citation:** {raw}")
        
        return '\n'.join(lines) if lines else "*No citation available*"
    
    def _convert_links(self, links_json: str) -> str:
        """Convert links JSON to markdown."""
        if pd.isna(links_json) or links_json == '[]':
            return "*No links*"
        
        try:
            links = json.loads(links_json)
        except json.JSONDecodeError:
            return "*Invalid link data*"
        
        formatted = []
        for link in links:
            if link.get('type') == 'internal':
                target = link['url'].replace('#', '')
                formatted.append(f"- [[{target}]]")
            else:
                text = link.get('text') or link.get('url', 'Link')
                url = link.get('url', '')
                formatted.append(f"- [{text}]({url})")
        
        return '\n'.join(formatted) if formatted else "*No links*"
    
    def _sanitize_filename(self, text: str, max_length: int = 100) -> str:
        """Sanitize text for use in filenames."""
        # Remove/replace invalid characters
        text = re.sub(r'[/\\:*?"<>|]', '-', text)
        text = re.sub(r'-+', '-', text)
        text = text.strip('-. ')
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0]
        
        return text or 'untitled'


def export_to_markdown(df: pd.DataFrame, output_dir: str) -> Dict:
    """
    Main entry point for Obsidian export.
    
    Args:
        df: Preprocessed philAnalyze DataFrame
        output_dir: Output directory for Obsidian vault
        
    Returns:
        dict: Export statistics
    """
    exporter = ObsidianExporter(output_dir)
    return exporter.export_to_markdown(df)
```

## 7. Testing Strategy

### 7.1 Unit Tests

```python
# tests/test_obsidian_export.py

import pytest
import pandas as pd
from obsidian_export import ObsidianExporter

def test_filename_sanitization():
    exporter = ObsidianExporter('test_output')
    
    assert exporter._sanitize_filename('Valid Name') == 'Valid Name'
    assert exporter._sanitize_filename('Name: With* Invalid? Chars') == 'Name- With- Invalid- Chars'
    assert exporter._sanitize_filename('A' * 200, max_length=50) == 'A' * 50

def test_link_conversion():
    exporter = ObsidianExporter('test_output')
    
    # Internal link
    json_str = '[{"text": "Tod", "url": "#Tod", "type": "internal"}]'
    assert '[[Tod]]' in exporter._convert_links(json_str)
    
    # External link
    json_str = '[{"text": "Article", "url": "https://example.com", "type": "external"}]'
    assert '[Article](https://example.com)' in exporter._convert_links(json_str)

def test_quote_tree_building():
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'type': ['quote', 'quote', 'quote'],
        'quote_level': [1.0, 2.0, 3.0],
        'subcategory': ['Test', 'Test', 'Test'],
        'citation_author': ['A', 'B', 'C'],
        'citation_title': ['T1', 'T2', 'T3'],
        'text': ['Q1', 'Q2', 'Q3']
    })
    
    exporter = ObsidianExporter('test_output')
    tree = exporter._build_quote_tree(df)
    
    assert '[[Quote - A' in tree
    assert '  - [[Quote - B' in tree  # Level 2 indented
```

### 7.2 Integration Tests

Create test dataset with known structure and verify:
- All folders created
- MOC files contain correct links
- Quote hierarchy preserved
- Citation metadata present

### 7.3 Manual Testing Checklist

- [ ] Import into Obsidian and verify graph view
- [ ] Check that all internal links resolve
- [ ] Verify frontmatter is recognized by Dataview plugin
- [ ] Confirm MOC navigation works
- [ ] Test with sample of different entry types

## 8. Usage Example

```python
# In main.py

def export_to_obsidian(data, output_dir):
    """Export data to Obsidian format."""
    import obsidian_export
    
    logging.info("Exporting data to Obsidian format...")
    
    os.makedirs(output_dir, exist_ok=True)
    export_stats = obsidian_export.export_to_markdown(data, output_dir)
    
    # Log results
    logging.info(f"Files created: {export_stats['files_created']}")
    logging.info(f"MOCs created: {export_stats['mocs_created']}")
    
    if export_stats['warnings']:
        logging.warning(f"{len(export_stats['warnings'])} warnings:")
        for warning in export_stats['warnings'][:5]:
            logging.warning(f"  {warning}")
    
    if export_stats['errors']:
        logging.error(f"{len(export_stats['errors'])} errors occurred")
    
    return export_stats
```

## 9. Future Enhancements

**Phase 2 Possibilities:**
- Dataview query blocks in MOCs for dynamic content
- Tag taxonomy generator
- Citation export to BibTeX/CSL-JSON
- Automatic backlink summary generation
- Search index optimization
- Template customization via config file

This specification is complete and ready for immediate implementation. The developer can begin coding the obsidian_export.py file with full understanding of requirements, architecture, and expected behavior.
