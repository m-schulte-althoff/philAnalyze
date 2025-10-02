"""
Unit tests for data_model module.

Tests for loading ODT files and preprocessing philosophical text data.
"""

import pytest
import pandas as pd
import os
from unittest.mock import Mock, patch, MagicMock
import data_model


class TestLoadODTData:
    """Test suite for load_odt_data function."""
    
    def test_load_odt_data_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError):
            data_model.load_odt_data('nonexistent_file.odt')
    
    @patch('data_model.Document')
    def test_load_odt_data_success(self, mock_document):
        """Test successful loading of ODT file."""
        # Mock the ODT document structure
        mock_paragraph1 = Mock()
        mock_paragraph1.text = "First paragraph text"
        mock_paragraph1.style = "body"
        
        mock_paragraph2 = Mock()
        mock_paragraph2.text = "Second paragraph text"
        mock_paragraph2.style = "heading"
        
        mock_body = Mock()
        mock_body.paragraphs = [mock_paragraph1, mock_paragraph2]
        
        mock_doc = Mock()
        mock_doc.body = mock_body
        mock_document.return_value = mock_doc
        
        # Load data
        result = data_model.load_odt_data('test.odt')
        
        # Assertions
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'text' in result.columns
        assert 'paragraph_num' in result.columns
        assert 'style' in result.columns
        assert 'length' in result.columns
    
    @patch('data_model.Document')
    def test_load_odt_data_empty_paragraphs_filtered(self, mock_document):
        """Test that empty paragraphs are filtered out."""
        mock_paragraph1 = Mock()
        mock_paragraph1.text = "Content paragraph"
        mock_paragraph1.style = "body"
        
        mock_paragraph2 = Mock()
        mock_paragraph2.text = "   "  # Empty/whitespace only
        mock_paragraph2.style = "body"
        
        mock_body = Mock()
        mock_body.paragraphs = [mock_paragraph1, mock_paragraph2]
        
        mock_doc = Mock()
        mock_doc.body = mock_body
        mock_document.return_value = mock_doc
        
        result = data_model.load_odt_data('test.odt')
        
        # Should only have 1 paragraph (empty one filtered)
        assert len(result) == 1
        assert result.iloc[0]['text'] == "Content paragraph"


class TestPreprocessPhilosophicalData:
    """Test suite for preprocess_philosophical_data function."""
    
    def test_preprocess_empty_dataframe(self):
        """Test preprocessing with empty DataFrame."""
        empty_df = pd.DataFrame()
        result = data_model.preprocess_philosophical_data(empty_df)
        assert len(result) == 0
    
    def test_preprocess_adds_required_columns(self):
        """Test that preprocessing adds all required columns."""
        test_data = pd.DataFrame({
            'text': ['This is a test sentence.', 'Another test sentence!'],
            'style': ['body', 'body']
        })
        
        result = data_model.preprocess_philosophical_data(test_data)
        
        # Check all required columns are present
        assert 'id' in result.columns
        assert 'word_count' in result.columns
        assert 'sentence_count' in result.columns
        assert 'section' in result.columns
    
    def test_preprocess_word_count_calculation(self):
        """Test that word count is calculated correctly."""
        test_data = pd.DataFrame({
            'text': ['one two three', 'single'],
            'style': ['body', 'body']
        })
        
        result = data_model.preprocess_philosophical_data(test_data)
        
        assert result.iloc[0]['word_count'] == 3
        assert result.iloc[1]['word_count'] == 1
    
    def test_preprocess_sentence_count_calculation(self):
        """Test that sentence count is estimated correctly."""
        test_data = pd.DataFrame({
            'text': ['First sentence. Second sentence!', 'Only one?'],
            'style': ['body', 'body']
        })
        
        result = data_model.preprocess_philosophical_data(test_data)
        
        assert result.iloc[0]['sentence_count'] == 2
        assert result.iloc[1]['sentence_count'] == 1
    
    def test_preprocess_id_generation(self):
        """Test that unique IDs are generated sequentially."""
        test_data = pd.DataFrame({
            'text': ['Text 1', 'Text 2', 'Text 3'],
            'style': ['body', 'body', 'body']
        })
        
        result = data_model.preprocess_philosophical_data(test_data)
        
        assert list(result['id']) == [1, 2, 3]


class TestInferSections:
    """Test suite for _infer_sections helper function."""
    
    def test_infer_sections_no_style_column(self):
        """Test section inference when no style column exists."""
        test_data = pd.DataFrame({
            'text': ['Text 1', 'Text 2']
        })
        
        result = data_model._infer_sections(test_data)
        
        # Should return default section for all
        assert len(result) == 2
        assert all(result == 'Section 1')
    
    def test_infer_sections_with_headings(self):
        """Test section inference with heading styles."""
        test_data = pd.DataFrame({
            'text': ['Intro', 'Heading 1', 'Content 1', 'Heading 2', 'Content 2'],
            'style': ['body', 'heading', 'body', 'heading', 'body']
        })
        
        result = data_model._infer_sections(test_data)
        
        # First should be Introduction, then sections increment
        assert result.iloc[0] == 'Introduction'
        assert result.iloc[1] == 'Section 1'
        assert result.iloc[2] == 'Section 1'
        assert result.iloc[3] == 'Section 2'
        assert result.iloc[4] == 'Section 2'


class TestGetTextStatistics:
    """Test suite for get_text_statistics function."""
    
    def test_statistics_empty_data(self):
        """Test statistics calculation with empty data."""
        result = data_model.get_text_statistics(None)
        assert result == {}
        
        empty_df = pd.DataFrame()
        result = data_model.get_text_statistics(empty_df)
        assert result == {}
    
    def test_statistics_calculation(self):
        """Test that statistics are calculated correctly."""
        test_data = pd.DataFrame({
            'word_count': [10, 20, 30],
            'length': [50, 100, 150]
        })
        
        result = data_model.get_text_statistics(test_data)
        
        assert result['total_paragraphs'] == 3
        assert result['total_words'] == 60
        assert result['total_characters'] == 300
        assert result['avg_words_per_paragraph'] == 20.0
        assert result['max_paragraph_length'] == 150
        assert result['min_paragraph_length'] == 50


class TestFilterByLength:
    """Test suite for filter_by_length function."""
    
    def test_filter_min_words(self):
        """Test filtering by minimum word count."""
        test_data = pd.DataFrame({
            'text': ['short', 'medium text here', 'very long text with many words'],
            'word_count': [1, 3, 6]
        })
        
        result = data_model.filter_by_length(test_data, min_words=3)
        
        assert len(result) == 2
        assert result.iloc[0]['word_count'] == 3
        assert result.iloc[1]['word_count'] == 6
    
    def test_filter_max_words(self):
        """Test filtering by maximum word count."""
        test_data = pd.DataFrame({
            'text': ['short', 'medium text here', 'very long text with many words'],
            'word_count': [1, 3, 6]
        })
        
        result = data_model.filter_by_length(test_data, max_words=3)
        
        assert len(result) == 2
        assert result.iloc[0]['word_count'] == 1
        assert result.iloc[1]['word_count'] == 3
    
    def test_filter_min_and_max_words(self):
        """Test filtering with both min and max constraints."""
        test_data = pd.DataFrame({
            'text': ['short', 'medium text here', 'very long text with many words'],
            'word_count': [1, 3, 6]
        })
        
        result = data_model.filter_by_length(test_data, min_words=2, max_words=5)
        
        assert len(result) == 1
        assert result.iloc[0]['word_count'] == 3


class TestExportToCSV:
    """Test suite for export_to_csv function."""
    
    def test_export_to_csv(self, tmp_path):
        """Test CSV export functionality."""
        test_data = pd.DataFrame({
            'text': ['Test text 1', 'Test text 2'],
            'word_count': [3, 3]
        })
        
        output_file = tmp_path / "test_output.csv"
        data_model.export_to_csv(test_data, str(output_file))
        
        # Verify file was created
        assert output_file.exists()
        
        # Verify content
        loaded_data = pd.read_csv(output_file)
        assert len(loaded_data) == 2
        assert list(loaded_data.columns) == ['text', 'word_count']
