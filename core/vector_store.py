import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from core.models import Chunk, DocumentRecord
from config import settings

class VectorStore:
    """
    Persistent ChromaDB vector store wrapper supporting:
      - Add chunks (with duplicate prevention by document_id)
      - Query (with optional where filtering by document_ids)
      - True deletion (purges all chunks for a document_id)
      - Document catalog listing with chunk counts
      - Persistence across restarts
    """

    def __init__(self, persist_dir: str = settings.CHROMA_PERSIST_DIR, collection_name: str = settings.COLLECTION_NAME):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Initialize persistent Chroma client
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        # Use cosine similarity space: distance in [0, 2], similarity = 1 - (distance / 2)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self._meta_file = Path(self.persist_dir) / "catalog.json"
        self._catalog: Dict[str, DocumentRecord] = self._load_catalog()

    def _load_catalog(self) -> Dict[str, DocumentRecord]:
        if self._meta_file.exists():
            try:
                with open(self._meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {k: DocumentRecord(**v) for k, v in data.items()}
            except Exception as e:
                print(f"Warning: Failed to load catalog from {self._meta_file}: {e}")
        return {}

    def _save_catalog(self):
        try:
            with open(self._meta_file, "w", encoding="utf-8") as f:
                json.dump({k: v.model_dump() for k, v in self._catalog.items()}, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save catalog: {e}")

    def document_exists(self, document_id: str) -> bool:
        """Check if document hash is already registered in catalog."""
        return document_id in self._catalog

    def add_document(self, doc_record: DocumentRecord, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        """
        Inserts chunks and their embeddings into Chroma and updates the local catalog.
        """
        if not chunks:
            return

        if self.document_exists(doc_record.document_id):
            return

        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch between chunks count ({len(chunks)}) and embeddings count ({len(embeddings)})")

        ids = [f"{c.document_id}_{c.chunk_id}" for c in chunks]
        texts = [c.text for c in chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "document_name": c.document_name,
                "chunk_id": c.chunk_id,
                "page_number": c.page_number
            }
            for c in chunks
        ]

        # Chroma add handles batched insertion
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.add(
                ids=ids[i:i + batch_size],
                embeddings=embeddings[i:i + batch_size],
                documents=texts[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size]
            )

        self._catalog[doc_record.document_id] = doc_record
        self._save_catalog()

    def query(self, query_embedding: List[float], n_results: int = 8, document_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Queries Chroma for nearest neighbors.
        Applies optional document_id filtering via Chroma `where` parameter.
        """
        where_filter = None
        if document_ids and len(document_ids) > 0:
            if len(document_ids) == 1:
                where_filter = {"document_id": document_ids[0]}
            else:
                where_filter = {"document_id": {"$in": document_ids}}

        total_count = self.collection.count()
        if total_count == 0:
            return []

        fetch_k = min(n_results, total_count)
        if fetch_k <= 0:
            return []

        try:
            res = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=fetch_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            print(f"Chroma query failed: {e}")
            return []

        results = []
        if res and res.get("ids") and len(res["ids"][0]) > 0:
            for i in range(len(res["ids"][0])):
                dist = res["distances"][0][i] if res.get("distances") else 0.0
                # Chroma cosine space: distance d = 1 - cosine_similarity, d in [0, 2].
                # Reported score is angular similarity in [0, 1]: (1 + cosine) / 2 == 1 - d/2.
                similarity = max(0.0, min(1.0, 1.0 - (dist / 2.0)))

                meta = res["metadatas"][0][i]
                doc_text = res["documents"][0][i]
                results.append({
                    "id": res["ids"][0][i],
                    "document_id": meta.get("document_id"),
                    "document_name": meta.get("document_name"),
                    "chunk_id": meta.get("chunk_id"),
                    "page_number": meta.get("page_number", 1),
                    "text": doc_text,
                    "distance": dist,
                    "similarity": round(similarity, 4)
                })

        return results

    def delete_document(self, document_id: str) -> int:
        """
        Performs true deletion of all chunks associated with document_id.
        Removes catalog record and persists changes.
        """
        # Query existing ids with document_id metadata
        try:
            get_res = self.collection.get(
                where={"document_id": document_id},
                include=["metadatas"]
            )
            deleted_count = len(get_res["ids"]) if get_res and "ids" in get_res else 0
            if deleted_count > 0:
                self.collection.delete(where={"document_id": document_id})
        except Exception as e:
            print(f"Error deleting vectors from Chroma for doc {document_id}: {e}")
            deleted_count = 0

        if document_id in self._catalog:
            # Delete stored copy of file if exists
            stored_path = self._catalog[document_id].file_path
            if stored_path and os.path.exists(stored_path):
                try:
                    os.remove(stored_path)
                except Exception:
                    pass
            del self._catalog[document_id]
            self._save_catalog()

        return deleted_count

    def list_documents(self) -> List[DocumentRecord]:
        """Returns catalog of all currently indexed documents."""
        return list(self._catalog.values())

    def get_document(self, document_id: str) -> Optional[DocumentRecord]:
        return self._catalog.get(document_id)

    def total_chunks(self) -> int:
        return self.collection.count()
