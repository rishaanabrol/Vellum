import time
import math
import random
import logging
from typing import List, Optional
from google import genai
from google.genai import types
from config import settings
from core.api_errors import EMBEDDING_FAILURE_MESSAGE, is_quota_error, is_transient_error

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Handles embedding generation via Google Gemini API (`gemini-embedding-001`).
    Correctly configures task types:
      - RETRIEVAL_DOCUMENT for ingested text chunks
      - RETRIEVAL_QUERY for user queries
    Includes batching, exponential backoff, jitter, and offline fallback (mock mode)
    if no API key is provided during testing.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = settings.EMBEDDING_MODEL):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model
        self.client = None
        key = (self.api_key or "").strip()
        if key and key != "your_gemini_api_key_here":
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning("Failed to initialize genai.Client: %s. Running in offline mock mode.", e)

    def _mock_embedding(self, text: str, dim: int = 768) -> List[float]:
        """Deterministic pseudo-embedding for testing or offline environments."""
        import hashlib
        hasher = hashlib.md5(text.encode("utf-8"))
        seed = int(hasher.hexdigest(), 16)
        rng = random.Random(seed)
        vec = [rng.gauss(0, 1) for _ in range(dim)]
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec]

    def embed_texts(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT", batch_size: int = 32, max_retries: int = 4) -> List[List[float]]:
        """
        Embeds a list of texts in batches with exponential backoff retry.
        """
        if not texts:
            return []

        if not self.client:
            return [self._mock_embedding(t) for t in texts]

        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            attempt = 0
            while attempt < max_retries:
                try:
                    # In google-genai SDK:
                    # client.models.embed_content(model=..., contents=..., config=types.EmbedContentConfig(task_type=...))
                    response = self.client.models.embed_content(
                        model=self.model,
                        contents=batch,
                        config=types.EmbedContentConfig(
                            task_type=task_type
                        )
                    )

                    if hasattr(response, 'embeddings') and response.embeddings:
                        for emb in response.embeddings:
                            all_embeddings.append(emb.values)
                    elif hasattr(response, 'embedding') and response.embedding:
                        all_embeddings.append(response.embedding.values)
                    else:
                        raise ValueError("Unexpected embedding response structure from Gemini API")
                    break

                except Exception as e:
                    attempt += 1
                    logger.warning("Embedding attempt %s failed: %s", attempt, e)
                    if is_quota_error(e) or not is_transient_error(e) or attempt >= max_retries:
                        raise RuntimeError(f"{EMBEDDING_FAILURE_MESSAGE} ({type(e).__name__})") from e
                    wait_time = (2 ** attempt) + random.uniform(0.1, 0.5)
                    time.sleep(wait_time)

        return all_embeddings

    def embed_chunks(self, texts: List[str]) -> List[List[float]]:
        """Generates document embeddings with task_type='RETRIEVAL_DOCUMENT'."""
        return self.embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")

    def embed_query(self, query: str) -> List[float]:
        """Generates query embedding with task_type='RETRIEVAL_QUERY'."""
        embeddings = self.embed_texts([query], task_type="RETRIEVAL_QUERY", batch_size=1)
        return embeddings[0]
