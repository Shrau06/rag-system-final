# RAG & Hallucination Verification Experiment Documentation

Welcome to the comprehensive, academically defensible documentation of the **RAG System with Hallucination Verification Layer**.

This documentation reconstructs the empirical development of the project across **17 distinct experiments**, tracing the technical evolution from initial PDF ingestion and retrieval parameter optimization to controlled NLI benchmarking, the claim-level verification crisis, and the ultimate architectural breakthrough using `ModernCE-base-nli` complete-answer progressive verification.

---

## Folder Organization

```
experiment_documentation/
├── README.md                           # This navigation guide
├── 00_executive_summary.md             # High-level project summary and key findings
├── 01_project_build_flow.md            # Visual build flow and chronological narrative
├── 02_master_experiment_chronology.md  # Master table of all 17 experiments
├── 03_experiment_details/              # Detailed documentation for all 17 experiments
│   ├── exp01_extraction_quality.md
│   ├── exp02_retrieval_optimization.md
│   ├── exp03_baseline_rag_generation.md
│   ├── exp04_verification_pilot_v1.md
│   ├── exp05_verification_pilot_v2.md
│   ├── exp06_280_triple_benchmark.md
│   ├── exp07_sentence_level_verification.md
│   ├── exp08_atomic_claim_decomposition.md
│   ├── exp09_latency_diagnostic.md
│   ├── exp10_evidence_granularity.md
│   ├── exp11_nli_model_comparison.md
│   ├── exp12_complete_answer_multichunk.md
│   ├── exp13_modernce_50q_benchmark.md
│   ├── exp14_production_parity.md
│   ├── exp15_progressive_verification_timing.md
│   ├── exp16_grounding_stability.md
│   └── exp17_ui_and_annotation_setup.md
├── 04_cross_experiment_comparisons.md  # 8 analytical cross-experiment syntheses & latency
├── 05_final_architecture.md            # Traceability matrix and production pipeline
├── 06_limitations_and_future_work.md   # Scientific boundaries and roadmap
├── 07_metric_definitions.md            # Mathematical formulas and interpretation rules
├── 08_artifact_index.md                # Repository-wide inventory of all raw artifacts
├── tables/                             # Source-backed CSV tables
│   ├── master_experiment_summary.csv
│   ├── retrieval_results.csv
│   ├── verification_benchmarks.csv
│   ├── claim_level_results.csv
│   ├── latency_comparison.csv
│   └── progressive_verification_results.csv
├── figures/                            # Publication-grade PNG figures (300 DPI)
│   ├── retrieval/
│   ├── baseline_rag/
│   ├── claim_level/
│   ├── model_comparison/
│   ├── complete_answer/
│   ├── latency/
│   └── final_system/
├── scripts/                            # Self-contained reproduction & validation scripts
│   ├── generate_figures.py             # Regenerates all 21 figures without API calls
│   └── validate_documentation.py       # Validates file integrity, links, and CSVs
└── evidence/
    └── evidence_manifest.json          # Machine-readable mapping of all evidence
```

---

## How to Regenerate Figures Without Running Pipelines

All figures can be reproduced directly from saved CSV and JSON artifacts without calling external APIs or executing model inference:

```bash
# From repository root:
python experiment_documentation/scripts/generate_figures.py
```
This script reads strictly saved artifacts and writes 21 publication-grade figures (300 DPI) into `experiment_documentation/figures/`.

---

## How to Validate the Documentation Suite

To verify that all 17 experiment pages exist, all figures resolve, all CSV tables parse cleanly, and no original project files have been altered:

```bash
# From repository root:
python experiment_documentation/scripts/validate_documentation.py
```

---

## Primary Original Artifacts Supplying the Results

| Phase | Key Finding | Primary Source Artifact |
| :--- | :--- | :--- |
| **Phase A** | PDF Ingestion & Extraction Quality | `evaluation_results.json` |
| **Phase A** | Candidate $K=15$ & Hybrid RRF Ablation | `outputs/experiments/final_k_selection/retrieval_analysis.json` |
| **Phase A** | Baseline RAG Generation Benchmark ($K=7$) | `outputs/experiments/final_k_comparison/final_k_comparison_report.md` |
| **Phase B** | Similarity Failure & DeBERTa 96.4% on 280 Triples | `verification_1/output/verifier_280_evaluation_report.md` |
| **Phase C** | 100% Neutral Failure on Sentence Claims | `verification_1/output/multichunk_pilot_1_5_report.md` |
| **Phase C** | 90.9% Neutral Failure on Atomic Claims | `verification_1/output/multichunk_pilot_atomic_1_5_report.md` |
| **Phase C** | Query 41 Latency Diagnostic (84.98s) | `verification_1/output/query41_granularity_test.json` |
| **Phase C** | Micro-Unit Evidence Fragmentation (18 Regressions) | `verification_1/output/evidence_granularity_diagnostic.json` |
| **Phase D** | DeBERTa Truncation (57.3%) vs ModernCE (0.0%) | `verification_1/output/q1_q5_nli_comparison.json` |
| **Phase D** | Complete Answer Multi-Chunk Synergy | `verification_1/output/complete_answer_multichunk_q1_q5_report.md` |
| **Phase D** | 50-Question Benchmark (45/48 Entailed = 93.75%) | `verification_1/output/modernce_50q_complete_answer/results.json` |
| **Phase D** | Production Parity (100% Status Agreement) | `verification_1/output/modernce_50q_production_validation/comparison_report.md` |
| **Phase D** | UI Integration Tests (4/4 Passed) | `tests/test_ui.py` |
| **Phase D** | Manual Annotation Schema (Labels Empty) | `outputs/manual_annotation_50q.json` |

---

## Critical Scientific Distinction: What Remains Uncertain

- **Entailment vs Factual Truth**: The benchmark result of **93.75% (45 / 48)** is an *NLI entailment rate against retrieved chunks*. It measures whether generated answers logically derive from the retrieved textbook context.
- **Human Annotation Pending**: In `outputs/manual_annotation_50q.json`, all 50 `manual_label` entries remain empty strings (`""`). Independent human-verified factual accuracy has not yet been collected.
