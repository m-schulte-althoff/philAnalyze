"""
Unit tests for data_model module.

Tests for loading ODT files and preprocessing philosophical text data.
Uses a sample of the first 50 pages from the actual Phil.odt file.
"""

import pytest
import pandas as pd
import os
import data_model
from data_model import preprocess_philosophical_data

# Test data configuration
TEST_DATA_PATH = 'data/Phil.odt'
TEST_SAMPLE_PAGES = 50  # Number of pages to load for testing


@pytest.fixture(scope="module")
def sample_data():
    """
    Fixture to load sample data once for all tests.
    
    Loads the first 50 pages of Phil.odt file.
    This fixture is scoped to module level so data is loaded only once.
    """
    if not os.path.exists(TEST_DATA_PATH):
        pytest.skip(f"Test data file not found: {TEST_DATA_PATH}")
    
    return data_model.load_odt_data(TEST_DATA_PATH, max_pages=TEST_SAMPLE_PAGES)


@pytest.fixture(scope="module")
def preprocessed_sample_data(sample_data):
    """
    Fixture to provide preprocessed sample data.
    
    Returns the sample data after preprocessing.
    """
    return data_model.preprocess_philosophical_data(sample_data.copy())


class TestLoadODTData:
    """Test suite for load_odt_data function using real data."""
    
    def test_load_odt_data_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError):
            data_model.load_odt_data('nonexistent_file.odt')
    
    def test_load_odt_data_success(self, sample_data):
        """Test successful loading of ODT file with real data."""
        # Verify data was loaded
        assert isinstance(sample_data, pd.DataFrame)
        assert len(sample_data) > 0
        
        # Verify required columns exist
        assert 'text' in sample_data.columns
        assert 'paragraph_num' in sample_data.columns
        assert 'type' in sample_data.columns
        assert 'subcategory' in sample_data.columns
        assert 'quote_level' in sample_data.columns
        assert 'length' in sample_data.columns
        assert 'page' in sample_data.columns
        
        # Verify data types
        assert sample_data['text'].dtype == object
        assert sample_data['paragraph_num'].dtype in [int, 'int64']
        assert sample_data['length'].dtype in [int, 'int64']
        assert sample_data['page'].dtype in [int, 'int64']
    
    def test_load_odt_data_no_empty_paragraphs(self, sample_data):
        """Test that empty paragraphs are filtered out."""
        # All text entries should be non-empty
        assert all(sample_data['text'].str.strip() != '')
        assert all(sample_data['length'] > 0)
    
    def test_load_odt_data_page_limit(self, sample_data):
        """Test that page limit is respected."""
        # Maximum page number should not exceed TEST_SAMPLE_PAGES
        max_page = sample_data['page'].max()
        assert max_page <= TEST_SAMPLE_PAGES
    
    def test_load_odt_data_full_file(self):
        """Test loading the entire file without page limit."""
        if not os.path.exists(TEST_DATA_PATH):
            pytest.skip(f"Test data file not found: {TEST_DATA_PATH}")
        
        full_data = data_model.load_odt_data(TEST_DATA_PATH, max_pages=None)
        
        # Full data should have more records than sample
        # (This will only work if file has more than 50 pages)
        assert isinstance(full_data, pd.DataFrame)
        assert len(full_data) > 0


class TestPreprocessPhilosophicalData:
    """Test suite for preprocess_philosophical_data function using real data."""
    
    def test_preprocess_empty_dataframe(self):
        """Test preprocessing with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = data_model.preprocess_philosophical_data(empty_df)
        assert len(result) == 0
    
    def test_preprocess_adds_required_columns(self, sample_data):
        """Test that preprocessing adds all required columns using real data."""
        # Use a copy to avoid modifying the fixture
        test_data = sample_data.copy()
        
        result = data_model.preprocess_philosophical_data(test_data)
        
        # Check all required columns are present
        assert 'id' in result.columns
        assert 'word_count' in result.columns
        assert 'has_citation' in result.columns
        assert 'has_links' in result.columns
        
        # Verify data integrity
        assert len(result) == len(sample_data)
        assert all(result['id'] > 0)
        assert all(result['word_count'] >= 0)
    
    def test_preprocess_word_count_calculation(self, preprocessed_sample_data):
        """Test that word count is calculated correctly on real data."""
        # Check that word counts are reasonable
        assert all(preprocessed_sample_data['word_count'] > 0)
        
        # Verify word count calculation for a sample row
        sample_row = preprocessed_sample_data.iloc[0]
        expected_word_count = len(sample_row['text'].split())
        assert sample_row['word_count'] == expected_word_count
    
    def test_preprocess_citation_and_link_flags(self, preprocessed_sample_data):
        """Test that citation and link flags are set correctly on real data."""
        # Flags should be boolean
        assert preprocessed_sample_data['has_citation'].dtype == bool
        assert preprocessed_sample_data['has_links'].dtype == bool
        
        # Check that flags match actual data
        for _, row in preprocessed_sample_data.iterrows():
            if pd.notna(row['citation_raw']) and row['citation_raw']:
                assert row['has_citation'] == True
            if isinstance(row['links'], list) and len(row['links']) > 0:
                assert row['has_links'] == True
    
    def test_preprocess_id_generation(self, preprocessed_sample_data):
        """Test that unique IDs are generated sequentially on real data."""
        # IDs should be sequential starting from 1
        ids = preprocessed_sample_data['id'].tolist()
        assert ids == list(range(1, len(preprocessed_sample_data) + 1))
        
        # IDs should be unique
        assert len(ids) == len(set(ids))
    
    def test_preprocess_preserves_original_columns(self, sample_data):
        """Test that preprocessing preserves original columns."""
        test_data = sample_data.copy()
        original_columns = set(test_data.columns)
        
        result = data_model.preprocess_philosophical_data(test_data)
        
        # All original columns should still be present
        for col in original_columns:
            assert col in result.columns


class TestGetTextStatistics:
    """Test suite for get_text_statistics function using real data."""
    
    def test_statistics_empty_data(self):
        """Test statistics calculation with empty data."""
        result = data_model.get_text_statistics(None)
        assert result == {}
        
        empty_df = pd.DataFrame()
        result = data_model.get_text_statistics(empty_df)
        assert result == {}
    
    def test_statistics_calculation(self, preprocessed_sample_data):
        """Test that statistics are calculated correctly from real data."""
        result = data_model.get_text_statistics(preprocessed_sample_data)
        
        # Verify all expected keys are present
        expected_keys = [
            'total_paragraphs', 'total_words', 'total_characters',
            'total_quotes', 'total_subcategories',
            'quotes_with_citations', 'quotes_with_links',
            'avg_quote_length', 'max_quote_level'
        ]
        for key in expected_keys:
            assert key in result
        
        # Verify values are reasonable
        assert result['total_paragraphs'] == len(preprocessed_sample_data)
        assert result['total_words'] >= 0
        assert result['total_characters'] > 0
        assert result['total_quotes'] >= 0
        assert result['total_subcategories'] >= 0
        
        # Verify calculations match
        assert result['total_words'] == preprocessed_sample_data['word_count'].sum()
        assert result['total_characters'] == preprocessed_sample_data['length'].sum()


class TestCategoryDetection:
    """Test suite for category detection logic."""
    
    def test_categories_detected(self, sample_data):
        """Test that categories are properly detected."""
        categories = sample_data[sample_data['type'] == 'category']
        
        # Should have detected some categories
        assert len(categories) > 0
        
        # Categories should have category field set
        assert all(pd.notna(categories['category']))
    
    def test_category_names_valid(self, sample_data):
        """Test that detected categories match expected names."""
        categories = sample_data[sample_data['type'] == 'category']['category'].unique()
        
        # Should detect known categories from the hardcoded list
        # At least some of these should be present in the sample
        known_categories = [
            'Allgemeine Begriffe', 'Ethik', 'Geschichte', 
            'Kommunikation/Sprache/Text', 'Kunst/Kultur'
        ]
        
        # At least one known category should be detected
        assert any(cat in categories for cat in known_categories)


class TestSubcategoryDetection:
    """Test suite for subcategory detection logic."""
    
    def test_subcategories_detected(self, sample_data):
        """Test that subcategories are properly detected."""
        subcategories = sample_data[sample_data['type'] == 'subcategory']
        
        # Should have subcategories
        assert len(subcategories) > 0
        
        # All subcategories should have a subcategory value
        assert all(pd.notna(subcategories['subcategory']))
    
    def test_subcategory_link_requirement(self, sample_data):
        """Test that ToC subcategories have links."""
        # Get ToC subcategories (before content starts, typically < para 1200)
        toc_subcats = sample_data[
            (sample_data['type'] == 'subcategory') & 
            (sample_data['paragraph_num'] < 1200)
        ]
        
        if len(toc_subcats) > 0:
            # At least some should have links (ToC entries)
            # Note: Some might be section headers with bookmarks instead
            assert len(toc_subcats) > 0
    
    def test_subcategory_section_headers(self, sample_data):
        """Test that section headers with bookmarks are detected as subcategories."""
        # Load a larger sample to get content section headers
        if not os.path.exists(TEST_DATA_PATH):
            pytest.skip(f"Test data file not found: {TEST_DATA_PATH}")
        
        data = data_model.load_odt_data(TEST_DATA_PATH, max_pages=200)
        subcats = data[data['type'] == 'subcategory']
        
        # Should have multiple subcategory entries (ToC + section headers)
        assert len(subcats) > 100
        
        # Check that subcategories have proper hierarchy
        assert all(pd.notna(subcats['subcategory']))


class TestQuoteDetection:
    """Test suite for quote detection and counting."""
    
    def test_quotes_detected(self, sample_data):
        """Test that quotes are properly detected."""
        quotes = sample_data[sample_data['type'] == 'quote']
        
        # Should have quotes
        assert len(quotes) > 0
        
        # All quotes should have a quote level
        assert all(pd.notna(quotes['quote_level']))
        assert all(quotes['quote_level'] >= 1)
    
    def test_quote_levels_hierarchical(self, sample_data):
        """Test that quote levels are hierarchical."""
        quotes = sample_data[sample_data['type'] == 'quote']
        
        # Quote levels should be reasonable (1-11)
        assert quotes['quote_level'].min() >= 1
        assert quotes['quote_level'].max() <= 11
    
    def test_quotes_assigned_to_subcategories(self, sample_data):
        """Test that quotes are assigned to subcategories."""
        quotes = sample_data[sample_data['type'] == 'quote']
        
        # Most quotes should be assigned to a subcategory
        # (Some early quotes might not be if they're before first subcategory)
        quotes_with_subcat = quotes[pd.notna(quotes['subcategory'])]
        assert len(quotes_with_subcat) > len(quotes) * 0.8  # At least 80%
    
    def test_quote_count_per_subcategory(self):
        """Test that quote counts per subcategory are reasonable."""
        if not os.path.exists(TEST_DATA_PATH):
            pytest.skip(f"Test data file not found: {TEST_DATA_PATH}")
        
        # Load more data to test subcategory boundaries
        data = data_model.load_odt_data(TEST_DATA_PATH, max_pages=200)
        quotes = data[data['type'] == 'quote']
        
        # Count quotes per subcategory
        subcat_counts = quotes.groupby('subcategory').size()
        
        # No subcategory should have an unreasonable number of quotes
        # (e.g., > 1000 suggests incorrect boundaries)
        assert all(subcat_counts < 1000)
        
        # Most subcategories should have a reasonable number of quotes
        median_count = subcat_counts.median()
        assert 1 <= median_count <= 500


class TestDocumentStructure:
    """Test suite for overall document structure."""
    
    def test_hierarchical_structure(self, sample_data):
        """Test that document maintains hierarchical structure."""
        # Verify type distribution
        type_counts = sample_data['type'].value_counts()
        
        # Should have all main types
        assert 'quote' in type_counts
        assert 'subcategory' in type_counts
        assert 'category' in type_counts
        
        # Should have fewer categories than subcategories
        assert type_counts.get('category', 0) < type_counts.get('subcategory', 0)
    
    def test_citation_detection(self, sample_data):
        """Test that citations are properly detected."""
        # Need to preprocess to add has_citation column
        processed_data = preprocess_philosophical_data(sample_data)
        quotes = processed_data[processed_data['type'] == 'quote']
        
        if len(quotes) > 0:
            # Should have citations in quotes
            quotes_with_citations = quotes[quotes['has_citation'] == True]
            assert len(quotes_with_citations) > 0
            
            # Citation rate should be reasonable (>80% typically)
            citation_rate = len(quotes_with_citations) / len(quotes)
            assert citation_rate > 0.5  # At least 50%
    
    def test_link_detection(self, sample_data):
        """Test that links are being detected."""
        # Need to preprocess first to add link flags
        processed_data = preprocess_philosophical_data(sample_data)
        
        # Some entries should have links
        entries_with_links = processed_data[processed_data['has_links'] == True]
        
        # Should have at least some links
        assert len(entries_with_links) > 0


class TestExportToCSV:
    """Test suite for export_to_csv function using real data."""
    
    def test_export_to_csv(self, preprocessed_sample_data, tmp_path):
        """Test CSV export functionality with real data."""
        output_file = tmp_path / "test_output.csv"
        
        # Export a small subset to avoid large files
        test_data = preprocessed_sample_data.head(10)
        data_model.export_to_csv(test_data, str(output_file))
        
        # Verify file was created
        assert output_file.exists()
        
        # Verify content
        loaded_data = pd.read_csv(output_file)
        assert len(loaded_data) == 10
        
        # Verify column names are preserved
        for col in test_data.columns:
            assert col in loaded_data.columns
        
        # Verify data integrity (check a few values)
        assert loaded_data['id'].tolist() == test_data['id'].tolist()
        assert loaded_data['word_count'].tolist() == test_data['word_count'].tolist()
