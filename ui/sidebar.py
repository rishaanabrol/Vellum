import streamlit as st
from typing import List, Callable

from core.embeddings import EmbeddingService
from core.ingest import DuplicateDocumentError, NoExtractableTextError, index_file_bytes
from core.llm import LLMService
from core.vector_store import VectorStore
from core.api_errors import user_message_for_exception


def _progress_row(filename: str, detail: str, current: int, total: int, ready: bool = False) -> str:
    pct = 100 if ready or total == 0 else int((current / total) * 100)
    status_class = "status-ready" if ready else "status-indexing"
    bar = f'<div class="doc-progress"><span style="width:{pct}%"></span></div>'
    return f"""
    <div class="doc-row">
      <div class="doc-title">{filename}</div>
      <div class="doc-meta"><span class="status-indicator {status_class}"></span>{detail}</div>
      {bar}
    </div>
    """


def render_sidebar(
    vector_store: VectorStore,
    embedding_service: EmbeddingService,
    llm_service: LLMService,
    on_document_ingested: Callable[[], None],
) -> List[str]:
    """
    Knowledge Base panel: upload, processing morph, catalog, scope filter.
    Returns selected_document_ids (empty list means all documents).
    """
    st.markdown("### Knowledge Base")
    st.caption("Documents stay on disk in the vector store, not only in this session.")
    if st.session_state.get("scan_warning"):
        # Shown once after indexing; the per-document pill keeps it available afterwards.
        st.warning(st.session_state.pop("scan_warning"))

    # A delete click clears the uploader on the NEXT run, before the widget is
    # created (Streamlit forbids touching widget state after instantiation).
    if st.session_state.pop("reset_uploader", False):
        st.session_state.pop("doc_uploader", None)

    uploaded_files = st.file_uploader(
        "Add documents",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        help="Upload lecture notes, textbooks, or lab manuals (.pdf, .txt)",
        key="doc_uploader",
    )

    if "handled_upload_ids" not in st.session_state:
        st.session_state.handled_upload_ids = []

    indexed_any = False
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_bytes = uploaded_file.getvalue()
            filename = uploaded_file.name
            upload_key = f"{uploaded_file.size}:{filename}:{len(file_bytes)}"
            if upload_key in st.session_state.handled_upload_ids:
                continue
            status_box = st.empty()

            # Every handled upload is recorded exactly once: a rerun never re-embeds a
            # file, and a failing file never retries in a loop.
            try:
                record, scanned_pages = index_file_bytes(
                    file_bytes,
                    filename,
                    vector_store,
                    embedding_service,
                    llm_service=llm_service,
                    progress=lambda step, detail, current, total, name=filename: status_box.markdown(
                        _progress_row(name, detail, current, total, ready=(step == "ready")),
                        unsafe_allow_html=True,
                    ),
                )
                st.session_state.handled_upload_ids.append(upload_key)
                indexed_any = True
                if scanned_pages:
                    st.session_state["scan_warning"] = (
                        f"Pages {', '.join(map(str, scanned_pages))} in '{filename}' "
                        "look scanned and could not be read."
                    )
            except DuplicateDocumentError as e:
                st.info(str(e))
                st.session_state.handled_upload_ids.append(upload_key)
            except NoExtractableTextError as e:
                st.warning(str(e))
                st.session_state.handled_upload_ids.append(upload_key)
            except ValueError as e:
                st.warning(str(e))
                st.session_state.handled_upload_ids.append(upload_key)
            except Exception as e:
                st.error(user_message_for_exception(e))
                st.session_state.handled_upload_ids.append(upload_key)

    if indexed_any:
        on_document_ingested()

    st.markdown("---")
    documents = vector_store.list_documents()
    if not documents:
        st.caption("No documents in workspace.")
        return []

    st.markdown("#### Document scope")
    scope_mode = st.radio(
        "Search scope",
        options=["All documents", "Select specific"],
        label_visibility="collapsed",
    )

    selected_doc_ids: List[str] = []
    if scope_mode == "Select specific":
        doc_options = {d.document_id: f"{d.document_name} ({d.total_chunks} sections)" for d in documents}
        selected_doc_ids = st.multiselect(
            "Select documents to query",
            options=list(doc_options.keys()),
            format_func=lambda x: doc_options[x],
        )

    st.markdown(f"#### Active documents ({len(documents)})")
    for doc in documents:
        page_label = "1 page" if doc.total_pages == 1 else f"{doc.total_pages} pages"
        sec_label = "1 section" if doc.total_chunks == 1 else f"{doc.total_chunks} sections"
        with st.expander(doc.document_name):
            st.markdown(
                f'<div class="doc-row"><div class="doc-meta">'
                f'<span class="status-indicator status-ready"></span>'
                f'{page_label} · {sec_label}</div></div>',
                unsafe_allow_html=True,
            )
            if doc.scanned_pages:
                pages = ", ".join(map(str, doc.scanned_pages))
                st.markdown(
                    f'<div class="scanned-pill">Pages {pages} look scanned and could not be read</div>',
                    unsafe_allow_html=True,
                )
            if doc.summary:
                st.caption(doc.summary)
            if doc.suggested_questions:
                st.caption("Suggested questions")
                for i, q in enumerate(doc.suggested_questions):
                    if st.button(q, key=f"sq_{doc.document_id}_{i}"):
                        st.session_state["pending_prompt"] = q
                        st.rerun()
            if st.button("Remove from workspace", key=f"del_{doc.document_id}"):
                vector_store.delete_document(doc.document_id)
                st.session_state.current_sources = []
                st.session_state["reset_uploader"] = True
                # Forget this file's upload key so it can be re-added later.
                st.session_state.handled_upload_ids = [
                    k for k in st.session_state.handled_upload_ids
                    if k.split(":", 1)[1].rsplit(":", 1)[0] != doc.document_name
                ]
                st.rerun()

    return selected_doc_ids
