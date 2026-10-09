import sys
from pathlib import Path

# Add project root to sys.path so core and config can be imported cleanly
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.embeddings import EmbeddingService
from core.ingest import DuplicateDocumentError, index_file_bytes
from core.llm import LLMService
from core.vector_store import VectorStore


def preseed_demo():
    print("Pre-seeding storage/chroma with sample documents...")
    emb_service = EmbeddingService()
    v_store = VectorStore()
    llm = LLMService()

    sample_files = [
        ROOT / "sample_documents/Physics_Module_1.pdf",
        ROOT / "sample_documents/Physics_Module_2.pdf",
        ROOT / "sample_documents/Lab_Safety_Protocol.txt",
    ]

    for path in sample_files:
        if not path.exists():
            print(f"  Warning: '{path}' not found, skipping.")
            continue
        content = path.read_bytes()
        try:
            record, scanned = index_file_bytes(
                content, path.name, v_store, emb_service, llm_service=llm
            )
            extra = f" (scanned pages: {scanned})" if scanned else ""
            print(f"  Seeded '{record.document_name}' with {record.total_chunks} chunks.{extra}")
        except DuplicateDocumentError as e:
            print(f"  {e}")

    print(f"Pre-seeding complete. Total chunks indexed: {v_store.total_chunks()}")


if __name__ == "__main__":
    preseed_demo()
