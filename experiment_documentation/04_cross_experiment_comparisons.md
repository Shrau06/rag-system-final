# 04: Cross-Experiment Comparisons & Analytical Insights

This document synthesizes the overarching experimental evidence, tracing how empirical findings in early experiments systematically motivated subsequent architectural decisions.

---

## 1. Retrieval Optimization & Baseline RAG Generation (Exp-01 $\rightarrow$ Exp-02 $\rightarrow$ Exp-03)

### Analytical Synthesis
Retrieval quality dictates the ceiling of downstream generation and verification. Exp-01 established that clean PDF text extraction achieved 91.8% key-term preservation across 341 pages. In Exp-02, evaluating candidate retrieval pools on 18 queries proved that setting $K_{cand}=15$ was necessary to achieve 100% retrieval hit rate. 

Furthermore, Exp-02 proved that hybrid retrieval via Reciprocal Rank Fusion ($k=60$) significantly outperformed both isolated dense retrieval (+8.7% MRR) and lexical BM25 (+20.1% MRR). When determining final prompt context size, $K=7$ achieved 98.6% keyword coverage while packing 19,322 characters—safely within the 20,000-character ceiling.

Finally, Exp-03 established the empirical baseline for end-to-end RAG generation using Llama-3.1-70B with production $K=7$ across the 50-question benchmark against human reference answers:
- Mean cosine semantic similarity reached **0.824**.
- High-similarity answers ($\ge 0.80$) comprised **66.0% (33 / 50)** of generated responses.
- Token overlap F1 reached **0.395**, with weak answers ($< 0.60$) limited to just 2 cases (4.0%).
- Average generation latency was **1.98s** per query.

| Configuration | Hit Rate (%) | MRR | Keyword Coverage (%) | Prompt Chars | Mean Sim | Weak Cases ($<0.60$) | Generation Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **BM25 Only ($K=7$)** | 83.3% | 0.584 | — | — | — | — | — |
| **Dense Only ($K=7$)** | 88.9% | 0.645 | — | — | — | — | — |
| **Hybrid RRF ($K=7$)** | **94.4%** | **0.702** | **98.6%** | **19,322** | **0.824** | **2 / 50 (4.0%)** | **1.98 s** |

![Retrieval Optimization](../figures/retrieval/fig_exp02_hybrid_ablation.png)
![Baseline RAG Generation Quality](../figures/baseline_rag/fig_exp03_baseline_rag_quality.png)

### Key Takeaway
Hybrid RRF with $K=7$ achieves 94.4% hit rate, 98.6% keyword coverage within prompt limits, and strong generation alignment (0.824 mean similarity), establishing the solid retrieval baseline (`TOP_K = 7`) upon which verification was built.

---

## 2. Embedding Cosine Similarity vs NLI Cross-Encoders (Exp-04 $\rightarrow$ Exp-06)

### Analytical Synthesis
A common naive approach to hallucination detection is measuring embedding cosine similarity between an answer and retrieved chunks. Experiments 04 and 06 conclusively proved that **cosine similarity is fundamentally incapable of acting as a factual verifier**:

1. **Massive Overlap on Contradictions**: In Exp-04, claims directly contradicting the evidence exhibited an average cosine similarity of **0.770**, overlapping heavily with entailed claims (**0.820**). Because a negated sentence shares almost all entities and nouns with its source passage, bi-encoders map them to adjacent points in vector space.
2. **Empirical Performance Ceiling**: On the 280-triple benchmark (Exp-06), sweeping similarity thresholds from 0.50 to 0.95 showed that cosine similarity peaked at an accuracy of only **61.43%** ($\tau=0.79$), with an unacceptable Contradiction F1 of **0.421**.
3. **Cross-Encoder Supremacy**: By evaluating full cross-attention over the concatenated pair, `DeBERTa-v3-base` achieved **96.43% accuracy** and a **0.963 Macro F1**, cleanly separating entailment ($P(E) > 0.94$) from contradiction ($P(C) > 0.91$).

| Verification Method | Sample Size & Dataset | Overall Accuracy | Macro F1 | Entailment F1 | Contradiction F1 | Core Failure Mode |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Cosine Similarity ($\tau=0.79$)** | 280 triples (`final_dataset_280eg`) | 61.43% | 0.587 | 0.712 | 0.421 | Fails on negation & entity swaps |
| **DeBERTa-v3-base NLI** | 280 triples (`final_dataset_280eg`) | **96.43%** | **0.963** | **0.968** | **0.969** | High compute cost on long text |

![Exp 06: DeBERTa vs Cosine Sim](../figures/claim_level/fig_exp06_280_metrics_comparison.png)

### Key Takeaway
Vector similarity measures topical relatedness, NOT truth. NLI cross-encoders are strictly mandatory for factual verification.

---

## 3. Claim-Level vs Complete-Answer Verification & Latency (Exp-07–10 vs Exp-12–14)

### Analytical Synthesis: The Architecture Paradigm Shift
While DeBERTa achieved 96.43% accuracy on isolated, pre-segmented triples, deploying it on live RAG outputs triggered a catastrophic failure:

1. **Sentence Claims (Exp-07)**: Decomposing answers into sentences yielded **100% NEUTRAL (15 / 15)** due to *premise dilution* (evaluating a 15-word claim against a 400-word chunk diffused attention) and *token truncation* (57.3% of pairs cut off at 512 tokens).
2. **Atomic Decomposition (Exp-08)**: Decomposing into 44 atomic claims did not help (**90.9% Neutral**) and stripped essential grammatical qualifiers.
3. **Evidence Micro-Units (Exp-10)**: Splitting chunks into 3-sentence micro-units under DeBERTa eliminated token truncation (57.3% $\to$ 0.0%) but premise dilution persisted (80.5% Neutral) with 1 context-loss regression (0.45%).
4. **Complete-Answer Paradigm Shift (Exp-12 & 13)**: Shifting to verifying the **complete answer** against **concatenated top chunks** under `ModernCE-base-nli` (2,048 tokens) resolved premise dilution, eliminated token truncation, and enabled multi-chunk synergy, achieving **93.75% Entailment (45 / 48)** across the 50-question benchmark.

### Detailed Latency & Computational Overhead Comparison
The computational cost differential between the two paradigms is enormous:

| Pipeline Architecture | Evaluated Condition | Sample Size & Scope | NLI Forward Passes | Claim Extraction Time | Verification NLI Time | Total Query Latency | Comparability Scope & Caveat |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Atomic Claim Decomposition** | Exp-09 (Query 41 Diagnostic) | 1 complex query (10 claims $\times$ 5 chunks) | 50 forward passes | 14.77 s | 57.88 s | **84.98 s** | Single-query worst-case complex query; includes live RAG generation (12.33s) |
| **Complete Answer Verification** | Exp-12 (Q1–Q5 Pilot) | 5 live queries | 1–3 passes / query | 0.00 s (Eliminated) | ~1.00 s / forward pass | **~2.0 – 3.0 s** | Verifier CPU execution on saved answers; excludes generation API latency |
| **Complete Answer Progressive** | Exp-13 (50Q Benchmark Avg) | 50 production queries | ~6.2 passes / query (312 total) | 0.00 s (Eliminated) | 8.33 s (benchmark avg) | **8.33 s** | Production CPU benchmark average on pre-generated answers |
| **Production Verifier (Abstention)**| Exp-14 (Parity 50Q) | 50 production queries | ~5.9 passes / query (298 total) | 0.00 s (Eliminated) | 7.85 s (benchmark avg) | **7.85 s** | Production module with regex abstention bypass saving 14 passes |

![Cross-Experiment Latency Comparison](../figures/latency/fig_cross_latency_claim_vs_complete.png)

### Key Takeaway
Claim-level decomposition required an expensive LLM extraction pass (14.77s) and 50 sequential NLI evaluations (57.88s), pushing latency to ~85s. Complete-answer verification eliminated claim extraction entirely, evaluated holistic entailment, and reduced forward passes by over **85%**.

---

## 4. DeBERTa-v3-base vs ModernCE-base-nli (Exp-11)

### Analytical Synthesis
The transition from DeBERTa to ModernCE was the technical prerequisite for multi-chunk verification:

1. **Context Window Expansion**: DeBERTa is restricted to 512 tokens. ModernCE (`dleemiller/ModernCE-base-nli`), built on ModernBERT with unpadded Flash Attention, supports sequences up to **2,048 tokens**.
2. **Elimination of Truncation**: On 100 live RAG chunk-answer pairs, DeBERTa truncated **57.3%** of pairs, hiding critical evidence located in the second half of passages. ModernCE truncated **0.0%** (maximum observed length was 1,180 tokens).
3. **Immediate Context Recovery**: Without altering the text, simply making the full context visible to ModernCE shifted **38 pairs from Neutral to Entailed**.

| Metric | `cross-encoder/nli-deberta-v3-base` | `dleemiller/ModernCE-base-nli` | Impact |
| :--- | :---: | :---: | :---: |
| **Maximum Context Window** | 512 tokens | **2,048 tokens** | $4\times$ capacity expansion |
| **Token Truncation Rate (N=100)** | 57.3% (57 / 100) | **0.0% (0 / 100)** | Complete elimination of truncation |
| **Max Observed Token Length** | 512 (hard cut) | 1,180 tokens | Accommodates 3 concatenated chunks |
| **Label Shifts (Neutral $\rightarrow$ Entailed)** | Baseline | **+38 pairs recovered** | Direct proof of truncation penalty |

![Model Comparison](../figures/model_comparison/fig_exp11_truncation_label_shift.png)

### Key Takeaway
DeBERTa's 512-token limit was a fatal bottleneck for multi-paragraph RAG. ModernCE provided the necessary context headroom to verify complete answers against multi-chunk evidence.

---

## 5. Single-Chunk vs Multi-Chunk Concatenated Evidence (Exp-12)

### Analytical Synthesis: Proving Context Synergy
In real RAG applications, generated answers rarely draw facts from a single isolated chunk; they synthesize definitions, mechanisms, and consequences across multiple retrieved passages. Exp-12 evaluated this phenomenon on Q1–Q5:

- **Single Chunk (Top-1 Alone)**: Verified only 2/5 answers (40.0%).
- **Concatenated Chunks (Top-1 + Top-2)**: Verified **4/5 answers (80.0%)**.

### Case Study: Query 1 Synergistic Concatenation
In Query 1 (*"What is the primary function of..."*):
- Evaluating Top-1 alone yielded **Neutral** ($P(E) = 0.348$) because it contained the functional mechanism but omitted the primary definition.
- Evaluating Top-2 alone yielded **Neutral** ($P(E) = 0.281$) because it contained the definition but omitted the operational mechanism.
- Evaluating Top-1 + Top-2 concatenated yielded **ENTAILED** ($P(E) = \mathbf{0.914}$).

| Evaluated Context | Content Available | $P(\text{Entailment})$ | $P(\text{Neutral})$ | Classification Verdict |
| :--- | :--- | :---: | :---: | :--- |
| **Top-1 Chunk Alone** | Operational mechanism only | 0.348 | 0.642 | Neutral (Incomplete context) |
| **Top-2 Chunk Alone** | Primary definition only | 0.281 | 0.709 | Neutral (Incomplete context) |
| **Concatenated Top-1 + Top-2** | **Joint Definition + Mechanism** | **0.914** | **0.082** | **ENTAILED (Synergistic Grounding)** |

![Exp 12: Concatenation Synergy](../figures/complete_answer/fig_exp12_multichunk_concatenation_synergy.png)

### Key Takeaway
Concatenating complementary chunks allows cross-attention to resolve cross-sentence dependencies, unlocking synergistic entailment for synthesized answers.

---

## 6. Experimental Benchmark vs Production Parity (Exp-13 $\rightarrow$ Exp-14)

### Analytical Synthesis
Experiment 14 verified whether migrating logic from the research benchmark (`evaluate_50q_modernce.py`) into the production engine (`verification_1/verifier.py`) preserved exact mathematical behavior:

- **100.0% Status Agreement**: All 50 queries received identical classifications (45 Entailed, 3 Neutral, 2 Abstentions).
- **Exact Stage Alignment**: Every query stopped at the exact same progressive stage (38 at Top-2, 7 at Top-3).
- **Abstention Efficiency**: Integrating `is_abstention_answer()` saved **14 NLI forward passes** on Q2 and Q48 by detecting out-of-scope non-retrieval answers via regex pre-checks.

| Benchmark Aspect | Experimental Script (Exp-13) | Production Engine (Exp-14) | Parity Status |
| :--- | :---: | :---: | :---: |
| **Entailed Verdicts** | 45 / 48 (93.75%) | 45 / 48 (93.75%) | Identical (100.0%) |
| **Neutral Verdicts** | 3 / 48 (6.25%) | 3 / 48 (6.25%) | Identical (100.0%) |
| **Abstention Verdicts** | 2 / 50 (4.0%) | 2 / 50 (4.0%) | Identical (100.0%) |
| **NLI Forward Passes** | 312 passes | **298 passes** | **-14 passes saved via regex bypass** |

### Key Takeaway
Production parity confirmed 100% implementation fidelity while optimizing inference latency on out-of-scope queries.

---

## 7. Progressive Verification Stopping Depth (Exp-15)

### Analytical Synthesis
Evaluating evidence progressively (TOP_1 $\rightarrow$ TOP_2 $\rightarrow$ TOP_3 $\rightarrow$ TOP_4) allows the system to exit early as soon as an entailment threshold ($P(E) \ge 0.60$) is satisfied:

- **TOP_1 Alone**: Grounded **18 queries (37.5%)** in ~1.2s.
- **TOP_2 Concatenated**: Grounded an additional **20 queries**, reaching **79.2% (38 / 48)** in ~2.3s.
- **TOP_3 Concatenated**: Recovered an additional **7 queries**, reaching **93.75% (45 / 48)** in ~3.8s.
- **TOP_4 Concatenated**: Grounded **0 additional queries**, while increasing input token length to ~1,600 and adding +1.6s latency.

![Exp 15: Progressive Stopping](../figures/complete_answer/fig_exp15_progressive_stopping_latency.png)

### Key Takeaway
TOP_3 represents the definitive point of diminishing returns. The production pipeline is strictly capped at TOP_3.

---

## 8. Model Verification vs Human Annotation (Exp-17)

### Analytical Synthesis: The Final Scientific Distinction
A rigorous scientific audit requires complete transparency regarding what has and has not been established:

1. **What Has Been Proven**: The ModernCE verifier demonstrates that **93.75% (45 / 48)** of generated substantive answers are mathematically entailed by the retrieved chunks under a cross-encoder model.
2. **What Remains Unproven**: **Independent human-verified factual accuracy has NOT yet been established**.
3. **Artifact Evidence**: Direct UTF-8 inspection of `outputs/manual_annotation_50q.json` confirms that all 50 entries have empty strings:
   ```json
   "manual_label": "",
   "manual_notes": ""
   ```

| Dimension | Automated ModernCE Verification (Exp-13) | Human Expert Annotation (Exp-17) |
| :--- | :--- | :--- |
| **Evaluator** | `dleemiller/ModernCE-base-nli` (Cross-encoder) | Domain experts (Medical/Technical) |
| **Target Evaluated** | Model-judged logical derivation from retrieved chunks | External real-world factual truth |
| **Measured Result** | **93.75% Entailment (45 / 48)** | **PENDING (0 / 50 annotated)** |
| **Artifact Path** | `verification_1/output/modernce_50q_complete_answer/results.json` | `outputs/manual_annotation_50q.json` |

### Key Takeaway
Entailment against retrieved text is an automated proxy for grounding; true ground-truth factual correctness requires expert completion of the manual annotation protocol.
