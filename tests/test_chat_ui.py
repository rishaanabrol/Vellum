"""Inline evidence rendering: citation chips must deep-link to the snippet cards
shown alongside each answer, and retrieved text must be escaped before it
touches the HTML (documents are untrusted content)."""
from core.models import Source
from ui.chat import format_citations_to_chips
from ui.sources import _snippet_html, _source_card_html


def make_source(**overrides) -> Source:
    payload = dict(
        document_name="Physics_Module_1.pdf",
        page_number=3,
        chunk_id=7,
        text="Gauss's theorem relates the flux through a surface to the divergence.",
        similarity=0.9,
        highlight_text="relates the flux",
    )
    payload.update(overrides)
    return Source(**payload)


def test_chips_default_to_panel_anchors():
    html = format_citations_to_chips("Claim [1] and [2].")
    assert 'href="#source-1"' in html
    assert 'href="#source-2"' in html


def test_chips_carry_message_scoped_prefix():
    html = format_citations_to_chips("Claim [1] and [3].", anchor_prefix="m4-")
    assert 'href="#source-m4-1"' in html
    assert 'href="#source-m4-3"' in html
    # The bare panel anchor must not leak through when a prefix is given.
    assert 'href="#source-1"' not in html


def test_chip_class_preserved():
    html = format_citations_to_chips("[1]")
    assert 'class="citation-chip"' in html


def test_source_card_carries_anchor_id_and_provenance():
    card = _source_card_html(make_source(), 2, anchor_id="source-m0-2")
    assert 'id="source-m0-2"' in card
    assert "[2] Physics_Module_1.pdf · Page 3" in card
    assert "90% match" in card


def test_source_card_escapes_document_text():
    evil = make_source(
        document_name='<img src=x onerror="alert(1)">.pdf',
        text="<script>alert('pwn')</script> safe text",
        highlight_text=None,
    )
    card = _source_card_html(evil, 1, anchor_id="source-m1-1")
    assert "<script>" not in card
    assert "<img" not in card
    assert "&lt;script&gt;" in card
    assert "&lt;img" in card


def test_snippet_marks_highlighted_sentence():
    snippet = _snippet_html(make_source())
    assert "<mark class='source-highlight'>relates the flux</mark>" in snippet


def test_snippet_without_highlight_is_plain():
    snippet = _snippet_html(make_source(highlight_text=None))
    assert "<mark" not in snippet
    # html.escape turns the apostrophe into &#x27; — that IS the plain, escaped form.
    assert "Gauss&#x27;s theorem" in snippet
