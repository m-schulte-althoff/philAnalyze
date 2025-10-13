"""
Tests for Obsidian export functionality.

Tests cover:
- Filename sanitization
- Link conversion (internal and external)
- Quote tree building
- YAML frontmatter generation
- MOC creation
- Complete export workflow
"""

import pytest
import pandas as pd
import json
import tempfile
import shutil
from pathlib import Path
from obsidian_export import ObsidianExporter, export_to_markdown


class TestObsidianExporter:
    """Test suite for ObsidianExporter class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'paragraph_num': [13, 14, 15, 16, 17],
            'text': [
                'Quote text about psychology',
                'Another quote about consciousness',
                'Reference to external work',
                'Personal note about philosophy',
                'Nested quote example'
            ],
            'type': ['quote', 'quote', 'reference', 'note', 'quote'],
            'category': ['Psychology', 'Psychology', 'Psychology', 'Philosophy', 'Psychology'],
            'subcategory': ['Psychoanalysis', 'Psychoanalysis', 'Psychoanalysis', 'Ethics', 'Psychoanalysis'],
            'quote_level': [1.0, 1.0, None, None, 2.0],
            'higherLevelQuoteRef': [None, None, None, None, 1],
            'quote_marker': ['~', '°', '', '', '°'],
            'quote_text': [
                'Quote text about psychology',
                'Another quote about consciousness',
                None,
                None,
                'Nested quote example'
            ],
            'citation_author': ['Jung', 'Freud', None, None, 'Sloterdijk'],
            'citation_title': ['Psychology and Religion', 'The Unconscious', None, None, 'Critique'],
            'citation_source': ['', 'Book', None, None, ''],
            'citation_raw': ['Jung, "Psychology and Religion"', 'Freud, "The Unconscious"', None, None, 'Sloterdijk, "Critique"'],
            'links': [
                '[]',
                '[{"text": "Tod", "url": "#Tod", "type": "internal"}]',
                '[{"text": "Article", "url": "https://example.com", "type": "external"}]',
                '[]',
                '[]'
            ],
            'page': [1, 1, 2, 3, 1],
            'length': [100, 150, 80, 120, 90],
            'word_count': [15, 20, 12, 18, 14],
            'has_citation': [True, True, False, False, True],
            'has_links': [False, True, True, False, False]
        })
    
    @pytest.fixture
    def exporter(self, temp_dir):
        """Create ObsidianExporter instance."""
        return ObsidianExporter(temp_dir)
    
    # Filename sanitization tests
    def test_sanitize_filename_valid(self, exporter):
        """Test that valid filenames are preserved."""
        assert exporter._sanitize_filename('Valid Name') == 'Valid Name'
        assert exporter._sanitize_filename('Name_With_Underscores') == 'Name_With_Underscores'
    
    def test_sanitize_filename_invalid_chars(self, exporter):
        """Test that invalid characters are replaced."""
        result = exporter._sanitize_filename('Name: With* Invalid? Chars')
        assert ':' not in result
        assert '*' not in result
        assert '?' not in result
        assert result == 'Name- With- Invalid- Chars'
    
    def test_sanitize_filename_multiple_dashes(self, exporter):
        """Test that multiple dashes are collapsed."""
        result = exporter._sanitize_filename('Name---With---Dashes')
        assert result == 'Name-With-Dashes'
    
    def test_sanitize_filename_max_length(self, exporter):
        """Test that filenames are truncated to max length."""
        long_name = 'A' * 200
        result = exporter._sanitize_filename(long_name, max_length=50)
        assert len(result) == 50
    
    def test_sanitize_filename_empty(self, exporter):
        """Test that empty strings return default."""
        assert exporter._sanitize_filename('') == 'untitled'
        assert exporter._sanitize_filename('   ') == 'untitled'
    
    # Link conversion tests
    def test_convert_links_empty(self, exporter):
        """Test conversion of empty links."""
        assert exporter._convert_links('[]') == '*No links*'
        assert exporter._convert_links('') == '*No links*'
    
    def test_convert_links_internal(self, exporter):
        """Test conversion of internal links."""
        json_str = '[{"text": "Tod", "url": "#Tod", "type": "internal"}]'
        result = exporter._convert_links(json_str)
        assert '[[Tod]]' in result
        assert exporter.stats['total_links'] > 0
    
    def test_convert_links_external(self, exporter):
        """Test conversion of external links."""
        json_str = '[{"text": "Article", "url": "https://example.com", "type": "external"}]'
        result = exporter._convert_links(json_str)
        assert '[Article](https://example.com)' in result
    
    def test_convert_links_mixed(self, exporter):
        """Test conversion of mixed link types."""
        json_str = '[{"text": "Internal", "url": "#Internal", "type": "internal"}, {"text": "External", "url": "https://example.com", "type": "external"}]'
        result = exporter._convert_links(json_str)
        assert '[[Internal]]' in result
        assert '[External](https://example.com)' in result
    
    def test_convert_links_invalid_json(self, exporter):
        """Test handling of invalid JSON."""
        result = exporter._convert_links('invalid json')
        assert result == '*Invalid links data*'
    
    # Frontmatter tests
    def test_format_frontmatter_quote(self, exporter, sample_data):
        """Test YAML frontmatter generation for quote."""
        row = sample_data.iloc[0]
        frontmatter = exporter._format_frontmatter(row)
        
        assert '---' in frontmatter
        assert 'type: quote' in frontmatter
        assert 'category: Psychology' in frontmatter
        assert 'subcategory: Psychoanalysis' in frontmatter
        assert 'quote_level: 1.0' in frontmatter
        assert 'citation:' in frontmatter
        assert 'author: Jung' in frontmatter
    
    def test_format_frontmatter_reference(self, exporter, sample_data):
        """Test YAML frontmatter generation for reference."""
        row = sample_data.iloc[2]
        frontmatter = exporter._format_frontmatter(row)
        
        assert 'type: reference' in frontmatter
        assert 'has_citation: False' in frontmatter
        # Check that citation metadata block is not present (not just substring)
        assert '\ncitation:\n' not in frontmatter
    
    def test_format_frontmatter_note(self, exporter, sample_data):
        """Test YAML frontmatter generation for note."""
        row = sample_data.iloc[3]
        frontmatter = exporter._format_frontmatter(row)
        
        assert 'type: note' in frontmatter
        assert 'category: Philosophy' in frontmatter
    
    # Citation formatting tests
    def test_format_citation_complete(self, exporter, sample_data):
        """Test citation formatting with all fields."""
        row = sample_data.iloc[0]
        citation = exporter._format_citation(row)
        
        assert '**Author:** [[Jung]]' in citation
        assert '**Title:** *Psychology and Religion*' in citation
        assert '**Full Citation:**' in citation
    
    def test_format_citation_missing(self, exporter, sample_data):
        """Test citation formatting when no citation exists."""
        row = sample_data.iloc[2]
        citation = exporter._format_citation(row)
        
        assert citation == '*No citation available*'
    
    # Quote tree building tests
    def test_build_quote_tree_hierarchical(self, exporter, sample_data):
        """Test building hierarchical quote tree."""
        tree = exporter._build_quote_tree(sample_data)
        
        # Should have both level 1 and level 2 quotes
        assert 'Quote - Jung' in tree
        assert 'Quote - Sloterdijk' in tree
        
        # Level 2 should be indented
        lines = tree.split('\n')
        level_2_lines = [l for l in lines if 'Sloterdijk' in l]
        if level_2_lines:
            assert level_2_lines[0].startswith('  -')
    
    def test_build_quote_tree_empty(self, exporter):
        """Test building quote tree with no quotes."""
        empty_df = pd.DataFrame({
            'id': [1],
            'type': ['reference'],
            'category': ['Test'],
            'subcategory': ['Test']
        })
        tree = exporter._build_quote_tree(empty_df)
        assert tree == '*No quotes*'
    
    # Reference list tests
    def test_build_reference_list(self, exporter, sample_data):
        """Test building reference list."""
        ref_list = exporter._build_reference_list(sample_data)
        
        assert 'Reference -' in ref_list
        assert 'id-3' in ref_list
    
    def test_build_reference_list_empty(self, exporter):
        """Test building reference list with no references."""
        empty_df = pd.DataFrame({
            'id': [1],
            'type': ['quote'],
            'category': ['Test'],
            'subcategory': ['Test']
        })
        ref_list = exporter._build_reference_list(empty_df)
        assert ref_list == '*No references*'
    
    # Note list tests
    def test_build_note_list(self, exporter, sample_data):
        """Test building note list."""
        note_list = exporter._build_note_list(sample_data)
        
        assert 'Note -' in note_list
        assert 'id-4' in note_list
    
    # Related subcategories tests
    def test_find_related_subcategories(self, exporter, sample_data):
        """Test finding related subcategories from links."""
        related = exporter._find_related_subcategories(sample_data)
        
        assert '[[Tod]]' in related
    
    def test_find_related_subcategories_none(self, exporter):
        """Test finding related subcategories when none exist."""
        df = pd.DataFrame({
            'id': [1],
            'type': ['quote'],
            'links': ['[]']
        })
        related = exporter._find_related_subcategories(df)
        assert related == '*No related subcategories*'
    
    # Validation tests
    def test_validate_dataframe_valid(self, exporter, sample_data):
        """Test validation of valid DataFrame."""
        errors = exporter._validate_dataframe(sample_data)
        assert len(errors) == 0
    
    def test_validate_dataframe_missing_columns(self, exporter):
        """Test validation with missing required columns."""
        invalid_df = pd.DataFrame({'id': [1], 'text': ['test']})
        errors = exporter._validate_dataframe(invalid_df)
        
        assert len(errors) > 0
        assert 'Missing required columns' in errors[0]
    
    def test_validate_dataframe_duplicate_ids(self, exporter):
        """Test validation with duplicate IDs."""
        invalid_df = pd.DataFrame({
            'id': [1, 1, 2],
            'category': ['A', 'A', 'B'],
            'subcategory': ['X', 'X', 'Y'],
            'type': ['quote', 'quote', 'quote'],
            'text': ['a', 'b', 'c']
        })
        errors = exporter._validate_dataframe(invalid_df)
        
        assert len(errors) > 0
        assert 'Duplicate IDs' in errors[0]
    
    def test_validate_internal_links(self, exporter, sample_data):
        """Test internal link validation."""
        warnings = exporter._validate_internal_links(sample_data)
        
        # 'Tod' is not a subcategory, so should generate warning
        assert len(warnings) > 0
    
    # Entry creation tests
    def test_create_quote_note(self, exporter, sample_data):
        """Test quote note creation."""
        row = sample_data.iloc[0]
        content = exporter._create_quote_note(row)
        
        assert '# Quote: Jung - Psychology and Religion' in content
        assert '> Quote text about psychology' in content
        assert '## Citation' in content
        assert '## Metadata' in content
        assert '## Context' in content
    
    def test_create_quote_note_with_parent(self, exporter, sample_data):
        """Test quote note with parent reference."""
        row = sample_data.iloc[4]  # Has higherLevelQuoteRef
        content = exporter._create_quote_note(row)
        
        assert '**Parent Quote:**' in content
        assert '[[Quote id-1]]' in content
    
    def test_create_reference_note(self, exporter, sample_data):
        """Test reference note creation."""
        row = sample_data.iloc[2]
        content = exporter._create_reference_note(row)
        
        assert '# Reference:' in content
        assert 'Reference to external work' in content
    
    def test_create_note(self, exporter, sample_data):
        """Test general note creation."""
        row = sample_data.iloc[3]
        content = exporter._create_note(row)
        
        assert '# Personal note about philosophy' in content
    
    # Folder structure tests
    def test_create_folder_structure(self, exporter, sample_data, temp_dir):
        """Test that folder structure is created correctly."""
        exporter._create_folder_structure(sample_data)
        
        psychology_path = Path(temp_dir) / 'Psychology'
        philosophy_path = Path(temp_dir) / 'Philosophy'
        
        assert psychology_path.exists()
        assert philosophy_path.exists()
    
    # Export entry tests
    def test_export_entry_quote(self, exporter, sample_data, temp_dir):
        """Test exporting a quote entry."""
        row = sample_data.iloc[0]
        subcategory_path = Path(temp_dir) / 'Psychology' / 'Psychoanalysis'
        subcategory_path.mkdir(parents=True, exist_ok=True)
        
        exporter._export_entry(row, subcategory_path)
        
        # Check that file was created
        files = list(subcategory_path.glob('*.md'))
        assert len(files) == 1
        assert 'Quote - Jung' in files[0].name
        
        # Check content
        content = files[0].read_text(encoding='utf-8')
        assert '# Quote: Jung - Psychology and Religion' in content
    
    def test_export_entry_reference(self, exporter, sample_data, temp_dir):
        """Test exporting a reference entry."""
        row = sample_data.iloc[2]
        subcategory_path = Path(temp_dir) / 'Psychology' / 'Psychoanalysis'
        subcategory_path.mkdir(parents=True, exist_ok=True)
        
        exporter._export_entry(row, subcategory_path)
        
        # Check that file was created
        files = list(subcategory_path.glob('*.md'))
        assert len(files) == 1
        assert 'Reference -' in files[0].name
    
    # MOC creation tests
    def test_create_moc(self, exporter, sample_data, temp_dir):
        """Test MOC creation."""
        subcategory_path = Path(temp_dir) / 'Psychology' / 'Psychoanalysis'
        subcategory_path.mkdir(parents=True, exist_ok=True)
        
        group = sample_data[sample_data['subcategory'] == 'Psychoanalysis']
        exporter._create_moc('Psychology', 'Psychoanalysis', group, subcategory_path)
        
        # Check that MOC file was created
        moc_file = subcategory_path / '_MOC - Psychoanalysis.md'
        assert moc_file.exists()
        
        # Check content
        content = moc_file.read_text(encoding='utf-8')
        assert '# Map of Content: Psychoanalysis' in content
        assert '## Quotes' in content
        assert '## References' in content
        assert '## Notes' in content
        assert 'entry_count: 4' in content  # 4 entries in Psychoanalysis
    
    # Full export tests
    def test_export_to_markdown_complete(self, sample_data, temp_dir):
        """Test complete export workflow."""
        stats = export_to_markdown(sample_data, temp_dir)
        
        # Check statistics
        assert stats['files_created'] > 0
        assert stats['mocs_created'] > 0
        assert len(stats['errors']) == 0
        
        # Check folder structure
        psychology_path = Path(temp_dir) / 'Psychology' / 'Psychoanalysis'
        philosophy_path = Path(temp_dir) / 'Philosophy' / 'Ethics'
        
        assert psychology_path.exists()
        assert philosophy_path.exists()
        
        # Check that MOCs were created
        assert (psychology_path / '_MOC - Psychoanalysis.md').exists()
        assert (philosophy_path / '_MOC - Ethics.md').exists()
        
        # Check that entries were created
        psychology_files = list(psychology_path.glob('*.md'))
        assert len(psychology_files) > 1  # MOC + entries
    
    def test_export_with_invalid_data(self, temp_dir):
        """Test export with invalid data."""
        invalid_df = pd.DataFrame({'id': [1], 'text': ['test']})
        stats = export_to_markdown(invalid_df, temp_dir)
        
        assert len(stats['errors']) > 0
        assert stats['files_created'] == 0
    
    def test_export_preserves_quote_hierarchy(self, sample_data, temp_dir):
        """Test that quote hierarchy is preserved in export."""
        stats = export_to_markdown(sample_data, temp_dir)
        
        # Find the nested quote file
        psychology_path = Path(temp_dir) / 'Psychology' / 'Psychoanalysis'
        nested_quote = psychology_path / 'Quote - Sloterdijk - Critique (id-5).md'
        
        assert nested_quote.exists()
        
        content = nested_quote.read_text(encoding='utf-8')
        assert '**Parent Quote:** [[Quote id-1]]' in content
        assert '**Quote Level:** 2.0' in content


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)
    
    def test_empty_dataframe(self, temp_dir):
        """Test export with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['id', 'category', 'subcategory', 'type', 'text'])
        exporter = ObsidianExporter(temp_dir)
        stats = exporter.export_to_markdown(empty_df)
        
        assert stats['files_created'] == 0
        assert stats['mocs_created'] == 0
    
    def test_missing_optional_fields(self, temp_dir):
        """Test export with missing optional fields."""
        minimal_df = pd.DataFrame({
            'id': [1],
            'category': ['Test'],
            'subcategory': ['Sub'],
            'type': ['quote'],
            'text': ['Some text'],
            'quote_level': [1.0]
        })
        
        stats = export_to_markdown(minimal_df, temp_dir)
        assert len(stats['errors']) == 0
        assert stats['files_created'] > 0
    
    def test_special_characters_in_categories(self, temp_dir):
        """Test handling of special characters in category names."""
        df = pd.DataFrame({
            'id': [1],
            'category': ['Test: Category/With*Special?Chars'],
            'subcategory': ['Sub|Category'],
            'type': ['quote'],
            'text': ['Test text'],
            'quote_level': [1.0]
        })
        
        stats = export_to_markdown(df, temp_dir)
        
        # Should complete without errors
        assert len(stats['errors']) == 0
        assert stats['files_created'] > 0
    
    def test_very_long_text(self, temp_dir):
        """Test handling of very long text content."""
        long_text = 'A' * 10000
        df = pd.DataFrame({
            'id': [1],
            'category': ['Test'],
            'subcategory': ['Sub'],
            'type': ['note'],
            'text': [long_text]
        })
        
        stats = export_to_markdown(df, temp_dir)
        assert stats['files_created'] > 0
        
        # Check that file was created with truncated filename
        test_path = Path(temp_dir) / 'Test' / 'Sub'
        files = list(test_path.glob('*.md'))
        assert len(files) == 2  # 1 note + 1 MOC
    
    def test_unicode_characters(self, temp_dir):
        """Test handling of Unicode characters."""
        df = pd.DataFrame({
            'id': [1],
            'category': ['Philosophie'],
            'subcategory': ['Éthique'],
            'type': ['quote'],
            'text': ['Übung macht den Meister – 练习使完美'],
            'citation_author': ['Nietzsche'],
            'citation_title': ['Also sprach Zarathustra'],
            'quote_level': [1.0],
            'has_citation': [True]
        })
        
        stats = export_to_markdown(df, temp_dir)
        assert stats['files_created'] > 0
        
        # Check that content is preserved correctly
        phil_path = Path(temp_dir) / 'Philosophie' / 'Éthique'
        files = list(phil_path.glob('Quote*.md'))
        assert len(files) == 1
        
        content = files[0].read_text(encoding='utf-8')
        assert 'Übung macht den Meister' in content
        assert '练习使完美' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
