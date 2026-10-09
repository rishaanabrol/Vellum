import pytest
from core.chunker import Chunker
from core.document_processor import ProcessedPage

def test_chunker_basic_and_overlap():
    chunker = Chunker(chunk_size=100, chunk_overlap=20)
    page_text = (
        "Paragraph one describes Coulomb's law and electric fields in space.\n\n"
        "Paragraph two discusses Gauss's divergence theorem and flux equations over closed surfaces.\n\n"
        "Paragraph three explains Stokes' theorem relating line integrals and surface integrals."
    )
    pages = [ProcessedPage(page_number=1, text=page_text)]
    chunks = chunker.chunk_document(pages, "doc_hash_1", "Physics.pdf")

    assert len(chunks) >= 2
    for c in chunks:
        assert len(c.text) > 0
        assert c.document_id == "doc_hash_1"
        assert c.page_number == 1
        assert c.document_name == "Physics.pdf"

    # Verify sequential chunk_ids
    ids = [c.chunk_id for c in chunks]
    assert ids == list(range(len(chunks)))

def test_chunker_page_preservation():
    chunker = Chunker(chunk_size=150, chunk_overlap=30)
    p1 = ProcessedPage(page_number=1, text="First page content discussing Maxwell's equations.")
    p2 = ProcessedPage(page_number=2, text="Second page content discussing wave propagation in vacuum.")
    chunks = chunker.chunk_document([p1, p2], "doc_hash_2", "Electrodynamics.pdf")

    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 2
    assert chunks[0].chunk_id == 0
    assert chunks[1].chunk_id == 1
