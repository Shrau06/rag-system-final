# 05: Final System Architecture

## Architecture Diagram

```
User Query
    │
    ▼
[Retriever: Hybrid RRF] ── (Exp 01, 02)
    ├── BGE-Large Dense Search (ChromaDB)
    └── BM25 Lexical Search (Rank_BM25)
    └── Candidate Pool: K_cand = 15
    └── Final Top-K Selection: TOP_K = 7  ── (Exp 03)
    │
    ▼
[Generator: Meta-Llama-3.1-70B-Instruct] ── (Exp 03)
    ├── Prompt Context: Top-7 Chunks (<= 20,000 chars)
    └── Output: Complete Generated Answer
    │
    ▼
[Hallucination Verifier: RAGVerifier] ── (Exp 11, 12, 13, 14, 15)
    │
    ├── Step 0: Regex Abstention Pre-check  ── (Exp 14)
    │     └── Match "NOT_FOUND" / "does not contain" ──► Verdict: ABSTAINED (0 NLI passes)
    │
    ├── Step 1: Stage 1 Evaluation  ── (Exp 15)
    │     └── Model: ModernCE-base-nli (ModernBERT, 2048 ctx)
    │     └── Premise: Top-1 Chunk (400w) | Hypothesis: Full Answer
    │     └── If P(Entail) >= 0.60 ──► Exit: VERIFIED (Top-1)
    │
    ├── Step 2: Stage 2 Evaluation  ── (Exp 12, 15)
    │     └── Premise: Top-1 + Top-2 Chunks (~800w) | Hypothesis: Full Answer
    │     └── If P(Entail) >= 0.60 ──► Exit: VERIFIED (Top-2)
    │
    └── Step 3: Stage 3 Evaluation  ── (Exp 13, 15)
          └── Premise: Top-1 + Top-2 + Top-3 Chunks (~1200w) | Hypothesis: Full Answer
          ├── If P(Entail) >= 0.60 ──► Exit: VERIFIED (Top-3)
          ├── If P(Contra) >= 0.50 ──► Exit: CONTRADICTED
          └── Residual ─────────────► Exit: PARTIAL / UNVERIFIED (Neutral)
    │
    ▼
[User Interface: Streamlit] ── (Exp 17)
    ├── Generated Answer Display
    ├── Dynamic Trust Badges (VERIFIED / PARTIAL / UNVERIFIED / ABSTAINED)
    └── Grounding Evidence Accordion
```

## Traceability Matrix: How Experiments Shaped Production

| Production Component | Architectural Choice | Selected Implementation | Experiments That Contributed | Rationale / Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **Ingestion** | Layout Parsing & Regex | PyMuPDF with heading restoration | `Exp-01` | Preserves 91.8% key-terms and 100% page coverage across 341 pages. |
| **Indexing** | Chunking Strategy | 400-word sliding window (50-word overlap) | `Exp-01`, `Exp-02` | Balances semantic coherence with retrieval granularity. |
| **Candidate Retrieval** | Candidate Pool Size | $K_{cand} = 15$ | `Exp-02` | Evaluated $K \in [3,20]$; $K=15$ achieved 100% hit rate on evaluation queries. |
| **Ranking** | Hybrid Fusion | Reciprocal Rank Fusion ($k=60$) | `Exp-02` | Outperformed Vector alone (+8.7% MRR) and BM25 alone (+20.1% MRR). |
| **Context Window** | Final Prompt Chunks | `TOP_K = 7` | `Exp-02`, `Exp-03` | Achieved 98.6% keyword coverage within 19,322 chars; validated 0.824 mean similarity on 50Q baseline. |
| **Generator** | Foundation LLM | Meta-Llama-3.1-70B-Instruct | `Exp-03` | High semantic similarity (0.824 mean) and rapid API response (~1.98s). |
| **Verifier Model** | NLI Architecture | `dleemiller/ModernCE-base-nli` | `Exp-04`, `Exp-06`, `Exp-11` | Overcame similarity failure (Exp-04/06) and DeBERTa 512 context truncation (Exp-11: 0% truncation). |
| **Verification Unit** | Granularity | Complete Generated Answer | `Exp-07`, `Exp-08`, `Exp-10`, `Exp-12` | Sentence/atomic claims caused >90% false neutrals and 85s latency; complete answer restored holistic grounding. |
| **Evidence Formulation**| Multi-Chunk Concatenation | Progressive Top-1 $\rightarrow$ Top-2 $\rightarrow$ Top-3 | `Exp-10`, `Exp-12`, `Exp-13`, `Exp-15` | Enables multi-chunk context synergy (Exp-12); capped at TOP_3 after Exp-15 showed 0 gains at TOP_4. |
| **Abstention Logic** | Out-of-Scope Bypass | `is_abstention_answer()` regex filter | `Exp-13`, `Exp-14` | Instantly flags out-of-scope non-retrieval responses, saving 14 NLI forward passes on 50 questions. |
| **User Interface** | Visual Grounding | Streamlit Trust Badges | `Exp-17` | Real-time display of verification status, probabilities, and supporting chunks; passes 4/4 UI tests. |
