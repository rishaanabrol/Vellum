from pathlib import Path
from typing import Callable, List, Optional, Tuple

from config import settings
from core.chunker import Chunker
from core.document_processor import DocumentProcessor
from core.embeddings import EmbeddingService
from core.llm import LLMService
from core.models import DocumentRecord
from core.vector_store import VectorStore

ProgressCallback = Callable[[str, str, int, int], None]


class DuplicateDocumentError(Exception):
    def __init__(self, filename: str, existing: DocumentRecord):
        self.existing = existing
        super().__init__(
            f"'{filename}' is a duplicate of '{existing.document_name}' (same file content)."
        )


class NoExtractableTextError(Exception):
    def __init__(self, filename: str, scanned_pages: List[int]):
        self.scanned_pages = scanned_pages
        pages = ", ".join(str(p) for p in scanned_pages) if scanned_pages else "all pages"
        super().__init__(
            f"No extractable text found in '{filename}'. Pages {pages} look scanned and could not be read."
        )


def index_file_bytes(
    file_bytes: bytes,
    filename: str,
    vector_store: VectorStore,
    embedding_service: EmbeddingService,
    llm_service: Optional[LLMService] = None,
    progress: Optional[ProgressCallback] = None,
    docs_dir: Optional[str] = None,
) -> Tuple[DocumentRecord, List[int]]:
    """Extract, chunk, embed, and persist a document. Embeds each chunk once."""

    def report(step: str, detail: str, current: int = 0, total: int = 0) -> None:
        if progress:
            progress(step, detail, current, total)

    report("reading", "Reading file…", 0, 1)
    doc_id = DocumentProcessor.compute_sha256(file_bytes)
    existing = vector_store.get_document(doc_id)
    if existing is not None:
        raise DuplicateDocumentError(filename, existing)

    doc_id, pages, scanned_pages = DocumentProcessor.process_file(file_bytes, filename)

    report("splitting", f"Splitting {len(pages)} pages…", 0, max(len(pages), 1))
    chunks = Chunker().chunk_document(pages, doc_id, filename)
    if not chunks:
        raise NoExtractableTextError(filename, scanned_pages)

    texts = [c.text for c in chunks]
    embeddings: List[List[float]] = []
    batch_size = 32
    total = len(texts)
    for i in range(0, total, batch_size):
        done = min(i + batch_size, total)
        report("indexing", f"Indexing · {done} / {total} sections", done, total)
        embeddings.extend(embedding_service.embed_chunks(texts[i:i + batch_size]))

    docs_dir_path = Path(docs_dir or settings.DOCUMENTS_DIR)
    docs_dir_path.mkdir(parents=True, exist_ok=True)
    saved_path = docs_dir_path / f"{doc_id}_{filename}"
    saved_path.write_bytes(file_bytes)

    insight = {"summary": None, "suggested_questions": []}
    if llm_service is not None:
        report("insight", "Writing a short document overview…", total, total)
        sample_text = " ".join(c.text for c in chunks[:4])
        insight = llm_service.generate_document_insight(filename, sample_text)

    record = DocumentRecord(
        document_id=doc_id,
        document_name=filename,
        file_type=Path(filename).suffix.lower(),
        total_pages=len(pages) + len(scanned_pages),
        total_chunks=len(chunks),
        scanned_pages=scanned_pages,
        summary=insight.get("summary"),
        suggested_questions=insight.get("suggested_questions", []),
        file_path=str(saved_path),
    )
    vector_store.add_document(record, chunks, embeddings)
    p_str = "1 page" if record.total_pages == 1 else f"{record.total_pages} pages"
    s_str = "1 section" if len(chunks) == 1 else f"{len(chunks)} sections"
    report("ready", f"{p_str} · {s_str}", len(chunks), len(chunks))
    return record, scanned_pages
