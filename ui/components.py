import streamlit as st


def render_empty_state():
    st.markdown(
        """
        <div class="empty-state">
          <div class="empty-state-eyebrow">The desk is clear</div>
          <div class="empty-state-title">No documents yet</div>
          <div class="empty-state-subtitle">
            Place your lecture notes, textbooks, or manuscripts in the library.<br/>
            Every answer will be grounded in verifiable passages from them.
          </div>
          <div class="empty-state-cta">Add a document to begin</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
