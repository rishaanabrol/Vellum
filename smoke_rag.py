"""Offline-friendly end-to-end smoke check for the RAG pipeline.

Exercises: live retrieval over the seeded store, deterministic refusal below the
threshold, follow-up query rewriting, and citation validation. Runs even when the
LLM quota is exhausted (the pipeline must degrade, not crash).
"""
from core.embeddings import EmbeddingService
from core.llm import LLMService
from core.rag import RAGPipeline
from core.retriever import Retriever
from core.vector_store import VectorStore


def main() -> None:
    store = VectorStore()
    emb = EmbeddingService()
    retriever = Retriever(store, emb)
    pipeline = RAGPipeline(retriever, LLMService())

    docs = store.list_documents()
    print(f"documents in store: {len(docs)} | vectors: {store.total_chunks()}")
    for d in docs:
        print(f"  - {d.document_name}: {d.total_chunks} chunks, {d.total_pages} pages")

    failures = []

    # 1. Grounded question
    ans = pipeline.answer_query("What is Gauss's divergence theorem?")
    print("\n[1] grounded question")
    print(f"    refusal={ans.no_answer_refusal} sources={len(ans.sources)}")
    for s in ans.sources:
        print(f"    · {s.document_name} p{s.page_number} sim={s.similarity}")
    print(f"    answer head: {ans.content[:220]!r}")
    if ans.no_answer_refusal or not ans.sources:
        failures.append("grounded question returned no sources")
    if ans.sources and not (0 <= ans.sources[0].similarity <= 1):
        failures.append("similarity out of range")

    # 2. Cross-document question
    ans2 = pipeline.answer_query("What was Maxwell's correction to Ampere's circuital law?")
    print("\n[2] cross-document question")
    print(f"    refusal={ans2.no_answer_refusal} sources={len(ans2.sources)}")
    for s in ans2.sources:
        print(f"    · {s.document_name} p{s.page_number} sim={s.similarity}")
    if ans2.no_answer_refusal or not ans2.sources:
        failures.append("cross-document question returned no sources")

    # 3. Off-topic question -> deterministic refusal, no LLM call
    ans3 = pipeline.answer_query("What is the recipe for baking chocolate brownies?")
    print("\n[3] off-topic question")
    print(f"    refusal={ans3.no_answer_refusal} sources={len(ans3.sources)}")
    print(f"    content: {ans3.content!r}")
    if not ans3.no_answer_refusal or ans3.sources:
        failures.append("off-topic question did not hit the refusal path")

    # 4. Follow-up rewriting (uses history)
    history = [{"role": "user", "content": "What is Gauss's divergence theorem?"},
               {"role": "assistant", "content": "It relates flux through a closed surface to enclosed charge [1]."}]
    ans4 = pipeline.answer_query("Explain it in simpler terms", chat_history=history)
    print("\n[4] follow-up rewrite")
    print(f"    rewritten={ans4.rewritten_query!r}")
    if not ans4.rewritten_query or "Gauss" not in ans4.rewritten_query:
        failures.append("follow-up was not rewritten into a standalone query")

    # 5. Citation validation strips hallucinated markers
    cleaned = RAGPipeline.validate_citations("Claim [1] and fake [9].", len(ans.sources) or 1)
    print(f"\n[5] citation validation -> {cleaned!r}")
    if "[9]" in cleaned:
        failures.append("hallucinated citation was not stripped")

    # 6. Scope filter: scoping to a non-matching doc must not return other docs
    if len(docs) >= 2:
        other = [d.document_id for d in docs if "Lab_Safety" in d.document_name]
        scoped = retriever.retrieve("What is Gauss's divergence theorem?", document_ids=other)
        bad = [s for s in scoped if s.document_id not in other]
        print(f"\n[6] scope filter -> {len(scoped)} sources, {len(bad)} out of scope")
        if bad:
            failures.append("scope filter leaked chunks from other documents")

    print("\n" + ("SMOKE FAILURES: " + "; ".join(failures) if failures else "SMOKE OK"))


if __name__ == "__main__":
    main()
