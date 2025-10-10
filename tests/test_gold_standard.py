"""
Test cases to validate preprocessed_data.csv against Phil_test_goldstandard.csv.

These tests ensure that the parsing and preprocessing logic correctly handles
all the edge cases found in the test dataset.
"""

import os
import pandas as pd
import pytest


@pytest.fixture
def test_data_paths():
    """Provide paths to test data files."""
    return {
        'preprocessed': 'output/test/preprocessed_data.csv',
        'gold_standard': 'output/test/Phil_test_goldstandard.csv'
    }


@pytest.fixture
def load_test_data(test_data_paths):
    """Load both preprocessed and gold standard data."""
    preprocessed = pd.read_csv(test_data_paths['preprocessed'])
    gold_standard = pd.read_csv(test_data_paths['gold_standard'])
    return preprocessed, gold_standard


def test_record_count(load_test_data):
    """Test that preprocessed data has the same number of records as gold standard."""
    preprocessed, gold_standard = load_test_data
    assert len(preprocessed) == len(gold_standard), \
        f"Record count mismatch: {len(preprocessed)} vs {len(gold_standard)}"


def test_all_entries_are_quotes(load_test_data):
    """Test that all entries in preprocessed data are quote-like types."""
    preprocessed, _ = load_test_data
    allowed_types = {'quote', 'reference', 'own remark'}
    assert preprocessed['type'].isin(allowed_types).all(), \
        f"All entries should be one of {allowed_types}, found: {preprocessed['type'].unique()}"


def test_merged_quote_paragraph_39(load_test_data):
    """Test that the 'Entdeckung des Unbewußten' quote (paragraph 39) is properly merged."""
    preprocessed, gold_standard = load_test_data
    
    curr = preprocessed[preprocessed['paragraph_num'] == 39].iloc[0]
    gold = gold_standard[gold_standard['paragraph_num'] == 39].iloc[0]
    
    # Check that citation is present
    assert curr['has_citation'] == True, "Paragraph 39 should have a citation"
    assert curr['citation_author'] == gold['citation_author'], \
        f"Citation author mismatch for paragraph 39"
    
    # Check text length is similar (allowing for small whitespace differences)
    assert abs(curr['length'] - gold['length']) < 10, \
        f"Text length mismatch for paragraph 39: {curr['length']} vs {gold['length']}"


def test_dash_continuation_paragraph_45(load_test_data):
    """Test that '- weil man den Abgrund...' is merged with paragraph 45."""
    preprocessed, gold_standard = load_test_data
    
    curr = preprocessed[preprocessed['paragraph_num'] == 45].iloc[0]
    gold = gold_standard[gold_standard['paragraph_num'] == 38].iloc[0]
    
    # Check that the quote text ends with the continuation
    assert 'weil man den Abgrund besser sieht' in curr['quote_text'], \
        "Paragraph 45 should include the continuation '- weil man...'"


def test_german_quotation_marks_removed(load_test_data):
    """Test that German quotation marks („ ") are removed from citation titles."""
    preprocessed, gold_standard = load_test_data
    
    # Check multiple paragraphs with German quotes
    test_paragraphs = [15, 17, 39, 45]
    
    for para_num in test_paragraphs:
        curr = preprocessed[preprocessed['paragraph_num'] == para_num]
        gold = gold_standard[gold_standard['paragraph_num'] == para_num]
        
        if len(curr) > 0 and len(gold) > 0:
            curr_title = curr.iloc[0]['citation_title']
            gold_title = gold.iloc[0]['citation_title']
            
            if pd.notna(curr_title) and pd.notna(gold_title):
                assert curr_title == gold_title, \
                    f"Citation title mismatch for paragraph {para_num}: '{curr_title}' vs '{gold_title}'"
                
                # Ensure no quotation marks remain
                assert '„' not in str(curr_title), \
                    f"German opening quote should be removed from paragraph {para_num}"


def test_nested_citation_source(load_test_data):
    """Test that nested citation sources are correctly extracted."""
    preprocessed, gold_standard = load_test_data
    
    # Paragraph 63: "in: The Secret Garden, May 1976; zitiert in: Clarke, "Piranesi""
    curr = preprocessed[preprocessed['paragraph_num'] == 63].iloc[0]
    gold = gold_standard[gold_standard['paragraph_num'] == 63].iloc[0]
    
    assert curr['citation_source'] == gold['citation_source'], \
        f"Nested citation source mismatch for paragraph 63"
    
    # Check that it contains the full nested reference
    assert 'zitiert in' in str(curr['citation_source']), \
        "Paragraph 63 should include the nested citation 'zitiert in: Clarke'"


def test_citation_title_date_preservation(load_test_data):
    """Test that dates are preserved in citation titles."""
    preprocessed, gold_standard = load_test_data
    
    # Test cases: (paragraph_num, expected_title)
    # Paragraph 84 (ID 65): "Twitter, 28.09.2025" should be preserved
    # Paragraph 24 (ID 19): "Episode 098: Dressed to Kill, 1980" should be preserved
    # Paragraph 91 (ID 70): "Episode 137: Shining (The Shining), 1980" should be preserved
    test_cases = [
        (84, 'Twitter, 28.09.2025'),
        (24, 'Episode 098: Dressed to Kill, 1980'),
        (91, 'Episode 137: Shining (The Shining), 1980')
    ]
    
    for para_num, expected_title in test_cases:
        curr = preprocessed[preprocessed['paragraph_num'] == para_num]
        gold = gold_standard[gold_standard['paragraph_num'] == para_num]
        
        if len(curr) > 0 and len(gold) > 0:
            curr_title = str(curr.iloc[0]['citation_title'])
            gold_title = str(gold.iloc[0]['citation_title'])
            
            # Check that the title matches expected value
            assert curr_title == expected_title, \
                f"Paragraph {para_num} title mismatch: '{curr_title}' vs '{expected_title}'"
            
            # Check that it matches gold standard
            assert curr_title == gold_title, \
                f"Paragraph {para_num} title doesn't match gold standard: '{curr_title}' vs '{gold_title}'"


def test_higher_level_quote_ref(load_test_data):
    """Test that higherLevelQuoteRef column is correctly populated."""
    preprocessed, gold_standard = load_test_data
    
    # Level 1 quotes should have '-' as higherLevelQuoteRef
    level_1_quotes = preprocessed[preprocessed['quote_level'] == 1.0]
    assert (level_1_quotes['higherLevelQuoteRef'] == '-').all(), \
        "All level 1 quotes should have higherLevelQuoteRef = '-'"
    
    # Level 2+ quotes should have a numeric ID
    level_2plus_quotes = preprocessed[preprocessed['quote_level'] > 1.0]
    if len(level_2plus_quotes) > 0:
        # Check that they have non-'-' values
        assert not (level_2plus_quotes['higherLevelQuoteRef'] == '-').any(), \
            "Level 2+ quotes should have a parent quote ID, not '-'"


def test_quote_levels_match(load_test_data):
    """Test that quote levels match between preprocessed and gold standard."""
    preprocessed, gold_standard = load_test_data
    
    # Compare each paragraph's quote level
    for para_num in preprocessed['paragraph_num'].unique():
        curr = preprocessed[preprocessed['paragraph_num'] == para_num].iloc[0]
        gold = gold_standard[gold_standard['paragraph_num'] == para_num]
        
        if len(gold) > 0:
            gold_row = gold.iloc[0]
            assert curr['quote_level'] == gold_row['quote_level'], \
                f"Quote level mismatch for paragraph {para_num}: {curr['quote_level']} vs {gold_row['quote_level']}"


def test_citation_authors_match(load_test_data):
    """Test that citation authors match between preprocessed and gold standard."""
    preprocessed, gold_standard = load_test_data
    
    mismatches = []
    
    for para_num in preprocessed['paragraph_num'].unique():
        curr = preprocessed[preprocessed['paragraph_num'] == para_num].iloc[0]
        gold = gold_standard[gold_standard['paragraph_num'] == para_num]
        
        if len(gold) > 0:
            gold_row = gold.iloc[0]
            
            curr_author = str(curr['citation_author']) if pd.notna(curr['citation_author']) else None
            gold_author = str(gold_row['citation_author']) if pd.notna(gold_row['citation_author']) else None
            
            if curr_author != gold_author:
                mismatches.append(f"Paragraph {para_num}: '{curr_author}' vs '{gold_author}'")
    
    assert len(mismatches) == 0, \
        f"Citation author mismatches found:\n" + "\n".join(mismatches)


def test_categories_and_subcategories(load_test_data):
    """Test that categories and subcategories are correctly assigned."""
    preprocessed, gold_standard = load_test_data
    
    for para_num in preprocessed['paragraph_num'].unique():
        curr = preprocessed[preprocessed['paragraph_num'] == para_num].iloc[0]
        gold = gold_standard[gold_standard['paragraph_num'] == para_num]
        
        if len(gold) > 0:
            gold_row = gold.iloc[0]
            
            assert curr['category'] == gold_row['category'], \
                f"Category mismatch for paragraph {para_num}: '{curr['category']}' vs '{gold_row['category']}'"
            
            assert curr['subcategory'] == gold_row['subcategory'], \
                f"Subcategory mismatch for paragraph {para_num}: '{curr['subcategory']}' vs '{gold_row['subcategory']}'"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
