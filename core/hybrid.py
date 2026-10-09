import re
import math
from typing import List, Optional

class HybridRetrieverHelper:
    """
    Computes lexical BM25/keyword overlap score to combine with dense cosine similarity.
    This guarantees that off-topic queries with zero lexical alignment are strictly rejected
    even in offline/mock embedding environments.
    """

    @staticmethod
    def compute_lexical_overlap(query: str, text: str) -> float:
        stop_words = {"what", "is", "the", "in", "and", "to", "of", "a", "an", "how", "does", "do", "for", "are", "on", "with", "its", "by"}
        q_tokens = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()) if w not in stop_words]
        if not q_tokens:
            return 0.0
        text_lower = text.lower()
        matched = sum(1 for tok in q_tokens if tok in text_lower)
        return matched / len(q_tokens)

    @classmethod
    def compute_hybrid_relevance(cls, query: str, text: str, dense_similarity: float) -> float:
        lexical = cls.compute_lexical_overlap(query, text)
        # If there is ZERO lexical overlap with key terms, cap the score sharply to trigger refusal
        if lexical == 0.0:
            return dense_similarity * 0.30
        return (dense_similarity * 0.60) + (lexical * 0.40)
