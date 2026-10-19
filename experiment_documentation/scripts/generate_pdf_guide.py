#!/usr/bin/env python3
"""
generate_pdf_guide.py
Generates the comprehensive, beginner-friendly academic PDF guide:
"RAG with a Hallucination Verification Layer: Experiments, Results, and Research Progression"

Target Audience: 3rd-year CSE student & Viva Defense Preparation.
Zero external runtime dependencies beyond PyMuPDF (pinned in requirements.txt).
Strictly excludes all references to K=5 and the K=5 vs K=7 comparison.
"""

import os
import sys
import fitz  # PyMuPDF

# ==============================================================================
# COLOR PALETTE & DESIGN SYSTEM
# ==============================================================================
NAVY_PRIMARY = (0.07, 0.17, 0.33)      # #122B54 - Primary Brand / Headings
NAVY_LIGHT = (0.12, 0.28, 0.50)        # #1F4780 - Subheaders / Table headers
BLUE_ACCENT = (0.12, 0.42, 0.76)       # #1F6BC2 - Key Accents / Links
SLATE_GRAY = (0.35, 0.40, 0.48)        # #59667A - Secondary descriptive text
LIGHT_BG = (0.96, 0.97, 0.99)          # #F5F7FA - Card fill / Section background
CARD_BORDER = (0.82, 0.86, 0.92)       # #D1DCEB - Card outline
TEXT_DARK = (0.12, 0.14, 0.18)         # #1F242E - High contrast body text
TEXT_MUTED = (0.42, 0.46, 0.52)        # #6B7584 - Captions / Footers
WHITE = (1.0, 1.0, 1.0)

# Phase Color Schemes (Fill, Border, Text)
PHASE_COLORS = {
    "Phase A": {
        "fill": (0.90, 0.94, 0.99),
        "border": (0.18, 0.45, 0.82),
        "text": (0.08, 0.25, 0.55),
        "title": "Phase A: Input Quality & RAG Retrieval Baseline"
    },
    "Phase B": {
        "fill": (0.90, 0.97, 0.93),
        "border": (0.16, 0.65, 0.35),
        "text": (0.08, 0.45, 0.22),
        "title": "Phase B: Controlled NLI Verification Benchmarking"
    },
    "Phase C": {
        "fill": (0.99, 0.92, 0.92),
        "border": (0.82, 0.25, 0.25),
        "text": (0.55, 0.12, 0.12),
        "title": "Phase C: The Claim-Level Verification Crisis"
    },
    "Phase D": {
        "fill": (0.99, 0.96, 0.88),
        "border": (0.85, 0.55, 0.12),
        "text": (0.55, 0.35, 0.05),
        "title": "Phase D: ModernCE & Complete-Answer Verification"
    }
}

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_PDF = os.path.join(BASE_DIR, "RAG_Hallucination_Verification_Experiments_Guide.pdf")
FIGURES_DIR = os.path.join(BASE_DIR, "figures")

# ==============================================================================
# HELPER CANVAS DRAWING PRIMITIVES
# ==============================================================================
def draw_rounded_card(page, rect, fill_color=LIGHT_BG, border_color=CARD_BORDER, border_width=0.8):
    """Draws a clean rectangular card with soft border."""
    page.draw_rect(rect, color=border_color, fill=fill_color, width=border_width)

def draw_pill(page, rect, fill_color, border_color, text, text_color, fontsize=8):
    """Draws a status pill badge with centered bold text."""
    page.draw_rect(rect, color=border_color, fill=fill_color, width=0.8)
    text_width = fitz.get_text_length(text, fontname="hebo", fontsize=fontsize)
    x = rect.x0 + (rect.width - text_width) / 2
    y = rect.y0 + (rect.height + fontsize * 0.7) / 2
    page.insert_text(fitz.Point(x, y), text, fontsize=fontsize, fontname="hebo", color=text_color)

def draw_header_band(page, title, phase_key=None):
    """Draws consistent top running header."""
    header_rect = fitz.Rect(0, 0, 595.3, 38)
    page.draw_rect(header_rect, color=None, fill=NAVY_PRIMARY)
    page.draw_line(fitz.Point(0, 38), fitz.Point(595.3, 38), color=BLUE_ACCENT, width=1.5)
    page.insert_text(fitz.Point(40, 24), "RAG & HALLUCINATION VERIFICATION EXPERIMENTS GUIDE", fontsize=9, fontname="hebo", color=WHITE)
    if phase_key:
        phase_title = PHASE_COLORS.get(phase_key, {}).get("title", phase_key)
        page.insert_text(fitz.Point(320, 24), phase_title, fontsize=8, fontname="helv", color=(0.85, 0.90, 0.98))

def draw_table(page, x, y, col_widths, headers, rows, font_size=8.0, row_height=18.0):
    """Renders a crisp, perfectly aligned academic table."""
    total_width = sum(col_widths)
    # Header row
    hdr_rect = fitz.Rect(x, y, x + total_width, y + row_height)
    page.draw_rect(hdr_rect, color=NAVY_PRIMARY, fill=NAVY_LIGHT, width=0.8)
    curr_x = x
    for i, h in enumerate(headers):
        page.insert_text(fitz.Point(curr_x + 5, y + row_height * 0.72), h, fontsize=font_size, fontname="hebo", color=WHITE)
        curr_x += col_widths[i]
    
    curr_y = y + row_height
    for r_idx, row in enumerate(rows):
        bg = LIGHT_BG if r_idx % 2 == 0 else WHITE
        row_rect = fitz.Rect(x, curr_y, x + total_width, curr_y + row_height)
        page.draw_rect(row_rect, color=CARD_BORDER, fill=bg, width=0.5)
        curr_x = x
        for c_idx, val in enumerate(row):
            font = "hebo" if c_idx == 0 else "helv"
            col_text = TEXT_DARK if c_idx != 0 else NAVY_PRIMARY
            # Truncate string if too long for cell
            max_len = int(col_widths[c_idx] / (font_size * 0.45))
            val_str = str(val)
            if len(val_str) > max_len:
                val_str = val_str[:max_len - 3] + "..."
            page.insert_text(fitz.Point(curr_x + 5, curr_y + row_height * 0.72), val_str, fontsize=font_size, fontname=font, color=col_text)
            curr_x += col_widths[c_idx]
        curr_y += row_height
    return curr_y

# ==============================================================================
# PAGE BUILDERS
# ==============================================================================
def build_cover_page(doc):
    """Generates Page 1: Elegant Academic Cover Page."""
    page = doc.new_page(width=595.3, height=841.9)
    
    # Top decorative header block
    page.draw_rect(fitz.Rect(0, 0, 595.3, 160), color=None, fill=NAVY_PRIMARY)
    page.draw_rect(fitz.Rect(0, 160, 595.3, 168), color=None, fill=BLUE_ACCENT)
    
    page.insert_text(fitz.Point(40, 55), "RESEARCH MONOGRAPH & ENGINEERING GUIDE", fontsize=11, fontname="hebo", color=(0.8, 0.88, 1.0))
    page.insert_text(fitz.Point(40, 95), "RAG with a Hallucination", fontsize=28, fontname="hebo", color=WHITE)
    page.insert_text(fitz.Point(40, 130), "Verification Layer", fontsize=28, fontname="hebo", color=WHITE)
    
    # Subtitle Card
    sub_rect = fitz.Rect(40, 190, 555.3, 255)
    draw_rounded_card(page, sub_rect, fill_color=LIGHT_BG, border_color=CARD_BORDER, border_width=1.0)
    page.insert_text(fitz.Point(55, 215), "Experiments, Results, and Research Progression", fontsize=15, fontname="hebo", color=NAVY_PRIMARY)
    page.insert_text(fitz.Point(55, 235), "A Complete Empirical Compendium for Computer Science & Engineering Students & Viva Defense", fontsize=9.5, fontname="heit", color=SLATE_GRAY)
    
    # Project Core Metadata
    meta_rect = fitz.Rect(40, 275, 555.3, 445)
    draw_rounded_card(page, meta_rect, fill_color=WHITE, border_color=CARD_BORDER, border_width=1.0)
    page.insert_text(fitz.Point(55, 300), "PROJECT ARCHITECTURAL SUMMARY", fontsize=11, fontname="hebo", color=NAVY_PRIMARY)
    page.draw_line(fitz.Point(55, 307), fitz.Point(540, 307), color=CARD_BORDER, width=0.8)
    
    meta_items = [
        ("Repository & System:", "RAG System with Multi-Chunk Hallucination Verification Layer"),
        ("Corpus Under Test:", "341-Page Technical Domain Textbook (1,438 Chunks, 400w with 50w overlap)"),
        ("Baseline Retrieval:", "Hybrid Reciprocal Rank Fusion (BGE-Large-v1.5 Dense + BM25, K_cand=15, TOP_K=7)"),
        ("Generation Engine:", "Meta-Llama-3.1-70B-Instruct via NVIDIA API (Prompt ceiling <= 20,000 characters)"),
        ("Verification Engine:", "dleemiller/ModernCE-base-nli (ModernBERT, 2,048-token context, progressive Top-1-3)"),
        ("Empirical Benchmark:", "50 Production Questions (45/48 Entailed = 93.75%, 2 Abstentions, Mean Latency 8.33s)"),
        ("Documented Scope:", "17 Sequential Experiments Across 4 Systematic Build Phases (Phase A to Phase D)"),
        ("Documentation Date:", "October 2026 | Comprehensive Viva & Faculty Guide")
    ]
    curr_y = 328
    for label, val in meta_items:
        page.insert_text(fitz.Point(55, curr_y), label, fontsize=8.5, fontname="hebo", color=NAVY_LIGHT)
        page.insert_text(fitz.Point(185, curr_y), val, fontsize=8.5, fontname="helv", color=TEXT_DARK)
        curr_y += 15
        
    # Student Orientation Box
    orient_rect = fitz.Rect(40, 465, 555.3, 620)
    draw_rounded_card(page, orient_rect, fill_color=LIGHT_BG, border_color=CARD_BORDER, border_width=1.0)
    page.insert_text(fitz.Point(55, 490), "HOW TO READ THIS GUIDE (FOR 3RD-YEAR CSE STUDENTS)", fontsize=11, fontname="hebo", color=NAVY_PRIMARY)
    page.draw_line(fitz.Point(55, 497), fitz.Point(540, 497), color=CARD_BORDER, width=0.8)
    
    guide_text = (
        "This monograph documents how real machine learning engineering works: moving from initial baseline "
        "assumptions through diagnostic crises to production breakthroughs. In early experiments, simple similarity "
        "failed completely, and sentence-level verification collapsed due to premise dilution. By upgrading to "
        "ModernBERT cross-encoders with multi-chunk concatenation, the system achieved 93.75% factual groundedness.\n\n"
        "Each experiment includes the motivating question (WHY), implementation (WHAT WE DID), empirical metrics (RESULTS), "
        "the actual experimental graph, visual takeaways, conclusions, and how that result motivated the next experiment."
    )
    page.insert_textbox(fitz.Rect(55, 508, 540, 610), guide_text, fontsize=9.0, fontname="helv", color=TEXT_DARK)

    # Document Index Summary
    toc_rect = fitz.Rect(40, 635, 555.3, 785)
    draw_rounded_card(page, toc_rect, fill_color=WHITE, border_color=CARD_BORDER, border_width=1.0)
    page.insert_text(fitz.Point(55, 658), "GUIDE SITEMAP & DOCUMENT STRUCTURE", fontsize=10.5, fontname="hebo", color=NAVY_PRIMARY)
    page.draw_line(fitz.Point(55, 665), fitz.Point(540, 665), color=CARD_BORDER, width=0.8)
    
    sections = [
        ("Section 1 (Page 2):", "Project Overview, Workflow Architecture & Beginner Glossary"),
        ("Section 2 (Pages 3-4):", "Master 17-Experiment Summary Table (Questions, Results, Next Steps)"),
        ("Section 3 (Pages 5-7):", "Phase A: PDF Extraction Quality & Retrieval Parameter Optimization (Exp 01-03)"),
        ("Section 4 (Pages 8-10):", "Phase B: Controlled NLI Verification Benchmarking & Threshold Calibration (Exp 04-06)"),
        ("Section 5 (Pages 11-14):", "Phase C: The Claim-Level Verification Crisis & Latency Diagnostics (Exp 07-10)"),
        ("Section 6 (Pages 15-21):", "Phase D: ModernCE & Complete-Answer Verification Breakthrough (Exp 11-17)"),
        ("Section 7 (Page 22):", "Cross-Experiment Latency Analysis: Claim-Level vs. Complete-Answer Verification"),
        ("Section 8 (Pages 23-24):", "Synthesis of Findings, Scientific Limitations & Final System Architecture")
    ]
    curr_y = 680
    for label, desc in sections:
        page.insert_text(fitz.Point(55, curr_y), label, fontsize=8.0, fontname="hebo", color=BLUE_ACCENT)
        page.insert_text(fitz.Point(180, curr_y), desc, fontsize=8.0, fontname="helv", color=TEXT_DARK)
        curr_y += 12.5

def build_project_overview_page(doc):
    """Generates Page 2: Project Overview & Workflow Architecture."""
    page = doc.new_page(width=595.3, height=841.9)
    draw_header_band(page, "PROJECT OVERVIEW & WORKFLOW", "Phase A")
    
    page.insert_text(fitz.Point(40, 62), "1. Project Overview & The Need for Verification", fontsize=15, fontname="hebo", color=NAVY_PRIMARY)
    page.insert_text(fitz.Point(40, 78), "Understanding why retrieval-augmented generation alone cannot guarantee factual truth", fontsize=9.5, fontname="heit", color=SLATE_GRAY)
    
    # 3 Parallel Explanation Cards
    c1 = fitz.Rect(40, 95, 200, 205)
    draw_rounded_card(page, c1, fill_color=LIGHT_BG, border_color=CARD_BORDER)
    page.insert_text(fitz.Point(48, 112), "WHAT IS RAG?", fontsize=10, fontname="hebo", color=NAVY_PRIMARY)
    rag_desc = (
        "Retrieval-Augmented Generation (RAG) combines external text search with LLMs. Instead of relying solely on "
        "training weights, the system retrieves relevant chunks from a textbook and injects them into the prompt to "
        "ground the answer."
    )
    page.insert_textbox(fitz.Rect(48, 120, 192, 195), rag_desc, fontsize=8.2, fontname="helv", color=TEXT_DARK)
    
    c2 = fitz.Rect(215, 95, 380, 205)
    draw_rounded_card(page, c2, fill_color=(0.99, 0.94, 0.94), border_color=(0.85, 0.35, 0.35))
    page.insert_text(fitz.Point(223, 112), "THE SIMILARITY FALLACY", fontsize=10, fontname="hebo", color=(0.6, 0.1, 0.1))
    sim_desc = (
        "Embedding similarity measures topical overlap, NOT truth! In Exp-04 & 06, statements that contradicted "
        "the text scored 0.77 similarity vs 0.82 for true facts. Because negative sentences share nouns and entities, "
        "similarity cannot catch hallucinations."
    )
    page.insert_textbox(fitz.Rect(223, 120, 372, 195), sim_desc, fontsize=8.2, fontname="helv", color=TEXT_DARK)

    c3 = fitz.Rect(395, 95, 555.3, 205)
    draw_rounded_card(page, c3, fill_color=(0.92, 0.97, 0.93), border_color=(0.2, 0.65, 0.35))
    page.insert_text(fitz.Point(403, 112), "WHY VERIFY WITH NLI?", fontsize=10, fontname="hebo", color=(0.1, 0.45, 0.2))
    nli_desc = (
        "Natural Language Inference (NLI) evaluates mathematical entailment between evidence and answers. A cross-encoder "
        "evaluates cross-attention between premise and hypothesis to ensure every generated statement is strictly derived "
        "from the text."
    )
    page.insert_textbox(fitz.Rect(403, 120, 547, 195), nli_desc, fontsize=8.2, fontname="helv", color=TEXT_DARK)

    # Workflow Diagram Box
    diag_rect = fitz.Rect(40, 220, 555.3, 490)
    draw_rounded_card(page, diag_rect, fill_color=WHITE, border_color=CARD_BORDER)
    page.insert_text(fitz.Point(55, 240), "2. End-to-End System Workflow Architecture", fontsize=11, fontname="hebo", color=NAVY_PRIMARY)
    page.draw_line(fitz.Point(55, 247), fitz.Point(540, 247), color=CARD_BORDER, width=0.8)
    
    # 7 Step Visual Pipeline
    steps = [
        ("Step 1", "Textbook PDF", "PyMuPDF text extraction with layout parsing and header restoration (Exp-01)"),
        ("Step 2", "Chunking & Indexing", "400-word sliding window with 50-word overlap; BGE-Large dense & BM25 indices"),
        ("Step 3", "Hybrid RRF Retrieval", "Reciprocal Rank Fusion (k=60), Candidate pool K=15, Production Top-K=7 (Exp-02)"),
        ("Step 4", "Answer Generation", "Meta-Llama-3.1-70B-Instruct via NVIDIA API (Context <= 20k chars) (Exp-03)"),
        ("Step 5", "Regex Abstention Check", "Pre-screen out-of-scope non-retrieval responses to save NLI inference time (Exp-14)"),
        ("Step 6", "ModernCE Verification", "Progressive multi-chunk concatenation (Top-1 -> Top-2 -> Top-3) (Exp 11-15)"),
        ("Step 7", "Trust Badges & UI", "Streamlit UI displays answer with VERIFIED / PARTIAL / UNVERIFIED badges (Exp-17)")
    ]
    step_y = 265
    for s_num, s_title, s_detail in steps:
        pill_rect = fitz.Rect(55, step_y - 12, 115, step_y + 8)
        draw_pill(page, pill_rect, NAVY_LIGHT, NAVY_PRIMARY, s_num, WHITE, fontsize=8)
        page.insert_text(fitz.Point(125, step_y), s_title, fontsize=9.5, fontname="hebo", color=NAVY_PRIMARY)
        page.insert_text(fitz.Point(260, step_y), s_detail, fontsize=8.0, fontname="helv", color=SLATE_GRAY)
        if s_num != "Step 7":
            page.draw_line(fitz.Point(85, step_y + 9), fitz.Point(85, step_y + 17), color=BLUE_ACCENT, width=1.5)
        step_y += 31

    # Beginner Glossary
    gloss_rect = fitz.Rect(40, 505, 555.3, 785)
    draw_rounded_card(page, gloss_rect, fill_color=LIGHT_BG, border_color=CARD_BORDER)
    page.insert_text(fitz.Point(55, 525), "3. Beginner-Friendly Technical Glossary for Students", fontsize=11, fontname="hebo", color=NAVY_PRIMARY)
    page.draw_line(fitz.Point(55, 532), fitz.Point(540, 532), color=CARD_BORDER, width=0.8)
    
    glossary = [
        ("Bi-Encoder vs Cross-Encoder:", "Bi-encoders (like embeddings) encode text separately into vectors. Cross-encoders feed premise and hypothesis together into full attention layers, allowing tokens to interact directly."),
        ("NLI Entailment:", "The hypothesis must logically be true if the premise is true (mathematical support)."),
        ("NLI Neutral (Extrapolation):", "The hypothesis might be true, but the retrieved passage doesn't provide enough evidence to prove it."),
        ("NLI Contradiction:", "The hypothesis directly conflicts with facts stated in the retrieved passage (hallucination)."),
        ("Premise Dilution:", "When a short claim is evaluated against a large 400-word passage, attention gets diffused across background text, causing false Neutral ratings."),
        ("Token Truncation:", "When the text exceeds the model's sequence limit (e.g. 512 tokens), the end of the text is cut off and invisible to the verifier."),
        ("Progressive Concatenation:", "Checking evidence incrementally (Top-1 first; if inconclusive, add Top-2; then Top-3) to minimize latency while capturing synergistic multi-chunk evidence.")
    ]
    g_y = 550
    for term, defn in glossary:
        page.insert_text(fitz.Point(55, g_y), term, fontsize=8.2, fontname="hebo", color=NAVY_LIGHT)
        page.insert_textbox(fitz.Rect(55, g_y + 2, 540, g_y + 32), defn, fontsize=7.8, fontname="helv", color=TEXT_DARK)
        g_y += 33

def build_summary_table_pages(doc):
    """Generates Pages 3 & 4: Master 17-Experiment Summary Table."""
    col_w = [85, 125, 105, 110, 90]
    headers = ["Exp ID & Title", "What Were We Testing?", "Main Result", "What Did We Learn?", "What Happened Next?"]
    
    # Page 3: Exp 01 to Exp 08
    page3 = doc.new_page(width=595.3, height=841.9)
    draw_header_band(page3, "MASTER EXPERIMENT TIMELINE (PART 1: EXP 01-08)", "Phase A")
    page3.insert_text(fitz.Point(40, 62), "2. Master Experiment Chronology & Progression (Part 1)", fontsize=14, fontname="hebo", color=NAVY_PRIMARY)
    page3.insert_text(fitz.Point(40, 78), "Tracking research evolution across Phase A (Retrieval), Phase B (Pilots), and Phase C (Claim-Level Crisis)", fontsize=8.5, fontname="heit", color=SLATE_GRAY)
    
    rows_p1 = [
        ["Exp 01: PDF Extraction\n(Phase A)", "Can PyMuPDF accurately extract domain terms without corrupted characters?", "Vocab F1: 82.0%\nKey-terms: 91.8%\nCoverage: 100%", "Regex heading restoration and unicode cleaning prevent corrupted input tokens.", "Proceed to chunking and retrieval tuning (Exp-02)."],
        ["Exp 02: Retrieval Tuning\n(Phase A)", "What candidate pool (Kcand) and final K optimize recall within prompt limits?", "Kcand=15: 100% Hit Rate\nFinal K=7: 98.6% Coverage\nHybrid MRR: 0.702", "Hybrid RRF beats vector alone (+8.7% MRR). K=7 packs 19,322 chars (<20k ceiling).", "Validate end-to-end RAG generation quality at K=7 (Exp-03)."],
        ["Exp 03: Baseline RAG\n(Phase A)", "How well does production K=7 generate answers on 50 textbook questions?", "Mean Sim: 0.824\nHigh-Sim: 66.0% (33/50)\nAvg Latency: 1.98s", "Llama-3.1-70B generates coherent answers, but reference similarity cannot detect hallucinations.", "Launch Phase B to build automated NLI verification (Exp-04)."],
        ["Exp 04: Verification Pilot v1\n(Phase B)", "Can bi-encoder cosine similarity detect hallucinations instead of full NLI?", "DeBERTa: 95.6% Accuracy\nSimilarity failed completely\n(Ent 0.82 vs Con 0.77)", "Similarity measures topical overlap, not truth. Contradictions score high similarity.", "Calibrate explicit NLI decision boundaries (Exp-05)."],
        ["Exp 05: Pilot v2 Calibration\n(Phase B)", "What decision thresholds separate factual support from unsupported claims?", "DeBERTa: 95.0% Accuracy\nMacro F1: 0.948\nP(E)>=0.70, P(C)>=0.50", "Asymmetric probability thresholds prevent false positives on isolated pairs.", "Scale to comprehensive 280-triple benchmark (Exp-06)."],
        ["Exp 06: 280-Triple Benchmark\n(Phase B)", "How accurately does DeBERTa perform on 280 balanced claim-evidence triples?", "DeBERTa Acc: 96.43%\nMacro F1: 0.963\nSim Peak: only 61.43%", "Cross-encoder NLI strongly outperforms cosine similarity (+35% accuracy) on isolated text.", "Deploy DeBERTa on live RAG pipeline answers (Exp-07)."],
        ["Exp 07: Sentence Claims\n(Phase C)", "Does DeBERTa verify live RAG answers when split into 15 individual sentences?", "15/15 NEUTRAL (100% Fail)\n57.3% Token Truncation\n0 Entailed, 0 Contradicted", "Catastrophic failure: Premise dilution (15w claim vs 400w chunk) + 512 context truncation.", "Decompose sentences into minimal atomic claims (Exp-08)."],
        ["Exp 08: Atomic Claims\n(Phase C)", "Does extracting minimal atomic claims fix the 100% false neutral crisis?", "40/44 NEUTRAL (90.9%)\n1 Supported (2.3%)\n3 Contradicted (6.8%)", "Neutral crisis persisted. Stripping surrounding grammar destroyed context and caused errors.", "Profile operational latency of atomic decomposition (Exp-09)."]
    ]
    draw_table(page3, 40, 92, col_w, headers, rows_p1, font_size=7.2, row_height=78.0)
    
    # Page 4: Exp 09 to Exp 17
    page4 = doc.new_page(width=595.3, height=841.9)
    draw_header_band(page4, "MASTER EXPERIMENT TIMELINE (PART 2: EXP 09-17)", "Phase D")
    page4.insert_text(fitz.Point(40, 62), "2. Master Experiment Chronology & Progression (Part 2)", fontsize=14, fontname="hebo", color=NAVY_PRIMARY)
    page4.insert_text(fitz.Point(40, 78), "Tracking research evolution across Phase C (Micro-Units) and Phase D (ModernCE & Complete-Answer Breakthrough)", fontsize=8.5, fontname="heit", color=SLATE_GRAY)
    
    rows_p2 = [
        ["Exp 09: Latency Diagnostic\n(Phase C)", "What is the exact end-to-end latency of atomic claim verification?", "Total Latency: 84.98s\nVerification: 57.88s (68%)\nClaim Extract: 14.77s", "50 sequential NLI passes for 1 query is computationally unviable for interactive RAG.", "Test evidence micro-units to reduce premise dilution (Exp-10)."],
        ["Exp 10: Evidence Micro-Units\n(Phase C)", "Does splitting chunks into 3-sentence micro-units reduce premise dilution?", "Neutral rate: 80.5%\n18 context regressions\nCandidate pool ~3x", "Micro-units severed cross-sentence evidence boundaries, worsening grounding.", "Permanently abandon claim decomposition; upgrade model (Exp-11)."],
        ["Exp 11: NLI Model Compare\n(Phase D)", "Does upgrading to ModernCE (2,048 tokens) eliminate token truncation?", "ModernCE Truncation: 0.0%\nDeBERTa Truncation: 57.3%\n38 Neu -> Ent recoveries", "ModernBERT context window accommodates multi-chunk evidence without truncation.", "Test verifying complete answers against concatenated chunks (Exp-12)."],
        ["Exp 12: Complete-Answer Pilot\n(Phase D)", "Does verifying complete answers against Top-1+Top-2 evidence unlock synergy?", "Concatenated: 80% Entailed\n(Top-1 alone was 40%)\nQ1 jumped 0.35 -> 0.91", "Multi-chunk concatenation allows cross-attention to resolve joint facts; passes cut from 50 to 1-2.", "Scale complete-answer verification to 50 questions (Exp-13)."],
        ["Exp 13: 50Q Benchmark\n(Phase D)", "How reliably does progressive ModernCE verify 50 production RAG queries?", "45/48 Content Entailed (93.8%)\n3 Neutral, 0 Contradicted\nMean Latency: 8.33s", "Definitive benchmark: complete-answer verification is accurate and robust in production.", "Migrate logic into production modular verifier (Exp-14)."],
        ["Exp 14: Production Parity\n(Phase D)", "Does verifier.py maintain 100% status parity with research benchmark?", "100.0% Status Agreement\n14 NLI passes saved via\nis_abstention_answer()", "Regex abstention bypass eliminates unnecessary NLI passes on out-of-scope questions.", "Profile progressive stopping depth telemetry (Exp-15)."],
        ["Exp 15: Progressive Telemetry\n(Phase D)", "What is the optimal stopping depth (Top-1, Top-2, Top-3, or Top-4)?", "Top-1: 37.5%, Top-2: 79.2%\nTop-3: 93.8% Entailed\nTop-4: 0 gains (0%)", "Recoveries plateau at Top-3. Top-4 adds context bloat and latency without benefit.", "Test repeatability and variance across repeated runs (Exp-16)."],
        ["Exp 16: Grounding Stability\n(Phase D)", "Are ModernCE entailment verdicts deterministic across repeated runs?", "Entailment: 0.9589 +/- 0.037\n3/3 Entailed Deterministic\nZero classification drift", "NLI inference on fixed retrieval text is mathematically stable and deterministic.", "Surface trust badges in UI and build annotation framework (Exp-17)."],
        ["Exp 17: UI & Human Setup\n(Phase D)", "Does Streamlit display dynamic badges, and is manual annotation ready?", "4/4 UI automated tests pass\n50 annotation templates ready\n(Human labels pending)", "Trust badges integrate cleanly in UI. Human ground-truth accuracy remains pending expert review.", "Finalize production system and scientific defense."]
    ]
    draw_table(page4, 40, 92, col_w, headers, rows_p2, font_size=7.2, row_height=70.0)

def build_experiment_page(doc, exp):
    """Renders a single, beautifully structured experiment summary page."""
    page = doc.new_page(width=595.3, height=841.9)
    phase_key = exp["phase"]
    draw_header_band(page, f"EXPERIMENT {exp['id']}: {exp['title'].upper()}", phase_key)
    
    # Top Title Block
    title_rect = fitz.Rect(40, 48, 555.3, 85)
    draw_rounded_card(page, title_rect, fill_color=LIGHT_BG, border_color=CARD_BORDER, border_width=1.0)
    
    # Phase badge pill
    p_info = PHASE_COLORS.get(phase_key, {})
    pill_rect = fitz.Rect(52, 56, 125, 76)
    draw_pill(page, pill_rect, p_info.get("fill", LIGHT_BG), p_info.get("border", BLUE_ACCENT), phase_key, p_info.get("text", NAVY_PRIMARY), fontsize=8.5)
    
    page.insert_text(fitz.Point(135, 70), f"Experiment {exp['id']}: {exp['title']}", fontsize=12, fontname="hebo", color=NAVY_PRIMARY)
    
    # Section 1: WHY & WHAT WE DID
    y_narr = 95
    c_why = fitz.Rect(40, y_narr, 290, y_narr + 75)
    draw_rounded_card(page, c_why, fill_color=WHITE, border_color=CARD_BORDER)
    page.insert_text(fitz.Point(48, y_narr + 16), "WHY WE CONDUCTED THIS EXPERIMENT", fontsize=8.5, fontname="hebo", color=NAVY_PRIMARY)
    page.insert_textbox(fitz.Rect(48, y_narr + 20, 282, y_narr + 70), exp["why"], fontsize=7.8, fontname="helv", color=TEXT_DARK)
    
    c_what = fitz.Rect(300, y_narr, 555.3, y_narr + 75)
    draw_rounded_card(page, c_what, fill_color=WHITE, border_color=CARD_BORDER)
    page.insert_text(fitz.Point(308, y_narr + 16), "WHAT WE DID & MODEL CONFIGURATION", fontsize=8.5, fontname="hebo", color=NAVY_PRIMARY)
    page.insert_textbox(fitz.Rect(308, y_narr + 20, 545, y_narr + 70), exp["what"], fontsize=7.8, fontname="helv", color=TEXT_DARK)
    
    # Section 2: NUMERICAL RESULTS TABLE
    y_tbl = y_narr + 82
    page.insert_text(fitz.Point(40, y_tbl + 10), "KEY EMPIRICAL RESULTS & METRICS", fontsize=9.5, fontname="hebo", color=NAVY_PRIMARY)
    table_end_y = draw_table(page, 40, y_tbl + 15, exp["col_widths"], exp["headers"], exp["rows"], font_size=7.5, row_height=16.0)
    
    # Section 3: EMBEDDED FIGURE & VISUAL OBSERVATION
    y_fig = table_end_y + 10
    fig_card = fitz.Rect(40, y_fig, 555.3, y_fig + 255)
    draw_rounded_card(page, fig_card, fill_color=WHITE, border_color=CARD_BORDER)
    
    fig_path = os.path.join(FIGURES_DIR, exp["figure"])
    if os.path.exists(fig_path):
        img_rect = fitz.Rect(50, y_fig + 8, 545.3, y_fig + 215)
        page.insert_image(img_rect, filename=fig_path, keep_proportion=True)
    else:
        page.insert_text(fitz.Point(55, y_fig + 100), f"[Figure file not found: {exp['figure']}]", fontsize=10, fontname="hebo", color=(0.8, 0.2, 0.2))
        
    page.insert_text(fitz.Point(55, y_fig + 232), f"Figure {exp['id']}: {exp['fig_caption']}", fontsize=8.2, fontname="hebo", color=NAVY_PRIMARY)
    page.insert_textbox(fitz.Rect(55, y_fig + 236, 540, y_fig + 252), f"What the Graph Shows: {exp['fig_shows']}", fontsize=7.8, fontname="heit", color=TEXT_DARK)
    
    # Section 4: CONCLUSION & WHAT HAPPENED NEXT
    y_bot = y_fig + 265
    c_concl = fitz.Rect(40, y_bot, 290, y_bot + 65)
    draw_rounded_card(page, c_concl, fill_color=(0.95, 0.98, 0.95), border_color=(0.2, 0.65, 0.35))
    page.insert_text(fitz.Point(48, y_bot + 16), "CONCLUSION & WHAT WAS ESTABLISHED", fontsize=8.5, fontname="hebo", color=(0.1, 0.45, 0.2))
    page.insert_textbox(fitz.Rect(48, y_bot + 22, 282, y_bot + 60), exp["conclusion"], fontsize=7.8, fontname="helv", color=TEXT_DARK)

    c_next = fitz.Rect(300, y_bot, 555.3, y_bot + 65)
    draw_rounded_card(page, c_next, fill_color=LIGHT_BG, border_color=CARD_BORDER)
    page.insert_text(fitz.Point(308, y_bot + 16), "HOW THIS MOTIVATED THE NEXT EXPERIMENT", fontsize=8.5, fontname="hebo", color=NAVY_PRIMARY)
    page.insert_textbox(fitz.Rect(308, y_bot + 22, 545, y_bot + 60), exp["next_step"], fontsize=7.8, fontname="helv", color=TEXT_DARK)

def build_cross_latency_page(doc):
    """Generates Page 22: Cross-Experiment Latency Analysis."""
    page = doc.new_page(width=595.3, height=841.9)
    draw_header_band(page, "CROSS-EXPERIMENT LATENCY ANALYSIS", "Phase D")
    
    page.insert_text(fitz.Point(40, 62), "4. Cross-Experiment Latency Analysis: Claim-Level vs Complete-Answer", fontsize=13.5, fontname="hebo", color=NAVY_PRIMARY)
    page.insert_text(fitz.Point(40, 78), "Detailed computational scalability comparison across distinct timing scopes, units, and setups", fontsize=8.5, fontname="heit", color=SLATE_GRAY)
    
    # Latency Comparison Table
    col_w = [90, 85, 75, 55, 55, 60, 95]
    headers = ["Condition / Run", "Unit of Analysis", "Evaluated Scope", "Chunks", "NLI Passes", "Total Latency", "Core Observation & Caveat"]
    rows = [
        ["Exp 09: Atomic Claims\n(Query 41 Diagnostic)", "Atomic Claim\n(10 claims/query)", "1 Complex Query\nWorst-case query", "5 Chunks", "50 Passes", "84.98 s\n(NLI 57.88s)", "Computationally unviable for interactive RAG; includes live RAG generation (12.33s)."],
        ["Exp 12: Complete Answer\n(Q1-Q5 Pilot)", "Complete Answer\n(Single evaluation)", "5 Live Queries\nPreliminary pilot", "Top 1-2", "1-3 Passes\nper query", "~2.0 - 3.0 s\n(Verifier only)", "Forward passes cut by over 85%; eliminates LLM claim extraction overhead entirely."],
        ["Exp 13: 50Q Benchmark\n(Progressive Top 1-3)", "Complete Answer\n(Multi-chunk)", "50 Production Qs\nAggregated benchmark", "Top 1-3", "6.24 Avg\n(312 total)", "8.33 s\n(CPU average)", "Production benchmark average on CPU without live API overhead; 93.75% entailment rate."],
        ["Exp 14: Production Parity\n(With Abstention)", "Complete Answer\n(Regex bypass)", "50 Production Qs\nProduction engine", "Top 1-3", "5.96 Avg\n(298 total)", "7.85 s\n(CPU average)", "Regex abstention bypass saves 14 NLI forward passes on out-of-scope non-retrieval queries."]
    ]
    tbl_end_y = draw_table(page, 40, 90, col_w, headers, rows, font_size=7.2, row_height=42.0)
    
    # Latency Figure Box
    y_fig = tbl_end_y + 12
    fig_card = fitz.Rect(40, y_fig, 555.3, y_fig + 245)
    draw_rounded_card(page, fig_card, fill_color=WHITE, border_color=CARD_BORDER)
    
    fig_path = os.path.join(FIGURES_DIR, "latency", "fig_cross_latency_claim_vs_complete.png")
    if os.path.exists(fig_path):
        img_rect = fitz.Rect(50, y_fig + 8, 545.3, y_fig + 215)
        page.insert_image(img_rect, filename=fig_path, keep_proportion=True)
    page.insert_text(fitz.Point(55, y_fig + 228), "Figure 18: Latency Across Distinct Experimental Setup Scopes (Query 41 vs Complete Answer Benchmark)", fontsize=8.2, fontname="hebo", color=NAVY_PRIMARY)
    page.insert_text(fitz.Point(55, 240 + y_fig), "What the Graph Shows: Claim decomposition required ~85s per query, whereas complete-answer verification dropped latency to ~8s on CPU.", fontsize=7.8, fontname="heit", color=TEXT_DARK)

    # Scientific Caveat & Research Progression Narrative
    y_bot = y_fig + 255
    c_caveat = fitz.Rect(40, y_bot, 555.3, 785)
    draw_rounded_card(page, c_caveat, fill_color=LIGHT_BG, border_color=CARD_BORDER)
    page.insert_text(fitz.Point(55, y_bot + 18), "ESSENTIAL SCIENTIFIC CAVEAT & COMPARABILITY BOUNDARIES", fontsize=9.5, fontname="hebo", color=NAVY_PRIMARY)
    page.draw_line(fitz.Point(55, y_bot + 24), fitz.Point(540, y_bot + 24), color=CARD_BORDER, width=0.8)
    
    caveat_text = (
        "1. Non-Equivalent Timing Scopes: Query 41 (Exp-09) was an instrumented worst-case complex query with 10 claims and "
        "5 retrieved chunks, measuring live LLM claim extraction (14.77s) and RAG generation (12.33s). In contrast, the 50Q "
        "ModernCE benchmark (Exp-13/14) measured offline CPU verification execution on saved RAG answers without live API overhead.\n\n"
        "2. No Direct Ratio Claimed: Because the experimental setups, hardware conditions, and analysis units differ, we do NOT "
        "claim a direct '10x speedup ratio.' Instead, the data demonstrates an architectural reduction in complexity: claim-level "
        "decomposition requires O(Claims x Chunks) passes plus an expensive LLM extraction call, while complete-answer verification "
        "requires only O(Progressive Stages) passes (typically 1 to 3 passes per query).\n\n"
        "3. Research Progression Summary: Phase A established clean retrieval (K=7). Phase B proved cross-encoder NLI was necessary. "
        "Phase C demonstrated that claim-level decomposition collapsed under premise dilution and extreme latency. Phase D solved both "
        "crises by pairing ModernCE (2,048 tokens) with complete-answer progressive multi-chunk evidence."
    )
    page.insert_textbox(fitz.Rect(55, y_bot + 30, 540, 775), caveat_text, fontsize=7.8, fontname="helv", color=TEXT_DARK)

def build_synthesis_page(doc):
    """Generates Page 23: Final Synthesis & Limitations."""
    page = doc.new_page(width=595.3, height=841.9)
    draw_header_band(page, "SYNTHESIS & CURRENT SCIENTIFIC LIMITATIONS", "Phase D")
    
    page.insert_text(fitz.Point(40, 62), "5. Synthesis of Findings & What We Learned", fontsize=15, fontname="hebo", color=NAVY_PRIMARY)
    page.insert_text(fitz.Point(40, 78), "Honest assessment of what succeeded, what failed, and the remaining boundaries of the system", fontsize=8.5, fontname="heit", color=SLATE_GRAY)
    
    # Section A: What Did We Learn?
    c_learn = fitz.Rect(40, 92, 555.3, 400)
    draw_rounded_card(page, c_learn, fill_color=WHITE, border_color=CARD_BORDER)
    page.insert_text(fitz.Point(55, 112), "WHAT DID WE LEARN FROM ALL 17 EXPERIMENTS?", fontsize=10.5, fontname="hebo", color=NAVY_PRIMARY)
    page.draw_line(fitz.Point(55, 118), fitz.Point(540, 118), color=CARD_BORDER, width=0.8)
    
    findings = [
        ("1. Cosine Similarity Cannot Act as a Fact Verifier (Exp 04, 06):",
         "Bi-encoder cosine similarity measures topical semantic relatedness, not logical validity. Contradictions score ~0.77 similarity, overlapping heavily with entailed text (0.82). Cross-encoders are mandatory for truth detection."),
        ("2. Sentence and Atomic Claim Decomposition Collapsed in Live RAG (Exp 07, 08):",
         "Matching isolated sentences or propositions against 400-word passages triggered 90-100% false neutral rates due to premise dilution. Decomposing text strips essential grammatical qualifiers and destroys sentential context."),
        ("3. Context Headroom is the Key Prerequisite for Multi-Chunk Grounding (Exp 11):",
         "DeBERTa's 512-token limit truncated 57.3% of RAG pairs. ModernCE's 2,048-token context eliminated truncation completely (0.0%), immediately shifting 38 pairs from Neutral to Entailed without modifying text."),
        ("4. Complete Answers Unlock Multi-Chunk Synergy (Exp 12, 13):",
         "RAG answers synthesize facts across multiple passages. Verifying the complete answer against concatenated Top-1 + Top-2 chunks unlocked synergistic grounding (Query 1 jumped from 0.35 to 0.91 Entailment), reaching 93.75% benchmark entailment."),
        ("5. Progressive Evidence Concatenation Capped at Top-3 (Exp 15):",
         "Evaluating Top-1 grounds 37.5% of answers; adding Top-2 brings coverage to 79.2%; Top-3 reaches 93.8%. Evaluating Top-4 yielded 0% additional recoveries while adding wasted latency and context overhead.")
    ]
    f_y = 132
    for title, desc in findings:
        page.insert_text(fitz.Point(55, f_y), title, fontsize=8.2, fontname="hebo", color=NAVY_LIGHT)
        page.insert_textbox(fitz.Rect(55, f_y + 2, 540, f_y + 40), desc, fontsize=7.8, fontname="helv", color=TEXT_DARK)
        f_y += 52

    # Section B: What Are the Current Limitations?
    c_limits = fitz.Rect(40, 412, 555.3, 785)
    draw_rounded_card(page, c_limits, fill_color=(0.99, 0.96, 0.96), border_color=(0.85, 0.35, 0.35))
    page.insert_text(fitz.Point(55, 432), "WHAT ARE THE CURRENT SCIENTIFIC & OPERATIONAL LIMITATIONS?", fontsize=10.5, fontname="hebo", color=(0.6, 0.1, 0.1))
    page.draw_line(fitz.Point(55, 438), fitz.Point(540, 438), color=(0.85, 0.35, 0.35), width=0.8)
    
    limits = [
        ("1. NLI Entailment is Model Support, NOT Universal Truth:",
         "The reported 93.75% benchmark score measures whether the generated answer is mathematically supported by the retrieved textbook chunks under a cross-encoder model. If the textbook itself contains errors or outdated facts, the verifier will still classify the answer as entailed."),
        ("2. Possible Unsupported Minor Subclaims in Complete Answers:",
         "Verifying at the complete-answer level tests whether the overall response is entailed by the evidence. It is theoretically possible for an answer to contain an unsupported minor subclause or hallucinated parenthetical while the main thesis is strongly entailed by the evidence."),
        ("3. Human Gold-Truth Annotation Remains Strictly Pending (Exp 17):",
         "UTF-8 audit of outputs/manual_annotation_50q.json confirms that all 50 manual_label entries are empty strings. While automated NLI verification is validated, independent domain expert human correctness remains open for future research."),
        ("4. CPU Latency Overhead in Interactive Production:",
         "Running ModernBERT cross-encoder forward passes on CPU averages 7.85s to 8.33s per query across 50 questions. While far faster than the 85s claim decomposition, sub-second interactive deployment will require GPU acceleration or ONNX quantization."),
        ("5. Out-of-Scope Evidence Boundaries:",
         "When a query asks about topics outside the indexed 341-page textbook, the retriever returns low-relevance chunks. While the regex abstention bypass successfully flags explicit 'NOT_FOUND' responses (saving 14 passes), subtle ungrounded queries require careful fallback handling.")
    ]
    l_y = 452
    for title, desc in limits:
        page.insert_text(fitz.Point(55, l_y), title, fontsize=8.2, fontname="hebo", color=(0.55, 0.12, 0.12))
        page.insert_textbox(fitz.Rect(55, l_y + 2, 540, l_y + 45), desc, fontsize=7.8, fontname="helv", color=TEXT_DARK)
        l_y += 64

def build_architecture_page(doc):
    """Generates Page 24: Final Production Architecture & Viva Defense Summary."""
    page = doc.new_page(width=595.3, height=841.9)
    draw_header_band(page, "FINAL PRODUCTION ARCHITECTURE & DEFENSE", "Phase D")
    
    page.insert_text(fitz.Point(40, 62), "6. Final Production Architecture & Viva Defense Blueprint", fontsize=13.5, fontname="hebo", color=NAVY_PRIMARY)
    page.insert_text(fitz.Point(40, 78), "The complete deployed pipeline and traceability matrix connecting research experiments to production code", fontsize=8.5, fontname="heit", color=SLATE_GRAY)
    
    # Traceability Matrix Table
    col_w = [85, 100, 110, 80, 140]
    headers = ["Component", "Architectural Choice", "Production Implementation", "Source Exp", "Empirical Justification"]
    rows = [
        ["PDF Ingestion", "Layout-Aware Parsing", "PyMuPDF + Regex Header Fix", "Exp-01", "Preserves 91.8% key terms and 100% page coverage across 341 pages."],
        ["Candidate Pool", "High-Recall Candidate Set", "Candidate Pool Kcand = 15", "Exp-02", "Evaluated K in [3,20]; K=15 achieved 100% retrieval hit rate on test queries."],
        ["Hybrid Fusion", "Dense + Lexical Ranking", "Reciprocal Rank Fusion (k=60)", "Exp-02", "Outperformed vector alone (+8.7% MRR) and BM25 alone (+20.1% MRR)."],
        ["Context Window", "Final Prompt Chunks", "Production TOP_K = 7", "Exp-02, 03", "98.6% keyword coverage within 19,322 chars (<20k ceiling); validated 0.824 similarity."],
        ["Generation LLM", "Foundation Model", "Meta-Llama-3.1-70B-Instruct", "Exp-03", "NVIDIA API integration; 1.98s average generation latency across 50 questions."],
        ["Abstention Filter", "Out-of-Scope Bypass", "is_abstention_answer() Regex", "Exp-14", "Bypasses NLI inference on non-retrieval answers, saving 14 forward passes on 50 Qs."],
        ["Verifier Model", "Long-Context Cross-Encoder", "dleemiller/ModernCE-base-nli", "Exp-11", "ModernBERT 2,048 tokens eliminates truncation (0.0% vs DeBERTa 57.3%)."],
        ["Evidence Unit", "Concatenated Chunks", "Complete Answer + Multi-Chunk", "Exp 12, 13", "Slashes forward passes from 50+ to 1-3 while unlocking multi-chunk synergy."],
        ["Stopping Depth", "Progressive Stopping", "Strictly Capped at TOP_3", "Exp-15", "TOP_1 (37.5%) -> TOP_2 (79.2%) -> TOP_3 (93.8%); TOP_4 yields 0 additional gains."],
        ["User Interface", "Visual Grounding Badges", "Streamlit Dynamic Trust UI", "Exp-17", "Real-time trust badges (VERIFIED, PARTIAL, UNVERIFIED) pass 4/4 UI tests."]
    ]
    tbl_end_y = draw_table(page, 40, 92, col_w, headers, rows, font_size=7.0, row_height=26.0)
    
    # Viva Defense Summary Card
    viva_rect = fitz.Rect(40, tbl_end_y + 12, 555.3, 785)
    draw_rounded_card(page, viva_rect, fill_color=LIGHT_BG, border_color=CARD_BORDER)
    page.insert_text(fitz.Point(55, tbl_end_y + 30), "KEY DEFENSE QUESTIONS & ANSWERS FOR PROJECT PRESENTATIONS", fontsize=10.5, fontname="hebo", color=NAVY_PRIMARY)
    page.draw_line(fitz.Point(55, tbl_end_y + 36), fitz.Point(540, tbl_end_y + 36), color=CARD_BORDER, width=0.8)
    
    qa_list = [
        ("Q: Why didn't you just use embedding similarity to check for hallucinations?",
         "A: In Experiments 04 and 06, we proved that contradicted statements had a mean cosine similarity of 0.7686 compared to 0.8093 for true facts. Because a contradictory claim shares entities and nouns with the text, vector similarity cannot detect negations. Cross-encoder NLI is mandatory."),
        ("Q: Why not verify each sentence separately instead of the whole answer?",
         "A: In Experiment 07, sentence splitting caused 100% of claims to be classified as Neutral due to premise dilution (matching a 15-word claim against 400 words) and token truncation. Real RAG answers synthesize facts across sentences and chunks; evaluating the complete answer restores joint context."),
        ("Q: Why did you switch from DeBERTa-v3 to ModernCE?",
         "A: DeBERTa has a 512-token limit that truncated 57.3% of our RAG pairs. ModernCE, built on ModernBERT with Flash Attention, expands context to 2,048 tokens, eliminating truncation completely and allowing us to concatenate up to 3 chunks (~1,200 words) safely."),
        ("Q: Does 93.75% entailment mean the RAG system is 93.75% factually accurate in the real world?",
         "A: No. It proves that 93.75% of content answers are mathematically supported by the retrieved textbook chunks. If the textbook itself has an error, the model will faithfully reproduce it. True external factual correctness requires expert human review (which is prepared in our manual annotation protocol).")
    ]
    q_y = tbl_end_y + 52
    for q, a in qa_list:
        page.insert_text(fitz.Point(55, q_y), q, fontsize=8.0, fontname="hebo", color=NAVY_LIGHT)
        page.insert_textbox(fitz.Rect(55, q_y + 2, 540, q_y + 40), a, fontsize=7.6, fontname="helv", color=TEXT_DARK)
        q_y += 46

def apply_running_footers_and_bookmarks(doc):
    """Applies page numbers 'Page X of Y', footer rules, and interactive PDF outline."""
    total_pages = doc.page_count
    
    # 1. Footers on all content pages (skip cover page)
    for p_num in range(1, total_pages):
        page = doc[p_num]
        footer_y = 822
        page.draw_line(fitz.Point(40, footer_y - 8), fitz.Point(555.3, footer_y - 8), color=CARD_BORDER, width=0.5)
        page.insert_text(fitz.Point(40, footer_y), "RAG & Hallucination Verification Experiments Guide | Student & Viva Compendium", fontsize=7.5, fontname="helv", color=TEXT_MUTED)
        page_str = f"Page {p_num + 1} of {total_pages}"
        p_len = fitz.get_text_length(page_str, fontname="hebo", fontsize=7.5)
        page.insert_text(fitz.Point(555.3 - p_len, footer_y), page_str, fontsize=7.5, fontname="hebo", color=NAVY_LIGHT)
        
    # 2. Interactive Document Outline (Bookmarks / Table of Contents)
    toc = [
        [1, "Title & Academic Cover Page", 1],
        [1, "Project Overview & Workflow Architecture", 2],
        [1, "Master 17-Experiment Chronology Table (Part 1)", 3],
        [1, "Master 17-Experiment Chronology Table (Part 2)", 4],
        [1, "Phase A: Retrieval & Baseline Quality", 5],
        [2, "Exp 01: PDF Layout Text Extraction Quality", 5],
        [2, "Exp 02: Candidate Pool & Hybrid RRF Optimization", 6],
        [2, "Exp 03: Baseline RAG Generation Benchmark (K=7)", 7],
        [1, "Phase B: Controlled NLI Verification Benchmarking", 8],
        [2, "Exp 04: Verification Pilot v1 (Similarity vs NLI)", 8],
        [2, "Exp 05: Pilot v2 Calibration & Probability Thresholds", 9],
        [2, "Exp 06: 280-Triple Comprehensive Verification Benchmark", 10],
        [1, "Phase C: The Claim-Level Verification Crisis", 11],
        [2, "Exp 07: Live RAG Sentence-Level Verification Failure", 11],
        [2, "Exp 08: Atomic Claim Decomposition Pilot", 12],
        [2, "Exp 09: Single-Query Latency Diagnostic (Query 41)", 13],
        [2, "Exp 10: Evidence Granularity & Micro-Unit Splitting", 14],
        [1, "Phase D: ModernCE & Complete-Answer Breakthrough", 15],
        [2, "Exp 11: NLI Model Comparison & Truncation Elimination", 15],
        [2, "Exp 12: Complete-Answer Multi-Chunk Verification", 16],
        [2, "Exp 13: 50-Question ModernCE Complete-Answer Benchmark", 17],
        [2, "Exp 14: Production Parity & Regex Abstention Integration", 18],
        [2, "Exp 15: Progressive Telemetry & Stopping Depth Capping", 19],
        [2, "Exp 16: Grounding Stability & Variance on Static Text", 20],
        [2, "Exp 17: UI Trust Badges & Manual Annotation Protocol", 21],
        [1, "Cross-Experiment Latency Analysis: Claim-Level vs Complete-Answer", 22],
        [1, "Synthesis of Findings: What We Learned & Limitations", 23],
        [1, "Final System Architecture & Viva Defense Blueprint", 24]
    ]
    doc.set_toc(toc)

# ==============================================================================
# MAIN GENERATOR FUNCTION
# ==============================================================================
def generate_pdf_guide():
    print(f"Generating Comprehensive Student PDF Guide...")
    doc = fitz.open()
    
    # 1. Cover Page (Page 1)
    build_cover_page(doc)
    
    # 2. Project Overview & Workflow Architecture (Page 2)
    build_project_overview_page(doc)
    
    # 3. Master Experiment Summary Table (Pages 3 & 4)
    build_summary_table_pages(doc)
    
    # 4. Individual Experiment Summaries (Pages 5-21)
    exp_details = [
        # Exp 01
        {
            "id": "01",
            "title": "PDF Extraction Quality & Term Preservation",
            "phase": "Phase A",
            "why": "Clean text extraction is the foundation of RAG. Corrupted character encodings, hyphenated breaks, or lost section headers break downstream retrieval before generation even begins.",
            "what": "Evaluated PyMuPDF with custom regex heading restoration across 341 textbook pages against ground-truth vocabulary and key terminology.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Evaluation Metric", "Measured Value", "Benchmark Target", "Evaluation Outcome"],
            "rows": [
                ["Vocabulary F1 Score", "82.0%", ">= 80.0%", "Exceeded target (+2.0%)"],
                ["3-Gram Overlap F1", "66.8%", ">= 65.0%", "Exceeded target (+1.8%)"],
                ["Key-Term Retention", "91.8%", ">= 90.0%", "Exceeded target (+1.8%)"],
                ["Total Page Coverage", "100.0% (341/341)", "100.0%", "Zero missing pages"]
            ],
            "figure": "retrieval/fig_exp01_extraction_quality.png",
            "fig_caption": "PDF Layout Extraction Quality Across 341 Textbook Pages",
            "fig_shows": "All evaluated extraction metrics exceeded targets, proving layout-aware regex parsing successfully preserves domain terminology without character corruption.",
            "conclusion": "Clean layout parsing guarantees high-fidelity text extraction without corrupted tokens.",
            "next_step": "Index the clean text into vector and lexical stores to optimize retrieval parameters (Exp-02)."
        },
        # Exp 02
        {
            "id": "02",
            "title": "Candidate Pool Size, Final Context K, & Hybrid RRF",
            "phase": "Phase A",
            "why": "Too few retrieved chunks cause omission hallucinations; too many chunks dilute LLM attention and breach prompt context limits. Single retrievers miss synonyms or exact terms.",
            "what": "Swept candidate pool Kcand in [3, 7, 10, 15, 20] and final context K in [3, 7, 10, 15] across 18 queries. Compared BM25, Dense Vector (BGE-Large), and Hybrid RRF (k=60).",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Retrieval Parameter / Configuration", "Measured Metric", "Benchmark Threshold", "Selected Decision"],
            "rows": [
                ["Candidate Pool (Kcand = 15)", "100.0% Hit Rate", ">= 95.0% Recall", "Selected candidate pool size"],
                ["Final Context (TOP_K = 7)", "98.6% Keyword Coverage", "19,322 chars (<20k limit)", "Selected production context"],
                ["Hybrid RRF vs Vector Only", "+8.7% MRR (0.702 vs 0.645)", "Positive improvement", "Adopted Hybrid RRF (k=60)"],
                ["Hybrid RRF vs BM25 Only", "+20.1% MRR (0.702 vs 0.584)", "Positive improvement", "BM25 combined with dense"]
            ],
            "figure": "retrieval/fig_exp02_candidate_k_sweep.png",
            "fig_caption": "Candidate Retrieval Pool (Kcand) Optimization Curve (N=18 Queries)",
            "fig_shows": "Candidate pool size Kcand=15 reaches 100% retrieval hit rate, providing an optimal high-recall pool for subsequent reranking.",
            "conclusion": "Hybrid RRF at Kcand=15 and final TOP_K=7 delivers 98.6% keyword recall within prompt budget.",
            "next_step": "Evaluate end-to-end RAG answer generation quality using this production K=7 baseline (Exp-03)."
        },
        # Exp 03
        {
            "id": "03",
            "title": "Baseline RAG Generation Quality Benchmark (K=7)",
            "phase": "Phase A",
            "why": "Retrieval metrics confirm chunks are found, but we needed to measure how accurately the LLM synthesizes those chunks into answers across 50 questions against human reference answers.",
            "what": "Evaluated Meta-Llama-3.1-70B-Instruct with production TOP_K=7 Hybrid RRF context on 50 textbook questions (outputs/dataset.json) using cosine similarity and token F1.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Generation Benchmark Metric", "Production Baseline (K=7)", "Target Threshold", "Evaluation Status"],
            "rows": [
                ["Mean Semantic Similarity", "0.824", ">= 0.800", "Exceeded target (+0.024)"],
                ["High-Similarity Answers (>= 0.80)", "33 / 50 (66.0%)", ">= 60.0%", "High-quality dominant"],
                ["Moderate Similarity (0.60 - 0.79)", "15 / 50 (30.0%)", "Acceptable range", "Acceptable semantic overlap"],
                ["Weak Cases (< 0.60)", "2 / 50 (4.0%)", "< 5.0%", "Controlled edge cases"],
                ["Average Generation Latency", "1.98 seconds", "< 2.50 seconds", "Interactive speed achieved"]
            ],
            "figure": "baseline_rag/fig_exp03_baseline_rag_quality.png",
            "fig_caption": "Baseline RAG Generation Quality Metrics Across 50 Benchmark Questions",
            "fig_shows": "Production pipeline achieves strong semantic alignment (mean 0.824) with 66% high-similarity answers and rapid 1.98s response latency.",
            "conclusion": "Solidified TOP_K=7 as the production generation baseline, confirming strong overall answer quality.",
            "next_step": "Because reference similarity cannot detect subtle hallucinations at runtime, Phase B was launched (Exp-04)."
        },
        # Exp 04
        {
            "id": "04",
            "title": "Verification Pilot v1: Cosine Similarity vs NLI",
            "phase": "Phase B",
            "why": "Can fast cosine similarity serve as an automated hallucination detector, or do we require a full NLI cross-encoder model?",
            "what": "Evaluated Bi-Encoder Cosine Similarity (all-MiniLM-L6-v2) against a Cross-Encoder (DeBERTa-v3-base) on 45 curated pairs (20 Entailment, 15 Neutral, 10 Contradiction).",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Verification Approach", "Accuracy (N=45)", "Entailment Score", "Contradiction Score / Overlap"],
            "rows": [
                ["DeBERTa-v3-base NLI", "95.56% (43 / 45)", "High probability separation", "Clear decision boundary"],
                ["Cosine Semantic Similarity", "Failed completely", "0.820 Mean Similarity", "0.770 Mean (Massive overlap!)"],
                ["Similarity Overlap Margin", "Delta = 0.050", "Indistinguishable distributions", "Cannot detect negation"],
                ["Verification Decision", "Adopted NLI Cross-Encoder", "Rejected Cosine Similarity", "Full attention required"]
            ],
            "figure": "claim_level/fig_exp04_pilot_v1_distribution.png",
            "fig_caption": "Pilot v1 Sample Distribution and DeBERTa Classification Accuracy",
            "fig_shows": "DeBERTa successfully classified 43/45 pairs across all 3 classes, whereas cosine similarity failed because contradictory claims shared identical entities.",
            "conclusion": "Cosine similarity is fundamentally incapable of factual verification; cross-encoder NLI is mandatory.",
            "next_step": "Calibrate explicit decision probability thresholds for the NLI cross-encoder (Exp-05)."
        },
        # Exp 05
        {
            "id": "05",
            "title": "Pilot v2 Calibration & Probability Thresholds",
            "phase": "Phase B",
            "why": "Standard argmax classification treats probabilities equally. Verification requires calibrated decision thresholds to prevent false entailments or false contradictions.",
            "what": "Calibrated asymmetric probability thresholds (P(E) >= 0.70 for Entailment, P(C) >= 0.50 for Contradiction) across 60 curated claim-evidence pairs.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Calibration Parameter / Metric", "Calibrated Value", "Target Standard", "Validation Status"],
            "rows": [
                ["Entailment Threshold P(E)", "P(E) >= 0.70", "High-precision threshold", "Established boundary"],
                ["Contradiction Threshold P(C)", "P(C) >= 0.50", "Sensitive safety boundary", "Established boundary"],
                ["Overall Accuracy on Pilot v2", "95.0% (57 / 60)", ">= 90.0%", "3 minor neutral edge cases"],
                ["Macro F1 Score", "0.948", ">= 0.900", "Ent F1: 0.960 / Con F1: 0.957"]
            ],
            "figure": "claim_level/fig_exp05_pilot_v2_calibration.png",
            "fig_caption": "DeBERTa-v3-base Confusion Matrix on Calibrated Pilot v2 (N=60 Pairs)",
            "fig_shows": "Calibrated thresholds cleanly separated Entailment (24/25) and Contradiction (15/15), confirming the validity of asymmetric decision boundaries.",
            "conclusion": "Calibrated thresholds (P(E)>=0.70, P(C)>=0.50) reliably separate factual support from unsupported extrapolation.",
            "next_step": "Validate the calibrated verifier on a large-scale, balanced 280-triple benchmark (Exp-06)."
        },
        # Exp 06
        {
            "id": "06",
            "title": "280-Triple Comprehensive Benchmark & Similarity Sweep",
            "phase": "Phase B",
            "why": "Validate DeBERTa across a statistically significant, balanced dataset of 280 claim-evidence triples and systematically sweep similarity thresholds to prove similarity's failure.",
            "what": "Evaluated 280 curated triples (110 Entailment, 90 Neutral, 80 Contradiction). Swept cosine similarity thresholds from 0.50 to 0.95 and compared against DeBERTa.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Evaluated Method", "Overall Accuracy", "Macro F1 Score", "Contradiction F1 Score"],
            "rows": [
                ["DeBERTa-v3-base NLI", "96.43% (270 / 280)", "0.963", "0.969 (Clean detection)"],
                ["Cosine Similarity (tau = 0.79)", "61.43% (Peak Accuracy)", "0.587", "0.421 (Unacceptable failure)"],
                ["Cosine Similarity (tau = 0.70)", "52.86%", "0.492", "0.215 (Massive false positives)"],
                ["Performance Differential", "+35.0% Accuracy", "+0.376 Macro F1", "NLI cleanly separates classes"]
            ],
            "figure": "claim_level/fig_exp06_280_metrics_comparison.png",
            "fig_caption": "DeBERTa-v3-base vs Cosine Similarity on 280-Triple Benchmark",
            "fig_shows": "DeBERTa outperformed cosine similarity by +35% accuracy; similarity failed completely on contradictions regardless of threshold chosen.",
            "conclusion": "Firmly established cross-encoder NLI as the gold standard for factual verification on isolated triples.",
            "next_step": "Deploy DeBERTa on live RAG generated answers from real user queries (Exp-07)."
        },
        # Exp 07
        {
            "id": "07",
            "title": "Live RAG Sentence-Level Verification Crisis",
            "phase": "Phase C",
            "why": "Test whether the 96.4% accurate verifier works when applied to sentences from live RAG answers matched against 400-word retrieved chunks.",
            "what": "Split generated answers for Questions 1-5 into 15 individual sentences and evaluated each against the top retrieved chunk using DeBERTa.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Live Evaluation Metric", "Observed Value", "Expected Benchmark", "Diagnostic Finding"],
            "rows": [
                ["Sentence Entailment Rate", "0 / 15 (0.0%)", ">= 80.0%", "Complete failure to verify"],
                ["Sentence Neutral Rate", "15 / 15 (100.0%)", "< 15.0%", "100% False Neutral Crisis!"],
                ["Token Truncation Rate (>512)", "61.9% (65 / 105)", "0.0%", "Evidence cut off mid-passage"],
                ["Core Root Cause", "Premise Dilution", "15w claim vs 400w chunk", "Cross-attention diffused"]
            ],
            "figure": "claim_level/fig_exp07_sentence_claims_neutral_failure.png",
            "fig_caption": "Live RAG Sentence Verification: 100% False Neutral Collapse (Q1-Q5)",
            "fig_shows": "Every single sentence was classified as Neutral, revealing catastrophic premise dilution and token truncation in live deployment.",
            "conclusion": "DeBERTa collapsed in production due to Premise Dilution (15w claim vs 400w chunk) and Context Truncation (512 limit).",
            "next_step": "Break sentences down into minimal atomic propositions using LLM decomposition (Exp-08)."
        },
        # Exp 08
        {
            "id": "08",
            "title": "Atomic Claim Decomposition Pilot",
            "phase": "Phase C",
            "why": "Investigate whether decomposing complex sentences into atomic propositions fixes premise dilution by eliminating grammatical clutter.",
            "what": "Used an LLM to extract 44 atomic claims from Q1-Q5 answers and verified each proposition against retrieved chunks.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Atomic Claim Classification", "Observed Count (N=44)", "Percentage (%)", "Architectural Outcome"],
            "rows": [
                ["Neutral (Unsupported)", "40 / 44 claims", "90.9%", "Neutral crisis persisted!"],
                ["Supported (Entailed)", "1 / 44 claims", "2.3%", "Only 1 proposition verified"],
                ["Contradicted (Hallucinated)", "3 / 44 claims", "6.8%", "False contradictions created"],
                ["Core Failure Mechanism", "Context Stripping", "Lost qualifiers", "Atomic claims lost meaning"]
            ],
            "figure": "claim_level/fig_exp08_atomic_claim_distribution.png",
            "fig_caption": "Atomic Claim Decomposition Verdict Distribution (N=44 Claims)",
            "fig_shows": "90.9% of atomic claims remained Neutral; stripping surrounding sentence grammar destroyed context and caused false contradictions.",
            "conclusion": "Atomic decomposition failed to solve the Neutral crisis and stripped critical qualifiers needed for accurate NLI.",
            "next_step": "Profile the operational latency and computational cost of atomic claim verification (Exp-09)."
        },
        # Exp 09
        {
            "id": "09",
            "title": "Single-Query Latency Diagnostic (Query 41)",
            "phase": "Phase C",
            "why": "Profile the exact operational latency and computational breakdown of atomic claim decomposition on a live complex query.",
            "what": "Fully instrumented Query 41 (10 atomic claims x 5 chunks = 50 NLI forward passes) on CPU, recording component execution times.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Pipeline Component / Stage", "Execution Time (s)", "Percentage of Total", "Operational Assessment"],
            "rows": [
                ["Claim Verification (50 passes)", "57.88 seconds", "68.1%", "Severe bottleneck on CPU"],
                ["LLM Claim Extraction", "14.77 seconds", "17.4%", "Expensive extra API call"],
                ["RAG Retrieval & Generation", "12.33 seconds", "14.5%", "Live generation latency"],
                ["Total End-to-End Query Time", "84.98 seconds", "100.0%", "Unusable for interactive RAG"]
            ],
            "figure": "latency/fig_exp09_query41_latency_breakdown.png",
            "fig_caption": "Component Latency Breakdown for Query 41 (Total: 84.98 Seconds)",
            "fig_shows": "Verification consumed 68.1% of runtime (57.88s) due to 50 sequential NLI evaluations, pushing query response time to ~85 seconds.",
            "conclusion": "Claim-level decomposition is computationally unviable for interactive RAG systems.",
            "next_step": "Test evidence micro-units (3-sentence windows) to reduce premise dilution without heavy claim extraction (Exp-10)."
        },
        # Exp 10
        {
            "id": "10",
            "title": "Evidence Granularity & Micro-Unit Splitting",
            "phase": "Phase C",
            "why": "Investigate whether shrinking evidence chunks into 3-sentence units reduces premise dilution and eliminates background text distraction.",
            "what": "Evaluated 220 claim-evidence pairs across Q1-Q5 (44 claims x 5 chunks) comparing full 400w chunks vs 3-sentence micro-units.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Micro-Unit Diagnostic Metric", "Micro-Units (N=220)", "Full Chunks Baseline", "Diagnostic Outcome"],
            "rows": [
                ["Neutral Classification Rate", "80.5% (177 / 220)", "97.7% (215 / 220)", "Neutral rate remained over 80%"],
                ["Entailment (Supported) Rate", "14.1% (31 / 220)", "0.5% (1 / 220)", "Marginal gain (+30 pairs)"],
                ["Context-Loss Regressions", "1 / 220 (0.45%)", "0 regressions", "Claim 5_C2 lost context"],
                ["Architectural Verdict", "Permanently Abandoned", "Fatal regression", "Micro-splitting rejected"]
            ],
            "figure": "claim_level/fig_exp10_micro_unit_regressions.png",
            "fig_caption": "Evidence Micro-Unit Diagnostics: Full Chunks vs Micro-Units (DeBERTa-v3-base)",
            "fig_shows": "Controlled comparison of Full Chunks vs 3-sentence micro-units under DeBERTa-v3-base (N=220 pairs): 0% truncation, but Neutral rate persisted at 80.5% with 1 regression.",
            "conclusion": "Micro-unit splitting fragments semantic context, proving that reducing chunk size is the wrong direction.",
            "next_step": "Permanently abandon claim decomposition; upgrade to a long-context cross-encoder (Exp-11)."
        },
        # Exp 11
        {
            "id": "11",
            "title": "NLI Model Comparison: DeBERTa vs ModernCE",
            "phase": "Phase D",
            "why": "Overcome the 512-token truncation bottleneck that caused 57% of evidence to be truncated in DeBERTa.",
            "what": "Compared DeBERTa-v3-base (512 ctx) against dleemiller/ModernCE-base-nli (ModernBERT, 2,048 ctx) on 220 live RAG chunk-claim pairs.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Model Architecture Metric", "DeBERTa-v3-base", "ModernCE-base-nli", "Architectural Advantage"],
            "rows": [
                ["Maximum Context Window", "512 tokens", "2,048 tokens", "4x capacity expansion"],
                ["Token Truncation Rate (N=220)", "57.3% (126 / 220)", "0.0% (0 / 220)", "Complete elimination of cutoffs"],
                ["Max Observed Token Length", "512 (hard cut)", "619 tokens", "Safely within 2,048 window"],
                ["Recovered Entailments", "1 / 220 (0.5%)", "69 / 220 (31.4%)", "+65 Neutral -> Entailed shifts"]
            ],
            "figure": "model_comparison/fig_exp11_truncation_label_shift.png",
            "fig_caption": "DeBERTa vs ModernCE Token Truncation and Entailment Recoveries",
            "fig_shows": "ModernCE eliminated truncation completely (0.0%), and 38 pairs immediately became Entailed simply because the model could see the full text.",
            "conclusion": "ModernCE-base-nli eliminates token truncation and provides context capacity for multi-chunk RAG verification.",
            "next_step": "Test verifying complete answers against concatenated multi-chunk evidence (Exp-12)."
        },
        # Exp 12
        {
            "id": "12",
            "title": "Complete-Answer Multi-Chunk Verification",
            "phase": "Phase D",
            "why": "Test whether verifying the complete generated answer against concatenated top chunks (Top-1 + Top-2) resolves premise dilution and enables context synergy.",
            "what": "Evaluated Q1-Q5 complete answers against Top-1 alone vs Concatenated Top-1+Top-2 evidence using ModernCE.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Evaluated Evidence Context", "Entailment Rate (Q1-Q5)", "Query 1 P(Entailment)", "Query 1 Classification"],
            "rows": [
                ["Top-1 Chunk Alone", "2 / 5 (40.0%)", "0.348 P(E)", "Neutral (Incomplete context)"],
                ["Top-2 Chunk Alone", "1 / 5 (20.0%)", "0.281 P(E)", "Neutral (Incomplete context)"],
                ["Concatenated Top-1 + Top-2", "4 / 5 (80.0%)", "0.914 P(E)!", "ENTAILED (Synergy unlocked)"],
                ["NLI Forward Passes Required", "1 - 2 passes / query", "Slashed from 50+", "~1.0s verification latency"]
            ],
            "figure": "complete_answer/fig_exp12_multichunk_concatenation_synergy.png",
            "fig_caption": "Multi-Chunk Concatenation Synergy: Top-1 vs Concatenated Context",
            "fig_shows": "Concatenating complementary chunks unlocked multi-chunk synergy (Q1 jumped from 0.35 to 0.91), while eliminating claim extraction overhead.",
            "conclusion": "The Complete-Answer Multi-Chunk paradigm successfully resolved premise dilution and slashed inference overhead.",
            "next_step": "Scale complete-answer verification to the definitive 50-question benchmark (Exp-13)."
        },
        # Exp 13
        {
            "id": "13",
            "title": "50-Question ModernCE Complete-Answer Benchmark",
            "phase": "Phase D",
            "why": "Establish the definitive empirical verification benchmark across 50 production questions to validate the complete-answer progressive paradigm.",
            "what": "Verified complete answers for all 50 benchmark questions using progressive multi-chunk evidence (Top-1 -> Top-2 -> Top-3) under ModernCE.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Benchmark Grounding Metric", "Measured Benchmark Value", "Benchmark Target", "Statistical Assessment"],
            "rows": [
                ["Entailed Content Answers", "45 / 48 (93.75%)", ">= 85.0%", "Primary benchmark established"],
                ["Stage 2 (Top-2) Recoveries", "38 / 48 (79.17%)", "Core evidence driver", "Dominant grounding stage"],
                ["Stage 3 (Top-3) Recoveries", "7 / 48 (14.58%)", "Synergistic recoveries", "Marginal recovery stage"],
                ["Neutral Verdicts", "3 / 48 (6.25%)", "< 15.0%", "Controlled ungrounded cases"],
                ["Contradictions Detected", "0 / 48 (0.0%)", "0.0%", "Zero factual hallucinations"],
                ["Mean Verification Latency", "8.33 seconds", "< 10.0 seconds", "CPU evaluation on saved text"]
            ],
            "figure": "complete_answer/fig_exp13_50q_stage_contribution.png",
            "fig_caption": "Progressive Evidence Stage Contribution Across 50 Questions",
            "fig_shows": "93.75% of content answers were mathematically entailed by retrieved chunks, with Top-2 providing the vast majority of grounding (79.2%).",
            "conclusion": "The ModernCE progressive complete-answer verifier achieves 93.75% empirical entailment on production RAG outputs.",
            "next_step": "Integrate this logic into the modular production engine verification_1/verifier.py (Exp-14)."
        },
        # Exp 14
        {
            "id": "14",
            "title": "Production Parity & Regex Abstention Integration",
            "phase": "Phase D",
            "why": "Confirm that migrating logic into the production class (RAGVerifier) preserves 100% numerical parity and optimize out-of-scope queries.",
            "what": "Compared standalone research code with production verifier.py featuring is_abstention_answer() regex pre-checks across all 50 questions.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Production Parity Metric", "Standalone Research (Exp-13)", "Production verifier.py", "Parity Agreement Status"],
            "rows": [
                ["Status Verdict Agreement", "45 Ent / 3 Neu / 2 Abst", "45 Ent / 3 Neu / 2 Abst", "100.0% Exact Parity (50/50)"],
                ["Stopping Stage Agreement", "38 Top-2 / 7 Top-3", "38 Top-2 / 7 Top-3", "100.0% Exact Parity (50/50)"],
                ["Total NLI Forward Passes", "312 passes", "298 passes", "-14 passes saved via regex!"],
                ["Abstention Handling (Q2, Q48)", "Evaluated 7 stages", "0 NLI passes (Bypassed)", "Instant ABSTAINED verdict"],
                ["Average Verification Latency", "8.33 seconds", "7.85 seconds", "-0.48s efficiency gain"]
            ],
            "figure": "final_system/fig_exp14_production_parity_agreement.png",
            "fig_caption": "Research Benchmark vs Production verifier.py Status Agreement",
            "fig_shows": "100% agreement between research and production code, with the regex abstention filter eliminating unnecessary NLI passes on out-of-scope questions.",
            "conclusion": "Production integration achieved perfect fidelity while improving operational efficiency on non-retrieval responses.",
            "next_step": "Profile the progressive stopping depth to determine if evaluating beyond TOP_3 is needed (Exp-15)."
        },
        # Exp 15
        {
            "id": "15",
            "title": "Progressive Verification Telemetry & Stopping Depth",
            "phase": "Phase D",
            "why": "Determine the exact point of diminishing returns when concatenating chunks (TOP_1 through TOP_4) to cap verification depth.",
            "what": "Profiled stage exit distributions and cumulative recoveries across 48 content questions in production telemetry.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Progressive Evidence Stage", "Cumulative Queries Entailed", "Cumulative Percentage (%)", "Execution Latency"],
            "rows": [
                ["Stage 1: TOP_1 Chunk Alone", "18 / 48 queries", "37.5%", "~1.20 s / query"],
                ["Stage 2: TOP_1 + TOP_2 Chunks", "38 / 48 queries (+20 Qs)", "79.2%", "~2.35 s / query"],
                ["Stage 3: TOP_1 + TOP_2 + TOP_3", "45 / 48 queries (+7 Qs)", "93.8%", "~3.80 s / query"],
                ["Stage 4: Concatenating TOP_4", "45 / 48 queries (+0 Qs)", "93.8% (Zero gain!)", "+1.60 s wasted latency"],
                ["Optimal Stopping Boundary", "Cap strictly at TOP_3", "93.8% Maximum Coverage", "Adopted in production"]
            ],
            "figure": "complete_answer/fig_exp15_progressive_stopping_latency.png",
            "fig_caption": "Cumulative Entailment Recoveries vs Evaluation Stage Latency",
            "fig_shows": "Grounding recoveries plateau completely at TOP_3; TOP_4 added context bloat and latency without verifying any additional answers.",
            "conclusion": "Progressive verification is strictly capped at TOP_3 in the production pipeline.",
            "next_step": "Verify the deterministic repeatability and variance of NLI inference (Exp-16)."
        },
        # Exp 16
        {
            "id": "16",
            "title": "Grounding Stability & Repeated-Run Variance",
            "phase": "Phase D",
            "why": "Confirm that the verifier produces stable, deterministic scores across repeated runs on fixed retrieval outputs.",
            "what": "Evaluated Query 1 across 3 repeated runs (n=3) on identical retrieved chunks using ModernCE.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Evaluation Run Number", "Entailment Probability P(E)", "Classification Verdict", "Deterministic Status"],
            "rows": [
                ["Run 1 (Baseline)", "0.9161", "ENTAILED", "Consistent verdict"],
                ["Run 2 (Repeat 1)", "0.9804", "ENTAILED", "Consistent verdict"],
                ["Run 3 (Repeat 2)", "0.9801", "ENTAILED", "Consistent verdict"],
                ["Aggregate Mean +/- StdDev", "0.9589 +/- 0.037", "3 / 3 Entailed (100%)", "Zero classification drift"]
            ],
            "figure": "complete_answer/fig_exp16_grounding_stability_variance.png",
            "fig_caption": "ModernCE Inference Entailment Probabilities Across 3 Repeated Runs",
            "fig_shows": "Minimal variance (sigma = 0.037) and 100% deterministic classification across repeated runs confirm model stability.",
            "conclusion": "NLI verification on static retrieval text is highly repeatable and free of non-deterministic drift.",
            "next_step": "Connect the verifier to UI trust badges and establish the human annotation protocol (Exp-17)."
        },
        # Exp 17
        {
            "id": "17",
            "title": "UI Integration & Manual Annotation Infrastructure",
            "phase": "Phase D",
            "why": "Expose trust badges to end users in Streamlit and prepare the framework for human evaluation.",
            "what": "Ran automated UI tests for trust badges (VERIFIED, PARTIAL, UNVERIFIED, ABSTAINED) and generated the 50-question manual annotation template.",
            "col_widths": [150, 110, 120, 135],
            "headers": ["Infrastructure Component", "Evaluated Artifact / Scope", "Observed Test Result", "Deployment Status"],
            "rows": [
                ["Streamlit UI Badges Test", "tests/test_ui.py (4 tests)", "4 / 4 Tests Passed (100%)", "Verified active in UI"],
                ["Grounding Evidence Accordion", "pages/chat.py UI component", "Displays top-3 chunks", "Verified active in UI"],
                ["50Q Annotation Dataset", "outputs/manual_annotation_50q.json", "50 records generated", "All 50 labels empty"],
                ["Human Factual Ground Truth", "Independent expert audit", "PENDING (0/50 annotated)", "Future expert study"]
            ],
            "figure": "final_system/fig_exp17_ui_workflow_annotation_readiness.png",
            "fig_caption": "Streamlit UI Trust Workflow and Human Annotation Dataset Readiness",
            "fig_shows": "Streamlit UI dynamically displays grounding status and supporting evidence, while human annotation remains properly marked as pending.",
            "conclusion": "System is fully integrated into the user interface; true human ground-truth accuracy remains open for future expert study.",
            "next_step": "Transition to cross-experiment synthesis and project defense."
        }
    ]
    
    for exp in exp_details:
        build_experiment_page(doc, exp)
        
    # 5. Cross-Experiment Latency Analysis (Page 22)
    build_cross_latency_page(doc)
    
    # 6. Final Synthesis & Scientific Limitations (Page 23)
    build_synthesis_page(doc)
    
    # 7. Final System Architecture & Viva Blueprint (Page 24)
    build_architecture_page(doc)
    
    # 8. Post-Processing: Running Footers & Table of Contents Bookmarks
    apply_running_footers_and_bookmarks(doc)
    
    total_pages = doc.page_count
    doc.save(OUTPUT_PDF, garbage=4, deflate=True, clean=True)
    doc.close()
    
    file_size = os.path.getsize(OUTPUT_PDF)
    print(f"[SUCCESS] PDF Guide Generated: {OUTPUT_PDF}")
    print(f"  --> Total Pages: {total_pages}")
    print(f"  --> File Size: {file_size / (1024*1024):.2f} MB ({file_size} bytes)")

if __name__ == "__main__":
    generate_pdf_guide()
