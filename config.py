import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    # Google GenAI Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    # Model ID must come from the environment; do not guess a Flash version here.
    LLM_MODEL: str = os.getenv("LLM_MODEL", "").strip()
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")

    # Chunking Defaults
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "120"))

    # Retrieval Thresholds (calibrated via eval/questions.json + eval/run_eval.py).
    # Measured on the sample corpus with gemini-embedding-001:
    #   on-topic expected chunks score 0.738-0.932 hybrid, off-topic peaks at 0.527.
    # 0.65 sits above the off-topic ceiling while keeping every on-topic chunk.
    TOP_K: int = int(os.getenv("TOP_K", "5"))
    CANDIDATE_K: int = int(os.getenv("CANDIDATE_K", "8"))
    MIN_RELEVANCE: float = float(os.getenv("MIN_RELEVANCE", "0.65"))

    # Persistence Directories
    BASE_DIR: Path = Path(__file__).resolve().parent
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / os.getenv("CHROMA_PERSIST_DIR", "./storage/chroma"))
    DOCUMENTS_DIR: str = str(BASE_DIR / os.getenv("DOCUMENTS_DIR", "./storage/docs"))

    # Uploads
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "25"))
    MAX_UPLOAD_BYTES: int = MAX_UPLOAD_MB * 1024 * 1024

    # System Constants
    COLLECTION_NAME: str = "document_knowledge_base"
    NO_ANSWER_MESSAGE: str = "I couldn't find enough information in your uploaded documents to answer this question."

    def has_api_key(self) -> bool:
        key = (self.GEMINI_API_KEY or "").strip()
        return bool(key) and key != "your_gemini_api_key_here"

settings = Settings()
