import re
from typing import List, Dict, Optional, Tuple, Iterator
from core.models import Source, Answer
from core.retriever import Retriever
from core.llm import LLMService
from config import settings

class RAGPipeline:
    """
    Orchestrates query rewriting, retrieval, threshold evaluation,
    LLM grounded generation, and post-processing citation validation.
    """

    def __init__(self, retriever: Retriever, llm_service: LLMService):
        self.retriever = retriever
        self.llm_service = llm_service

    @staticmethod
    def validate_citations(text: str, max_source_index: int) -> str:
        """
        Validates citation markers like [1], [2] in text.
        Strips any citation markers whose index is > max_source_index or <= 0.
        """
        def replace_cite(match):
            idx = int(match.group(1))
            if 1 <= idx <= max_source_index:
                return f"[{idx}]"
            return "" # Strip invalid citation hallucination

        cleaned = re.sub(r'\[(\d+)\]', replace_cite, text)
        # Collapse only the mid-line gaps left behind by stripped citations so
        # markdown indentation (code blocks, nested lists) survives intact.
        cleaned = re.sub(r'(?<=\S) {2,}', ' ', cleaned)
        # …and close the gap a removed marker leaves before punctuation: "fake [9]." -> "fake."
        cleaned = re.sub(r'(?<=\S) +(?=[,.;:!?])', '', cleaned)
        return cleaned

    def answer_query_stream(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        document_ids: Optional[List[str]] = None,
        on_status=None,
    ) -> Tuple[Optional[str], List[Source], Iterator[str], bool]:
        """
        Executes query through pipeline:
          1. Query rewriting if conversational history exists.
          2. Retrieval with candidate deduplication and threshold cutoff.
          3. Deterministic refusal if zero sources pass threshold (skips LLM entirely).
          4. Returns (rewritten_query, sources, answer_stream, is_refusal).
        """
        chat_history = chat_history or []

        def status(label: str) -> None:
            if on_status:
                on_status(label)

        # 1. Query rewriting for follow-ups
        rewritten_query = None
        search_query = query
        if chat_history and len(chat_history) > 0:
            status("Rewriting follow-up into a standalone search query")
            rewritten_query = self.llm_service.rewrite_query(query, chat_history)
            search_query = rewritten_query

        # 2. Semantic retrieval
        status("Finding relevant passages")
        sources = self.retriever.retrieve(search_query, document_ids=document_ids)
        if not sources and rewritten_query and search_query != query:
            # If the rewritten query yielded zero results, retry retrieval with the raw query
            sources = self.retriever.retrieve(query, document_ids=document_ids)
            if sources:
                rewritten_query = None  # Revert to original query as it was the successful one

        # 3. Deterministic refusal: if no chunk passes threshold, skip LLM call
        if not sources:
            def refusal_stream():
                yield settings.NO_ANSWER_MESSAGE

            return rewritten_query, [], refusal_stream(), True

        # 4. Format context blocks for LLM
        context_blocks = []
        for idx, s in enumerate(sources, 1):
            block = f"[{idx}] Source Document: {s.document_name} (Page {s.page_number})\n{s.text}"
            context_blocks.append(block)

        # 5. Generate grounded response stream
        status("Writing answer")
        raw_stream = self.llm_service.generate_grounded_answer_stream(query, context_blocks)

        return rewritten_query, sources, raw_stream, False

    def answer_query(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        document_ids: Optional[List[str]] = None
    ) -> Answer:
        """
        Synchronous non-streaming evaluation execution of RAG pipeline.
        """
        rewritten_query, sources, stream, is_refusal = self.answer_query_stream(
            query=query,
            chat_history=chat_history,
            document_ids=document_ids
        )

        full_content = "".join(list(stream))

        if is_refusal:
            return Answer(
                content=settings.NO_ANSWER_MESSAGE,
                sources=[],
                rewritten_query=rewritten_query,
                is_grounded=True,
                no_answer_refusal=True
            )

        # Post-processing citation validation
        validated_content = self.validate_citations(full_content, len(sources))

        return Answer(
            content=validated_content,
            sources=sources,
            rewritten_query=rewritten_query,
            is_grounded=True,
            no_answer_refusal=False
        )
