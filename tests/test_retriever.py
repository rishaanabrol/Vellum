"""Retrieval behaviour: relevance, refusal, multi-document results, scope, dedup, top-k.

Runs offline (mock embeddings) but against the production MIN_RELEVANCE, so the
threshold semantics are exercised exactly as the app configures them.

Mock embeddings are ~uncorrelated vectors, so every pair scores dense ~= 0.5.
The hybrid score therefore behaves as 0.3 + 0.4 * lexical_overlap:
  - a query that shares all its key terms with a chunk scores ~0.70 -> passes
  - a query sharing no key term scores ~0.15 -> refused
Queries below are written so their key terms are either fully present or fully absent.
"""
import shutil
import uuid

import pytest

from config import settings
from core.embeddings import EmbeddingService
from core.models import Chunk, DocumentRecord
from core.retriever import Retriever
from core.vector_store import VectorStore

PHYSICS_TEXT = (
    "Gauss's divergence theorem relates the electric flux through a closed surface "
    "to the charge enclosed inside the volume."
)
STOKES_TEXT = (
    "Stokes' theorem states that the line integral around a closed loop equals the "
    "surface integral of the curl of the vector field."
)
CHEM_TEXT = (
    "A titration adds an acidic solution to a basic solution until the neutralization "
    "endpoint is reached in the volume of the flask."
)
CHEM_TEXT_DUP = (
    "A titration adds an acidic solution to a basic solution until the neutralization "
    "endpoint is reached in the volume of the container."
)

RELEVANT_QUERY = "divergence theorem electric flux closed surface charge enclosed"
SHARED_QUERY = "volume"
UNRELATED_QUERY = "chocolate brownie recipe baking oven temperature"


@pytest.fixture
def env():
    persist = f"./storage/test_retriever_{uuid.uuid4().hex[:8]}"
    store = VectorStore(persist_dir=persist, collection_name=f"ret_{uuid.uuid4().hex[:6]}")
    emb = EmbeddingService(api_key="your_gemini_api_key_here")
    retriever = Retriever(vector_store=store, embedding_service=emb)

    def build(chunks_by_doc):
        for doc_id, name, texts in chunks_by_doc:
            record = DocumentRecord(
                document_id=doc_id,
                document_name=name,
                file_type=".txt",
                total_pages=1,
                total_chunks=len(texts),
            )
            chunks = [
                Chunk(
                    document_id=doc_id,
                    document_name=name,
                    chunk_id=i,
                    page_number=1,
                    text=text,
                )
                for i, text in enumerate(texts)
            ]
            store.add_document(record, chunks, emb.embed_chunks([c.text for c in chunks]))

    yield store, retriever, build

    try:
        del store.collection
        del store.client
    finally:
        shutil.rmtree(persist, ignore_errors=True)


def test_relevant_query_returns_grounded_source(env):
    store, retriever, build = env
    build([
        ("doc_physics", "Physics.txt", [PHYSICS_TEXT, STOKES_TEXT]),
        ("doc_chem", "Chem.txt", [CHEM_TEXT, CHEM_TEXT_DUP]),
    ])

    sources = retriever.retrieve(RELEVANT_QUERY)

    assert sources, "a relevant query must return sources"
    assert sources[0].document_name == "Physics.txt"
    assert sources[0].page_number == 1
    assert 0.0 <= sources[0].similarity <= 1.0
    assert sources[0].similarity >= settings.MIN_RELEVANCE
    assert PHYSICS_TEXT[:40] in sources[0].text
    # Only the chunk that actually discusses the theorem should clear the threshold.
    assert all(s.document_name == "Physics.txt" for s in sources)


def test_unrelated_query_is_refused_by_threshold(env):
    store, retriever, build = env
    build([("doc_physics", "Physics.txt", [PHYSICS_TEXT, STOKES_TEXT])])

    sources = retriever.retrieve(UNRELATED_QUERY)

    assert sources == [], "no chunk may pass MIN_RELEVANCE for an off-topic question"


def test_multi_document_retrieval(env):
    store, retriever, build = env
    build([
        ("doc_physics", "Physics.txt", [PHYSICS_TEXT]),
        ("doc_chem", "Chem.txt", [CHEM_TEXT]),
    ])

    sources = retriever.retrieve(SHARED_QUERY)

    names = {s.document_name for s in sources}
    assert names == {"Physics.txt", "Chem.txt"}, f"expected both documents, got {names}"


def test_scope_filter_limits_results(env):
    store, retriever, build = env
    build([
        ("doc_physics", "Physics.txt", [PHYSICS_TEXT]),
        ("doc_chem", "Chem.txt", [CHEM_TEXT]),
    ])

    scoped = retriever.retrieve(SHARED_QUERY, document_ids=["doc_chem"])

    assert scoped, "scoped query should still find the selected document"
    assert all(s.document_id == "doc_chem" for s in scoped)


def test_scope_filter_to_unrelated_document_returns_nothing(env):
    store, retriever, build = env
    build([
        ("doc_physics", "Physics.txt", [PHYSICS_TEXT]),
        ("doc_chem", "Chem.txt", [CHEM_TEXT]),
    ])

    # The Gauss question is only answerable from Physics.txt; scoping it away
    # must produce an empty result rather than leaking the other document.
    sources = retriever.retrieve(RELEVANT_QUERY, document_ids=["doc_chem"])

    assert sources == []


def test_near_duplicates_are_collapsed(env):
    store, retriever, build = env
    build([("doc_chem", "Chem.txt", [CHEM_TEXT, CHEM_TEXT_DUP])])

    sources = retriever.retrieve(SHARED_QUERY)

    assert len(sources) == 1, "near-identical chunks must not both be surfaced"


def test_result_count_never_exceeds_top_k(env):
    store, retriever, build = env
    texts = [
        "The burette delivers a measured volume of base solution into the flask.",
        "Electrons occupy a quantized energy level within the volume of the crystal lattice.",
        "A piston compresses gas to reduce the volume inside the cylinder during the stroke.",
        "The glacier advanced, carving the valley volume of rock over many centuries.",
        "Chlorophyll captures sunlight across the leaf volume where photosynthesis proceeds.",
        "The auditor counted every crate stored in the warehouse volume before closing.",
        "Rain filled the reservoir volume, rising above the dam spillway level in spring.",
    ]
    build([("doc_big", "Big.txt", texts)])

    sources = retriever.retrieve(SHARED_QUERY)

    assert len(sources) <= settings.TOP_K
    assert len(sources) >= 3, "should still return the 3-5 chunk range for a rich match"


def test_highlight_points_at_the_matching_sentence(env):
    store, retriever, build = env
    two_sentences = (
        "Laboratory safety goggles must be worn at all times in the workshop. "
        "Gauss's divergence theorem relates the electric flux through a closed surface "
        "to the charge enclosed inside the volume."
    )
    build([("doc_physics", "Physics.txt", [two_sentences])])

    sources = retriever.retrieve(RELEVANT_QUERY)

    assert sources, "expected a source"
    assert sources[0].highlight_text is not None
    assert "Gauss's divergence theorem" in sources[0].highlight_text
    assert "goggles" not in sources[0].highlight_text
