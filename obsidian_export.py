"""
Obsidian Export Module for philAnalyze.

Transforms preprocessed philosophical notes DataFrame into 
Obsidian-compatible markdown vault with hierarchical structure.
"""

import os
import json
import re
import logging
from urllib.parse import unquote
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd


# Configure logging
logger = logging.getLogger(__name__)


class ObsidianExporter:
    """Export philAnalyze data to Obsidian markdown vault."""
    
    def __init__(self, output_dir: str):
        """
        Initialize exporter.
        
        Args:
            output_dir: Base directory for Obsidian vault export
        """
        self.output_dir = Path(output_dir)
        self.moc_paths = {}
        self.bookmark_paths = {}
        self.other_bookmarks = set()
        self.partial_export = False
        self.stats = {
            'files_created': 0,
            'mocs_created': 0,
            'total_links': 0,
            'resolved_internal_links': 0,
            'unresolved_internal_links': 0,
            'skipped_entries': 0,
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
        logger.info("Starting Obsidian export...")
        
        # Validate input
        errors = self._validate_dataframe(df)
        if errors:
            self.stats['errors'].extend(errors)
            logger.error(f"Validation failed: {errors}")
            return self.stats
        
        self._prepare_destinations(df)
        if self.stats['errors']:
            return self.stats

        # Pandas otherwise deep-copies the document's bookmark catalog for every row.
        df = df.copy(deep=False)
        df.attrs = {}

        assigned = df['category'].notna() & df['subcategory'].notna()
        self.stats['skipped_entries'] = int((~assigned).sum())
        if not assigned.all():
            self.stats['warnings'].append(
                f"Skipped entries without category/subcategory: {df.loc[~assigned, 'id'].tolist()}"
            )
        df = df.loc[assigned]

        # Check for link issues (warnings only)
        warnings = self._validate_internal_links(df)
        if warnings:
            self.stats['warnings'].extend(warnings)
            logger.warning(f"Found {len(warnings)} link warnings")
        
        # Create folder structure
        self._create_folder_structure(df)
        
        grouped = dict(tuple(df.groupby(['category', 'subcategory'])))
        for (category, subcategory), moc_path in self.moc_paths.items():
            group = grouped.get((category, subcategory), df.iloc[:0])
            subcategory_path = (self.output_dir / moc_path).parent
            subcategory_path.mkdir(parents=True, exist_ok=True)
            for _, row in group.iterrows():
                self._export_entry(row, subcategory_path)
            self._create_moc(category, subcategory, group, subcategory_path)

        logger.info(f"Export complete: {self.stats}")
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
    
    @staticmethod
    def _read_links(value):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return []
        if isinstance(value, str):
            value = json.loads(value) if value else []
        if not isinstance(value, list) or any(
            not isinstance(link, dict) or not isinstance(link.get('url'), str)
            or not isinstance(link.get('text', ''), str) for link in value
        ):
            raise ValueError('Expected a list of link dictionaries with text and URL')
        return value

    def _moc_path(self, category, subcategory):
        return '/'.join((self._sanitize_filename(str(category), 200),
                         self._sanitize_filename(str(subcategory), 200),
                         self._sanitize_filename(f'_MOC - {subcategory}', 97) + '.md'))

    def _prepare_destinations(self, df):
        sections = df.attrs.get('sections', [])
        pairs = set(df[['category', 'subcategory']].dropna().itertuples(index=False, name=None))
        pairs.update((s['category'], s['subcategory']) for s in sections if s['category'] is not None)
        self.moc_paths = {pair: self._moc_path(*pair) for pair in sorted(pairs)}
        if len(set(self.moc_paths.values())) != len(self.moc_paths):
            self.stats['errors'].append('Category paths collide after filename sanitization; export stopped')
        self.bookmark_paths = {}
        for section in sections:
            path = self.moc_paths.get((section['category'], section['subcategory']))
            if path:
                for bookmark in section['bookmarks']:
                    self.bookmark_paths.setdefault(bookmark, []).append(path)
        self.other_bookmarks = set(df.attrs.get('other_bookmarks', []))
        self.partial_export = df.attrs.get('partial_export', False)

    def _resolve_link(self, link):
        target = unquote(link['url'][1:])
        paths = self.bookmark_paths.get(target, [])
        if len(paths) == 1 and target not in self.other_bookmarks:
            return paths[0], None
        if len(paths) > 1 or (paths and target in self.other_bookmarks):
            return None, 'ambiguous bookmark'
        if target in self.other_bookmarks:
            return None, 'bookmark is not a category heading'
        return None, 'missing or excluded from partial export' if self.partial_export else 'missing category bookmark'

    def _validate_internal_links(self, df: pd.DataFrame) -> List[str]:
        warnings = []
        for idx, row in df.iterrows():
            try:
                links = self._read_links(row.get('links', []))
            except (ValueError, TypeError) as exc:
                warnings.append(f"Entry {row.get('id', idx)}: Invalid links data: {exc}")
                continue
            for link in links:
                if link.get('type') == 'internal':
                    path, reason = self._resolve_link(link)
                    key = 'resolved_internal_links' if path else 'unresolved_internal_links'
                    self.stats[key] += 1
                    if not path:
                        warnings.append(f"Entry {row.get('id', idx)}: {link['url']!r}: {reason}")
        self.stats['total_links'] = self.stats['resolved_internal_links']
        return warnings

    def _format_link(self, link):
        label = link.get('text') or link['url']
        if link.get('type') == 'internal':
            path, _ = self._resolve_link(link)
            if not path:
                return label
            # Markdown links handle labels containing wikilink delimiters safely.
            if any(c in path + label for c in '|[]#'):
                from urllib.parse import quote
                escaped = label.replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]')
                return f"[{escaped}]({quote(path, safe='/')})"
            return f"[[{path.removesuffix('.md')}|{label}]]"
        label = label.replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]')
        url = link['url'].replace(' ', '%20').replace('(', '%28').replace(')', '%29')
        return f'[{label}]({url})' if url else label

    def _inline_text(self, row, text):
        raw = row.get('text', '')
        offset = raw.find(text)
        if offset < 0:
            return text
        try:
            links = self._read_links(row.get('links', []))
        except (ValueError, TypeError):
            return text
        for link in sorted(links, key=lambda item: item.get('start', -1), reverse=True):
            start, end = link.get('start'), link.get('end')
            if isinstance(start, int) and isinstance(end, int):
                start, end = start - offset, end - offset
                if 0 <= start <= end <= len(text) and text[start:end] == link.get('text'):
                    text = text[:start] + self._format_link(link) + text[end:]
        return text

    def _create_folder_structure(self, df: pd.DataFrame):
        """Create category and subcategory folders."""
        for category in df['category'].dropna().unique():
            sanitized_category = self._sanitize_filename(str(category), max_length=200)
            category_path = self.output_dir / sanitized_category
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
        quote_text = self._inline_text(row, row.get('quote_text', row.get('text', '')))
        
        # Citation block
        citation_block = self._format_citation(row)
        
        # Links
        links_block = self._convert_links(row.get('links', []))
        
        # Parent quote reference
        parent_ref = ""
        higher_ref = row.get('higherLevelQuoteRef')
        if pd.notna(higher_ref) and str(higher_ref).strip() not in ['', '-', 'nan', 'None']:
            try:
                parent_ref = f"\n- **Parent Quote:** [[Quote id-{int(float(higher_ref))}]]"
            except (ValueError, TypeError):
                pass  # Skip invalid values
        
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
        links_block = self._convert_links(row.get('links', []))
        
        content = f"""{frontmatter}

# Reference: {text[:80]}

{self._inline_text(row, text)}

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
        links_block = self._convert_links(row.get('links', []))
        
        content = f"""{frontmatter}

# {text[:80]}

{self._inline_text(row, text)}

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
        moc_filename = Path(self.moc_paths.get((category, subcategory),
                                                self._moc_path(category, subcategory))).name
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
        
        # Find related subcategories
        related = self._find_related_subcategories(group)
        
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
  - {self._sanitize_filename(str(subcategory).lower())}
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
        
        if quotes.empty:
            return "*No quotes*"
        
        lines = []
        
        # Sort by quote_level for hierarchical display
        quotes = quotes.sort_values(['quote_level', 'id'])
        
        for _, row in quotes.iterrows():
            level = row.get('quote_level', 1.0)
            indent = '  ' * int(level - 1)
            
            author = row.get('citation_author', 'Unknown')
            title = row.get('citation_title', 'Untitled')
            row_id = row['id']
            
            # Create snippet for preview
            text = row.get('quote_text', row.get('text', ''))
            snippet = text[:60] + '...' if len(str(text)) > 60 else text
            snippet = snippet.replace('\n', ' ')
            
            lines.append(f"{indent}- [[Quote - {author} - {title} (id-{row_id})]] — {snippet}")
        
        return '\n'.join(lines)
    
    def _build_reference_list(self, group: pd.DataFrame) -> str:
        """Build reference entry list."""
        refs = group[group['type'] == 'reference']
        
        if refs.empty:
            return "*No references*"
        
        lines = []
        for _, row in refs.iterrows():
            text = row.get('text', '')
            snippet = text[:60] + '...' if len(str(text)) > 60 else text
            snippet = snippet.replace('\n', ' ')
            lines.append(f"- [[Reference - {snippet} (id-{row['id']})]]")
        
        return '\n'.join(lines)
    
    def _build_note_list(self, group: pd.DataFrame) -> str:
        """Build note entry list."""
        notes = group[(group['type'] != 'quote') & (group['type'] != 'reference')]
        
        if notes.empty:
            return "*No notes*"
        
        lines = []
        for _, row in notes.iterrows():
            text = row.get('text', '')
            snippet = text[:60] + '...' if len(str(text)) > 60 else text
            snippet = snippet.replace('\n', ' ')
            lines.append(f"- [[Note - {snippet} (id-{row['id']})]]")
        
        return '\n'.join(lines)
    
    def _find_related_subcategories(self, group: pd.DataFrame) -> str:
        related = {}
        for _, row in group.iterrows():
            try:
                links = self._read_links(row.get('links', []))
            except (ValueError, TypeError):
                continue
            for link in links:
                if link.get('type') == 'internal':
                    path, _ = self._resolve_link(link)
                    if path:
                        related[path] = self._format_link(link)
        return '\n'.join(f'- {related[path]}' for path in sorted(related)) if related else '*No related subcategories*'

    def _format_frontmatter(self, row: pd.Series) -> str:
        """Generate YAML frontmatter."""
        lines = ["---"]
        
        # Basic metadata
        entry_type = row.get('type', 'note')
        lines.append(f"type: {entry_type}")
        lines.append(f"category: {row.get('category', '')}")
        lines.append(f"subcategory: {row.get('subcategory', '')}")
        lines.append(f"id: {row.get('id', '')}")
        lines.append(f"paragraph_num: {row.get('paragraph_num', '')}")
        lines.append(f"page: {row.get('page', '')}")
        lines.append(f"word_count: {row.get('word_count', 0)}")
        lines.append(f"has_citation: {row.get('has_citation', False)}")
        lines.append(f"has_links: {row.get('has_links', False)}")
        
        # Quote-specific fields
        if entry_type == 'quote':
            lines.append(f"quote_level: {row.get('quote_level', 1.0)}")
            higher_ref = row.get('higherLevelQuoteRef')
            if pd.notna(higher_ref) and str(higher_ref).strip() not in ['', '-', 'nan', 'None']:
                try:
                    lines.append(f"higher_level_quote_ref: {int(float(higher_ref))}")
                except (ValueError, TypeError):
                    pass  # Skip invalid values
            
            # Citation metadata
            if row.get('has_citation'):
                lines.append("citation:")
                lines.append(f"  author: {row.get('citation_author', '')}")
                lines.append(f"  title: {row.get('citation_title', '')}")
                lines.append(f"  source: {row.get('citation_source', '')}")
                lines.append(f"  raw: {row.get('citation_raw', '')}")
        
        # Tags
        lines.append("tags:")
        lines.append(f"  - {self._sanitize_filename(str(row.get('subcategory', '')).lower())}")
        if entry_type == 'quote' and pd.notna(row.get('citation_author')):
            author_tag = self._sanitize_filename(str(row.get('citation_author', '')).lower())
            lines.append(f"  - {author_tag}")
        
        lines.append(f"created: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("---")
        
        return '\n'.join(lines)
    
    def _format_citation(self, row: pd.Series) -> str:
        """Format citation block."""
        lines = []
        
        if row.get('has_citation'):
            author = row.get('citation_author', '')
            title = row.get('citation_title', '')
            source = row.get('citation_source', '')
            raw = row.get('citation_raw', '')
            
            if author:
                lines.append(f"**Author:** [[{author}]]")
            if title:
                lines.append(f"**Title:** *{title}*")
            if source:
                lines.append(f"**Source:** {source}")
            if raw:
                lines.append(f"**Full Citation:** {self._inline_text(row, raw)}")
        
        return '\n'.join(lines) if lines else "*No citation available*"
    
    def _convert_links(self, value) -> str:
        try:
            links = self._read_links(value)
        except (ValueError, TypeError):
            return '*Invalid links data*'
        return '\n'.join('- ' + self._format_link(link) for link in links) if links else '*No links*'

    def _sanitize_filename(self, text: str, max_length: int = 100) -> str:
        """Sanitize text for use in filenames."""
        # Replace invalid chars with dash
        text = str(text)
        text = re.sub(r'[/\\:*?"<>|]', '-', text)
        
        # Remove multiple dashes
        text = re.sub(r'-+', '-', text)
        
        # Trim and limit length
        text = text.strip().strip('-')[:max_length]
        
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
