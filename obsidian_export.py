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
        self.stats = {
            'files_created': 0,
            'mocs_created': 0,
            'total_links': 0,
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
        
        # Check for link issues (warnings only)
        warnings = self._validate_internal_links(df)
        if warnings:
            self.stats['warnings'].extend(warnings)
            logger.warning(f"Found {len(warnings)} link warnings")
        
        # Create folder structure
        self._create_folder_structure(df)
        
        # Group by subcategory for MOC creation
        grouped = df.groupby(['category', 'subcategory'])
        
        for (category, subcategory), group in grouped:
            # Create subcategory folder (sanitize names for filesystem)
            sanitized_category = self._sanitize_filename(str(category), max_length=200)
            sanitized_subcategory = self._sanitize_filename(str(subcategory), max_length=200)
            
            category_path = self.output_dir / sanitized_category
            subcategory_path = category_path / sanitized_subcategory
            subcategory_path.mkdir(parents=True, exist_ok=True)
            
            # Export individual entries
            for _, row in group.iterrows():
                self._export_entry(row, subcategory_path)
            
            # Create MOC (using original subcategory name for content, sanitized for filename)
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
    
    def _validate_internal_links(self, df: pd.DataFrame) -> List[str]:
        """Check internal link validity."""
        warnings = []
        all_subcategories = set(df['subcategory'].dropna().unique())
        
        for idx, row in df.iterrows():
            if 'links' in row.index:
                links_value = row['links']
                # Convert to string first to avoid array comparison issues
                links_str = str(links_value) if not (isinstance(links_value, float) and pd.isna(links_value)) else '[]'
                if links_str not in ['[]', 'nan', 'None', '']:
                    try:
                        links = json.loads(links_str)
                        for link in links:
                            if link.get('type') == 'internal':
                                target = link.get('url', '').lstrip('#')
                                if target and target not in all_subcategories:
                                    warnings.append(
                                        f"Row {idx}: Link target '{target}' not found in subcategories"
                                    )
                    except (json.JSONDecodeError, TypeError) as e:
                        warnings.append(f"Row {idx}: Invalid links JSON: {e}")
        
        return warnings
    
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
        quote_text = row.get('quote_text', row.get('text', ''))
        
        # Citation block
        citation_block = self._format_citation(row)
        
        # Links
        links_value = row.get('links', '[]')
        links_str = str(links_value) if not (isinstance(links_value, float) and pd.isna(links_value)) else '[]'
        links_block = self._convert_links(links_str)
        
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
        links_value = row.get('links', '[]')
        links_str = str(links_value) if not (isinstance(links_value, float) and pd.isna(links_value)) else '[]'
        links_block = self._convert_links(links_str)
        
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
        links_value = row.get('links', '[]')
        links_str = str(links_value) if not (isinstance(links_value, float) and pd.isna(links_value)) else '[]'
        links_block = self._convert_links(links_str)
        
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
        moc_filename = self._sanitize_filename(moc_filename)
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
        """Extract related subcategories from internal links."""
        related = set()
        
        for _, row in group.iterrows():
            links_json = row.get('links', '[]')
            # Convert to string first to avoid array comparison issues
            links_json_str = str(links_json) if not (isinstance(links_json, float) and pd.isna(links_json)) else '[]'
            if links_json_str not in ['[]', 'nan', 'None', '']:
                try:
                    links = json.loads(links_json_str)
                    for link in links:
                        if link.get('type') == 'internal':
                            target = link.get('url', '').lstrip('#')
                            if target:
                                related.add(target)
                except (json.JSONDecodeError, TypeError):
                    pass
        
        return '\n'.join([f"- [[{sub}]]" for sub in sorted(related)]) if related else "*No related subcategories*"
    
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
                lines.append(f"**Full Citation:** {raw}")
        
        return '\n'.join(lines) if lines else "*No citation available*"
    
    def _convert_links(self, links_json: str) -> str:
        """Convert links JSON to markdown."""
        if pd.isna(links_json) or links_json == '[]' or links_json == '':
            return "*No links*"
        
        try:
            links = json.loads(links_json)
        except (json.JSONDecodeError, TypeError):
            return "*Invalid links data*"
        
        formatted = []
        
        for link in links:
            if link.get('type') == 'internal':
                # Remove '#' and create wikilink
                target = link.get('url', '').lstrip('#')
                if target:
                    formatted.append(f"- [[{target}]]")
                    self.stats['total_links'] += 1
            else:
                text = link.get('text') or link.get('url', '')
                url = link.get('url', '')
                if url:
                    formatted.append(f"- [{text}]({url})")
        
        return '\n'.join(formatted) if formatted else "*No links*"
    
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
