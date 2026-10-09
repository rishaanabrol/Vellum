import pytest
from core.models import Chunk, Source, Answer, DocumentRecord

def test_models_instantiation():
    chunk = Chunk(
        document_id="abc123hash",
        document_name="Lecture_Notes.pdf",
        chunk_id=1,
        page_number=3,
        text="Sample paragraph regarding thermodynamics."
    )
    assert chunk.document_id == "abc123hash"
    assert chunk.chunk_id == 1
    assert chunk.page_number == 3

    source = Source(
        document_name="Lecture_Notes.pdf",
        page_number=3,
        chunk_id=1,
        text="Sample paragraph regarding thermodynamics.",
        similarity=0.88,
        highlight_text="Sample paragraph"
    )
    assert source.similarity == 0.88

    answer = Answer(
        content="Thermodynamics is explained in [1].",
        sources=[source]
    )
    assert len(answer.sources) == 1
    assert answer.is_grounded is True
