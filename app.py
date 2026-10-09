import logging
import streamlit as st

from config import settings
from core.api_errors import MISSING_CONFIGURATION_MESSAGE, user_message_for_exception
from core.embeddings import EmbeddingService
from core.llm import LLMService
from core.rag import RAGPipeline
from core.retriever import Retriever
from core.vector_store import VectorStore
from ui.chat import format_citations_to_chips, render_chat_interface
from ui.components import render_empty_state
from ui.cover import render_cover
from ui.sidebar import render_sidebar
from ui.sources import render_sources_panel
from ui.styles import CSS_STYLES

logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="Vellum — Knowledge Workspace",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(CSS_STYLES, unsafe_allow_html=True)

# KaTeX: render LaTeX math ($...$, $$...$$, \(...\), \[...\]) in answers and
# in the page body. st.markdown never executes <script> tags and strips inline
# event handlers, so the libraries are injected from a tiny components.html
# iframe, which shares the parent origin and can append <script> tags that the
# browser really executes. A debounced MutationObserver re-typesets chat content
# as it streams in.
import streamlit.components.v1 as components

_KATEX_IFRAME_HTML = r"""
<script>
(function () {
  var p = window.parent;
  if (!p || !p.document) { return; }
  var d = p.document;
  /* Re-inject on every version bump so an updated page never keeps a stale
     bootstrap around (the guard id is part of the version). */
  if (d.getElementById('vellum-katex-boot-v2')) { return; }
  var src = `
var BS = String.fromCharCode(92);
var VELLUM_DELIMS = [
  { left: '$$', right: '$$', display: true },
  { left: BS + '[', right: BS + ']', display: true },
  { left: '$', right: '$', display: false },
  { left: BS + '(', right: BS + ')', display: false }
];
var VELLUM_OPTS = {
  delimiters: VELLUM_DELIMS,
  throwOnError: false,
  ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'option']
};
function vellumWrap() {
  if (window.__vellumRenderWrapped || !window.renderMathInElement) { return; }
  window.__vellumRenderWrapped = true;
  var orig = window.renderMathInElement;
  window.renderMathInElement = function (el) {
    return orig.call(this, el, VELLUM_OPTS);
  };
}
function vellumRender() {
  if (!window.renderMathInElement) { return; }
  try { window.renderMathInElement(document.body, VELLUM_OPTS); } catch (e) {}
}
var vellumScheduled = 0;
function vellumRenderSoon() {
  if (vellumScheduled) { return; }
  vellumScheduled = setTimeout(function () { vellumScheduled = 0; vellumRender(); }, 150);
}
function vellumAttach() {
  vellumWrap();
  vellumRender();
  if (!window.__vellumMathObserverV2) {
    window.__vellumMathObserverV2 = true;
    new MutationObserver(vellumRenderSoon).observe(document.body, { childList: true, subtree: true });
  }
}
window.__vellumKatex = true;
if (window.katex && window.renderMathInElement) {
  vellumAttach();
} else {
  var css = document.createElement('link');
  css.rel = 'stylesheet';
  css.href = 'https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.css';
  document.head.appendChild(css);
  var core = document.createElement('script');
  core.src = 'https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.js';
  core.onload = function () {
    var auto = document.createElement('script');
    auto.src = 'https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/contrib/auto-render.min.js';
    auto.onload = vellumAttach;
    document.head.appendChild(auto);
  };
  document.head.appendChild(core);
}
`;
  var s = d.createElement('script');
  s.id = 'vellum-katex-boot-v2';
  s.textContent = src;
  d.head.appendChild(s);
})();
</script>
"""

# `st.components.v1.html` is deprecated (removal announced for 2026-06-01) and
# `st.iframe` is its replacement; older Streamlit releases only have the former.
if hasattr(st, "iframe"):
    st.iframe(_KATEX_IFRAME_HTML, height=1)
else:
    components.html(_KATEX_IFRAME_HTML, height=1)

@st.cache_resource
def get_services():
    emb_service = EmbeddingService()
    v_store = VectorStore()
    retriever = Retriever(v_store, emb_service)
    llm = LLMService()
    rag = RAGPipeline(retriever, llm)
    return emb_service, v_store, retriever, llm, rag


emb_service, vector_store, retriever, llm_service, rag_pipeline = get_services()

# The cover is the front door of the product: it shows until the reader
# chooses to enter. Everything after it is the real workspace.
if not st.session_state.get("entered_vellum"):
    render_cover()
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_sources" not in st.session_state:
    st.session_state.current_sources = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "awaiting_answer" not in st.session_state:
    st.session_state.awaiting_answer = False
if "highlight_source" not in st.session_state:
    st.session_state.highlight_source = 0

# Pin the chat input bar to the viewport bottom without overlapping content.
#
# The correct approach: inject a <style> tag that turns stMain into a full-height
# flex column. stMainBlockContainer grows to fill available space (and scrolls).
# stBottom — already the last child — naturally lands at the viewport bottom.
# No position:fixed, no move-to-body, no overlap.
_PIN_CHAT_INPUT = """
<script>
(function(){
  var p = window.parent;
  if (!p || !p.document) return;

  var old = p.document.getElementById('vellum-chat-pin-v7');
  if (old) old.remove();

  var s = p.document.createElement('style');
  s.id = 'vellum-chat-pin-v7';
  s.textContent = `
    /* ── Layout: full-height flex column ── */
    [data-testid="stMain"] {
      height: 100vh !important;
      display: flex !important;
      flex-direction: column !important;
      overflow: hidden !important;
    }
    [data-testid="stMainBlockContainer"] {
      flex: 1 1 auto !important;
      overflow-y: auto !important;
      min-height: 0 !important;
    }

    /* ── Chat bar: sits naturally at bottom of flex column ── */
    .stBottom, [data-testid="stBottom"] {
      flex-shrink: 0 !important;
      position: relative !important;
      bottom: auto !important; left: auto !important; right: auto !important;
      width: 100% !important;
      background: #E8E0D2 !important;
      border-top: 1px solid rgba(36,35,31,.20) !important;
      padding: 10px 24px 14px !important;
      margin: 0 !important;
      z-index: 100 !important;
      box-sizing: border-box !important;
      transform: none !important;
    }
    [data-testid="stBottomBlockContainer"] {
      padding: 0 !important;
      margin: 0 !important;
    }

    /* ── Chat textarea: indented text ── */
    [data-testid="stChatInput"] textarea {
      padding-left: 16px !important;
      font-family: 'Cormorant Garamond', Georgia, serif !important;
      font-size: 16.5px !important;
    }

    /* ── Expanders: rounded corners ── */
    [data-testid="stExpander"] {
      border-radius: 10px !important;
      overflow: hidden !important;
    }
    [data-testid="stExpander"] summary {
      border-radius: 10px !important;
    }

    /* ── Hide Streamlit chrome ── */
    header[data-testid="stHeader"]    { display: none !important; }
    [data-testid="stDecoration"]      { display: none !important; }
    [data-testid="stStatusWidget"]    { display: none !important; }

    /* ── Brand text: force Vellum casing ── */
    .desk-brand {
      text-transform: none !important;
      font-variant: normal !important;
    }
  `;

  p.document.head.appendChild(s);

  /* Re-append whenever Streamlit injects a new <style> so we always win */
  new MutationObserver(function(muts) {
    for (var m of muts) {
      for (var n of m.addedNodes) {
        if (n.nodeName === 'STYLE' && n.id !== 'vellum-chat-pin-v7') {
          p.document.head.appendChild(s);
          return;
        }
      }
    }
  }).observe(p.document.head, { childList: true });
})();
</script>
"""

if hasattr(st, "iframe"):
    st.iframe(_PIN_CHAT_INPUT, height=1)
else:
    components.html(_PIN_CHAT_INPUT, height=1)


# Workspace titleplate — the cover's wordmark settles onto the desk.
st.markdown(
    """
<div class="desk-header">
  <div class="desk-title-row">
    <div class="desk-brand" style="text-transform:none!important;font-variant:normal!important">Vellum<em>a new way of learning</em></div>
    <div class="desk-folio">
      <strong>Your library · Your questions · Your evidence</strong>
      Grounded in the pages you place here
    </div>
  </div>
  <p class="desk-intro">
    Place lecture notes, PDFs, and text files on the desk. Ask in your own words and
    every answer arrives with the passages that ground it, so you can read, verify,
    and understand with confidence.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

if not settings.has_api_key() or not settings.LLM_MODEL:
    st.warning(MISSING_CONFIGURATION_MESSAGE)

documents = vector_store.list_documents()
total_docs = len(documents)

knowledge_col, chat_col, sources_col = st.columns([0.95, 1.7, 1.15], gap="medium")


def on_doc_ingested():
    st.rerun()


with knowledge_col:
    selected_doc_ids = render_sidebar(
        vector_store=vector_store,
        embedding_service=emb_service,
        llm_service=llm_service,
        on_document_ingested=on_doc_ingested,
    )

with chat_col:
    if total_docs == 0:
        render_empty_state()
    else:
        render_chat_interface(
            messages=st.session_state.messages,
            on_send_message=lambda msg: None,
        )

        if st.session_state.awaiting_answer and st.session_state.messages:
            last_user = next(
                (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"),
                None,
            )
            if last_user:
                with st.chat_message("assistant"):
                    status_placeholder = st.empty()
                    scope_count = len(selected_doc_ids) if selected_doc_ids else total_docs
                    status_placeholder.markdown(
                        f'<div class="process-status"><span class="process-bar"></span>'
                        f"Searching {scope_count} documents</div>",
                        unsafe_allow_html=True,
                    )

                    history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[:-1]
                    ]

                    def on_status(label: str) -> None:
                        status_placeholder.markdown(
                            f'<div class="process-status"><span class="process-bar"></span>{label}</div>',
                            unsafe_allow_html=True,
                        )

                    try:
                        rewritten_q, sources, stream, _is_refusal = rag_pipeline.answer_query_stream(
                            query=last_user,
                            chat_history=history,
                            document_ids=selected_doc_ids if selected_doc_ids else None,
                            on_status=on_status,
                        )
                    except Exception as e:
                        logging.exception("RAG pipeline failed")
                        st.error(user_message_for_exception(e))
                        st.session_state.awaiting_answer = False
                        st.stop()

                    status_placeholder.empty()
                    # Show this answer's snippets in the Evidence panel right away
                    # (before the stream starts) so live citation chips resolve.
                    st.session_state.current_sources = sources
                    st.session_state.highlight_source = 0
                    if rewritten_q and rewritten_q != last_user:
                        st.markdown(
                            f'<div class="rewritten-notice">Searched for: <em>{rewritten_q}</em></div>',
                            unsafe_allow_html=True,
                        )

                    answer_placeholder = st.empty()
                    full_response = ""
                    for token in stream:
                        full_response += token
                        answer_placeholder.markdown(
                            format_citations_to_chips(full_response),
                            unsafe_allow_html=True,
                        )

                    validated_response = RAGPipeline.validate_citations(full_response, len(sources))
                    answer_placeholder.markdown(
                        format_citations_to_chips(validated_response),
                        unsafe_allow_html=True,
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": validated_response,
                            "rewritten_query": rewritten_q if rewritten_q != last_user else None,
                            "n_sources": len(sources),
                            # Kept per message so citation chips can re-open the
                            # evidence for any earlier answer, not just the latest.
                            "sources": sources,
                        }
                    )
                    st.session_state.current_sources = sources
                    st.session_state.highlight_source = 0
                    st.session_state.awaiting_answer = False
                    st.rerun()

with sources_col:
    render_sources_panel(st.session_state.current_sources, vector_store=vector_store)

prompt_input = st.chat_input(
    "Ask a question about your documents…",
    disabled=(total_docs == 0 or st.session_state.awaiting_answer),
)

active_prompt = prompt_input or st.session_state.pending_prompt
if st.session_state.pending_prompt:
    st.session_state.pending_prompt = None

if active_prompt and total_docs > 0 and not st.session_state.awaiting_answer:
    st.session_state.messages.append({"role": "user", "content": active_prompt})
    st.session_state.awaiting_answer = True
    st.rerun()
