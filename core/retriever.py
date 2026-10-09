import re
from typing import List, Optional
from core.models import Source
from core.embeddings import EmbeddingService
from core.vector_store import VectorStore
from core.hybrid import HybridRetrieverHelper
from config import settings

class Retriever:
    """
    Coordinates semantic search, candidate deduplication, relevance thresholding,
    and snippet key-sentence highlighting.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        top_k: Optional[int] = None,
        candidate_k: Optional[int] = None,
        min_relevance: Optional[float] = None,
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self._top_k = top_k
        self._candidate_k = candidate_k
        self._min_relevance = min_relevance

    @property
    def top_k(self) -> int:
        return self._top_k if self._top_k is not None else settings.TOP_K

    @top_k.setter
    def top_k(self, val: int) -> None:
        self._top_k = val

    @property
    def candidate_k(self) -> int:
        return self._candidate_k if self._candidate_k is not None else settings.CANDIDATE_K

    @candidate_k.setter
    def candidate_k(self, val: int) -> None:
        self._candidate_k = val

    @property
    def min_relevance(self) -> float:
        return self._min_relevance if self._min_relevance is not None else settings.MIN_RELEVANCE

    @min_relevance.setter
    def min_relevance(self, val: float) -> None:
        self._min_relevance = val

    def _extract_highlight(self, text: str, query: str) -> Optional[str]:
        """
        Finds the single most salient sentence in the chunk corresponding to the query terms.
        """
        if not text:
            return None

        query_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()))
        if not query_words:
            return None

        sentences = re.split(r'(?<=[.!?])\s+', text)
        best_sentence = None
        max_overlap = 0

        for sentence in sentences:
            s_clean = sentence.strip()
            if len(s_clean) < 15:
                continue
            s_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', s_clean.lower()))
            overlap = len(query_words.intersection(s_words))
            if overlap > max_overlap:
                max_overlap = overlap
                best_sentence = s_clean

        return best_sentence

    def _deduplicate_candidates(self, candidates: List[dict], max_count: int) -> List[dict]:
        """
        Removes near-duplicate chunks based on text jaccard similarity
        to ensure diverse retrieved evidence.
        """
        selected = []
        for cand in candidates:
            cand_words = set(cand["text"].lower().split())
            is_duplicate = False
            for sel in selected:
                sel_words = set(sel["text"].lower().split())
                intersection = len(cand_words.intersection(sel_words))
                union = len(cand_words.union(sel_words))
                jaccard = (intersection / union) if union > 0 else 0.0
                if jaccard > 0.65:
                    is_duplicate = True
                    break

            if not is_duplicate:
                selected.append(cand)
            if len(selected) >= max_count:
                break

        return selected

    def retrieve(self, query: str, document_ids: Optional[List[str]] = None) -> List[Source]:
        """
        Executes query retrieval:
          1. Embeds query with RETRIEVAL_QUERY task type.
          2. Queries vector store for top candidate_k chunks.
          3. Re-scores candidates using hybrid dense-lexical relevance.
          4. Deduplicates near-identical passages.
          5. Filters chunks against MIN_RELEVANCE threshold.
          6. Constructs validated Pydantic Source objects.
        """
        query_emb = self.embedding_service.embed_query(query)
        candidates = self.vector_store.query(
            query_embedding=query_emb,
            n_results=self.candidate_k,
            document_ids=document_ids
        )

        if not candidates:
            return []

        # Compute hybrid relevance for each candidate
        for c in candidates:
            c["similarity"] = round(HybridRetrieverHelper.compute_hybrid_relevance(
                query=query,
                text=c["text"],
                dense_similarity=c["similarity"]
            ), 4)

        # Re-sort candidates by hybrid score descending
        candidates.sort(key=lambda x: x["similarity"], reverse=True)

        # Deduplicate candidates
        deduped = self._deduplicate_candidates(candidates, max_count=self.top_k)

        # Apply relevance threshold filter
        filtered = [c for c in deduped if c["similarity"] >= self.min_relevance]

        sources: List[Source] = []
        for c in filtered:
            highlight = self._extract_highlight(c["text"], query)
            sources.append(Source(
                document_id=str(c.get("document_id") or ""),
                document_name=c["document_name"],
                page_number=int(c["page_number"]),
                chunk_id=int(c["chunk_id"]),
                text=c["text"],
                similarity=c["similarity"],
                highlight_text=highlight
            ))

        return sources
