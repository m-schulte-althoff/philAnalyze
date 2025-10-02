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
    
    @patch('views._plot_text_length_distribution')
    @patch('views._plot_content_statistics')
    def test_visualize_calls_subfunctions(self, mock_stats, mock_length):
        """Test that visualization calls the appropriate plotting functions."""
        test_data = pd.DataFrame({
            'text': ['Test text 1', 'Test text 2'],
            'length': [100, 200]
        })
        
        views.visualize_text_overview(test_data)
        
        # Verify sub-functions were called
        mock_length.assert_called_once()
        mock_stats.assert_called_once()
    
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
            'length': [100, 200, 150]
        })
        
        views._plot_content_statistics(test_data, str(tmp_path))
        
        # Verify plot was saved
        mock_savefig.assert_called_once()
        mock_close.assert_called_once()
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_plot_handles_missing_length_column(self, mock_close, mock_savefig, tmp_path):
        """Test that plotting handles missing length column gracefully."""
        test_data = pd.DataFrame({
            'text': ['Text 1', 'Text 2']
        })
        
        # Should not raise error
        views._plot_content_statistics(test_data, str(tmp_path))
        
        mock_savefig.assert_called_once()
        mock_close.assert_called_once()


class TestVisualizeSectionBreakdown:
    """Test suite for visualize_section_breakdown function."""
    
    def test_visualize_missing_section_column(self):
        """Test visualization when section column is missing."""
        test_data = pd.DataFrame({
            'text': ['Test text']
        })
        
        # Should not raise error, just log warning
        views.visualize_section_breakdown(test_data)
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_visualize_section_breakdown_success(self, mock_close, mock_savefig, tmp_path, monkeypatch):
        """Test successful section breakdown visualization."""
        monkeypatch.chdir(tmp_path)
        
        test_data = pd.DataFrame({
            'text': ['Text 1', 'Text 2', 'Text 3', 'Text 4'],
            'section': ['Section 1', 'Section 1', 'Section 2', 'Section 3']
        })
        
        views.visualize_section_breakdown(test_data)
        
        # Verify plot was saved
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
