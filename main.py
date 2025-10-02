"""
Main entry point for philAnalyze - A philosophical text analysis tool.

This module orchestrates the complete analysis workflow for philosophical texts,
following a Model-View-Controller architecture pattern.
"""

import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# =============================================================================
# CONFIGURATION - Modify these flags to control which analyses to run
# =============================================================================

# Analysis module toggles
USE_VISUALIZATIONS = True       # Generate exploratory plots and result visualizations
EXPORT_TO_OBSIDIAN = False      # Export processed data in Obsidian-compatible format

# Data file paths
DATA_PATH = 'data/Phil.odt'     # Main philosophical text dataset (ODT format)

# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================

OUTPUT_DIR = 'output'           # Directory for analysis results and exports


def load_data(file_path):
    """
    Load data from an ODT file.
    
    This function reads philosophical text data from ODT (OpenDocument Text) files.
    ODT files are loaded and parsed to extract textual content for analysis.
    
    Args:
        file_path (str): Path to the ODT file to load
        
    Returns:
        pd.DataFrame: Loaded dataset with extracted text and metadata
        
    Raises:
        FileNotFoundError: If the specified file does not exist
        ValueError: If the file cannot be parsed as valid ODT
    """
    import data_model
    return data_model.load_odt_data(file_path)


def preprocess_data(data):
    """
    Preprocess the loaded data for analysis.
    
    Performs data cleaning and transformation operations:
    - Adds unique ID column for tracking records
    - Cleans and normalizes text content
    - Extracts metadata from document structure
    - Prepares data for downstream analysis modules
    
    Args:
        data (pd.DataFrame): Raw loaded dataset
        
    Returns:
        pd.DataFrame: Preprocessed dataset ready for analysis
    """
    import data_model
    return data_model.preprocess_philosophical_data(data)


def visualize_data(data):
    """
    Generate exploratory data visualizations.
    
    Creates visual overviews of the philosophical text dataset to understand:
    - Text length distributions
    - Content structure and organization
    - Key themes and patterns
    
    This helps with data quality assessment and understanding the
    composition of the dataset before running detailed analyses.
    
    Args:
        data (pd.DataFrame): Preprocessed philosophical text dataset
    """
    import views
    
    logging.info("Generating data visualizations...")
    
    # Generate exploratory visualizations
    views.visualize_text_overview(data)
    
    logging.info("Visualization complete.")


def export_to_obsidian(data, output_dir):
    """
    Transform and export data to Obsidian-compatible format.
    
    Converts the analyzed philosophical texts into a structure that can be
    imported into Obsidian (a markdown-based knowledge management system).
    
    The export includes:
    - Individual markdown files for each text/section
    - Metadata frontmatter (YAML)
    - Internal links between related concepts
    - Tag structure for organization
    
    Args:
        data (pd.DataFrame): Processed dataset to export
        output_dir (str): Directory where Obsidian files will be saved
        
    Returns:
        dict: Export statistics (files created, links generated, etc.)
    """
    import obsidian_export
    
    logging.info("Exporting data to Obsidian format...")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Perform export
    export_stats = obsidian_export.export_to_markdown(data, output_dir)
    
    logging.info(f"Export complete. Files created: {export_stats.get('files_created', 0)}")
    
    return export_stats


def main():
    """
    Main analysis pipeline for philosophical text analysis.
    
    This function orchestrates the complete analysis workflow:
    1. Data loading from ODT file
    2. Data preprocessing and cleaning
    3. Exploratory data visualization
    4. Optional export to Obsidian format
    
    The pipeline is modular - each analysis step can be enabled/disabled
    via configuration flags at the top of the file.
    """
    
    logging.info("Starting philAnalyze pipeline...")
    
    # STEP 1: Load the philosophical text data
    logging.info(f"Loading data from {DATA_PATH}...")
    phil_data = load_data(DATA_PATH)
    
    # STEP 2: Preprocess the data
    logging.info("Preprocessing data...")
    phil_data = preprocess_data(phil_data)
    
    logging.info(f"Loaded {len(phil_data)} records.")
    
    # STEP 3: Generate exploratory visualizations (if enabled)
    if USE_VISUALIZATIONS:
        visualize_data(phil_data)
    
    # STEP 4: Export to Obsidian format (if enabled)
    if EXPORT_TO_OBSIDIAN:
        obsidian_output_dir = os.path.join(OUTPUT_DIR, 'obsidian')
        export_to_obsidian(phil_data, obsidian_output_dir)
    
    logging.info("Pipeline complete!")


if __name__ == "__main__":
    main()
