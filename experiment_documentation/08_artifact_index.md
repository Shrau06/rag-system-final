# 08: Complete Artifact Index

This index inventories all experiment-related artifacts across the repository, documenting their exact relative paths, content types, provenance, and associated experiments.

| Relative File Path | File Type | Purpose & Contents | Content Classification | Original vs Derived | Associated Experiment |
| :--- | :---: | :--- | :--- | :---: | :---: |
| `evaluation_results.json` | JSON | PDF layout parsing metrics (Vocab F1, 3-gram, Key-terms) | Metrics | Derived | `Exp-01` |
| `data/processed_sections.json` | JSON | Parsed textbook sections with headings and metadata | Raw Ingestion Data | Derived | `Exp-01` |
| `outputs/experiments/final_k_selection/retrieval_analysis.json` | JSON | Candidate pool and final K evaluation on 18 queries | Metrics & Analysis | Derived | `Exp-02` |
| `outputs/experiments/final_k_selection/k_selection_report.md` | Markdown | Narrative analysis of candidate K and hybrid retrieval | Narrative Report | Derived | `Exp-02` |
| `outputs/dataset.json` | JSON | 50 benchmark textbook questions with human reference answers | Raw Eval Dataset | Original | `Exp-03` |
| `outputs/submission.csv` | CSV | 50 benchmark baseline RAG generated answers | Predictions | Derived | `Exp-03` |
| `outputs/experiments/final_k_comparison/k7/comparison_summary.json` | JSON | Generation outputs and similarity metrics for production K=7 baseline | Predictions & Metrics | Derived | `Exp-03` |
| `outputs/experiments/final_k_comparison/final_k_comparison_report.md` | Markdown | Baseline RAG generation report evaluating production K=7 context | Narrative & Metrics | Derived | `Exp-03` |
| `verification_1/input/pilot_dataset_v1.json` | JSON | 45 curated claim-evidence pairs with gold NLI labels | Labeled Dataset | Original | `Exp-04` |
| `verification_1/output/pilot_summary_stats.json` | JSON | Performance metrics of DeBERTa on Pilot v1 | Metrics | Derived | `Exp-04` |
| `verification_1/output/pilot_dataset_v1_audit.json` | JSON | Audit of similarity overlap on Pilot v1 | Metrics | Derived | `Exp-04` |
| `verification_1/input/pilot_dataset_v2.json` | JSON | 60 curated claim-evidence pairs with gold NLI labels | Labeled Dataset | Original | `Exp-05` |
| `verification_1/output/verifier_evaluation_v2.json` | JSON | Calibrated threshold evaluation results on Pilot v2 | Predictions & Metrics | Derived | `Exp-05` |
| `verification_1/final_dataset_280eg_metadata_fixed.json` | JSON | 280 curated claim-evidence triples with gold labels | Labeled Benchmark | Original | `Exp-06` |
| `verification_1/output/verifier_280_evaluation_report.md` | Markdown | Full benchmark evaluation report of DeBERTa on 280 triples | Narrative & Metrics | Derived | `Exp-06` |
| `verification_1/output/nli_280_results.csv` | CSV | Per-triple DeBERTa prediction logits and gold labels | Predictions & Labels | Derived | `Exp-06` |
| `verification_1/output/similarity_threshold_sweep.csv` | CSV | Cosine similarity accuracy across threshold sweep (0.50–0.95)| Metrics | Derived | `Exp-06` |
| `verification_1/output/multichunk_pilot_1_5_report.md` | Markdown | Report documenting the 100% Neutral failure on sentences | Narrative & Metrics | Derived | `Exp-07` |
| `verification_1/output/multichunk_pilot_1_5.json` | JSON | Sentence-level verification predictions on Q1–Q5 | Predictions | Derived | `Exp-07` |
| `verification_1/output/multichunk_pilot_atomic_1_5_report.md` | Markdown | Report documenting 90.9% Neutral on atomic claims | Narrative & Metrics | Derived | `Exp-08` |
| `verification_1/output/multichunk_pilot_atomic_1_5.json` | JSON | Atomic claim extraction outputs and DeBERTa predictions | Predictions | Derived | `Exp-08` |
| `verification_1/output/query41_granularity_test.json` | JSON | Component latency telemetry on Query 41 (84.98s total) | Timing Telemetry | Derived | `Exp-09` |
| `verification_1/output/evidence_granularity_diagnostic.json` | JSON | Evaluation of 3-sentence micro-units and context regressions | Predictions & Errors | Derived | `Exp-10` |
| `verification_1/output/q1_q5_nli_comparison.json` | JSON | Head-to-head comparison of DeBERTa vs ModernCE on 100 pairs | Predictions & Lengths | Derived | `Exp-11` |
| `verification_1/output/q1_q5_nli_comparison_report.txt` | TXT | Narrative report on truncation elimination and label shifts | Narrative Report | Derived | `Exp-11` |
| `verification_1/output/complete_answer_multichunk_q1_q5_report.md` | Markdown | Pilot report of complete-answer multi-chunk verification | Narrative & Metrics | Derived | `Exp-12` |
| `verification_1/output/complete_answer_multichunk_q1_q5.json` | JSON | Multi-chunk evaluation outputs and synergy demonstration | Predictions & Scores | Derived | `Exp-12` |
| `data/queries.json` | JSON | 50 production evaluation questions (Q1–Q50) | Raw Queries | Original | `Exp-13` |
| `verification_1/output/modernce_50q_complete_answer/experiment_report.md`| Markdown | Definitive benchmark report (93.75% entailment on 48 Qs) | Narrative & Metrics | Derived | `Exp-13` |
| `verification_1/output/modernce_50q_complete_answer/results.json` | JSON | Complete per-query verification records across 50 questions | Predictions & Metadata| Derived | `Exp-13` |
| `verification_1/output/modernce_50q_complete_answer/evaluation_summary.json`| JSON | Aggregated benchmark counts, stage distribution, and latency | Summary Metrics | Derived | `Exp-13` |
| `verification_1/output/modernce_50q_production_validation/comparison_report.md`| Markdown | 100% production parity report comparing `verifier.py` | Parity Analysis | Derived | `Exp-14` |
| `verification_1/output/modernce_50q_production_validation/results.json` | JSON | Execution output of production `RAGVerifier` on 50 questions | Predictions & Telemetry| Derived | `Exp-14` |
| `verification_1/output/diagnostic_timing_log.jsonl` | JSONL | Timestamped progressive evaluation telemetry across stages | Raw Telemetry Logs | Derived | `Exp-15` |
| `verification_1/output/task9_grounding_experiment.json` | JSON | Repeated-run grounding stability scores ($n=3$, Query 1) | Stability Telemetry | Derived | `Exp-16` |
| `tests/test_ui.py` | Python | Automated unit and integration tests for Streamlit UI | Test Code | Original | `Exp-17` |
| `outputs/manual_annotation_50q.json` | JSON | 50-query human annotation protocol (All 50 labels empty) | Annotation Template | Original | `Exp-17` |
| `verification_1/verifier.py` | Python | Modular production verifier class (`RAGVerifier`) | Source Code | Original | Production |
| `src/run_pipeline.py` | Python | Main pipeline runner with `TOP_K = 7` default | Source Code | Original | Production |
