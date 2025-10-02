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
    
    # Visualization 3: Quote hierarchy
    visualize_quote_hierarchy(data, output_dir)
    
    # Visualization 4: Subcategory distribution
    visualize_subcategory_distribution(data, output_dir)
    
    # Visualization 5: Top sources in citations
    visualize_top_sources(data, output_dir)
    
    # Visualization 6: Top authors in citations
    visualize_top_authors(data, output_dir)
    
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
    Plot content statistics from the dataset, including hierarchical metrics.
    
    Args:
        data (pd.DataFrame): Dataset with text content
        output_dir (str): Directory to save the plot
    """
    
    # Calculate statistics
    quotes = data[data['type'] == 'quote'] if 'type' in data.columns else pd.DataFrame()
    subcategories = data[data['type'] == 'subcategory'] if 'type' in data.columns else pd.DataFrame()
    categories = data[data['type'] == 'category'] if 'type' in data.columns else pd.DataFrame()
    
    stats = {
        'Total Records': len(data),
        'Categories': len(categories),
        'Subcategories': len(subcategories),
        'Quotes': len(quotes),
        'With Citations': data.get('has_citation', pd.Series([False])).sum(),
        'With Links': data.get('has_links', pd.Series([False])).sum(),
    }
    
    # Create bar plot of statistics
    plt.figure(figsize=(12, 6))
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


def visualize_quote_hierarchy(data, output_dir='output'):
    """
    Visualize the distribution of quotes across hierarchical levels.
    
    Args:
        data (pd.DataFrame): Dataset with 'type' and 'quote_level' columns
        output_dir (str): Directory to save the plot
    """
    
    if 'quote_level' not in data.columns:
        logger.warning("'quote_level' column not found. Skipping hierarchy visualization.")
        return
    
    quotes = data[data['type'] == 'quote'].copy()
    
    if len(quotes) == 0:
        logger.warning("No quotes found. Skipping hierarchy visualization.")
        return
    
    # Count quotes by level
    level_counts = quotes['quote_level'].value_counts().sort_index()
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(level_counts.index, level_counts.values, alpha=0.7, color='steelblue')
    plt.xlabel('Quote Level')
    plt.ylabel('Number of Quotes')
    plt.title('Distribution of Quotes Across Hierarchical Levels')
    plt.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom')
    
    output_path = os.path.join(output_dir, 'quote_hierarchy.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved quote hierarchy visualization to {output_path}")


def visualize_subcategory_distribution(data, output_dir='output', top_n=15):
    """
    Visualize the distribution of quotes across subcategories.
    
    Args:
        data (pd.DataFrame): Dataset with 'subcategory' column
        output_dir (str): Directory to save the plot
        top_n (int): Number of top subcategories to display
    """
    
    if 'subcategory' not in data.columns or 'type' not in data.columns:
        logger.warning("Required columns not found. Skipping subcategory visualization.")
        return
    
    quotes = data[data['type'] == 'quote'].copy()
    
    if len(quotes) == 0:
        logger.warning("No quotes found. Skipping subcategory visualization.")
        return
    
    # Filter out None values and count quotes by subcategory
    quotes_with_subcat = quotes[quotes['subcategory'].notna()]
    
    if len(quotes_with_subcat) == 0:
        logger.warning("No quotes with subcategories found. Skipping visualization.")
        return
    
    subcat_counts = quotes_with_subcat['subcategory'].value_counts().head(top_n)
    
    plt.figure(figsize=(12, 8))
    bars = plt.barh(range(len(subcat_counts)), subcat_counts.values, alpha=0.7, color='coral')
    
    # Clean up subcategory names (remove extra whitespace from ToC formatting)
    labels = []
    for name in subcat_counts.index:
        # Remove extra spaces and truncate if too long
        cleaned = ' '.join(str(name).split())  # Remove multiple spaces
        if len(cleaned) > 50:
            cleaned = cleaned[:50] + '...'
        labels.append(cleaned)
    
    plt.yticks(range(len(subcat_counts)), labels)
    
    plt.xlabel('Number of Quotes')
    plt.title(f'Top {top_n} Subcategories by Quote Count')
    plt.grid(True, alpha=0.3, axis='x')
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2.,
                f' {int(width)}',
                ha='left', va='center')
    
    output_path = os.path.join(output_dir, 'subcategory_distribution.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved subcategory distribution to {output_path}")


def visualize_top_sources(data, output_dir='output', top_n=15):
    """
    Visualize the top sources used in citations.
    
    Args:
        data (pd.DataFrame): Dataset with 'citation_source' column
        output_dir (str): Directory to save the plot
        top_n (int): Number of top sources to display
    """
    
    if 'citation_source' not in data.columns:
        logger.warning("'citation_source' column not found. Skipping source visualization.")
        return
    
    # Filter to entries with citations
    citations_with_source = data[data['citation_source'].notna()]
    
    if len(citations_with_source) == 0:
        logger.warning("No citations with sources found. Skipping source visualization.")
        return
    
    # Count occurrences of each source
    source_counts = citations_with_source['citation_source'].value_counts().head(top_n)
    
    plt.figure(figsize=(12, 8))
    bars = plt.barh(range(len(source_counts)), source_counts.values, alpha=0.7, color='mediumseagreen')
    
    # Clean up source names
    labels = []
    for source in source_counts.index:
        cleaned = str(source).strip()
        if len(cleaned) > 60:
            cleaned = cleaned[:60] + '...'
        labels.append(cleaned)
    
    plt.yticks(range(len(source_counts)), labels)
    plt.xlabel('Number of Citations')
    plt.title(f'Top {top_n} Sources Used in Citations')
    plt.grid(True, alpha=0.3, axis='x')
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2.,
                f' {int(width)}',
                ha='left', va='center')
    
    output_path = os.path.join(output_dir, 'top_sources_citations.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved top sources visualization to {output_path}")


def visualize_top_authors(data, output_dir='output', top_n=15):
    """
    Visualize the top authors used in citations.
    
    Args:
        data (pd.DataFrame): Dataset with 'citation_author' column
        output_dir (str): Directory to save the plot
        top_n (int): Number of top authors to display
    """
    
    if 'citation_author' not in data.columns:
        logger.warning("'citation_author' column not found. Skipping author visualization.")
        return
    
    # Filter to entries with citations
    citations_with_author = data[data['citation_author'].notna()]
    
    if len(citations_with_author) == 0:
        logger.warning("No citations with authors found. Skipping author visualization.")
        return
    
    # Count occurrences of each author
    author_counts = citations_with_author['citation_author'].value_counts().head(top_n)
    
    plt.figure(figsize=(12, 8))
    bars = plt.barh(range(len(author_counts)), author_counts.values, alpha=0.7, color='steelblue')
    
    # Clean up author names
    labels = []
    for author in author_counts.index:
        cleaned = str(author).strip()
        if len(cleaned) > 50:
            cleaned = cleaned[:50] + '...'
        labels.append(cleaned)
    
    plt.yticks(range(len(author_counts)), labels)
    plt.xlabel('Number of Citations')
    plt.title(f'Top {top_n} Authors in Citations')
    plt.grid(True, alpha=0.3, axis='x')
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2.,
                f' {int(width)}',
                ha='left', va='center')
    
    output_path = os.path.join(output_dir, 'top_authors_citations.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved top authors visualization to {output_path}")


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
