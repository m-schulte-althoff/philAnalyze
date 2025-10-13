"""
Unit tests for main module.

Tests for the main pipeline orchestration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import main


class TestLoadData:
    """Test suite for load_data function."""
    
    @patch('data_model.load_odt_data')
    def test_load_data_calls_data_model(self, mock_load_odt):
        """Test that load_data delegates to data_model module."""
        mock_df = pd.DataFrame({'text': ['test']})
        mock_load_odt.return_value = mock_df
        
        result = main.load_data('test.odt')
        
        mock_load_odt.assert_called_once_with('test.odt', max_pages=None)
        assert result is mock_df


class TestPreprocessData:
    """Test suite for preprocess_data function."""
    
    @patch('data_model.preprocess_philosophical_data')
    def test_preprocess_data_calls_data_model(self, mock_preprocess):
        """Test that preprocess_data delegates to data_model module."""
        mock_input = pd.DataFrame({'text': ['test']})
        mock_output = pd.DataFrame({'text': ['test'], 'id': [1]})
        mock_preprocess.return_value = mock_output
        
        result = main.preprocess_data(mock_input)
        
        mock_preprocess.assert_called_once_with(mock_input)
        assert result is mock_output


class TestVisualizeData:
    """Test suite for visualize_data function."""
    
    @patch('views.visualize_text_overview')
    def test_visualize_data_calls_views(self, mock_visualize):
        """Test that visualize_data delegates to views module."""
        test_data = pd.DataFrame({'text': ['test']})
        
        main.visualize_data(test_data)
        
        mock_visualize.assert_called_once_with(test_data)


class TestExportToObsidian:
    """Test suite for export_to_obsidian function."""
    
    @patch('obsidian_export.export_to_markdown')
    @patch('main.os.makedirs')
    def test_export_to_obsidian_creates_directory(self, mock_makedirs, mock_export):
        """Test that export creates output directory."""
        test_data = pd.DataFrame({'text': ['test']})
        mock_export.return_value = {'files_created': 1}
        
        main.export_to_obsidian(test_data, 'output/obsidian')
        
        mock_makedirs.assert_called_once_with('output/obsidian', exist_ok=True)
    
    @patch('obsidian_export.export_to_markdown')
    @patch('main.os.makedirs')
    def test_export_to_obsidian_calls_export_module(self, mock_makedirs, mock_export):
        """Test that export delegates to obsidian_export module."""
        test_data = pd.DataFrame({'text': ['test']})
        expected_stats = {'files_created': 5, 'total_links': 10}
        mock_export.return_value = expected_stats
        
        result = main.export_to_obsidian(test_data, 'output/obsidian')
        
        mock_export.assert_called_once_with(test_data, 'output/obsidian')
        assert result == expected_stats


class TestMain:
    """Test suite for main function."""
    
    @patch('main.load_data')
    @patch('main.preprocess_data')
    @patch('main.visualize_data')
    @patch('main.export_to_obsidian')
    def test_main_pipeline_with_all_flags_enabled(self, mock_export, mock_viz, mock_preprocess, mock_load):
        """Test main pipeline with all features enabled."""
        # Setup mocks
        mock_data = pd.DataFrame({'text': ['test']})
        mock_load.return_value = mock_data
        mock_preprocess.return_value = mock_data
        
        # Temporarily enable all flags
        original_viz_flag = main.USE_VISUALIZATIONS
        original_export_flag = main.EXPORT_TO_OBSIDIAN
        
        main.USE_VISUALIZATIONS = True
        main.EXPORT_TO_OBSIDIAN = True
        
        try:
            main.main()
            
            # Verify pipeline execution
            mock_load.assert_called_once()
            mock_preprocess.assert_called_once()
            mock_viz.assert_called_once()
            mock_export.assert_called_once()
        finally:
            # Restore original flags
            main.USE_VISUALIZATIONS = original_viz_flag
            main.EXPORT_TO_OBSIDIAN = original_export_flag
    
    @patch('main.load_data')
    @patch('main.preprocess_data')
    @patch('main.visualize_data')
    @patch('main.export_to_obsidian')
    def test_main_pipeline_visualization_disabled(self, mock_export, mock_viz, mock_preprocess, mock_load):
        """Test that visualization is skipped when disabled."""
        # Setup mocks
        mock_data = pd.DataFrame({'text': ['test']})
        mock_load.return_value = mock_data
        mock_preprocess.return_value = mock_data
        
        # Disable visualization
        original_viz_flag = main.USE_VISUALIZATIONS
        original_export_flag = main.EXPORT_TO_OBSIDIAN
        
        main.USE_VISUALIZATIONS = False
        main.EXPORT_TO_OBSIDIAN = False
        
        try:
            main.main()
            
            # Verify visualization was skipped
            mock_viz.assert_not_called()
            mock_export.assert_not_called()
        finally:
            main.USE_VISUALIZATIONS = original_viz_flag
            main.EXPORT_TO_OBSIDIAN = original_export_flag
    
    @patch('main.load_data')
    @patch('main.preprocess_data')
    @patch('main.visualize_data')
    @patch('main.export_to_obsidian')
    def test_main_pipeline_export_disabled(self, mock_export, mock_viz, mock_preprocess, mock_load):
        """Test that export is skipped when disabled."""
        # Setup mocks
        mock_data = pd.DataFrame({'text': ['test']})
        mock_load.return_value = mock_data
        mock_preprocess.return_value = mock_data
        
        # Enable viz but disable export
        original_viz_flag = main.USE_VISUALIZATIONS
        original_export_flag = main.EXPORT_TO_OBSIDIAN
        
        main.USE_VISUALIZATIONS = True
        main.EXPORT_TO_OBSIDIAN = False
        
        try:
            main.main()
            
            # Verify export was skipped but viz was called
            mock_viz.assert_called_once()
            mock_export.assert_not_called()
        finally:
            main.USE_VISUALIZATIONS = original_viz_flag
            main.EXPORT_TO_OBSIDIAN = original_export_flag


class TestConfigurationConstants:
    """Test suite to verify configuration constants exist."""
    
    def test_configuration_flags_exist(self):
        """Test that all configuration flags are defined."""
        assert hasattr(main, 'USE_VISUALIZATIONS')
        assert hasattr(main, 'EXPORT_TO_OBSIDIAN')
        assert isinstance(main.USE_VISUALIZATIONS, bool)
        assert isinstance(main.EXPORT_TO_OBSIDIAN, bool)
    
    def test_data_paths_exist(self):
        """Test that data path constants are defined."""
        assert hasattr(main, 'DATA_PATH')
        assert isinstance(main.DATA_PATH, str)
    
    def test_output_dir_exists(self):
        """Test that output directory constant is defined."""
        assert hasattr(main, 'OUTPUT_DIR')
        assert isinstance(main.OUTPUT_DIR, str)
