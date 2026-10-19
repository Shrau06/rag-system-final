# 00: Executive Summary

## Project Overview
This repository implements an end-to-end **Retrieval-Augmented Generation (RAG) system with an integrated Hallucination Verification Layer** designed for domain-specific question answering over complex textbook corpora.

The project addresses the critical vulnerability of large language models (LLMs) in high-stakes domains: **factual hallucination**, where an LLM generates fluent, confident assertions that are unsupported by or contradict the source material.

## The Core Technical Journey
The experimental trajectory of this project is characterized by three major phases that culminated in a fundamental architectural breakthrough:

```
[Phase A: Retrieval & Baseline]
  Exp 01 (PDF Ingestion) -> Exp 02 (Candidate K=15, Final K=7, Hybrid RRF) -> Exp 03 (Baseline RAG Generation Benchmark)
         │
         ▼
[Phase B: Controlled Verification]
  Exp 04 (Pilot v1: Similarity Fails) -> Exp 05 (Pilot v2: Calibration) -> Exp 06 (280 Triples: DeBERTa 96.4%)
         │
         ▼
[Phase C: Claim-Level Verification Failure]
  Exp 07 (Live RAG Sentences: 100% Neutral) -> Exp 08 (Atomic Claims: 90.9% Neutral)
  -> Exp 09 (Query 41 Latency: 84.98s) -> Exp 10 (Micro-Units: 18 Context Regressions)
         │
         ▼
[Phase D: Architectural Breakthrough & Production]
  Exp 11 (ModernCE 2,048-token Window) -> Exp 12 (Complete Answer Multi-Chunk Synergy)
  -> Exp 13 (50Q Benchmark: 93.75% Entailed) -> Exp 14 (Production Parity & Abstention Bypass)
  -> Exp 15 (Progressive Telemetry Capped at TOP_3) -> Exp 16 (Stability) -> Exp 17 (UI & Annotation)
```

### 1. Retrieval Optimization & Baseline RAG (Phase A: Exp 01–03)
- **High-Fidelity Extraction**: Parsing 341 pages yielded 82.0% Vocabulary F1 and 91.8% key-term preservation (`Exp-01`).
- **Hybrid Retrieval Superiority**: Combining dense embeddings (`BGE-Large-EN-v1.5`) and lexical matching (`BM25`) via Reciprocal Rank Fusion ($k=60$) achieved 94.4% hit rate and an MRR of 0.702 (+8.7% over vector alone, +20.1% over BM25 alone).
- **Candidate & Final $K$ Selection**: Candidate pool $K_{cand}=15$ achieved 100% hit rate. Final context $K=7$ delivered 98.6% keyword coverage within 19,322 characters (safely below the 20,000-character ceiling), establishing high baseline generation quality (0.824 mean similarity, 66% high-similarity answers) (`Exp-02`, `Exp-03`).

### 2. The Verification Crisis: Claim-Level Collapse (Phases B & C: Exp 04–10)
- **Embedding Similarity Fails as a Verifier**: High cosine similarity ($\approx 0.77$) occurred even on explicit contradictions, proving semantic similarity cannot verify factual truth (`Exp-04`, `Exp-06`).
- **The DeBERTa Illusion**: `cross-encoder/nli-deberta-v3-base` achieved an outstanding 96.43% accuracy on isolated, pre-segmented claim-evidence triples (`Exp-06`).
- **Catastrophic Live RAG Collapse**: When deployed on live RAG outputs, DeBERTa classified **15/15 sentence claims as NEUTRAL (100% failure rate)** (`Exp-07`).
- **The Dual Bottleneck**:
  1. *Premise Dilution*: Evaluating a 15-word claim against a 400-word retrieved chunk diffused cross-attention across irrelevant background text.
  2. *Token Truncation*: 57.3% of chunk-claim pairs exceeded DeBERTa's 512-token context limit, silently discarding supporting evidence.
- **Failed Remediation Attempts**:
  - *Atomic Claim Decomposition* (`Exp-08`): Resulted in 90.9% Neutral, stripped necessary grammatical qualifiers, and generated false contradictions.
  - *Latency Explosion* (`Exp-09`): Query 41 took **84.98 seconds** end-to-end (50 NLI forward passes taking 57.88s), proving claim-level decomposition computationally prohibitive.
  - *Micro-Unit Evidence Splitting* (`Exp-10`): Splitting chunks into 3-sentence units created 18 context-loss regressions and kept Neutral at 80.5%.

### 3. The Architecture Paradigm Shift & Final Benchmark (Phase D: Exp 11–17)
- **ModernCE Context Upgrade**: Upgrading to `dleemiller/ModernCE-base-nli` (ModernBERT architecture, 2,048 tokens) completely eliminated token truncation (0.0% truncated) and recovered 38 grounded pairs from Neutral to Entailed (`Exp-11`).
- **Complete-Answer Multi-Chunk Verification**: Rather than decomposing answers into fragile propositions, verifying the **complete answer** against **concatenated top retrieved chunks** solved premise dilution and enabled multi-chunk context synergy (Query 1 entailment jumped from 0.348 to 0.914) while collapsing forward passes from 50+ to 1–3 passes (`Exp-12`).
- **Definitive 50-Question Benchmark**: On the 50 production queries (48 substantive content answers + 2 explicit abstentions), the verifier achieved **93.75% Entailment (45 / 48)**:
  - 38 answers entailed at Top-2 stage (79.17%).
  - 7 answers recovered at Top-3 stage (14.58%).
  - 3 persistent Neutral answers (6.25%).
  - 0 false contradictions detected (`Exp-13`).
- **Production Integration & Optimization**: Integrated into `verification_1/verifier.py` with 100% parity (50/50 status agreement), saving 14 evaluations via regex-based abstention filtering (`Exp-14`) and capping progressive search at TOP_3 (`Exp-15`).

## Key Scientific Caveats & Metric Integrity
1. **Entailment $\ne$ Factual Accuracy**: The 93.75% result is an *automated NLI entailment rate against retrieved chunks*. It establishes that the generated answers logically derive from the retrieved textbook context.
2. **Human Annotation Pending**: Inspection of `outputs/manual_annotation_50q.json` confirms all 50 `manual_label` entries remain empty strings (`""`). Independent human-verified factual accuracy has not yet been collected.
3. **Subclaim Masking Trade-Off**: Complete-answer verification evaluates holistic entailment. While fast and robust, it can potentially mask an unsupported secondary clause if the primary claim strongly dominates.
