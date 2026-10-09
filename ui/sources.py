import html
from pathlib import Path
from typing import List, Optional

import streamlit as st

from config import settings
from core.models import Source
from core.page_renderer import PDFPageRenderer
from core.vector_store import VectorStore


def _resolve_source_path(source: Source, vector_store: Optional[VectorStore]) -> Optional[Path]:
    if vector_store and source.document_id:
        record = vector_store.get_document(source.document_id)
        if record and record.file_path:
            path = Path(record.file_path)
            if path.exists():
                return path

    docs_dir = Path(settings.DOCUMENTS_DIR)
    if docs_dir.exists() and source.document_id:
        matches = sorted(docs_dir.glob(f"{source.document_id}_*"))
        if matches:
            return matches[0]
    if docs_dir.exists() and source.document_name:
        matches = [p for p in docs_dir.iterdir() if p.name.endswith(source.document_name)]
        if len(matches) == 1:
            return matches[0]
    sample = Path("./sample_documents") / source.document_name
    if sample.exists():
        return sample
    return None


def _snippet_html(source: Source) -> str:
    """Snippet text with the key sentence marked.

    Retrieved text is untrusted document content: escape it before it touches HTML.
    """
    snippet_text = html.escape(source.text)
    highlight_html = html.escape(source.highlight_text) if source.highlight_text else ""
    if highlight_html and highlight_html in snippet_text:
        parts = snippet_text.split(highlight_html, 1)
        return (
            f"<div class='source-snippet'>{parts[0]}"
            f"<mark class='source-highlight'>{highlight_html}</mark>"
            f"{parts[1]}</div>"
        )
    return f"<div class='source-snippet'>{snippet_text}</div>"


def _source_card_html(
    source: Source,
    number: int,
    anchor_id: str,
    active: bool = False,
    delay: int = 0,
) -> str:
    """One evidence card: provenance header plus the verifiable snippet text.

    ``anchor_id`` is what citation chips deep-link to; ids must be unique per
    rendering context (panel vs. a specific chat message).
    """
    doc_name = html.escape(source.document_name)
    active_cls = " source-card-active" if active else ""
    return (
        f'<div class="source-card{active_cls}" id="{anchor_id}" style="animation-delay:{delay}ms">'
        f'<div class="source-header">'
        f'<span class="source-doc-ref">[{number}] {doc_name} · Page {source.page_number}</span>'
        f'<span class="source-sim-score">{int(source.similarity * 100)}% match</span>'
        f"</div>"
        f"{_snippet_html(source)}"
        f"</div>"
    )


def render_inline_sources(sources: List[Source], anchor_prefix: str) -> None:
    """
    Renders an answer's evidence snippets directly beneath that answer so the
    source text sits alongside the claim it grounds. ``anchor_prefix`` scopes
    card ids per message (e.g. "m3-") so each chip deep-links to the right card.
    """
    if not sources:
        return
    st.markdown(
        f'<div class="inline-evidence-label">Source snippets · {len(sources)}</div>',
        unsafe_allow_html=True,
    )
    for number, source in enumerate(sources, 1):
        st.markdown(
            _source_card_html(
                source,
                number,
                anchor_id=f"source-{anchor_prefix}{number}",
                delay=(number - 1) * 50,
            ),
            unsafe_allow_html=True,
        )


def render_sources_panel(sources: List[Source], vector_store: Optional[VectorStore] = None):
    highlight = int(st.session_state.get("highlight_source") or 0)
    st.markdown(f"### Evidence · {len(sources)}")

    if not sources:
        st.caption("Retrieved snippets will appear here after you ask a question.")
        return

    for idx, source in enumerate(sources, 1):
        st.markdown(
            _source_card_html(
                source,
                idx,
                anchor_id=f"source-{idx}",
                active=(highlight == idx),
                delay=(idx - 1) * 50,
            ),
            unsafe_allow_html=True,
        )

        with st.expander(f"View page {source.page_number}"):
            file_path = _resolve_source_path(source, vector_store)
            if file_path is None:
                st.caption("Original file is not cached locally for page inspection.")
            elif file_path.suffix.lower() == ".pdf":
                page_img = PDFPageRenderer.render_page_image(file_path.read_bytes(), source.page_number)
                if page_img:
                    st.image(
                        page_img,
                        caption=f"{source.document_name} — Page {source.page_number}",
                        use_container_width=True,
                    )
                else:
                    st.caption("Unable to render that PDF page.")
            else:
                full_txt = file_path.read_text(encoding="utf-8", errors="replace")
                loc = full_txt.find(source.text[:80]) if source.text else -1
                start = max(0, loc - 400) if loc >= 0 else 0
                st.text_area(
                    "Surrounding text",
                    full_txt[start:start + 2000],
                    height=220,
                    disabled=True,
                    key=f"txt_ctx_{idx}_{source.chunk_id}",
                )
