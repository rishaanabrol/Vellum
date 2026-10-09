import re
from typing import List, Optional

class HybridRetrieverHelper:
    """
    Computes lexical BM25/keyword overlap score to combine with dense cosine similarity.
    Balances semantic matching for conceptual queries (definitions, formulas, summaries)
    while strictly filtering off-topic queries with no contextual grounding.
    """

    STOP_WORDS = {
        "what", "is", "the", "in", "and", "to", "of", "a", "an", "how", "does", "do", "for",
        "are", "on", "with", "its", "by", "you", "your", "which", "that", "this", "these",
        "those", "have", "has", "had", "can", "could", "will", "would", "should", "from",
        "about", "into", "been", "were", "was"
    }

    META_WORDS = {
        "definition", "definitions", "theorem", "theorems", "formula", "formulas",
        "procedure", "procedures", "idea", "ideas", "topic", "topics", "summary",
        "summarize", "overview", "document", "test", "exam", "paper", "concept", "concepts",
        "question", "questions", "problem", "problems", "exercise", "exercises", "explain",
        "discuss", "state", "stated", "appear", "appears", "solve", "solution", "section",
        "sections", "chapter", "chapters", "content", "contents", "main", "key"
    }

    @classmethod
    def compute_lexical_overlap(cls, query: str, text: str) -> float:
        q_tokens = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()) if w not in cls.STOP_WORDS]
        if not q_tokens:
            return 0.0
        text_lower = text.lower()
        matched = sum(1 for tok in q_tokens if tok in text_lower)
        return matched / len(q_tokens)

    @classmethod
    def compute_hybrid_relevance(cls, query: str, text: str, dense_similarity: float) -> float:
        lexical = cls.compute_lexical_overlap(query, text)
        if lexical > 0.0:
            return (dense_similarity * 0.60) + (lexical * 0.40)

        # When lexical overlap is 0.0:
        # If query is a meta/conceptual question about document structure or ideas,
        # AND the dense similarity is genuinely high (>= 0.78, indicating real semantic embedding alignment),
        # preserve the dense semantic score.
        q_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()))
        if dense_similarity >= 0.78 and q_words.intersection(cls.META_WORDS):
            return dense_similarity

        # Off-topic queries / unrelated domains / mock embeddings without lexical overlap get capped
        return dense_similarity * 0.30
