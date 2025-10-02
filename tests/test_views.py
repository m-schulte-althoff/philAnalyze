"""
Unit tests for views module.

Tests for visualization and reporting functions.
"""

import pytest
import pandas as pd
import os
from unittest.mock import Mock, patch, MagicMock
import views


class TestVisualizeTextOverview:
    """Test suite for visualize_text_overview function."""
    
    def test_visualize_empty_data(self):
        """Test visualization with empty data."""
        # Should not raise error, just log warning
        views.visualize_text_overview(None)
        
        empty_df = pd.DataFrame()
        views.visualize_text_overview(empty_df)
    
    @patch('views.visualize_top_authors')
    @patch('views.visualize_top_sources')
    @patch('views.visualize_subcategory_distribution')
    @patch('views.visualize_quote_hierarchy')
    @patch('views._plot_content_statistics')
    @patch('views._plot_text_length_distribution')
    def test_visualize_calls_subfunctions(self, mock_length, mock_stats, mock_hierarchy, 
                                          mock_subcat, mock_sources, mock_authors):
        """Test that visualize_text_overview calls expected sub-functions."""
        test_data = pd.DataFrame({
            'text': ['Test'],
            'length': [100]
        })
        
        views.visualize_text_overview(test_data)
        
        # Verify sub-functions were called
        mock_length.assert_called_once()
        mock_stats.assert_called_once()
        mock_hierarchy.assert_called_once()
        mock_subcat.assert_called_once()
        mock_sources.assert_called_once()
        mock_authors.assert_called_once()
    
    def test_visualize_creates_output_directory(self, tmp_path, monkeypatch):
        """Test that output directory is created if it doesn't exist."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        test_data = pd.DataFrame({
            'text': ['Test'],
            'length': [100]
        })
        
        with patch('matplotlib.pyplot.savefig'):
            with patch('matplotlib.pyplot.close'):
                views.visualize_text_overview(test_data)
        
        # Check that output directory was created
        assert os.path.exists('output')


class TestPlotTextLengthDistribution:
    """Test suite for _plot_text_length_distribution function."""
    
    def test_plot_missing_length_column(self, tmp_path):
        """Test plotting when length column is missing."""
        test_data = pd.DataFrame({
            'text': ['Test text']
        })
        
        # Should not raise error, just log warning
        views._plot_text_length_distribution(test_data, str(tmp_path))
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_plot_creates_histogram(self, mock_close, mock_savefig, tmp_path):
        """Test that histogram is created and saved."""
        test_data = pd.DataFrame({
            'length': [100, 200, 150, 300, 250]
        })
        
        views._plot_text_length_distribution(test_data, str(tmp_path))
        
        # Verify plot was saved
        mock_savefig.assert_called_once()
        mock_close.assert_called_once()


class TestPlotContentStatistics:
    """Test suite for _plot_content_statistics function."""
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_plot_content_statistics_basic(self, mock_close, mock_savefig, tmp_path):
        """Test basic content statistics plotting."""
        test_data = pd.DataFrame({
            'text': ['Text 1', 'Text 2', 'Text 3'],
            'length': [100, 200, 150],
            'type': ['quote', 'subcategory', 'quote']
        })
        
        views._plot_content_statistics(test_data, str(tmp_path))
        
        # Verify plot was saved
        mock_savefig.assert_called_once()
        mock_close.assert_called_once()
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_plot_includes_categories(self, mock_close, mock_savefig, tmp_path):
        """Test that content statistics include categories."""
        test_data = pd.DataFrame({
            'text': ['Cat 1', 'Subcat 1', 'Quote 1', 'Quote 2'],
            'type': ['category', 'subcategory', 'quote', 'quote'],
            'length': [10, 20, 100, 150]
        })
        
        views._plot_content_statistics(test_data, str(tmp_path))
        
        # Verify plot was created
        mock_savefig.assert_called_once()
        mock_close.assert_called_once()
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_plot_handles_missing_type_column(self, mock_close, mock_savefig, tmp_path):
        """Test that plotting handles missing type column gracefully."""
        test_data = pd.DataFrame({
            'text': ['Text 1', 'Text 2']
        })
        
        # Should not raise error
        views._plot_content_statistics(test_data, str(tmp_path))
        
        mock_savefig.assert_called_once()
        mock_close.assert_called_once()


class TestGenerateSummaryReport:
    """Test suite for generate_summary_report function."""
    
    def test_generate_summary_report_basic(self, tmp_path):
        """Test basic summary report generation."""
        test_data = pd.DataFrame({
            'text': ['Text 1', 'Text 2', 'Text 3'],
            'length': [100, 200, 150]
        })
        
        output_path = tmp_path / 'summary.txt'
        views.generate_summary_report(test_data, str(output_path))
        
        # Verify file was created
        assert output_path.exists()
        
        # Verify content
        content = output_path.read_text(encoding='utf-8')
        assert 'SUMMARY REPORT' in content
        assert 'Total Records: 3' in content
        assert 'TEXT LENGTH STATISTICS' in content
    
    def test_generate_summary_report_no_length_column(self, tmp_path):
        """Test summary report without length column."""
        test_data = pd.DataFrame({
            'text': ['Text 1', 'Text 2']
        })
        
        output_path = tmp_path / 'summary.txt'
        views.generate_summary_report(test_data, str(output_path))
        
        # Should still create file
        assert output_path.exists()
        
        content = output_path.read_text(encoding='utf-8')
        assert 'Total Records: 2' in content
    
    def test_generate_summary_report_creates_directory(self, tmp_path):
        """Test that report function creates output directory if needed."""
        output_path = tmp_path / 'nested' / 'dir' / 'summary.txt'
        
        test_data = pd.DataFrame({
            'text': ['Test']
        })
        
        views.generate_summary_report(test_data, str(output_path))
        
        # Verify directory and file were created
        assert output_path.exists()
        assert output_path.parent.exists()


class TestVisualizeTopSources:
    """Test suite for top sources visualization."""
    
    def test_visualize_top_sources_basic(self, tmp_path):
        """Test basic top sources visualization."""
        test_data = pd.DataFrame({
            'citation_source': ['Source A', 'Source B', 'Source A', 'Source C', 'Source A']
        })
        
        views.visualize_top_sources(test_data, str(tmp_path), top_n=3)
        
        # Verify output file was created
        output_file = tmp_path / 'top_sources_citations.png'
        assert output_file.exists()
    
    def test_visualize_top_sources_missing_column(self, tmp_path, caplog):
        """Test handling of missing citation_source column."""
        test_data = pd.DataFrame({
            'text': ['Test 1', 'Test 2']
        })
        
        views.visualize_top_sources(test_data, str(tmp_path))
        
        # Should log warning and not create file
        assert 'citation_source' in caplog.text
        output_file = tmp_path / 'top_sources_citations.png'
        assert not output_file.exists()
    
    def test_visualize_top_sources_empty_citations(self, tmp_path, caplog):
        """Test handling of data with no citations."""
        test_data = pd.DataFrame({
            'citation_source': [None, None, None]
        })
        
        views.visualize_top_sources(test_data, str(tmp_path))
        
        # Should log warning and not create file
        assert 'No citations with sources found' in caplog.text
        output_file = tmp_path / 'top_sources_citations.png'
        assert not output_file.exists()


class TestVisualizeTopAuthors:
    """Test suite for top authors visualization."""
    
    def test_visualize_top_authors_basic(self, tmp_path):
        """Test basic top authors visualization."""
        test_data = pd.DataFrame({
            'citation_author': ['Kant', 'Hegel', 'Kant', 'Nietzsche', 'Kant', 'Hegel']
        })
        
        views.visualize_top_authors(test_data, str(tmp_path), top_n=3)
        
        # Verify output file was created
        output_file = tmp_path / 'top_authors_citations.png'
        assert output_file.exists()
    
    def test_visualize_top_authors_missing_column(self, tmp_path, caplog):
        """Test handling of missing citation_author column."""
        test_data = pd.DataFrame({
            'text': ['Test 1', 'Test 2']
        })
        
        views.visualize_top_authors(test_data, str(tmp_path))
        
        # Should log warning and not create file
        assert 'citation_author' in caplog.text
        output_file = tmp_path / 'top_authors_citations.png'
        assert not output_file.exists()
    
    def test_visualize_top_authors_empty_citations(self, tmp_path, caplog):
        """Test handling of data with no authors."""
        test_data = pd.DataFrame({
            'citation_author': [None, None, None]
        })
        
        views.visualize_top_authors(test_data, str(tmp_path))
        
        # Should log warning and not create file
        assert 'No citations with authors found' in caplog.text
        output_file = tmp_path / 'top_authors_citations.png'
        assert not output_file.exists()
