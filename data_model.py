"""
Data model module for philAnalyze - Data loading and preprocessing.

This module handles all data-related operations:
- Loading ODT (OpenDocument Text) files with hierarchical quote structure
- Extracting text, citations, and hyperlinks
- Parsing hierarchical quotes with indentation levels
- Building nested data structures for subcategories and quotes
- Preprocessing and cleaning data
"""

import logging
import re
import pandas as pd
from odfdo import Document

# Configure logging
logger = logging.getLogger(__name__)

# Regular expressions for parsing
CITATION_PATTERN = re.compile(r'\[([^\]]+)\]$')  # Match citation in square brackets at end
QUOTE_MARKER_PATTERN = re.compile(r'^[\t\s]*([°^~+\-])\s+(.+)$')  # Match quote markers with indentation
LINK_REFERENCE_PATTERN = re.compile(r'\(vgl\.\)', re.IGNORECASE)  # Match (vgl.) link indicators


def parse_citation(text):
    """
    Parse citation information from quote text.
    
    Citations are in the format: [AUTHOR, "TITLE", in: COLLECTION/BOOK]
    The "in: COLLECTION" part is optional.
    
    Args:
        text (str): Text potentially ending with citation
        
    Returns:
        tuple: (quote_text, citation_dict) where citation_dict contains:
            - 'author': Author name
            - 'title': Title of work
            - 'source': Collection/book (optional)
            - 'raw': Raw citation text
    """
    match = CITATION_PATTERN.search(text.strip())
    
    if not match:
        return text.strip(), None
    
    # Extract quote without citation
    quote_text = text[:match.start()].strip()
    citation_raw = match.group(1)
    
    # Parse citation components
    citation = {'raw': citation_raw}
    
    # Split by commas (but be careful with commas in quotes)
    # Handle both straight quotes (") and curly quotes (" ")
    parts = []
    current_part = []
    in_quotes = False
    
    for char in citation_raw:
        # Check for quote characters (ASCII 34, left curly 8220, right curly 8221)
        if char in ['"', '\u201c', '\u201d']:
            in_quotes = not in_quotes
        elif char == ',' and not in_quotes:
            parts.append(''.join(current_part).strip())
            current_part = []
            continue
        current_part.append(char)
    
    if current_part:
        parts.append(''.join(current_part).strip())
    
    # Extract components
    if len(parts) >= 1:
        citation['author'] = parts[0]
    
    if len(parts) >= 2:
        # Extract title (remove quotes if present - handle both straight and curly quotes)
        title = parts[1].strip()
        # Remove leading quote (ASCII 34, left curly 8220, or right curly 8221)
        if title and title[0] in ['"', '\u201c', '\u201d']:
            title = title[1:]
        # Remove trailing quote (ASCII 34, left curly 8220, or right curly 8221)
        if title and title[-1] in ['"', '\u201c', '\u201d']:
            title = title[:-1]
        citation['title'] = title
    
    if len(parts) >= 3:
        # Check for "in:" prefix
        source = parts[2].strip()
        if source.lower().startswith('in:'):
            source = source[3:].strip()
        citation['source'] = source
    
    return quote_text, citation


def detect_quote_level(text):
    """
    Detect the hierarchical level of a quote based on indentation and marker.
    
    Quote levels are indicated by tab stops:
    - Level 1: 1 tab + marker (°, ^, ~, +, -)
    - Level 2: 2 tabs + marker
    - Level 3: 3 tabs + marker
    - etc.
    
    Args:
        text (str): Text line to analyze
        
    Returns:
        tuple: (level, marker, content) or (None, None, text) if not a quote
    """
    # Count leading tabs/spaces (treat 4 spaces as 1 tab)
    stripped = text.lstrip('\t ')
    indent_chars = text[:len(text) - len(stripped)]
    
    # Count tabs (convert spaces to tabs: 4 spaces = 1 tab)
    tab_count = indent_chars.count('\t') + (indent_chars.count(' ') // 4)
    
    # Check for quote marker
    match = QUOTE_MARKER_PATTERN.match(text)
    
    if match and tab_count > 0:
        marker = match.group(1)
        content = match.group(2).strip()
        level = tab_count
        return level, marker, content
    
    return None, None, text


def is_category_heading(paragraph, text):
    """
    Determine if a paragraph is a category heading.
    
    Category headings in the ToC are from a known list of 14 categories.
    They have:
    - Bold text (via span style, typically T1 or similar)
    - No tabs or indentation
    - No actual hyperlinks (<text:a> elements)
    - Short text matching expected category names
    - Not a quote (no markers)
    - Wrapped in Internet_20_link span (blue styling) with nested bold span
    
    Args:
        paragraph: ODT paragraph object
        text (str): Paragraph text
        
    Returns:
        bool: True if paragraph is a category heading
    """
    
    # List of known categories in the ToC
    EXPECTED_CATEGORIES = [
        'Allgemeine Begriffe', 'Ethik', 'Geschichte', 'Kommunikation, Sprache & Text',
        'Kunst & Kultur', 'Mathematik & Logik', 'Menschlich- & Soziales', 'Physik',
        'Politik', 'Recht', 'Religion', 'Technik & IT', 'Wirtschaft', 'Wissenschaft'
    ]
    
    stripped = text.strip()
    clean_text = ' '.join(stripped.split())  # Normalize spaces
    
    # Must match one of the expected categories exactly
    if clean_text not in EXPECTED_CATEGORIES:
        return False
    
    # Must not have tabs
    if '\t' in text:
        return False
    
    # Check for actual hyperlink elements (not just link styling)
    # Categories have NO <text:a> elements
    xml = paragraph.serialize() if hasattr(paragraph, 'serialize') else ''
    if '<text:a' in xml:
        return False
    
    return True


def is_subcategory_heading(paragraph, text):
    """
    Determine if a paragraph is a subcategory heading.
    
    Two types of subcategory headings:
    1. ToC entries: Have <text:a> hyperlink, no bookmark
    2. Content section headers: Have <text:bookmark-start>, bold/underlined, no link
    
    Both types are:
    - NOT indented (no tabs at start)
    - NOT a quote (no markers: °~^+-)
    - Relatively short (< 100 chars)
    - NOT a citation (no [...] pattern)
    
    Args:
        paragraph: ODT paragraph object
        text (str): Paragraph text
        
    Returns:
        bool: True if paragraph is a subcategory heading
    """
    
    stripped = text.strip()
    
    # Must not start with tab (subcategories are at root level)
    if text.startswith('\t') or text.startswith('    '):
        return False
    
    # Must not be a quote (no markers)
    if stripped and len(stripped) > 0 and stripped[0] in ['°', '~', '^', '+', '-']:
        return False
    
    # Must be reasonably short (subcategory names are typically < 100 chars)
    if len(stripped) == 0 or len(stripped) > 100:
        return False
    
    # Check XML structure
    xml = paragraph.serialize()
    
    # Type 1: ToC entries with hyperlinks (entire text is linked)
    # Type 2: Content section headers with bookmark (may or may not have link)
    has_link = '<text:a' in xml
    has_bookmark = '<text:bookmark-start' in xml
    
    if has_link and not has_bookmark:
        # Potential ToC entry: hyperlink to bookmark (no bookmark in this paragraph)
        # BUT: The entire text should be inside the link (not just a word)
        # Extract link text to verify
        import re
        link_match = re.search(r'<text:a[^>]*>(.*?)</text:a>', xml, re.DOTALL)
        if link_match:
            link_html = link_match.group(1)
            # Extract text from link (remove tags)
            link_text = re.sub(r'<[^>]+>', '', link_html).strip()
            # The link text should match the paragraph text (allowing for whitespace differences)
            if link_text and stripped and link_text.replace(' ', '') == stripped.replace(' ', ''):
                return True
        return False
    
    # Check if bookmark is inside the link (self-referential content header)
    bookmark_in_link = False
    if has_link and has_bookmark:
        # Simple check: if bookmark appears after <text:a and before </text:a>
        import re
        link_match = re.search(r'<text:a[^>]*>.*?</text:a>', xml, re.DOTALL)
        if link_match:
            link_content = link_match.group(0)
            bookmark_in_link = '<text:bookmark-start' in link_content
    
    if has_bookmark:
        # Content section header: has bookmark (with or without link)
        # Accept any paragraph with bookmark that meets basic criteria
        # (short, no tabs, no quote markers) regardless of styling
        return True
    
    return False


def get_text_with_tabs(paragraph):
    """
    Extract text from paragraph while preserving tab characters.
    
    The standard paragraph.text property strips out <text:tab> elements.
    This function reconstructs the text with \t characters where tabs appear.
    
    Args:
        paragraph: ODT paragraph object
        
    Returns:
        str: Text content with tabs preserved as \t characters
    """
    
    # Get the XML representation
    xml = paragraph.serialize()
    
    # Parse XML to reconstruct text with tabs
    # This is a simple approach that replaces <text:tab/> with \t
    import re
    
    try:
        # First, replace <text:tab.../> with \t
        content = re.sub(r'<text:tab[^/>]*/?>', '\t', xml)
        
        # Then strip all other XML tags to get just text
        content = re.sub(r'<[^>]+>', '', content)
        
        # Unescape XML entities
        content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        
        return content
        
    except Exception:
        # Fallback to text_recursive which handles nested spans
        return paragraph.text_recursive if hasattr(paragraph, 'text_recursive') else ''


def extract_links(paragraph):
    """
    Extract hyperlinks from a paragraph.
    
    Args:
        paragraph: ODT paragraph object
        
    Returns:
        list: List of link dictionaries with 'text', 'url', and 'type'
    """
    
    links = []
    
    try:
        # Extract links from paragraph
        # In odfdo, links are separate elements
        for link in paragraph.get_links():
            link_info = {
                'text': link.text if hasattr(link, 'text') else '',
                'url': link.url if hasattr(link, 'url') else '',
                'type': 'internal' if (hasattr(link, 'url') and link.url.startswith('#')) else 'external'
            }
            links.append(link_info)
    except Exception:
        pass
    
    return links


def load_odt_data(file_path, max_pages=None):
    """
    Load and parse an ODT file with hierarchical quote structure.
    
    The file structure includes:
    - ToC pages (skipped after detection)
    - Category headings (bold, no links)
    - Subcategory headings (bold, underlined, bookmarked)
    - Hierarchical quotes with tab indentation (supports unlimited depth: 1-10+ levels)
    - Quote markers: °, ^, ~, +, -
    - Citations in format: [AUTHOR, "TITLE", in: SOURCE]
    - Internal (#) and external hyperlinks
    
    Args:
        file_path (str): Path to the ODT file to load
        max_pages (int, optional): Maximum number of pages to load
        
    Returns:
        pd.DataFrame: DataFrame with columns:
            - 'paragraph_num': Sequential paragraph number
            - 'text': Full text content
            - 'type': 'subcategory', 'quote', 'toc', or 'other'
            - 'subcategory': Current subcategory name
            - 'quote_level': Hierarchical level (1, 2, 3, ...) for quotes
            - 'quote_marker': Marker symbol (°, ^, ~, +, -)
            - 'quote_text': Quote text without citation
            - 'citation_author': Citation author
            - 'citation_title': Citation title
            - 'citation_source': Citation source/collection
            - 'citation_raw': Raw citation text
            - 'links': List of hyperlinks
            - 'page': Estimated page number
            
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file cannot be parsed as valid ODT
    """
    
    if max_pages is not None:
        logger.info("Loading ODT file: %s (sampling first %d pages)", file_path, max_pages)
    else:
        logger.info("Loading ODT file: %s (loading entire file)", file_path)
    
    try:
        # Load the ODT document
        document = Document(file_path)
        body = document.body
        
        # Extract all paragraphs
        paragraphs = body.paragraphs
        
        # Build structured data
        data_records = []
        
        # Estimate pages
        PARAGRAPHS_PER_PAGE = 40
        max_paragraphs = max_pages * PARAGRAPHS_PER_PAGE if max_pages is not None else None
        
        paragraph_count = 0
        current_category = None
        current_subcategory = None
        in_toc = True  # Assume we start in ToC
        
        for idx, paragraph in enumerate(paragraphs, start=1):
            # Use the new function to get text WITH tabs preserved
            text = get_text_with_tabs(paragraph)
            
            # Skip empty paragraphs
            if not text or text.strip() == '':
                continue
            
            paragraph_count += 1
            
            # Stop if we've reached the maximum
            if max_paragraphs is not None and paragraph_count > max_paragraphs:
                logger.info("Reached page limit (%d pages), stopping at paragraph %d", 
                           max_pages, paragraph_count-1)
                break
            
            # Estimate page number
            estimated_page = ((paragraph_count - 1) // PARAGRAPHS_PER_PAGE) + 1
            
            # Extract links
            links = extract_links(paragraph)
            
            # Initialize record
            record = {
                'paragraph_num': idx,
                'text': text.strip(),
                'type': 'other',
                'category': current_category,
                'subcategory': current_subcategory,
                'quote_level': None,
                'quote_marker': None,
                'quote_text': None,
                'citation_author': None,
                'citation_title': None,
                'citation_source': None,
                'citation_raw': None,
                'links': links,
                'page': estimated_page,
                'length': len(text.strip())
            }
            
            # Detect if still in ToC (heuristic: ToC has many tabs/short lines with links)
            if in_toc:
                # ToC entries with tabs and links are subcategory names
                if '\t' in text and len(links) > 0:
                    # This is a ToC subcategory entry - extract the name
                    toc_subcat_name = ' '.join(text.strip().split())  # Clean up spaces/tabs
                    # Don't set current_subcategory yet - wait for actual content
                    record['type'] = 'toc'
                    record['text'] = toc_subcat_name  # Store cleaned name
                    data_records.append(record)
                    continue
                
                # Exit ToC when we see a category, subcategory heading, or a quote
                if (is_category_heading(paragraph, text) or 
                    is_subcategory_heading(paragraph, text) or 
                    detect_quote_level(text)[0] is not None):
                    in_toc = False
                    # Don't continue - process this paragraph below
                else:
                    record['type'] = 'toc'
                    data_records.append(record)
                    continue
            
            # Check if this is a category heading
            if is_category_heading(paragraph, text) and '\t' not in text:
                current_category = text.strip()
                record['type'] = 'category'
                record['category'] = current_category
                data_records.append(record)
                continue
            
            # Check if this is a subcategory heading
            if is_subcategory_heading(paragraph, text):
                current_subcategory = text.strip()
                record['type'] = 'subcategory'
                record['category'] = current_category
                record['subcategory'] = current_subcategory
                data_records.append(record)
                continue
            
            # Check if this is a quote
            level, marker, content = detect_quote_level(text)
            
            if level is not None:
                # Parse citation
                quote_text, citation = parse_citation(content)
                
                record['type'] = 'quote'
                record['quote_level'] = level
                record['quote_marker'] = marker
                record['quote_text'] = quote_text
                
                if citation:
                    record['citation_author'] = citation.get('author')
                    record['citation_title'] = citation.get('title')
                    record['citation_source'] = citation.get('source')
                    record['citation_raw'] = citation.get('raw')
            
            data_records.append(record)
        
        # Convert to DataFrame
        df = pd.DataFrame(data_records)
        
        if max_pages is not None:
            logger.info("Successfully loaded %d paragraphs from first ~%d pages of %s",
                       len(df), max_pages, file_path)
        else:
            logger.info("Successfully loaded %d paragraphs from %s", len(df), file_path)
        
        return df
        
    except FileNotFoundError as e:
        logger.error("File not found: %s", file_path)
        raise FileNotFoundError(f"Cannot find ODT file: {file_path}") from e
    
    except Exception as e:
        logger.error("Error parsing ODT file: %s", str(e))
        raise ValueError(f"Failed to parse ODT file {file_path}: {str(e)}") from e


def preprocess_philosophical_data(data):
    """
    Preprocess hierarchical quote data for analysis.
    
    Performs data cleaning and enrichment:
    - Adds unique identifiers
    - Calculates text statistics
    - Counts quotes per subcategory
    - Analyzes citation patterns
    
    Args:
        data (pd.DataFrame): Raw data loaded from ODT file
        
    Returns:
        pd.DataFrame: Preprocessed data with additional columns:
            - 'id': Unique identifier for each record
            - 'word_count': Number of words in the text
            - 'has_citation': Boolean indicating if quote has citation
            - 'has_links': Boolean indicating if paragraph has hyperlinks
    """
    
    logger.info("Preprocessing philosophical text data...")
    
    if data is None or len(data) == 0:
        logger.warning("No data to preprocess.")
        return data
    
    # Add unique ID column
    data['id'] = range(1, len(data) + 1)
    
    # Calculate word count
    data['word_count'] = data['text'].apply(lambda x: len(str(x).split()))
    
    # Add boolean flags
    data['has_citation'] = data['citation_raw'].notna()
    data['has_links'] = data['links'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)
    
    # Statistics
    total_quotes = len(data[data['type'] == 'quote'])
    total_subcategories = len(data[data['type'] == 'subcategory'])
    quotes_with_citations = data['has_citation'].sum()
    
    logger.info("Preprocessing complete. Total records: %d", len(data))
    logger.info("Total subcategories: %d", total_subcategories)
    logger.info("Total quotes: %d", total_quotes)
    logger.info("Quotes with citations: %d (%.1f%%)", 
               quotes_with_citations, 
               100 * quotes_with_citations / total_quotes if total_quotes > 0 else 0)
    
    return data


def get_text_statistics(data):
    """
    Calculate comprehensive statistics about the text dataset.
    
    Args:
        data (pd.DataFrame): Preprocessed data
        
    Returns:
        dict: Dictionary of statistics including:
            - total_paragraphs: Total number of paragraphs
            - total_words: Total word count
            - total_quotes: Number of quotes
            - total_subcategories: Number of subcategories
            - quotes_with_citations: Number of quotes with citations
            - avg_quote_length: Average quote length
            - quote_levels: Distribution of quote hierarchy levels
    """
    
    if data is None or len(data) == 0:
        return {}
    
    quotes = data[data['type'] == 'quote']
    subcategories = data[data['type'] == 'subcategory']
    
    stats = {
        'total_paragraphs': len(data),
        'total_words': data.get('word_count', pd.Series([0])).sum(),
        'total_characters': data.get('length', pd.Series([0])).sum(),
        'total_quotes': len(quotes),
        'total_subcategories': len(subcategories),
        'quotes_with_citations': data.get('has_citation', pd.Series([False])).sum(),
        'quotes_with_links': data.get('has_links', pd.Series([False])).sum(),
        'avg_quote_length': quotes.get('word_count', pd.Series([0])).mean() if len(quotes) > 0 else 0,
        'max_quote_level': quotes.get('quote_level', pd.Series([0])).max() if len(quotes) > 0 else 0,
    }
    
    # Add quote level distribution
    if len(quotes) > 0 and 'quote_level' in quotes.columns:
        level_counts = quotes['quote_level'].value_counts().to_dict()
        stats['quote_levels'] = level_counts
    
    return stats


def build_hierarchical_structure(data):
    """
    Build a hierarchical nested structure from flat quote data.
    
    Args:
        data (pd.DataFrame): Preprocessed data with subcategories and quotes
        
    Returns:
        dict: Nested dictionary structure:
            {
                'subcategory_name': {
                    'quotes': [
                        {
                            'text': '...',
                            'citation': {...},
                            'level': 1,
                            'children': [...]  # nested quotes
                        },
                        ...
                    ]
                },
                ...
            }
    """
    
    hierarchy = {}
    current_subcategory = None
    quote_stack = []  # Stack to track parent quotes at each level
    
    for _, row in data.iterrows():
        if row['type'] == 'subcategory':
            current_subcategory = row['text']
            hierarchy[current_subcategory] = {'quotes': [], 'metadata': {}}
            quote_stack = []  # Reset stack for new subcategory
            
        elif row['type'] == 'quote' and current_subcategory:
            quote_level = row['quote_level']
            
            quote_obj = {
                'text': row['quote_text'],
                'citation': {
                    'author': row['citation_author'],
                    'title': row['citation_title'],
                    'source': row['citation_source'],
                    'raw': row['citation_raw']
                } if row['has_citation'] else None,
                'level': quote_level,
                'marker': row['quote_marker'],
                'links': row['links'],
                'children': []
            }
            
            # Add to appropriate level in hierarchy
            if quote_level == 1:
                # Top-level quote
                hierarchy[current_subcategory]['quotes'].append(quote_obj)
                quote_stack = [quote_obj]
            elif quote_level > len(quote_stack):
                # Child of previous quote
                if quote_stack:
                    quote_stack[-1]['children'].append(quote_obj)
                    quote_stack.append(quote_obj)
            else:
                # Sibling or going back up
                quote_stack = quote_stack[:quote_level-1]
                if quote_stack:
                    quote_stack[-1]['children'].append(quote_obj)
                    quote_stack.append(quote_obj)
                else:
                    hierarchy[current_subcategory]['quotes'].append(quote_obj)
                    quote_stack = [quote_obj]
    
    return hierarchy


def export_to_csv(data, output_path):
    """
    Export data to CSV format.
    
    Args:
        data (pd.DataFrame): Data to export
        output_path (str): Path where CSV file will be saved
    """
    
    # Convert list columns to strings for CSV compatibility
    export_data = data.copy()
    if 'links' in export_data.columns:
        export_data['links'] = export_data['links'].apply(
            lambda x: '|'.join([link['url'] if isinstance(link, dict) else str(link) for link in x]) if isinstance(x, list) else str(x)
        )
    
    export_data.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f"Data exported to {output_path}")

