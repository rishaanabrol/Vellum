import os
import shutil
import pytest
from core.models import Chunk, DocumentRecord
from core.vector_store import VectorStore

TEST_CHROMA_DIR = "./storage/test_chroma"

@pytest.fixture
def vector_store():
    # Use unique subdirectories per test to isolate dimensions
    import uuid
    sub_dir = f"./storage/test_chroma_{uuid.uuid4().hex[:8]}"
    store = VectorStore(persist_dir=sub_dir, collection_name=f"test_coll_{uuid.uuid4().hex[:6]}")
    yield store
    # Best-effort cleanup
    try:
        del store.collection
        del store.client
        shutil.rmtree(sub_dir, ignore_errors=True)
    except Exception:
        pass

def test_vector_store_add_and_query(vector_store):
    doc_record = DocumentRecord(
        document_id="doc_1",
        document_name="Math.txt",
        file_type=".txt",
        total_pages=1,
        total_chunks=2
    )
    chunks = [
        Chunk(document_id="doc_1", document_name="Math.txt", chunk_id=0, page_number=1, text="Calculus derivative rules."),
        Chunk(document_id="doc_1", document_name="Math.txt", chunk_id=1, page_number=1, text="Linear algebra eigenvectors.")
    ]
    embeddings = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0]
    ]

    vector_store.add_document(doc_record, chunks, embeddings)
    assert vector_store.document_exists("doc_1") is True
    assert vector_store.total_chunks() == 2

    # Query with match for first embedding
    results = vector_store.query(query_embedding=[1.0, 0.0, 0.0], n_results=1)
    assert len(results) == 1
    assert results[0]["chunk_id"] == 0
    assert "Calculus" in results[0]["text"]
    assert results[0]["similarity"] > 0.9

def test_vector_store_scope_filter(vector_store):
    doc1 = DocumentRecord(document_id="doc_1", document_name="Physics.txt", file_type=".txt", total_pages=1, total_chunks=1)
    doc2 = DocumentRecord(document_id="doc_2", document_name="Chemistry.txt", file_type=".txt", total_pages=1, total_chunks=1)
    
    chunks1 = [Chunk(document_id="doc_1", document_name="Physics.txt", chunk_id=0, page_number=1, text="Quantum mechanics wave function.")]
    chunks2 = [Chunk(document_id="doc_2", document_name="Chemistry.txt", chunk_id=0, page_number=1, text="Organic chemistry hydrocarbons.")]

    vector_store.add_document(doc1, chunks1, [[1.0, 0.0, 0.0]])
    vector_store.add_document(doc2, chunks2, [[1.0, 0.0, 0.0]])

    # Query scoping only to doc_2
    results = vector_store.query(query_embedding=[1.0, 0.0, 0.0], n_results=5, document_ids=["doc_2"])
    assert len(results) == 1
    assert results[0]["document_id"] == "doc_2"
    assert "Organic chemistry" in results[0]["text"]

def test_vector_store_true_deletion(vector_store):
    doc1 = DocumentRecord(document_id="doc_1", document_name="Test.txt", file_type=".txt", total_pages=1, total_chunks=2)
    chunks = [
        Chunk(document_id="doc_1", document_name="Test.txt", chunk_id=0, page_number=1, text="A"),
        Chunk(document_id="doc_1", document_name="Test.txt", chunk_id=1, page_number=1, text="B")
    ]
    vector_store.add_document(doc1, chunks, [[0.5, 0.5, 0.0], [0.1, 0.9, 0.0]])
    assert vector_store.total_chunks() == 2

    deleted_count = vector_store.delete_document("doc_1")
    assert deleted_count == 2
    assert vector_store.total_chunks() == 0
    assert vector_store.document_exists("doc_1") is False
