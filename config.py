import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

def _get_conf(key: str, default: str = "") -> str:
    # 1. Check environment variables (all case variations)
    for k in (key, key.upper(), key.lower()):
        val = os.getenv(k)
        if val is not None and str(val).strip():
            return str(val).strip()

    # Also check GOOGLE_API_KEY if looking for GEMINI_API_KEY
    if "GEMINI" in key.upper():
        alt_key = key.upper().replace("GEMINI", "GOOGLE")
        for k in (alt_key, alt_key.lower()):
            val = os.getenv(k)
            if val is not None and str(val).strip():
                return str(val).strip()

    # 2. Check Streamlit secrets (all case variations)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            for k in (key, key.upper(), key.lower()):
                try:
                    if k in st.secrets and st.secrets[k]:
                        return str(st.secrets[k]).strip()
                except Exception:
                    pass
            if "GEMINI" in key.upper():
                alt = key.upper().replace("GEMINI", "GOOGLE")
                for k in (alt, alt.lower()):
                    try:
                        if k in st.secrets and st.secrets[k]:
                            return str(st.secrets[k]).strip()
                    except Exception:
                        pass
    except Exception:
        pass

    return default

class Settings:
    # Base directory
    BASE_DIR: Path = Path(__file__).resolve().parent

    @property
    def GEMINI_API_KEY(self) -> str:
        return _get_conf("GEMINI_API_KEY", "")

    @property
    def LLM_MODEL(self) -> str:
        return _get_conf("LLM_MODEL", "gemini-3.5-flash-lite")

    @property
    def EMBEDDING_MODEL(self) -> str:
        return _get_conf("EMBEDDING_MODEL", "gemini-embedding-001")

    @property
    def CHUNK_SIZE(self) -> int:
        return int(_get_conf("CHUNK_SIZE", "800"))

    @property
    def CHUNK_OVERLAP(self) -> int:
        return int(_get_conf("CHUNK_OVERLAP", "120"))

    @property
    def TOP_K(self) -> int:
        return int(_get_conf("TOP_K", "5"))

    @property
    def CANDIDATE_K(self) -> int:
        return int(_get_conf("CANDIDATE_K", "8"))

    @property
    def MIN_RELEVANCE(self) -> float:
        return float(_get_conf("MIN_RELEVANCE", "0.65"))

    @property
    def CHROMA_PERSIST_DIR(self) -> str:
        return str(self.BASE_DIR / _get_conf("CHROMA_PERSIST_DIR", "./storage/chroma"))

    @property
    def DOCUMENTS_DIR(self) -> str:
        return str(self.BASE_DIR / _get_conf("DOCUMENTS_DIR", "./storage/docs"))

    @property
    def MAX_UPLOAD_MB(self) -> int:
        return int(_get_conf("MAX_UPLOAD_MB", "25"))

    @property
    def MAX_UPLOAD_BYTES(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    # System Constants
    COLLECTION_NAME: str = "document_knowledge_base"
    NO_ANSWER_MESSAGE: str = "I couldn't find enough information in your uploaded documents to answer this question."

    def has_api_key(self) -> bool:
        key = (self.GEMINI_API_KEY or "").strip()
        return bool(key) and key != "your_gemini_api_key_here"

settings = Settings()
