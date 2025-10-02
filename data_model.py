"""
Data model module for philAnalyze - Data loading and preprocessing.

This module handles all data-related operations:
- Loading ODT (OpenDocument Text) files
- Extracting text and metadata
- Preprocessing and cleaning data
- Data structure transformations
"""

import logging
import pandas as pd
from odfdo import Document

# Configure logging
logger = logging.getLogger(__name__)


def load_odt_data(file_path):
    """
    Load and parse an ODT (OpenDocument Text) file.
    
    Extracts textual content from ODT files, preserving structure where possible.
    ODT files are XML-based documents that may contain:
    - Paragraphs of text
    - Headings and sections
    - Lists and tables
    - Metadata (author, creation date, etc.)
    
    Args:
        file_path (str): Path to the ODT file to load
        
    Returns:
        pd.DataFrame: DataFrame with columns:
            - 'text': Extracted text content
            - 'paragraph_num': Sequential paragraph number
            - 'style': Paragraph style (heading, body, etc.)
            
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file cannot be parsed as valid ODT
    """
    
    logger.info(f"Loading ODT file: {file_path}")
    
    try:
        # Load the ODT document
        document = Document(file_path)
        body = document.body
        
        # Extract all paragraphs
        paragraphs = body.paragraphs
        
        # Build structured data
        data_records = []
        
        for idx, paragraph in enumerate(paragraphs, start=1):
            text = paragraph.text
            
            # Skip empty paragraphs
            if not text or text.strip() == '':
                continue
            
            # Extract paragraph style if available
            style_name = paragraph.style if hasattr(paragraph, 'style') else 'body'
            
            data_records.append({
                'paragraph_num': idx,
                'text': text.strip(),
                'style': style_name,
                'length': len(text.strip())
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data_records)
        
        logger.info(f"Successfully loaded {len(df)} paragraphs from {file_path}")
        
        return df
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Cannot find ODT file: {file_path}") from e
    
    except Exception as e:
        logger.error(f"Error parsing ODT file: {str(e)}")
        raise ValueError(f"Failed to parse ODT file {file_path}: {str(e)}") from e


def preprocess_philosophical_data(data):
    """
    Preprocess philosophical text data for analysis.
    
    Performs data cleaning and enrichment:
    - Adds unique identifiers
    - Calculates text statistics
    - Identifies section boundaries
    - Normalizes text formatting
    
    Args:
        data (pd.DataFrame): Raw data loaded from ODT file
        
    Returns:
        pd.DataFrame: Preprocessed data with additional columns:
            - 'id': Unique identifier for each record
            - 'word_count': Number of words in the text
            - 'sentence_count': Estimated number of sentences
            - 'section': Inferred section label (if detectable)
    """
    
    logger.info("Preprocessing philosophical text data...")
    
    if data is None or len(data) == 0:
        logger.warning("No data to preprocess.")
        return data
    
    # Add unique ID column
    data['id'] = range(1, len(data) + 1)
    
    # Calculate word count
    data['word_count'] = data['text'].apply(lambda x: len(str(x).split()))
    
    # Estimate sentence count (simple heuristic: count periods, exclamation marks, question marks)
    data['sentence_count'] = data['text'].apply(
        lambda x: str(x).count('.') + str(x).count('!') + str(x).count('?')
    )
    
    # Infer sections based on style (headings typically indicate new sections)
    data['section'] = _infer_sections(data)
    
    logger.info(f"Preprocessing complete. Total records: {len(data)}")
    logger.info(f"Total words: {data['word_count'].sum():,}")
    logger.info(f"Average words per paragraph: {data['word_count'].mean():.2f}")
    
    return data


def _infer_sections(data):
    """
    Infer section boundaries from paragraph styles.
    
    Identifies headings and assigns section labels to subsequent paragraphs
    until the next heading is encountered.
    
    Args:
        data (pd.DataFrame): Data with 'style' column
        
    Returns:
        pd.Series: Section labels for each paragraph
    """
    
    if 'style' not in data.columns:
        # If no style information, create single section
        return pd.Series(['Section 1'] * len(data), index=data.index)
    
    sections = []
    current_section = 'Introduction'
    section_counter = 0
    
    for idx, row in data.iterrows():
        style = str(row.get('style', '')).lower()
        
        # Check if this is a heading (various heading style names)
        if 'heading' in style or 'title' in style or style.startswith('h'):
            section_counter += 1
            current_section = f"Section {section_counter}"
        
        sections.append(current_section)
    
    return pd.Series(sections, index=data.index)


def get_text_statistics(data):
    """
    Calculate comprehensive statistics about the text dataset.
    
    Args:
        data (pd.DataFrame): Preprocessed data
        
    Returns:
        dict: Dictionary of statistics including:
            - total_paragraphs: Total number of paragraphs
            - total_words: Total word count
            - total_characters: Total character count
            - avg_words_per_paragraph: Average words per paragraph
            - avg_chars_per_paragraph: Average characters per paragraph
    """
    
    if data is None or len(data) == 0:
        return {}
    
    stats = {
        'total_paragraphs': len(data),
        'total_words': data.get('word_count', pd.Series([0])).sum(),
        'total_characters': data.get('length', pd.Series([0])).sum(),
        'avg_words_per_paragraph': data.get('word_count', pd.Series([0])).mean(),
        'avg_chars_per_paragraph': data.get('length', pd.Series([0])).mean(),
        'max_paragraph_length': data.get('length', pd.Series([0])).max(),
        'min_paragraph_length': data.get('length', pd.Series([0])).min()
    }
    
    return stats


def filter_by_length(data, min_words=None, max_words=None):
    """
    Filter data by text length criteria.
    
    Args:
        data (pd.DataFrame): Data to filter
        min_words (int, optional): Minimum word count threshold
        max_words (int, optional): Maximum word count threshold
        
    Returns:
        pd.DataFrame: Filtered data
    """
    
    if 'word_count' not in data.columns:
        logger.warning("'word_count' column not found. Cannot filter by length.")
        return data
    
    filtered = data.copy()
    
    if min_words is not None:
        filtered = filtered[filtered['word_count'] >= min_words]
        logger.info(f"Filtered to paragraphs with >= {min_words} words: {len(filtered)} records")
    
    if max_words is not None:
        filtered = filtered[filtered['word_count'] <= max_words]
        logger.info(f"Filtered to paragraphs with <= {max_words} words: {len(filtered)} records")
    
    return filtered


def export_to_csv(data, output_path):
    """
    Export data to CSV format.
    
    Args:
        data (pd.DataFrame): Data to export
        output_path (str): Path where CSV file will be saved
    """
    
    data.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f"Data exported to {output_path}")
