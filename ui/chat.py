import re
import streamlit as st
from typing import List, Dict, Callable

from ui.sources import render_inline_sources


def format_citations_to_chips(text: str, anchor_prefix: str = "") -> str:
    """
    Turns [1], [2] into citation chips.
    Each chip deep-links to the evidence card rendered alongside its answer
    (#source-<prefix>N); the card lights up via CSS :target. The default prefix
    targets the right-hand Evidence panel (used while an answer streams, before
    its message exists in history).
    """
    return re.sub(
        r"\[(\d+)\]",
        lambda m: f'<a class="citation-chip" href="#source-{anchor_prefix}{m.group(1)}">[{m.group(1)}]</a>',
        text,
    )


def render_chat_interface(
    messages: List[Dict],
    on_send_message: Callable[[str], None],
    is_answering: bool = False,
):
    st.markdown(
        '<h3 style="text-align:center;font-family:\'Cormorant Garamond\',Georgia,serif;'
        'font-weight:600;font-size:27px;color:#24231F;letter-spacing:0.01em;margin-bottom:2px">Discussion</h3>',
        unsafe_allow_html=True,
    )

    for idx, msg in enumerate(messages):
        role = msg["role"]
        content = msg["content"]
        rewritten = msg.get("rewritten_query")
        n_sources = int(msg.get("n_sources") or 0)

        with st.chat_message(role):
            if role == "assistant" and rewritten:
                st.markdown(
                    f'<div class="rewritten-notice">Searched for: <em>{rewritten}</em></div>',
                    unsafe_allow_html=True,
                )

            if role == "assistant":
                anchor_prefix = f"m{idx}-"
                st.markdown(format_citations_to_chips(content, anchor_prefix), unsafe_allow_html=True)
                answer_sources = msg.get("sources") or []
                # Show this answer's evidence right beneath it so the source text
                # can be read alongside the claim it grounds.
                render_inline_sources(answer_sources, anchor_prefix)
                if n_sources > 0:
                    chip_cols = st.columns(n_sources)
                    for i in range(n_sources):
                        if chip_cols[i].button(f"[{i + 1}]", key=f"cite_{idx}_{i}"):
                            # Swap the Evidence panel to THIS answer's sources, then
                            # highlight the clicked one for page inspection.
                            if answer_sources:
                                st.session_state["current_sources"] = answer_sources
                            st.session_state["highlight_source"] = i + 1
            else:
                st.markdown(content)

    if messages:
        export_md = "# Document Knowledge Assistant — Study Notes\n\n"
        for m in messages:
            export_md += f"### {m['role'].capitalize()}\n{m['content']}\n\n"
            rewritten = m.get("rewritten_query")
            if rewritten:
                export_md += f"_Searched for:_ {rewritten}\n\n"
        st.download_button(
            label="Export notes (Markdown)",
            data=export_md,
            file_name="study_notes_export.md",
            mime="text/markdown",
            key="export_chat_btn",
        )
