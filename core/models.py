from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Chunk(BaseModel):
    """Represents a text chunk extracted from a document with full provenance metadata."""
    document_id: str = Field(description="SHA-256 hash of the parent file content")
    document_name: str = Field(description="Filename of the uploaded document")
    chunk_id: int = Field(description="Sequential index of this chunk within document")
    page_number: int = Field(default=1, description="1-indexed page number where chunk originates")
    text: str = Field(description="Cleaned textual snippet")

class Source(BaseModel):
    """Verifiable evidence snippet presented to the user."""
    document_id: str = ""
    document_name: str
    page_number: int
    chunk_id: int
    text: str
    similarity: float = Field(ge=0.0, le=1.0, description="Normalized similarity score [0, 1]")
    highlight_text: Optional[str] = Field(default=None, description="Most relevant sentence within the chunk")

class Answer(BaseModel):
    """Grounded answer from RAG pipeline."""
    content: str
    sources: List[Source] = Field(default_factory=list)
    rewritten_query: Optional[str] = None
    is_grounded: bool = True
    no_answer_refusal: bool = False

class DocumentRecord(BaseModel):
    """Catalog record of an ingested document."""
    document_id: str
    document_name: str
    file_type: str
    total_pages: int
    total_chunks: int
    scanned_pages: List[int] = Field(default_factory=list)
    summary: Optional[str] = None
    suggested_questions: List[str] = Field(default_factory=list)
    file_path: Optional[str] = None

class ProcessingProgress(BaseModel):
    """Status updates emitted during document ingestion."""
    step: str # "reading", "splitting", "embedding", "indexing", "ready", "error"
    detail: str
    current: int = 0
    total: int = 0
    is_done: bool = False
    error: Optional[str] = None
