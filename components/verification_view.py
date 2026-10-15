# components/verification_view.py

import streamlit as st
from typing import Any, Dict, Optional


def render_verification_block(verification: Optional[Dict[str, Any]]):
    """
    Renders the official user-facing verification status badge, explanation expander,
    and nested technical details for Streamlit responses.
    """
    if not verification:
        return

    status = verification.get("status", "")
    verdict = verification.get("verdict", "")
    is_abstention = verification.get("is_abstention", False)
    comb_used = verification.get("combination_used")
    entail_p = float(verification.get("entailment_prob", 0.0))
    neutral_p = float(verification.get("neutral_prob", 0.0))
    contra_p = float(verification.get("contradiction_prob", 0.0))
    nli_time = float(verification.get("total_nli_time_sec", 0.0))
    sel_chunks = verification.get("selected_chunk_numbers", [])

    # 1. Main Status Badge Configuration
    if status == "SUPPORTED":
        status_badge = "🟢 Supported by textbook"
        badge_bg = "rgba(16, 185, 129, 0.12)"
        badge_border = "#10b981"
        badge_text = "#10b981"

        if comb_used == "TOP_2" or verdict == "ENTAILED_BY_TOP2":
            specific_exp = "The answer was verified using the two strongest relevant textbook passages."
            evidence_depth = "Top-2"
        elif comb_used == "TOP_3" or verdict == "ENTAILED_BY_TOP3":
            specific_exp = "The first two passages were not sufficient on their own, so an additional relevant passage was considered to verify the complete answer."
            evidence_depth = "Top-3"
        else:
            specific_exp = "The answer was verified against the strongest relevant textbook evidence."
            evidence_depth = "Top-2 / Top-3"

        main_explanation = (
            "The retrieved textbook evidence strongly supports the information in the generated answer.\n\n"
            f"{specific_exp}\n\n"
            "For this answer, the system did not rely only on the generated response. It checked the complete answer "
            "against relevant information retrieved from the textbook to ensure the response is grounded in the source material."
        )

    elif status == "INSUFFICIENT_EVIDENCE":
        status_badge = "🟡 Insufficient textbook evidence"
        badge_bg = "rgba(245, 158, 11, 0.12)"
        badge_border = "#f59e0b"
        badge_text = "#f59e0b"
        evidence_depth = "Top-3 (Evaluated)"
        main_explanation = (
            "The available retrieved textbook evidence was not sufficient to verify the complete answer. "
            "This does not necessarily mean the answer is incorrect; it means the system could not find enough supporting evidence in the retrieved material."
        )

    elif status == "CONTRADICTED":
        status_badge = "🔴 Conflicts with textbook"
        badge_bg = "rgba(239, 68, 68, 0.12)"
        badge_border = "#ef4444"
        badge_text = "#ef4444"
        evidence_depth = "Top-3 (Evaluated)"
        main_explanation = (
            "The retrieved textbook evidence contains information that conflicts with the generated answer."
        )

    elif status == "NOT_FOUND" or is_abstention:
        status_badge = "⚪ Not found in textbook"
        badge_bg = "rgba(148, 163, 184, 0.12)"
        badge_border = "#94a3b8"
        badge_text = "#94a3b8"
        evidence_depth = "Bypassed (Abstention)"
        main_explanation = (
            "The system could not find sufficient information about this question in the provided textbook."
        )

    else:
        status_badge = "⚪ Verification temporarily unavailable"
        badge_bg = "rgba(148, 163, 184, 0.08)"
        badge_border = "#94a3b8"
        badge_text = "#94a3b8"
        evidence_depth = "N/A"
        main_explanation = "Verification information could not be processed for this response."

    # 2. Render Styled Status Pill Badge
    st.markdown(
        f"<div style='"
        f"display: inline-block; "
        f"padding: 5px 14px; "
        f"margin: 8px 0 10px 0; "
        f"border-radius: 16px; "
        f"background: {badge_bg}; "
        f"border: 1px solid {badge_border}; "
        f"font-size: 13.5px; "
        f"font-weight: 600; "
        f"color: {badge_text};'>"
        f"{status_badge}"
        f"</div>",
        unsafe_allow_html=True
    )

    # 3. Render "How was this verified?" Expander
    with st.expander("▾ How was this verified?", expanded=False):
        st.markdown(main_explanation)

        # 4. Technical details Popover
        with st.popover("Technical details"):
            if is_abstention or status == "NOT_FOUND":
                st.markdown(
                    "- **Verification Model**: ModernCE (`dleemiller/ModernCE-base-nli`)\n"
                    "- **Evidence Depth**: Bypassed (Explicit out-of-scope response)\n"
                    "- **NLI Inference**: Safely bypassed to avoid false contradictions on missing context"
                )
            elif status in ["SUPPORTED", "INSUFFICIENT_EVIDENCE", "CONTRADICTED"]:
                chunks_label = f"Chunks {sel_chunks}" if sel_chunks else "N/A"
                st.markdown(
                    f"- **Verification Model**: ModernCE (`dleemiller/ModernCE-base-nli`)\n"
                    f"- **Evidence Depth**: {evidence_depth} ({chunks_label})\n"
                    f"- **Entailment Probability**: `{entail_p:.4f}`\n"
                    f"- **Neutral Probability**: `{neutral_p:.4f}`\n"
                    f"- **Contradiction Probability**: `{contra_p:.4f}`\n"
                    f"- **Verification Time**: `{nli_time:.2f} s`"
                )
            else:
                st.caption("Verification metrics unavailable.")
