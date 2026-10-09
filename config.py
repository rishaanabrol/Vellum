import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

def _get_conf(key: str, default: str = "") -> str:
    val = os.getenv(key)
    if val is not None and str(val).strip():
        return str(val).strip()
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default

class Settings:
    # Google GenAI Settings
    GEMINI_API_KEY: str = _get_conf("GEMINI_API_KEY", "")
    # Model ID from env or Streamlit secrets; defaults to gemini-2.5-flash if not specified
    LLM_MODEL: str = _get_conf("LLM_MODEL", "gemini-2.5-flash")
    EMBEDDING_MODEL: str = _get_conf("EMBEDDING_MODEL", "gemini-embedding-001")

    # Chunking Defaults
    CHUNK_SIZE: int = int(_get_conf("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(_get_conf("CHUNK_OVERLAP", "120"))

    # Retrieval Thresholds (calibrated via eval/questions.json + eval/run_eval.py).
    TOP_K: int = int(_get_conf("TOP_K", "5"))
    CANDIDATE_K: int = int(_get_conf("CANDIDATE_K", "8"))
    MIN_RELEVANCE: float = float(_get_conf("MIN_RELEVANCE", "0.45"))

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
