import pytest
from core.rag import RAGPipeline

def test_citation_validation_strips_hallucinated_citations():
    # Only 2 sources retrieved: [1] and [2] are valid; [3], [4], [99] are hallucinated
    raw_text = "Gauss law states this formula [1]. Moreover Stokes theorem applies [2]. External fact mentioned [3] and [99]."
    cleaned = RAGPipeline.validate_citations(raw_text, max_source_index=2)
    assert "[1]" in cleaned
    assert "[2]" in cleaned
    assert "[3]" not in cleaned
    assert "[99]" not in cleaned
    assert "External fact mentioned" in cleaned

def test_citation_validation_preserves_valid():
    raw_text = "The electric flux is given by integral [1]."
    cleaned = RAGPipeline.validate_citations(raw_text, max_source_index=1)
    assert cleaned.strip() == "The electric flux is given by integral [1]."
