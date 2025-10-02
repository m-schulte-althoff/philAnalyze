"""
Views module for philAnalyze - Visualization functions for philosophical text analysis.

This module contains all visualization and reporting functions for exploring
and presenting philosophical text data analysis results.
"""

import logging
import matplotlib.pyplot as plt
import pandas as pd
import os

# Configure logging
logger = logging.getLogger(__name__)


def visualize_text_overview(data):
    """
    Generate comprehensive visualizations of the philosophical text dataset.
    
    Creates multiple plots to understand:
    - Distribution of text lengths
    - Document structure and composition
    - Content characteristics
    
    Args:
        data (pd.DataFrame): Preprocessed philosophical text dataset with columns
                            like 'text', 'length', 'section', etc.
    """
    
    if data is None or len(data) == 0:
        logger.warning("No data available for visualization.")
        return
    
    # Create output directory for plots
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("Creating text overview visualizations...")
    
    # Visualization 1: Text length distribution
    _plot_text_length_distribution(data, output_dir)
    
    # Visualization 2: Content statistics
    _plot_content_statistics(data, output_dir)
    
    logger.info(f"Visualizations saved to {output_dir}/")


def _plot_text_length_distribution(data, output_dir):
    """
    Plot the distribution of text lengths in the dataset.
    
    Args:
        data (pd.DataFrame): Dataset with 'length' column
        output_dir (str): Directory to save the plot
    """
    
    if 'length' not in data.columns:
        logger.warning("'length' column not found. Skipping length distribution plot.")
        return
    
    plt.figure(figsize=(10, 6))
    plt.hist(data['length'], bins=30, edgecolor='black', alpha=0.7)
    plt.xlabel('Text Length (characters)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Text Lengths')
    plt.grid(True, alpha=0.3)
    
    output_path = os.path.join(output_dir, 'text_length_distribution.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved text length distribution to {output_path}")


def _plot_content_statistics(data, output_dir):
    """
    Plot basic content statistics from the dataset.
    
    Args:
        data (pd.DataFrame): Dataset with text content
        output_dir (str): Directory to save the plot
    """
    
    # Calculate basic statistics
    stats = {
        'Total Records': len(data),
        'Total Characters': data.get('length', pd.Series([0])).sum() if 'length' in data.columns else 0,
        'Avg Length': data.get('length', pd.Series([0])).mean() if 'length' in data.columns else 0,
        'Max Length': data.get('length', pd.Series([0])).max() if 'length' in data.columns else 0
    }
    
    # Create bar plot of statistics
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(stats)), list(stats.values()), alpha=0.7)
    plt.xticks(range(len(stats)), list(stats.keys()), rotation=45, ha='right')
    plt.ylabel('Count')
    plt.title('Content Statistics Overview')
    plt.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom')
    
    output_path = os.path.join(output_dir, 'content_statistics.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved content statistics to {output_path}")
    
    # Log statistics to console
    logger.info("Content Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.2f}")
        else:
            logger.info(f"  {key}: {value:,}")


def visualize_section_breakdown(data, section_column='section'):
    """
    Visualize the breakdown of content by sections.
    
    Args:
        data (pd.DataFrame): Dataset with section information
        section_column (str): Name of the column containing section labels
    """
    
    if section_column not in data.columns:
        logger.warning(f"'{section_column}' column not found. Skipping section breakdown.")
        return
    
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    # Count records per section
    section_counts = data[section_column].value_counts()
    
    plt.figure(figsize=(12, 6))
    section_counts.plot(kind='bar', alpha=0.7)
    plt.xlabel('Section')
    plt.ylabel('Number of Records')
    plt.title('Distribution of Records by Section')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    
    output_path = os.path.join(output_dir, 'section_breakdown.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved section breakdown to {output_path}")


def generate_summary_report(data, output_path='output/summary_report.txt'):
    """
    Generate a text-based summary report of the dataset.
    
    Args:
        data (pd.DataFrame): Dataset to summarize
        output_path (str): Path where the report will be saved
    """
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("PHILOSOPHICAL TEXT ANALYSIS - SUMMARY REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Total Records: {len(data)}\n")
        f.write(f"Columns: {', '.join(data.columns)}\n\n")
        
        if 'length' in data.columns:
            f.write("TEXT LENGTH STATISTICS:\n")
            f.write(f"  Mean: {data['length'].mean():.2f} characters\n")
            f.write(f"  Median: {data['length'].median():.2f} characters\n")
            f.write(f"  Min: {data['length'].min()} characters\n")
            f.write(f"  Max: {data['length'].max()} characters\n")
            f.write(f"  Total: {data['length'].sum():,} characters\n\n")
        
        f.write("=" * 60 + "\n")
    
    logger.info(f"Summary report saved to {output_path}")
