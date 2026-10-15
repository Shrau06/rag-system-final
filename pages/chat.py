# pages/chat.py

import streamlit as st
import time
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from retrieve import retrieve
from generate import generate_answer
from utils.citation import find_exact_citations, build_references_from_citations
from components.sidebar import render_sidebar
from components.chat_history import render_chat_history, render_chat_message

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

MIN_RRF_SCORE = 0.02


# ─────────────────────────────────────────────
# INIT SESSION STATE
# ─────────────────────────────────────────────

def init_chat_session():
    defaults = {
        "chat_history":          [],
        "sidebar_question":      "",
        "trigger_from_sidebar":  False,
        "chat_input_value":      "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────
# PROCESS QUESTION
# ─────────────────────────────────────────────

def process_question(question: str, components: dict, answer_style: str = "Standard (2-5 Sentences)"):
    """
    Runs full RAG pipeline for one question.
    Appends result to chat history and logs comprehensive stage timings.
    """
    t0_pipeline = time.perf_counter()
    chat_qid = f"chat_{int(time.time() * 1000)}"

    # Add user message to history
    st.session_state.chat_history.append({
        "role":    "user",
        "content": {"text": question}
    })

    # Retrieve
    t0_retrieval = time.perf_counter()
    retrieved = retrieve(
        query      = question,
        collection = components["collection"],
        model      = components["model"],
        bm25       = components["bm25"],
        chunks     = components["chunks"],
        top_k      = 7
    )
    t_retrieval = time.perf_counter() - t0_retrieval

    # Relevance gate
    top_score = retrieved[0]['rrf_score'] if retrieved else 0

    if top_score < MIN_RRF_SCORE:
        t_total_pipeline = time.perf_counter() - t0_pipeline
        abstention_data = {
            "status": "NOT_FOUND",
            "verdict": "ABSTENTION",
            "is_abstention": True,
            "explanation": "The system could not find sufficient information about this question in the provided textbook."
        }
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": {
                "answer":     "This question does not appear to be "
                              "covered in the OpenStax Psychology 2e "
                              "textbook. Please ask a psychology-related "
                              "question.",
                "citations":  [],
                "references": {},
                "retrieved":  [],
                "elapsed":    round(t_total_pipeline, 3),
                "verification": abstention_data
            }
        })

        # Log diagnostic record for relevance gate abstention
        try:
            from verification_1.diagnostic_logger import build_diagnostic_record, log_diagnostic_record
            diag_rec = build_diagnostic_record(
                query_id             = chat_qid,
                question             = question,
                answer               = "Not found in textbook (relevance gate abstention)",
                total_wall_clock_sec = t_total_pipeline,
                retrieval_sec        = t_retrieval,
                generation_sec       = 0.0,
                citation_sec         = 0.0,
                verification_sec     = 0.0,
                snapshot_sec         = 0.0,
                api_metrics          = None,
                verification_data    = abstention_data,
                retrieved_chunks     = retrieved
            )
            log_diagnostic_record(diag_rec)
        except Exception:
            pass

        return

    # Generate
    t0_gen = time.perf_counter()
    result = generate_answer(
        client           = components["client"],
        query_id         = "chat",
        question         = question,
        retrieved_chunks = retrieved,
        answer_style     = answer_style
    )
    t_generation = time.perf_counter() - t0_gen
    elapsed = t_generation

    # Find exact citations
    t0_citations = time.perf_counter()
    citations = find_exact_citations(
        answer           = result["answer"],
        retrieved_chunks = retrieved
    )

    # Build precise references
    if citations:
        references = build_references_from_citations(citations)
    else:
        references = json.loads(result["references"])
    t_citations = time.perf_counter() - t0_citations

    # ModernCE Verification Layer (Complete-Answer Multi-Chunk NLI)
    t0_verif = time.perf_counter()
    verification_data = None
    try:
        from verification_1.verifier import verify_answer
        v_res = verify_answer(
            answer           = result["answer"],
            retrieved_chunks = retrieved,
            query            = question
        )
        verification_data = v_res.to_dict()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Verification error during chat processing: {e}", exc_info=True)
        verification_data = {
            "status": "UNAVAILABLE",
            "verdict": "ERROR",
            "explanation": "Verification temporarily unavailable."
        }
    t_verification = time.perf_counter() - t0_verif

    # Save verification snapshot (safe, non-blocking)
    t0_snapshot = time.perf_counter()
    try:
        from verification_1.context_snapshot import create_snapshot, save_snapshot
        snapshot_obj = create_snapshot(
            query_id         = chat_qid,
            question         = question,
            answer           = result["answer"],
            retrieved_chunks = retrieved
        )
        save_snapshot(snapshot_obj)
    except Exception:
        pass
    t_snapshot = time.perf_counter() - t0_snapshot

    t_total_pipeline = time.perf_counter() - t0_pipeline

    # Save structured diagnostic log record
    try:
        from verification_1.diagnostic_logger import build_diagnostic_record, log_diagnostic_record
        diag_rec = build_diagnostic_record(
            query_id             = chat_qid,
            question             = question,
            answer               = result["answer"],
            total_wall_clock_sec = t_total_pipeline,
            retrieval_sec        = t_retrieval,
            generation_sec       = t_generation,
            citation_sec         = t_citations,
            verification_sec     = t_verification,
            snapshot_sec         = t_snapshot,
            api_metrics          = result.get("api_metrics"),
            verification_data    = verification_data,
            retrieved_chunks     = retrieved
        )
        log_diagnostic_record(diag_rec)
    except Exception as log_err:
        import logging
        logging.getLogger(__name__).warning(f"Diagnostic timing logging error: {log_err}")

    # Add assistant message to history
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": {
            "answer":       result["answer"],
            "citations":    citations,
            "references":   references,
            "retrieved":    retrieved,
            "elapsed":      elapsed,
            "verification": verification_data
        }
    })


# ─────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────

def render_chat(components: dict):
    """
    Renders the full chat interface.
    Called from app.py when Chat mode is active.
    """
    init_chat_session()

    # Apply Theme Dynamics
    theme = st.session_state.get("ui_theme", "Standard (System)")
    
    # ── Professional Core Styling ──
    core_css = """
    <style>
    /* Clean up the main chat area */
    [data-testid="stChatMessage"] {
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.1);
    }
    
    /* Make Assistant/User icons look premium */
    [data-testid="chatAvatarIcon-user"] { background-color: #6366f1 !important; color: white !important; }
    [data-testid="chatAvatarIcon-assistant"] { background-color: #10b981 !important; color: white !important; }
    
    /* Input Box styling */
    [data-testid="stChatInput"] { padding-bottom: 25px; }
    </style>
    """

    # ── Dynamic Theme Toggles ──
    if theme == "Light Mode":
        theme_css = """
        <style>
        .stApp { background-color: #f8fafc !important; }
        [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0; }
        [data-testid="stChatMessage"] { background-color: #ffffff !important; }
        
        /* Safely colorize only the reading text, leaving buttons/inputs alone */
        .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown span { color: #0f172a !important; }
        </style>
        """
    elif theme == "Dark Mode":
        theme_css = """
        <style>
        .stApp { background-color: #0f172a !important; }
        [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
        [data-testid="stChatMessage"] { background-color: #1e293b !important; border: 1px solid #334155 !important; }
        
        /* Safely colorize only the reading text, leaving buttons/inputs alone */
        .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown span { color: #f8fafc !important; }
        </style>
        """
    else:
        theme_css = ""

    st.markdown(core_css + theme_css, unsafe_allow_html=True)

    # Render sidebar with sample questions
    render_sidebar(components, active_mode="chat")

    # ── Page Header ──
    st.markdown(
        "<h2 style='margin-bottom:0;'>Psychology Textbook Assistant</h2>"
        "<p style='color:gray; margin-top:4px;'>"
        "Answers grounded in OpenStax Psychology 2e — "
        "with verifiable section and page citations"
        "</p>",
        unsafe_allow_html=True
    )
    st.divider()

    # ── Chat History Area ──
    if not st.session_state.chat_history:
        # Empty state
        st.markdown(
            "<div style='"
            "text-align:center;"
            "color:gray;"
            "padding:60px 20px;"
            "'>"
            "<h3 style='color:gray;'>Ask a question about Psychology</h3>"
            "<p>Select a sample question from the sidebar "
            "or type your own below.</p>"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        render_chat_history(st.session_state.chat_history)

    # ── Clear Chat Area ──
    if st.session_state.chat_history:
        st.divider()
        if st.button("🗑️ Clear Conversation", use_container_width=False):
            st.session_state.chat_history = []
            st.rerun()

    # ── Input Area ──
    # Handle sidebar question trigger
    prefill = ""
    if st.session_state.trigger_from_sidebar:
        prefill = st.session_state.sidebar_question
        st.session_state.trigger_from_sidebar = False
        st.session_state.sidebar_question     = ""

    question_input = st.chat_input("Ask a question about psychology...")

    # ── Process Input ──
    query_to_process = None
    if prefill:
        query_to_process = prefill
    elif question_input and question_input.strip():
        query_to_process = question_input.strip()

    if query_to_process:
        render_chat_message("user", {"text": query_to_process})
        with st.spinner("Searching and generating answer..."):
            process_question(query_to_process, components)
        st.rerun()