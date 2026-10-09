"""Classify Gemini API failures and map them to user-facing messages."""

from __future__ import annotations


RATE_LIMIT_MESSAGE = (
    "The answering service is temporarily rate-limited. "
    "Wait a minute and try again — your documents stay indexed and sources are unchanged."
)
SERVICE_UNAVAILABLE_MESSAGE = (
    "The answering service is temporarily unavailable. Please try again in a moment."
)
MISSING_CONFIGURATION_MESSAGE = (
    "The app is not fully configured. Add GEMINI_API_KEY and LLM_MODEL to your .env file, then restart."
)
GENERIC_GENERATION_MESSAGE = (
    "Could not generate an answer right now. Please try again. Technical details were written to the log."
)
EMBEDDING_FAILURE_MESSAGE = (
    "Could not embed this document because the embedding service failed. "
    "Check your API key, quota, and network, then try again."
)


def error_text(exc: BaseException) -> str:
    return str(exc) if exc is not None else ""


def is_quota_error(exc: BaseException) -> bool:
    text = error_text(exc).upper()
    return "RESOURCE_EXHAUSTED" in text or "QUOTA" in text


def is_rate_limit_error(exc: BaseException) -> bool:
    text = error_text(exc)
    upper = text.upper()
    return "429" in text or "RATE" in upper or is_quota_error(exc)


def is_transient_error(exc: BaseException) -> bool:
    """Retry only short-lived failures, not daily quota exhaustion."""
    if is_quota_error(exc):
        return False
    text = error_text(exc).upper()
    return any(token in text for token in ("503", "UNAVAILABLE", "DEADLINE", "TIMEOUT", "CONNECTION"))


def user_message_for_exception(exc: BaseException) -> str:
    if is_quota_error(exc) or is_rate_limit_error(exc):
        return RATE_LIMIT_MESSAGE
    if is_transient_error(exc):
        return SERVICE_UNAVAILABLE_MESSAGE
    return GENERIC_GENERATION_MESSAGE
