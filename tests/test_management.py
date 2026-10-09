import shutil
import uuid

from core.embeddings import EmbeddingService
from core.ingest import DuplicateDocumentError, index_file_bytes
from core.llm import LLMService
from core.models import Chunk, DocumentRecord
from core.vector_store import VectorStore


def _tmp_store():
    path = f"./storage/test_mgmt_{uuid.uuid4().hex[:8]}"
    store = VectorStore(persist_dir=path, collection_name=f"mgmt_{uuid.uuid4().hex[:6]}")
    return store, path


def test_duplicate_same_content_different_name(tmp_path):
    store, persist = _tmp_store()
    try:
        emb = EmbeddingService(api_key="your_gemini_api_key_here")
        payload = b"Stokes theorem relates circulation to curl over a surface."
        rec, _ = index_file_bytes(
            payload, "Notes_A.txt", store, emb, llm_service=None, docs_dir=str(tmp_path)
        )
        assert rec.total_chunks >= 1
        try:
            index_file_bytes(
                payload, "Notes_B.txt", store, emb, llm_service=None, docs_dir=str(tmp_path)
            )
            assert False, "duplicate content should be rejected"
        except DuplicateDocumentError as err:
            assert "Notes_A.txt" in str(err)
        assert store.total_chunks() == rec.total_chunks
    finally:
        del store.collection
        del store.client
        shutil.rmtree(persist, ignore_errors=True)


def test_persistence_across_restart():
    persist = f"./storage/test_persist_{uuid.uuid4().hex[:8]}"
    name = f"persist_{uuid.uuid4().hex[:6]}"
    try:
        store = VectorStore(persist_dir=persist, collection_name=name)
        record = DocumentRecord(
            document_id="persist_doc",
            document_name="Persist.txt",
            file_type=".txt",
            total_pages=1,
            total_chunks=1,
        )
        chunks = [
            Chunk(
                document_id="persist_doc",
                document_name="Persist.txt",
                chunk_id=0,
                page_number=1,
                text="Gauss divergence theorem persistence check.",
            )
        ]
        store.add_document(record, chunks, [[1.0, 0.0, 0.0]])
        del store.collection
        del store.client

        store2 = VectorStore(persist_dir=persist, collection_name=name)
        assert store2.document_exists("persist_doc")
        assert store2.total_chunks() == 1
        results = store2.query([1.0, 0.0, 0.0], n_results=1)
        assert "Gauss" in results[0]["text"]
        del store2.collection
        del store2.client
    finally:
        shutil.rmtree(persist, ignore_errors=True)


def test_delete_removes_vectors():
    store, persist = _tmp_store()
    try:
        record = DocumentRecord(
            document_id="gone",
            document_name="Gone.txt",
            file_type=".txt",
            total_pages=1,
            total_chunks=1,
        )
        chunks = [
            Chunk(document_id="gone", document_name="Gone.txt", chunk_id=0, page_number=1, text="delete me")
        ]
        store.add_document(record, chunks, [[0.2, 0.8, 0.0]])
        assert store.total_chunks() == 1
        assert store.delete_document("gone") == 1
        assert store.total_chunks() == 0
        assert store.document_exists("gone") is False
        assert store.query([0.2, 0.8, 0.0], n_results=3) == []
    finally:
        del store.collection
        del store.client
        shutil.rmtree(persist, ignore_errors=True)


def test_followup_rewrite_without_api():
    llm = LLMService(api_key="your_gemini_api_key_here")
    rewritten = llm.rewrite_query(
        "Explain it in simpler terms",
        [{"role": "user", "content": "What is Gauss's divergence theorem?"}],
    )
    assert "Gauss" in rewritten
    assert "simpler" in rewritten.lower()
    assert llm.rewrite_query("standalone question", []) == "standalone question"
