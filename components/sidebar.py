# components/sidebar.py

import streamlit as st

SAMPLE_QUESTIONS = [
    "What is classical conditioning?",
    "Explain Maslow's hierarchy of needs",
    "What are the stages of sleep?",
    "What are the basic parts of a neuron?",
    "What is the difference between classical and operant conditioning?",
    "What are Freud's stages of psychosexual development?",
    "How does short-term memory work?",
    "What is the Big Five personality model?",
    "What is cognitive dissonance?",
    "What are the symptoms of major depressive disorder?",
]


def render_sidebar(components: dict, active_mode: str = "chat"):
    """
    Renders the clean textbook assistant sidebar with:
    - Contents (Chapter navigation)
    - Sample questions
    """
    with st.sidebar:
        st.markdown(
            """
            <style>
            [data-testid="stSidebarNav"] {
                display: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # ── Contents ──
        st.markdown("### Contents")
        chunks = components.get("chunks", [])
        chapters = sorted(list(set(
            c['chapter'] for c in chunks
            if not c.get('is_supplementary', False)
        )))

        with st.expander("Chapters Covered", expanded=False):
            for ch in chapters:
                short = ch.replace("Chapter ", "Ch.")
                st.markdown(f"- {short}")

        st.divider()

        # ── Sample Questions ──
        st.markdown("### Sample Questions")
        st.caption("Click any question to ask:")

        for sample in SAMPLE_QUESTIONS:
            if st.button(
                sample,
                key=f"sidebar_btn_{hash(sample)}",
                use_container_width=True
            ):
                st.session_state.sidebar_question = sample
                st.session_state.trigger_from_sidebar = True
                st.rerun()

        st.divider()

        # ── Footer ──
        st.markdown(
            "<p style='color:gray; font-size:11px; text-align:center; margin-top:20px;'>"
            "OpenStax Psychology 2e"
            "</p>",
            unsafe_allow_html=True
        )