"""
Unit tests for obsidian_export module.

Tests for Obsidian markdown export functionality.
"""

import pytest
import pandas as pd
import os
from datetime import datetime
import obsidian_export


class TestExportToMarkdown:
    """Test suite for export_to_markdown function."""
    
    def test_export_creates_directory(self, tmp_path):
        """Test that export creates output directory."""
        test_data = pd.DataFrame({
            'text': ['Test text'],
            'section': ['Section 1']
        })
        
        output_dir = tmp_path / 'obsidian_output'
        result = obsidian_export.export_to_markdown(test_data, str(output_dir))
        
        # Verify directory was created
        assert output_dir.exists()
        assert output_dir.is_dir()
    
    def test_export_returns_statistics(self, tmp_path):
        """Test that export returns statistics dictionary."""
        test_data = pd.DataFrame({
            'text': ['Test text'],
            'section': ['Section 1']
        })
        
        output_dir = tmp_path / 'obsidian_output'
        result = obsidian_export.export_to_markdown(test_data, str(output_dir))
        
        # Verify statistics structure
        assert isinstance(result, dict)
        assert 'files_created' in result
        assert 'total_links' in result
        assert 'export_date' in result
        assert 'output_directory' in result
    
    def test_export_creates_index_file(self, tmp_path):
        """Test that an index file is created."""
        test_data = pd.DataFrame({
            'text': ['Test text 1', 'Test text 2'],
            'section': ['Section 1', 'Section 2']
        })
        
        output_dir = tmp_path / 'obsidian_output'
        obsidian_export.export_to_markdown(test_data, str(output_dir))
        
        # Verify index file exists
        index_path = output_dir / 'Index.md'
        assert index_path.exists()


class TestCreateIndexFile:
    """Test suite for _create_index_file function."""
    
    def test_index_file_creation(self, tmp_path):
        """Test that index file is created with proper content."""
        test_data = pd.DataFrame({
            'text': ['Text 1', 'Text 2', 'Text 3'],
            'section': ['Section 1', 'Section 1', 'Section 2']
        })
        
        obsidian_export._create_index_file(test_data, str(tmp_path))
        
        index_path = tmp_path / 'Index.md'
        assert index_path.exists()
        
        content = index_path.read_text(encoding='utf-8')
        
        # Verify YAML frontmatter
        assert '---' in content
        assert 'title: Philosophical Text Analysis Index' in content
        assert 'tags:' in content
        
        # Verify content
        assert 'Total Entries: 3' in content
        assert 'Section 1' in content
        assert 'Section 2' in content
    
    def test_index_file_without_sections(self, tmp_path):
        """Test index file creation when no section column exists."""
        test_data = pd.DataFrame({
            'text': ['Text 1', 'Text 2']
        })
        
        obsidian_export._create_index_file(test_data, str(tmp_path))
        
        index_path = tmp_path / 'Index.md'
        assert index_path.exists()
        
        content = index_path.read_text(encoding='utf-8')
        assert 'Total Entries: 2' in content


class TestSanitizeFilename:
    """Test suite for sanitize_filename function."""
    
    def test_sanitize_removes_invalid_characters(self):
        """Test that invalid filename characters are removed."""
        test_cases = [
            ('file:name', 'filename'),
            ('file/name', 'filename'),
            ('file\\name', 'filename'),
            ('file<name>', 'filename'),
            ('file|name', 'filename'),
            ('file?name', 'filename'),
            ('file*name', 'filename'),
        ]
        
        for input_str, expected in test_cases:
            result = obsidian_export.sanitize_filename(input_str)
            assert result == expected
    
    def test_sanitize_replaces_spaces(self):
        """Test that spaces are replaced with underscores."""
        result = obsidian_export.sanitize_filename('my file name')
        assert result == 'my_file_name'
    
    def test_sanitize_length_limit(self):
        """Test that filenames are limited to maximum length."""
        long_name = 'a' * 250
        result = obsidian_export.sanitize_filename(long_name)
        assert len(result) <= 200
    
    def test_sanitize_strips_periods_and_spaces(self):
        """Test that leading/trailing periods and spaces are removed."""
        result = obsidian_export.sanitize_filename('  .filename.  ')
        assert not result.startswith('.')
        assert not result.endswith('.')
        assert not result.startswith(' ')
        assert not result.endswith(' ')


class TestCreateYAMLFrontmatter:
    """Test suite for create_yaml_frontmatter function."""
    
    def test_simple_metadata(self):
        """Test YAML frontmatter with simple key-value pairs."""
        metadata = {
            'title': 'Test Title',
            'author': 'Test Author',
            'date': '2025-01-01'
        }
        
        result = obsidian_export.create_yaml_frontmatter(metadata)
        
        assert result.startswith('---')
        assert result.endswith('---')
        assert 'title: Test Title' in result
        assert 'author: Test Author' in result
        assert 'date: 2025-01-01' in result
    
    def test_list_metadata(self):
        """Test YAML frontmatter with list values."""
        metadata = {
            'title': 'Test Title',
            'tags': ['philosophy', 'analysis', 'text']
        }
        
        result = obsidian_export.create_yaml_frontmatter(metadata)
        
        assert 'tags:' in result
        assert '  - philosophy' in result
        assert '  - analysis' in result
        assert '  - text' in result
    
    def test_mixed_metadata(self):
        """Test YAML frontmatter with mixed types."""
        metadata = {
            'title': 'Test',
            'tags': ['tag1', 'tag2'],
            'date': '2025-01-01',
            'categories': ['cat1']
        }
        
        result = obsidian_export.create_yaml_frontmatter(metadata)
        
        # Should handle both simple values and lists
        assert 'title: Test' in result
        assert 'tags:' in result
        assert '  - tag1' in result
        assert 'date: 2025-01-01' in result
        assert 'categories:' in result


class TestExtractLinks:
    """Test suite for extract_links function."""
    
    def test_extract_links_placeholder(self):
        """Test that extract_links returns a list (placeholder implementation)."""
        result = obsidian_export.extract_links("Some text with potential links")
        assert isinstance(result, list)


class TestCreateWikilink:
    """Test suite for create_wikilink function."""
    
    def test_create_wikilink_format(self):
        """Test that wikilinks are formatted correctly."""
        result = obsidian_export.create_wikilink('Target Note')
        assert result == '[[Target Note]]'
    
    def test_create_wikilink_special_characters(self):
        """Test wikilink creation with special characters."""
        result = obsidian_export.create_wikilink('Note-with-dashes')
        assert result == '[[Note-with-dashes]]'


class TestExportMetadataCSV:
    """Test suite for export_metadata_csv function."""
    
    def test_export_metadata_excludes_text(self, tmp_path):
        """Test that metadata export excludes long text columns."""
        test_data = pd.DataFrame({
            'text': ['Long text content here...', 'More long text...'],
            'id': [1, 2],
            'section': ['Section 1', 'Section 2'],
            'word_count': [10, 15]
        })
        
        obsidian_export.export_metadata_csv(test_data, str(tmp_path))
        
        metadata_path = tmp_path / 'metadata.csv'
        assert metadata_path.exists()
        
        # Load and verify
        loaded = pd.read_csv(metadata_path)
        assert 'text' not in loaded.columns
        assert 'id' in loaded.columns
        assert 'section' in loaded.columns
        assert 'word_count' in loaded.columns
    
    def test_export_metadata_creates_file(self, tmp_path):
        """Test that metadata CSV file is created."""
        test_data = pd.DataFrame({
            'text': ['Test'],
            'id': [1]
        })
        
        obsidian_export.export_metadata_csv(test_data, str(tmp_path))
        
        metadata_path = tmp_path / 'metadata.csv'
        assert metadata_path.exists()
