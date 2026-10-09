from pathlib import Path

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
        "sample_documents/Physics_Module_1.pdf",
        "sample_documents/Physics_Module_2.pdf",
        "sample_documents/Lab_Safety_Protocol.txt",
    ]

    for fpath in sample_files:
        path = Path(fpath)
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
