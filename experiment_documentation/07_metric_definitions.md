# 07: Metric Definitions & Interpretation Guidelines

This reference defines all mathematical metrics, evaluation targets, units of analysis, and common interpretation pitfalls across the project.

---

## 1. Document Extraction & Ingestion Metrics

### Vocabulary F1
- **Definition**: Harmonic mean of unigram precision and recall between the extracted textbook tokens and reference gold tokenization.
- **Formula**:
  $$\text{Precision} = \frac{|V_{ext} \cap V_{ref}|}{|V_{ext}|}, \quad \text{Recall} = \frac{|V_{ext} \cap V_{ref}|}{|V_{ref}|}, \quad F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$
- **Unit**: Percentage (0–100%).
- **Interpretation**: Measures word-level vocabulary preservation and freedom from character-level OCR corruption.

### 3-gram F1
- **Definition**: Harmonic mean of precision and recall over consecutive 3-token sequences (trigrams).
- **Unit**: Percentage (0–100%).
- **Interpretation**: Measures local syntactic and phrase-level ordering integrity.

### Key-Term Preservation
- **Definition**: Recall of domain-specific glossary terms, abbreviations, and chemical/biological nomenclature in the extracted text.
- **Unit**: Percentage (0–100%).

---

## 2. Retrieval Evaluation Metrics

### Hit Rate @ K (Recall @ K)
- **Definition**: Percentage of test queries where at least one ground-truth relevant chunk is retrieved in the top $K$ candidates.
- **Formula**:
  $$\text{Hit Rate}@K = \frac{1}{|Q|} \sum_{q \in Q} \mathbb{I}(\text{rank}(d_q^*) \le K)$$
- **Unit**: Percentage (0–100%).

### Mean Reciprocal Rank (MRR)
- **Definition**: Average of reciprocal ranks of the first relevant retrieved document across queries.
- **Formula**:
  $$\text{MRR} = \frac{1}{|Q|} \sum_{q \in Q} \frac{1}{\text{rank}_q}$$
- **Unit**: Scalar between 0.0 and 1.0 (higher is better).

### Reciprocal Rank Fusion (RRF)
- **Definition**: Rank aggregation score combining rankings from multiple retrieval modalities without score calibration.
- **Formula**:
  $$RRF(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
  where $k=60$, $M = \{\text{Dense}, \text{BM25}\}$, and $r_m(d)$ is the 1-indexed rank of chunk $d$ in system $m$.

---

## 3. RAG Generation Quality Metrics

### Semantic Similarity (Cosine)
- **Definition**: Cosine similarity between embedding vectors of the generated answer ($\vec{a}$) and human reference answer ($\vec{r}$).
- **Formula**:
  $$\text{Cosine Sim}(\vec{a}, \vec{r}) = \frac{\vec{a} \cdot \vec{r}}{\|\vec{a}\|_2 \|\vec{r}\|_2}$$
- **Unit**: Scalar between -1.0 and 1.0 (typically 0.40–0.95).
- **CRITICAL CAVEAT**: **Semantic similarity is NOT factual accuracy.** An answer with high semantic similarity ($\approx 0.82$) can state the exact opposite of reality while retaining high similarity due to shared terminology.

### Token-level F1
- **Definition**: Word-level token overlap between generated answer and reference answer after stripping stop words and punctuation.
- **Unit**: Scalar between 0.0 and 1.0.

---

## 4. Hallucination Verification & NLI Metrics

### NLI Entailment Probability $P(\text{Entailment})$
- **Definition**: The softmax probability assigned by a cross-encoder model to the Entailment class given premise $P$ and hypothesis $H$.
- **Formula**:
  $$P(\text{Class} = c \mid P, H) = \frac{\exp(z_c)}{\sum_{j \in \{E, N, C\}} \exp(z_j)}$$
- **Unit**: Probability between 0.0 and 1.0.

### Entailment Rate (%)
- **Definition**: Percentage of evaluated answers classified as Entailed ($P(E) \ge 0.60$) by the verification model.
- **Formula**:
  $$\text{Entailment Rate} = \frac{\text{Count of Entailed Answers}}{\text{Total Substantive Content Answers}}$$
- **CRITICAL CAVEAT**: In Exp-13, the reported result **93.75% (45 / 48)** is an **entailment rate against retrieved chunks**, NOT independent proof of factual truth!

### Accuracy (NLI Benchmark)
- **Definition**: Fraction of labeled test pairs where model prediction matches the ground truth annotation.
- **Unit**: Percentage (0–100%).

### Macro F1 (NLI Benchmark)
- **Definition**: Unweighted arithmetic mean of per-class F1 scores across Entailment, Neutral, and Contradiction.
- **Formula**:
  $$\text{Macro } F_1 = \frac{F_{1,\text{Entail}} + F_{1,\text{Neutral}} + F_{1,\text{Contra}}}{3}$$
- **Unit**: Scalar between 0.0 and 1.0.

---

## 5. Verification Operational Metrics

### Production Parity Agreement (%)
- **Definition**: Percentage of queries where the modular production verifier (`verifier.py`) produces identical classification verdicts and stopping stages as the standalone benchmark script.
- **Result**: **100.0% (50 / 50 queries)**.
- **Caveat**: Parity validates implementation correctness against the experiment; it does not measure external world truth.

### Token Truncation Rate (%)
- **Definition**: Percentage of evaluated input pairs where the combined (premise + hypothesis) token length exceeds the model's maximum sequence length limit ($L_{\text{max}}$), resulting in truncation of context during inference.
- **Formula**:
  $$\text{Truncation Rate} = \left( \frac{\text{Number of pairs exceeding } L_{\text{max}}}{\text{Total pairs evaluated}} \right) \times 100$$
- **Measurement Methodology**: Pairs are first tokenized with `truncation=False` to measure their true combined sequence length. Any pair with token count $> L_{\text{max}}$ (e.g., 512 for DeBERTa, 2,048 for ModernCE) is recorded as truncated; during inference, the tokenizer truncates the input to $L_{\text{max}}$.
- **Important Distinction**: This measures the **percentage of evaluated pairs affected by truncation**, NOT the percentage of individual tokens discarded.
- **Observed Values**:
  - Live RAG Sentence-Level Pairs (Exp 06 / Repo Exp 07): **61.9% (65 / 105 pairs)** on DeBERTa ($L_{\text{max}} = 512$).
  - Live RAG Atomic Claim Pairs (Exp 07 & 10 / Repo Exp 08 & 11): **57.3% (126 / 220 pairs)** on DeBERTa ($L_{\text{max}} = 512$).
  - 3-Sentence Micro-Unit Pairs (Exp 09 / Repo Exp 10): **0.0% (0 / 220 pairs)** on DeBERTa ($L_{\text{max}} = 512$).
  - ModernCE-base-nli Pairs (Exp 10 / Repo Exp 11): **0.0% (0 / 220 pairs)** on ModernCE ($L_{\text{max}} = 2,048$).

### Context-Loss Regression Rate (%)
- **Definition**: Percentage of evaluated pairs where fine-grained micro-unit segmentation severs inter-sentence discourse structure, causing a claim that was Entailed against a full chunk to drop to Neutral against micro-units.
- **Formula**:
  $$\text{Regression Rate} = \left( \frac{\text{Number of } E \to N \text{ transitions caused by severed discourse}}{\text{Total pairs evaluated}} \right) \times 100$$
- **Classification Distinction**:
  1. **Genuine Context Loss**: Antecedent qualifiers, definitions, or coreference links located in adjacent sentences are split across micro-unit boundaries, rendering the isolated micro-unit insufficient to entail the claim.
  2. **Distractor / Noise Shift**: A spurious or incidental entailment on an irrelevant chunk disappears because irrelevant surrounding text is excluded.
- **Observed Values (Exp 09 / Repo Exp 10)**:
  - **DeBERTa Top-1 Micro-Units**: **0.45% (1 / 220 pairs)** (Claim `5_C2` on Chunk 3).
  - **ModernCE Top-2 Micro-Units**: **8.18% (18 / 220 pairs)** total transitions, comprising:
    - **Genuine Context-Loss Regressions**: **5.91% (13 / 220 pairs)**.
    - **Distractor / Spurious Noise Reductions**: **2.27% (5 / 220 pairs)**.
- **Important Distinction**: **Token truncation and context-loss regressions are fundamentally different mechanisms**. Truncation is an architectural sequence length overflow ($>512$ tokens), whereas context-loss regressions stem from artificial boundaries cutting interdependent sentences.

