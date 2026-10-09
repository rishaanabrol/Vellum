import pytest
import fitz
from core.document_processor import DocumentProcessor

def create_sample_pdf_bytes():
    doc = fitz.open()
    # Page 1: normal text with hyphenation and double newline
    p1 = doc.new_page()
    p1.insert_text((50, 72), "Gauss's Divergence Theorem states that the surface integral of a vector field over a closed surface is equal to the volume integral of the divergence of that field over the enclosed volume.")
    p1.insert_text((50, 150), "Mathematically, it is expressed as:\n\n\\oint_S \\vec{E} \\cdot d\\vec{A} = \\frac{Q_{enc}}{\\epsilon_0}")

    # Page 2: short unreadable page (simulating scanned/empty)
    p2 = doc.new_page()
    p2.insert_text((50, 72), "x") # under character threshold

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def test_pdf_extraction_and_scanned_detection():
    pdf_bytes = create_sample_pdf_bytes()
    doc_id, pages, scanned = DocumentProcessor.process_file(pdf_bytes, "Physics_Module_1.pdf")
    
    assert len(doc_id) == 64 # SHA-256
    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "Gauss's Divergence Theorem" in pages[0].text
    assert 2 in scanned # Page 2 correctly flagged as scanned/unreadable

def test_txt_processing():
    txt_content = "This is a plain text document.\n\nIt describes Coulomb's Law and electrostatic force between two charges."
    txt_bytes = txt_content.encode("utf-8")
    doc_id, pages, scanned = DocumentProcessor.process_file(txt_bytes, "Electrostatics.txt")
    
    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "Coulomb's Law" in pages[0].text
    assert len(scanned) == 0

def test_clean_text_hyphenation_repair():
    raw = "The compu-\n tation of electric flux requires integration."
    cleaned = DocumentProcessor.clean_text(raw)
    assert "computation" in cleaned

def test_empty_file_rejection():
    with pytest.raises(ValueError, match="empty"):
        DocumentProcessor.process_file(b"   ", "empty.txt")


def test_empty_bytes_rejection():
    with pytest.raises(ValueError, match="empty"):
        DocumentProcessor.process_file(b"", "blank.pdf")


def test_unsupported_type():
    with pytest.raises(ValueError, match="Unsupported"):
        DocumentProcessor.process_file(b"hello", "notes.docx")


def test_corrupt_pdf_rejection():
    with pytest.raises(ValueError, match="unreadable|Corrupt"):
        DocumentProcessor.process_file(b"%PDF-1.4 not a real pdf", "broken.pdf")


def test_scanned_like_pdf():
    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()
    _doc_id, pages, scanned = DocumentProcessor.process_file(pdf_bytes, "scan.pdf")
    assert pages == []
    assert scanned == [1]


def test_header_footer_stripping():
    pages = []
    for i in range(4):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "NEXUS PHYSICS HEADER")
        page.insert_text((50, 120), f"Unique body text for page {i} about Gauss law and flux integrals.")
        page.insert_text((50, 780), "Page footer confidential")
        pages.append(doc.tobytes())
        doc.close()
    # Combine into one PDF
    combined = fitz.open()
    for blob in pages:
        src = fitz.open(stream=blob, filetype="pdf")
        combined.insert_pdf(src)
        src.close()
    pdf_bytes = combined.tobytes()
    combined.close()
    _doc_id, extracted, _scanned = DocumentProcessor.process_file(pdf_bytes, "headers.pdf")
    joined = "\n".join(p.text for p in extracted)
    assert "Unique body text" in joined
    assert joined.count("NEXUS PHYSICS HEADER") == 0
