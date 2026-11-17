"""Exercise real ODT links across extraction, merging, filtering and export."""
import json
import re

import pandas as pd
import pytest
from odfdo import Document, Element

from data_model import load_odt_data, preprocess_philosophical_data
from obsidian_export import ObsidianExporter


@pytest.fixture
def linked_odt(tmp_path):
    document = Document('text')
    document.body.clear()
    paragraphs = [
        'Wirtschaft',
        '<text:bookmark-start text:name="intro"/>Einleitung',
        '<text:tab/>° Analogien, (vgl.) <text:a xlink:href="#analogie-id"><text:span>andere</text:span> Analogien</text:a>; '
        '(Vgl.) <text:a xlink:href="#reiz%20id">Anreiz</text:a>.',
        'Fortsetzung: <text:a xlink:href="#empty">leere Kategorie</text:a>, '
        '<text:a xlink:href="https://example.org/a">Website</text:a>. [Autor, "Titel"]',
        '<text:tab/>° Vgl. <text:a xlink:href="#analogie-id">Analogien</text:a>.',
        '<text:tab/>° Vgl. Analogien (unverlinkt).',
        '<text:tab/>° <text:bookmark text:name="entry-anchor"/>Vergleiche '
        '<text:a xlink:href="#missing">fehlt</text:a>, '
        '<text:a xlink:href="#entry-anchor">Eintrag</text:a>, '
        '<text:a xlink:href="#duplicate">mehrdeutig</text:a>.',
        '<text:tab/><text:tab/>~ Ohne Präfix: <text:a xlink:href="#other-analogy">Analogien</text:a>.',
        '<text:bookmark-start text:name="analogie-id"/>Analogien',
        '<text:tab/>° Inhalt. [Autor, "Buch"]',
        '<text:bookmark text:name="reiz id"/>Anreiz',
        '<text:bookmark text:name="empty"/>Leer/Ähnlich',
        '<text:bookmark text:name="duplicate"/>Erste',
        '<text:bookmark text:name="duplicate"/>Zweite',
        'Politik',
        '<text:bookmark-start text:name="other-analogy"/>Analogien',
    ]
    # Put another target beyond the one-page sampling boundary.
    paragraphs += ['Fülltext'] * 25
    paragraphs += ['<text:bookmark text:name="late"/>Spät']
    paragraphs[6] += ' <text:a xlink:href="#late">später</text:a>.'
    for text in paragraphs:
        document.body.append(Element.from_tag(f'<text:p>{text}</text:p>'))
    path = tmp_path / 'links.odt'
    document.save(path)
    return path


def test_odt_links_end_to_end(linked_odt, tmp_path):
    raw = load_odt_data(linked_odt)
    data = preprocess_philosophical_data(raw)
    exporter = ObsidianExporter(tmp_path / 'vault')
    stats = exporter.export_to_markdown(data)
    assert not stats['errors']
    assert stats['resolved_internal_links'] == 6
    assert stats['unresolved_internal_links'] == 3
    assert all('Entry ' in warning for warning in stats['warnings'])
    assert any('not a category heading' in warning for warning in stats['warnings'])
    assert any('ambiguous' in warning for warning in stats['warnings'])
    quote = next((tmp_path / 'vault').rglob('Quote - Autor - Titel*.md')).read_text()
    assert '> Analogien, (vgl.) [[Wirtschaft/Analogien/_MOC - Analogien|andere Analogien]]; (Vgl.) [[Wirtschaft/Anreiz/_MOC - Anreiz|Anreiz]]. Fortsetzung:' in quote
    assert '[[Wirtschaft/Leer-Ähnlich/_MOC - Leer-Ähnlich|leere Kategorie]]' in quote
    assert '[Website](https://example.org/a)' in quote
    notes = list((tmp_path / 'vault').rglob('*.md'))
    combined = '\n'.join(p.read_text() for p in notes)
    assert '[[Politik/Analogien/_MOC - Analogien|Analogien]]' in combined
    assert 'Vgl. Analogien (unverlinkt).' in combined
    assert 'Vgl. [[Wirtschaft/Analogien/_MOC - Analogien|Analogien]].' in combined
    # Every generated source-hyperlink destination (aliased link) must exist.
    targets = re.findall(r'\[\[([^|\]]+)\|[^\]]*\]\]', combined)
    assert targets
    assert all((tmp_path / 'vault' / (target + '.md')).is_file() for target in targets)
    assert (tmp_path / 'vault/Wirtschaft/Leer-Ähnlich/_MOC - Leer-Ähnlich.md').is_file()
    row = data[data['citation_title'] == 'Titel'].iloc[0]
    assert len(row['links']) == 4
    assert row['citation_author'] == 'Autor'
    nested = data[data['quote_level'] == 2].iloc[0]
    assert nested['higherLevelQuoteRef'] != '-'
    assert '## Related Subcategories\n\n- [[' in (tmp_path / 'vault/Wirtschaft/Einleitung/_MOC - Einleitung.md').read_text()


def test_partial_export_reports_excluded_target(linked_odt, tmp_path):
    data = preprocess_philosophical_data(load_odt_data(linked_odt, max_pages=1))
    stats = ObsidianExporter(tmp_path / 'partial').export_to_markdown(data)
    assert stats['unresolved_internal_links'] == 4
    assert any("'#late'" in warning and 'partial export' in warning for warning in stats['warnings'])


def test_native_and_json_links_have_identical_rendering(tmp_path):
    exporter = ObsidianExporter(tmp_path)
    exporter.bookmark_paths = {'id': ['Wirtschaft/Analogien/_MOC - Analogien.md']}
    links = [{'text': 'mehrere Wörter', 'url': '#id', 'type': 'internal'}]
    assert exporter._convert_links(links) == exporter._convert_links(json.dumps(links))
    assert exporter._convert_links({'url': '#id'}) == '*Invalid links data*'


def test_filename_collision_stops_before_writing(tmp_path):
    data = pd.DataFrame({'id': [1, 2], 'category': ['Wirtschaft'] * 2,
                         'subcategory': ['A/B', 'A:B'], 'type': ['note'] * 2, 'text': ['x', 'y']})
    stats = ObsidianExporter(tmp_path / 'vault').export_to_markdown(data)
    assert stats['errors']
    assert not (tmp_path / 'vault').exists()


def test_toc_bookmarks_disambiguate_duplicate_names(tmp_path):
    document = Document('text')
    document.body.clear()
    for text in [
        'Wirtschaft', '<text:bookmark text:name="incidental"/><text:a xlink:href="#economic">Analogien</text:a>',
        'Politik', '<text:a xlink:href="#political">Analogien</text:a>',
        '<text:bookmark-start text:name="economic"/>Analogien',
        '<text:tab/>° Vgl. <text:a xlink:href="#political">Analogien</text:a>.',
        '<text:bookmark-start text:name="political"/>Analogien',
    ]:
        document.body.append(Element.from_tag(f'<text:p>{text}</text:p>'))
    path = tmp_path / 'duplicates.odt'
    document.save(path)
    data = preprocess_philosophical_data(load_odt_data(path))
    assert data.iloc[0]['category'] == 'Wirtschaft'
    exporter = ObsidianExporter(tmp_path / 'vault')
    stats = exporter.export_to_markdown(data)
    assert stats['resolved_internal_links'] == 1
    assert stats['unresolved_internal_links'] == 0
    assert exporter.bookmark_paths['political'] == ['Politik/Analogien/_MOC - Analogien.md']


def test_long_moc_names_keep_markdown_extension(tmp_path):
    exporter = ObsidianExporter(tmp_path)
    path = exporter._moc_path('Wirtschaft', 'Ä' * 110)
    assert path.endswith('.md')
    assert len(path.rsplit('/', 1)[1]) == 100


def test_link_positions_preserve_spaces_linebreaks_and_repeated_words(tmp_path):
    from data_model import paragraph_content, detect_quote_level
    paragraph = Element.from_tag(
        '<text:p><text:tab/>° Wort<text:s text:c="2"/>'
        '<text:line-break/><text:a xlink:href="#id"><text:span>Wort</text:span> &amp; mehr</text:a>.</text:p>'
    )
    text, links, _ = paragraph_content(paragraph)
    assert text == '\t° Wort  \nWort & mehr.'
    assert detect_quote_level(text)[:2] == (1, '°')
    exporter = ObsidianExporter(tmp_path)
    exporter.bookmark_paths = {'id': ['Wirtschaft/Analogien/_MOC - Analogien.md']}
    rendered = exporter._inline_text({'text': text, 'links': links}, text)
    assert rendered == '\t° Wort  \n[[Wirtschaft/Analogien/_MOC - Analogien|Wort & mehr]].'


def test_supercategory_bookmark_is_reported_not_guessed(tmp_path):
    document = Document('text')
    document.body.clear()
    for text in [
        '<text:bookmark text:name="super"/>Wirtschaft',
        '<text:bookmark text:name="sub"/>Analogien',
        '<text:tab/>° <text:a xlink:href="#super">Wirtschaft</text:a>.',
    ]:
        document.body.append(Element.from_tag(f'<text:p>{text}</text:p>'))
    path = tmp_path / 'supercategory.odt'
    document.save(path)
    data = preprocess_philosophical_data(load_odt_data(path))
    stats = ObsidianExporter(tmp_path / 'vault').export_to_markdown(data)
    assert stats['unresolved_internal_links'] == 1
    assert "'#super': bookmark is not a category heading" in stats['warnings'][0]


def test_links_inside_citation_keep_their_position(tmp_path):
    from data_model import paragraph_content, parse_citation
    paragraph = Element.from_tag(
        '<text:p>Zitat. [Autor, "<text:a xlink:href="#id">Titel</text:a>"]</text:p>'
    )
    text, links, _ = paragraph_content(paragraph)
    _, citation = parse_citation(text)
    exporter = ObsidianExporter(tmp_path)
    exporter.bookmark_paths = {'id': ['Wirtschaft/Analogien/_MOC - Analogien.md']}
    row = {'text': text, 'links': links, 'has_citation': True, 'citation_raw': citation['raw']}
    assert '**Full Citation:** Autor, "[[Wirtschaft/Analogien/_MOC - Analogien|Titel]]"' in exporter._format_citation(row)


def test_unassigned_entries_are_reported(tmp_path):
    data = pd.DataFrame({'id': [1], 'category': ['Wirtschaft'],
                         'subcategory': [None], 'type': ['note'], 'text': ['Intro']})
    stats = ObsidianExporter(tmp_path / 'vault').export_to_markdown(data)
    assert stats['skipped_entries'] == 1
    assert stats['files_created'] == 0
    assert stats['warnings'] == ['Skipped entries without category/subcategory: [1]']
