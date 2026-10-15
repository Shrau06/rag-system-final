# app.py

import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import streamlit as st
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from embed_index import load_chunks, load_chroma_collection, load_embed_model
from retrieve   import load_or_build_bm25
from generate   import init_client

from pages.chat       import render_chat
from pages.batch_json import render_batch_json
from pages.batch_csv  import render_batch_csv

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title = "Psychology RAG System",
    page_icon  = "book",
    layout     = "wide"
)

# ── Hide default Streamlit multipage navigation in sidebar ──
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

# ─────────────────────────────────────────────
# LOAD COMPONENTS ONCE
# ─────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_all():
    chunks     = load_chunks("cache/chunks.json")
    collection = load_chroma_collection()
    model      = load_embed_model()
    bm25       = load_or_build_bm25(chunks)
    client     = init_client()
    return {
        "chunks":     chunks,
        "collection": collection,
        "model":      model,
        "bm25":       bm25,
        "client":     client
    }

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():

    # Load components
    with st.spinner("Loading system..."):
        try:
            components = load_all()
        except Exception as e:
            st.error(f"Failed to load system: {e}")
            st.info("Make sure ingest.py and embed_index.py have been run.")
            st.stop()
            return

    # ── Main Chat Interface ──
    render_chat(components)


if __name__ == "__main__":
    main()