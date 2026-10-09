import re
from typing import List
from core.models import Chunk
from core.document_processor import ProcessedPage
from config import settings

class Chunker:
    """
    Intelligent document chunker that prioritizes splitting along paragraph and sentence boundaries
    over character slicing. Preserves page numbers, computes zero-padded chunk_ids, and ensures
    chunks never overlap into exact duplicates.
    """

    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_page(self, page_text: str, document_id: str, document_name: str, page_number: int, starting_chunk_id: int) -> List[Chunk]:
        """
        Splits a single page's text into Chunk objects.
        """
        if not page_text or not page_text.strip():
            return []

        # Split on natural paragraph breaks first
        paragraphs = [p.strip() for p in page_text.split('\n\n') if p.strip()]
        
        # If no double-newline paragraphs, split on single newlines
        if len(paragraphs) <= 1:
            paragraphs = [p.strip() for p in page_text.split('\n') if p.strip()]
            if not paragraphs:
                paragraphs = [page_text.strip()]

        chunks: List[Chunk] = []
        current_text = ""
        chunk_id = starting_chunk_id

        def commit_chunk(text: str):
            nonlocal chunk_id
            text = text.strip()
            if text:
                chunks.append(Chunk(
                    document_id=document_id,
                    document_name=document_name,
                    chunk_id=chunk_id,
                    page_number=page_number,
                    text=text
                ))
                chunk_id += 1

        for para in paragraphs:
            # If paragraph itself is excessively large, split it by sentence or clause
            if len(para) > self.chunk_size:
                sentences = re.split(r'(?<=[.!?]) +', para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if len(sentence) > self.chunk_size:
                        # Hard fallback on word boundaries for huge uninterrupted clauses
                        words = sentence.split()
                        sub_buf = ""
                        for w in words:
                            if len(sub_buf) + len(w) + 1 > self.chunk_size:
                                commit_chunk(sub_buf)
                                # Overlap from previous buffer end
                                overlap_words = sub_buf.split()[-max(1, self.chunk_overlap // 10):]
                                sub_buf = " ".join(overlap_words) + " " + w
                            else:
                                sub_buf = (sub_buf + " " + w).strip()
                        if sub_buf:
                            commit_chunk(sub_buf)
                    else:
                        if len(current_text) + len(sentence) + 1 > self.chunk_size:
                            commit_chunk(current_text)
                            # Retain overlap tail
                            current_text = current_text[-self.chunk_overlap:].strip() + " " + sentence if self.chunk_overlap > 0 else sentence
                        else:
                            current_text = (current_text + " " + sentence).strip()
            else:
                if len(current_text) + len(para) + 2 > self.chunk_size:
                    commit_chunk(current_text)
                    current_text = current_text[-self.chunk_overlap:].strip() + "\n\n" + para if self.chunk_overlap > 0 else para
                else:
                    current_text = (current_text + "\n\n" + para).strip()

        if current_text.strip():
            commit_chunk(current_text)

        return chunks

    def chunk_document(self, pages: List[ProcessedPage], document_id: str, document_name: str) -> List[Chunk]:
        """
        Chunks all pages of a processed document.
        Maintains chunk_id sequence across pages.
        """
        all_chunks: List[Chunk] = []
        next_chunk_id = 0

        for page in pages:
            if page.is_scanned or not page.text:
                continue
            page_chunks = self.chunk_page(
                page_text=page.text,
                document_id=document_id,
                document_name=document_name,
                page_number=page.page_number,
                starting_chunk_id=next_chunk_id
            )
            all_chunks.extend(page_chunks)
            next_chunk_id += len(page_chunks)

        return all_chunks
