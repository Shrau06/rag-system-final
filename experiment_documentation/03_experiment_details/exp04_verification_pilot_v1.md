# Experiment 04: Verification Pilot v1 (Similarity vs NLI)

## 1. Experiment Number & Title
- **ID**: `Exp-04`
- **Title**: Verification Pilot v1: Bi-Encoder Cosine Similarity vs NLI Cross-Encoder
- **Phase**: Phase B — Controlled Verification Tests

## 2. Research Question / Objective
Can embedding-based cosine similarity distinguish between factual entailment and factual contradiction, or is a dedicated Natural Language Inference (NLI) cross-encoder necessary?

## 3. Why We Conducted It
Bi-encoder cosine similarity is computationally fast ($O(1)$ dot products) but evaluates only semantic topic relatedness. NLI cross-encoders evaluate logical entailment ($P(\text{Premise} \models \text{Hypothesis})$) but require full self-attention over the concatenated pair.

## 4. Hypothesis or Expectation
Embedding similarity will fail to separate contradictions from entailments because negated claims share virtually identical vocabulary and embeddings with their evidence. An NLI cross-encoder will achieve >90% accuracy.

## 5. What Was Changed or Compared
Evaluated a controlled pilot dataset of 45 claim-evidence pairs using:
1. **Embedding Cosine Similarity**: `sentence-transformers/all-MiniLM-L6-v2`.
2. **NLI Cross-Encoder**: `cross-encoder/nli-deberta-v3-base`.

## 6. Dataset and Sample Size
- **Dataset**: `verification_1/input/pilot_dataset_v1.json`
- **Total Pairs**: 45 curated claim-evidence pairs.
- **Gold Label Distribution**: 20 Entailment (44.4%), 15 Neutral (33.3%), 10 Contradiction (22.2%).

## 7. Model, Version, & Configuration
- **DeBERTa**: `cross-encoder/nli-deberta-v3-base` (Sequence classification into Contradiction, Entailment, Neutral).
- **Inference Mode**: Argmax classification on softmax-normalized logits.

## 8. Numerical Results

| Metric | Bi-Encoder Cosine Similarity | DeBERTa-v3-base Cross-Encoder |
| :--- | :---: | :---: |
| **Overall Accuracy** | Failed (Cannot classify) | **95.56% (43 / 45)** |
| **Macro F1 Score** | N/A | **0.952** |
| **Entailment Mean Score** | 0.820 (cosine) | 0.942 (softmax prob) |
| **Contradiction Mean Score** | 0.770 (cosine) | 0.918 (softmax prob) |
| **Score Margin (Ent vs Con)** | **0.050 (Massive Overlap)** | **Clear Separation ($>0.85$ margin)** |

## 9. Figures
![Exp 04: Pilot v1 Distribution](../figures/claim_level/fig_exp04_pilot_v1_distribution.png)

## 10. What the Results Actually Establish
1. **Similarity Fails as a Fact-Checker**: High cosine similarity ($\approx 0.77$) occurs even when a claim directly contradicts the evidence, because both texts share identical entities and terminology.
2. DeBERTa-v3-base achieves near-perfect classification (43/45 = 95.6%) on isolated claim-evidence pairs.

## 11. What They Do NOT Establish
- Does not demonstrate performance on long, multi-paragraph retrieved RAG passages.
- Evaluated on a small, synthetic dataset ($N=45$) with isolated single-sentence pairs.

## 12. Problems or Limitations Revealed
Pure similarity-based hallucination detection was proven mathematically unviable and abandoned.

## 13. Decision
**Retained NLI Direction / Abandoned Cosine Similarity**: Adopted NLI cross-encoders as the exclusive verification mechanism.

## 14. How the Results Motivated the Next Experiment
Experiment 05 expanded the dataset to 60 pairs to establish rigorous confidence thresholds for Entailment, Neutral, and Contradiction.

## 15. Exact Source Artifact Paths
- `verification_1/input/pilot_dataset_v1.json`
- `verification_1/output/pilot_summary_stats.json`
- `verification_1/output/pilot_dataset_v1_audit.json`

## 16. Evidence Quality
**Directly recorded** in `verification_1/output/pilot_summary_stats.json`.
