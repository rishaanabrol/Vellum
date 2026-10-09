import sys
import os
import json
import shutil
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.embeddings import EmbeddingService
from core.vector_store import VectorStore
from core.retriever import Retriever
from core.llm import LLMService
from core.rag import RAGPipeline
from core.ingest import index_file_bytes
from config import settings

def run_evaluation():
    print("=" * 60)
    print("NEXUS 2026 - SMART DOCUMENT KNOWLEDGE ASSISTANT EVALUATION")
    print("=" * 60)

    eval_storage = "./storage/eval_chroma"
    if os.path.exists(eval_storage):
        shutil.rmtree(eval_storage, ignore_errors=True)

    emb_service = EmbeddingService()
    vector_store = VectorStore(persist_dir=eval_storage, collection_name="eval_collection")
    retriever = Retriever(vector_store, emb_service)
    # Evaluate at the same threshold the app runs with, so the report reflects
    # real behaviour; edit MIN_RELEVANCE in .env to re-calibrate.
    retriever.min_relevance = settings.MIN_RELEVANCE
    pipeline = RAGPipeline(retriever, LLMService())

    # 1. Ingest sample documents
    sample_files = [
        "sample_documents/Physics_Module_1.pdf",
        "sample_documents/Physics_Module_2.pdf",
        "sample_documents/Lab_Safety_Protocol.txt"
    ]

    print(f"Indexing {len(sample_files)} sample documents...")
    for fpath in sample_files:
        content = Path(fpath).read_bytes()
        fname = Path(fpath).name
        record, scanned = index_file_bytes(
            content, fname, vector_store, emb_service, llm_service=None
        )
        print(f"  Indexed '{fname}': {record.total_pages} pages, {record.total_chunks} chunks.")

    print(f"\nTotal vectors in store: {vector_store.total_chunks()}")

    # 2. Load eval questions with utf-8-sig to handle BOM
    with open("eval/questions.json", "r", encoding="utf-8-sig") as f:
        questions = json.load(f)

    on_topic_total = 0
    on_topic_hits = 0
    off_topic_total = 0
    off_topic_refusals = 0

    print("\nRunning Evaluation Suite...")
    print("-" * 60)

    for item in questions:
        qid = item["id"]
        q = item["question"]
        is_off = item["is_off_topic"]
        expected_doc = item["expected_doc"]
        expected_page = item["expected_page"]

        answer = pipeline.answer_query(q)

        if is_off:
            off_topic_total += 1
            if answer.no_answer_refusal:
                off_topic_refusals += 1
                status = "PASS (Correctly Refused)"
            else:
                status = "FAIL (Hallucinated / Unrefused)"
            print(f"[{qid}] [OFF-TOPIC] {q[:45]}... -> {status}")
        else:
            on_topic_total += 1
            # Check if expected document appears in top retrieved sources
            hit = any(
                s.document_name == expected_doc and (expected_page is None or s.page_number == expected_page)
                for s in answer.sources
            )
            if hit:
                on_topic_hits += 1
                status = "HIT"
            else:
                status = "MISS"
            top_doc = answer.sources[0].document_name if answer.sources else "None"
            top_sim = answer.sources[0].similarity if answer.sources else 0.0
            print(f"[{qid}] [ON-TOPIC]  {q[:45]}... -> {status} (Top: {top_doc}, Sim: {top_sim:.2f})")

    hit_rate = (on_topic_hits / on_topic_total) * 100 if on_topic_total else 0
    refusal_rate = (off_topic_refusals / off_topic_total) * 100 if off_topic_total else 0

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"On-Topic Questions:   {on_topic_total}")
    print(f"Retrieval Top-5 Hits: {on_topic_hits} / {on_topic_total} ({hit_rate:.1f}%)")
    print(f"Off-Topic Questions:  {off_topic_total}")
    print(f"Refusal Accuracy:     {off_topic_refusals} / {off_topic_total} ({refusal_rate:.1f}%)")
    print("=" * 60)

    report = {
        "on_topic_total": on_topic_total,
        "on_topic_hits": on_topic_hits,
        "hit_rate_pct": round(hit_rate, 2),
        "off_topic_total": off_topic_total,
        "off_topic_refusals": off_topic_refusals,
        "refusal_accuracy_pct": round(refusal_rate, 2),
        "min_relevance_threshold": retriever.min_relevance
    }
    with open("eval/eval_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    run_evaluation()
