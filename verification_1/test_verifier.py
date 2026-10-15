"""
Unit & Integration Tests for ModernCE Ranked Progressive NLI Complete-Answer Verifier (verification_1/verifier.py).

Tests:
1. Entailment at comparison 1 stops immediately.
2. Entailment at comparison 2 stops immediately.
3. Entailment at comparison 3 stops immediately.
4. Entailment at comparison 4 stops immediately.
5. If comparison 3 produces the best non-entailment result and comparison 4 is weaker, comparison 3's result is retained.
6. If comparison 4 produces the best result, comparison 4's result is retained.
7. Contradiction and neutral are handled according to the existing verdict mapping.
8. Chunks are ranked by individual entailment probability before concatenation.
9. Original chunk identifiers and evidence metadata remain correct.
10. Explicit abstention bypasses NLI.
11. Fewer than four chunks are handled safely.
12. Existing callers continue to receive the expected output schema.
"""

import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from typing import Any, Dict, List

from verification_1.verifier import (
    ModernCEVerifier,
    VerificationResult,
    verify_answer,
    is_abstention_answer,
    STATUS_SUPPORTED,
    STATUS_INSUFFICIENT_EVIDENCE,
    STATUS_CONTRADICTED,
    STATUS_NOT_FOUND,
    VERDICT_ENTAILED_BY_TOP1,
    VERDICT_ENTAILED_BY_TOP2,
    VERDICT_ENTAILED_BY_TOP3,
    VERDICT_ENTAILED_BY_TOP4,
    VERDICT_NOT_ENTAILED,
    VERDICT_ABSTENTION,
    get_verifier,
)

project_root = Path(__file__).resolve().parent.parent


def make_nli_return(entail_p: float, neutral_p: float, contra_p: float, pred_label: str) -> Dict[str, Any]:
    """Helper to generate mock return dictionary from _evaluate_pair."""
    return {
        "token_count": 128,
        "is_truncated": False,
        "raw_logits": [0.0, 0.0, 0.0],
        "entailment_prob": round(entail_p, 4),
        "neutral_prob": round(neutral_p, 4),
        "contradiction_prob": round(contra_p, 4),
        "predicted_label": pred_label,
        "eval_time_sec": 0.005,
    }


class TestMockedRankedProgressiveVerifier(unittest.TestCase):
    """
    Mocked NLI unit tests validating all 12 Task 22 requirements for
    ranked progressive complete-answer verification.
    """

    def setUp(self):
        # Create verifier with mock model bundle to avoid heavy model loads in mock tests
        mock_tokenizer = MagicMock()
        mock_model = MagicMock()
        mock_label_map = {"contradiction": 0, "entailment": 1, "neutral": 2}
        self.verifier = ModernCEVerifier(model_bundle=(mock_tokenizer, mock_model, mock_label_map))
        
        self.sample_chunks = [
            {"chunk_number": 1, "chunk_id": "c1", "section": "Sec 1", "pages": "10-12", "hybrid_score": 0.03, "text": "Evidence chunk 1 text."},
            {"chunk_number": 2, "chunk_id": "c2", "section": "Sec 2", "pages": "20-22", "hybrid_score": 0.02, "text": "Evidence chunk 2 text."},
            {"chunk_number": 3, "chunk_id": "c3", "section": "Sec 3", "pages": "30-32", "hybrid_score": 0.01, "text": "Evidence chunk 3 text."},
            {"chunk_number": 4, "chunk_id": "c4", "section": "Sec 4", "pages": "40-42", "hybrid_score": 0.01, "text": "Evidence chunk 4 text."},
            {"chunk_number": 5, "chunk_id": "c5", "section": "Sec 5", "pages": "50-52", "hybrid_score": 0.01, "text": "Evidence chunk 5 text."},
        ]
        self.sample_answer = "The generated answer explaining the psychological phenomenon."

    @patch("verification_1.verifier._evaluate_pair")
    def test_1_entailment_at_comparison_1_stops_immediately(self, mock_eval):
        """1. Entailment at comparison 1 stops immediately (comparison count = 1)."""
        # Step 1 individual evaluations: Chunk 1 has entailment (0.85)
        # 5 individual calls + 0 multi-chunk calls because Comp 1 reuses top-1 individual score
        mock_eval.side_effect = [
            make_nli_return(0.85, 0.14, 0.01, "entailment"),  # chunk 1
            make_nli_return(0.10, 0.89, 0.01, "neutral"),     # chunk 2
            make_nli_return(0.05, 0.94, 0.01, "neutral"),     # chunk 3
            make_nli_return(0.02, 0.97, 0.01, "neutral"),     # chunk 4
            make_nli_return(0.01, 0.98, 0.01, "neutral"),     # chunk 5
        ]

        res = self.verifier.verify(answer=self.sample_answer, retrieved_chunks=self.sample_chunks)

        self.assertEqual(res.status, STATUS_SUPPORTED)
        self.assertEqual(res.verdict, VERDICT_ENTAILED_BY_TOP1)
        self.assertEqual(res.combination_used, "TOP_1")
        self.assertEqual(res.selected_chunk_numbers, [1])
        self.assertEqual(res.entailment_prob, 0.85)
        self.assertEqual(len(res.progressive_evaluations), 1)
        self.assertEqual(res.timing_breakdown["num_progressive_comparisons"], 1)
        self.assertEqual(mock_eval.call_count, 5)  # 5 individual, 0 subsequent multi-chunk

    @patch("verification_1.verifier._evaluate_pair")
    def test_2_entailment_at_comparison_2_stops_immediately(self, mock_eval):
        """2. Entailment at comparison 2 stops immediately (comparison count = 2)."""
        # 5 individual (all neutral) + 1 for Comp 2 (entailment)
        mock_eval.side_effect = [
            make_nli_return(0.40, 0.59, 0.01, "neutral"),     # chunk 1
            make_nli_return(0.35, 0.64, 0.01, "neutral"),     # chunk 2
            make_nli_return(0.20, 0.79, 0.01, "neutral"),     # chunk 3
            make_nli_return(0.10, 0.89, 0.01, "neutral"),     # chunk 4
            make_nli_return(0.05, 0.94, 0.01, "neutral"),     # chunk 5
            make_nli_return(0.92, 0.07, 0.01, "entailment"),  # Comp 2 (C1+C2)
        ]

        res = self.verifier.verify(answer=self.sample_answer, retrieved_chunks=self.sample_chunks)

        self.assertEqual(res.status, STATUS_SUPPORTED)
        self.assertEqual(res.verdict, VERDICT_ENTAILED_BY_TOP2)
        self.assertEqual(res.combination_used, "TOP_2")
        self.assertEqual(res.selected_chunk_numbers, [1, 2])
        self.assertEqual(res.entailment_prob, 0.92)
        self.assertEqual(len(res.progressive_evaluations), 2)
        self.assertEqual(res.timing_breakdown["num_progressive_comparisons"], 2)
        self.assertEqual(mock_eval.call_count, 6)  # 5 individual + 1 Comp 2

    @patch("verification_1.verifier._evaluate_pair")
    def test_3_entailment_at_comparison_3_stops_immediately(self, mock_eval):
        """3. Entailment at comparison 3 stops immediately (comparison count = 3)."""
        # 5 individual (all neutral) + 1 for Comp 2 (neutral) + 1 for Comp 3 (entailment)
        mock_eval.side_effect = [
            make_nli_return(0.30, 0.69, 0.01, "neutral"),     # chunk 1
            make_nli_return(0.25, 0.74, 0.01, "neutral"),     # chunk 2
            make_nli_return(0.20, 0.79, 0.01, "neutral"),     # chunk 3
            make_nli_return(0.15, 0.84, 0.01, "neutral"),     # chunk 4
            make_nli_return(0.10, 0.89, 0.01, "neutral"),     # chunk 5
            make_nli_return(0.45, 0.54, 0.01, "neutral"),     # Comp 2 (C1+C2)
            make_nli_return(0.88, 0.11, 0.01, "entailment"),  # Comp 3 (C1+C2+C3)
        ]

        res = self.verifier.verify(answer=self.sample_answer, retrieved_chunks=self.sample_chunks)

        self.assertEqual(res.status, STATUS_SUPPORTED)
        self.assertEqual(res.verdict, VERDICT_ENTAILED_BY_TOP3)
        self.assertEqual(res.combination_used, "TOP_3")
        self.assertEqual(res.selected_chunk_numbers, [1, 2, 3])
        self.assertEqual(res.entailment_prob, 0.88)
        self.assertEqual(len(res.progressive_evaluations), 3)
        self.assertEqual(res.timing_breakdown["num_progressive_comparisons"], 3)
        self.assertEqual(mock_eval.call_count, 7)  # 5 indiv + 1 Comp 2 + 1 Comp 3

    @patch("verification_1.verifier._evaluate_pair")
    def test_4_entailment_at_comparison_4_stops_immediately(self, mock_eval):
        """4. Entailment at comparison 4 stops immediately (comparison count = 4)."""
        # 5 individual (all neutral) + 1 for Comp 2 (neutral) + 1 for Comp 3 (neutral) + 1 for Comp 4 (entailment)
        mock_eval.side_effect = [
            make_nli_return(0.20, 0.79, 0.01, "neutral"),     # chunk 1
            make_nli_return(0.18, 0.81, 0.01, "neutral"),     # chunk 2
            make_nli_return(0.15, 0.84, 0.01, "neutral"),     # chunk 3
            make_nli_return(0.12, 0.87, 0.01, "neutral"),     # chunk 4
            make_nli_return(0.10, 0.89, 0.01, "neutral"),     # chunk 5
            make_nli_return(0.35, 0.64, 0.01, "neutral"),     # Comp 2 (C1+C2)
            make_nli_return(0.48, 0.51, 0.01, "neutral"),     # Comp 3 (C1+C2+C3)
            make_nli_return(0.91, 0.08, 0.01, "entailment"),  # Comp 4 (C1+C2+C3+C4)
        ]

        res = self.verifier.verify(answer=self.sample_answer, retrieved_chunks=self.sample_chunks)

        self.assertEqual(res.status, STATUS_SUPPORTED)
        self.assertEqual(res.verdict, VERDICT_ENTAILED_BY_TOP4)
        self.assertEqual(res.combination_used, "TOP_4")
        self.assertEqual(res.selected_chunk_numbers, [1, 2, 3, 4])
        self.assertEqual(res.entailment_prob, 0.91)
        self.assertEqual(len(res.progressive_evaluations), 4)
        self.assertEqual(res.timing_breakdown["num_progressive_comparisons"], 4)
        self.assertEqual(mock_eval.call_count, 8)  # 5 indiv + 3 multi-chunk

    @patch("verification_1.verifier._evaluate_pair")
    def test_5_comp3_best_non_entailment_retained_over_weaker_comp4(self, mock_eval):
        """5. If comparison 3 produces the best non-entailment result and comparison 4 is weaker, comparison 3 is retained."""
        # 5 individual (all neutral) + Comp 2 (neutral 0.35) + Comp 3 (neutral 0.48) + Comp 4 (neutral 0.30, diluted/weaker)
        mock_eval.side_effect = [
            make_nli_return(0.20, 0.79, 0.01, "neutral"),     # chunk 1
            make_nli_return(0.18, 0.81, 0.01, "neutral"),     # chunk 2
            make_nli_return(0.15, 0.84, 0.01, "neutral"),     # chunk 3
            make_nli_return(0.12, 0.87, 0.01, "neutral"),     # chunk 4
            make_nli_return(0.10, 0.89, 0.01, "neutral"),     # chunk 5
            make_nli_return(0.35, 0.64, 0.01, "neutral"),     # Comp 2 (0.35)
            make_nli_return(0.48, 0.51, 0.01, "neutral"),     # Comp 3 (0.48 -> BEST)
            make_nli_return(0.30, 0.68, 0.02, "neutral"),     # Comp 4 (0.30 -> WEAKER)
        ]

        res = self.verifier.verify(answer=self.sample_answer, retrieved_chunks=self.sample_chunks)

        self.assertEqual(res.status, STATUS_INSUFFICIENT_EVIDENCE)
        self.assertEqual(res.verdict, VERDICT_NOT_ENTAILED)
        self.assertEqual(res.combination_used, "TOP_3")  # Comp 3 retained!
        self.assertEqual(res.selected_chunk_numbers, [1, 2, 3])
        self.assertEqual(res.entailment_prob, 0.48)
        self.assertEqual(len(res.progressive_evaluations), 4)  # All 4 ran
        self.assertEqual(res.timing_breakdown["num_progressive_comparisons"], 4)

    @patch("verification_1.verifier._evaluate_pair")
    def test_6_comp4_best_non_entailment_retained(self, mock_eval):
        """6. If comparison 4 produces the best result, comparison 4's result is retained."""
        # 5 individual (all neutral) + Comp 2 (0.20) + Comp 3 (0.30) + Comp 4 (0.49 -> BEST)
        mock_eval.side_effect = [
            make_nli_return(0.10, 0.89, 0.01, "neutral"),     # chunk 1
            make_nli_return(0.08, 0.91, 0.01, "neutral"),     # chunk 2
            make_nli_return(0.06, 0.93, 0.01, "neutral"),     # chunk 3
            make_nli_return(0.04, 0.95, 0.01, "neutral"),     # chunk 4
            make_nli_return(0.02, 0.97, 0.01, "neutral"),     # chunk 5
            make_nli_return(0.20, 0.79, 0.01, "neutral"),     # Comp 2
            make_nli_return(0.30, 0.69, 0.01, "neutral"),     # Comp 3
            make_nli_return(0.49, 0.50, 0.01, "neutral"),     # Comp 4 (BEST)
        ]

        res = self.verifier.verify(answer=self.sample_answer, retrieved_chunks=self.sample_chunks)

        self.assertEqual(res.status, STATUS_INSUFFICIENT_EVIDENCE)
        self.assertEqual(res.verdict, VERDICT_NOT_ENTAILED)
        self.assertEqual(res.combination_used, "TOP_4")  # Comp 4 retained!
        self.assertEqual(res.selected_chunk_numbers, [1, 2, 3, 4])
        self.assertEqual(res.entailment_prob, 0.49)
        self.assertEqual(len(res.progressive_evaluations), 4)

    @patch("verification_1.verifier._evaluate_pair")
    def test_7_contradiction_and_neutral_verdict_mapping(self, mock_eval):
        """7. Contradiction and neutral are handled according to the existing verdict mapping."""
        # 7A: Mixed contradiction and neutral -> Neutral (INSUFFICIENT_EVIDENCE) is preferred over Contradiction
        mock_eval.side_effect = [
            make_nli_return(0.05, 0.15, 0.80, "contradiction"),  # chunk 1
            make_nli_return(0.25, 0.70, 0.05, "neutral"),        # chunk 2 (higher entailment, neutral)
            make_nli_return(0.02, 0.97, 0.01, "neutral"),        # chunk 3
            make_nli_return(0.01, 0.98, 0.01, "neutral"),        # chunk 4
            make_nli_return(0.01, 0.98, 0.01, "neutral"),        # chunk 5
            make_nli_return(0.10, 0.20, 0.70, "contradiction"),  # Comp 2
            make_nli_return(0.15, 0.20, 0.65, "contradiction"),  # Comp 3
            make_nli_return(0.20, 0.20, 0.60, "contradiction"),  # Comp 4
        ]

        res_7a = self.verifier.verify(answer=self.sample_answer, retrieved_chunks=self.sample_chunks)
        # Comp 1 was neutral with entail=0.25 (chunk 2 was ranked 1st due to higher entailment 0.25 > 0.05)
        self.assertEqual(res_7a.status, STATUS_INSUFFICIENT_EVIDENCE)
        self.assertEqual(res_7a.verdict, VERDICT_NOT_ENTAILED)
        self.assertEqual(res_7a.combination_used, "TOP_1")

        # 7B: All comparisons are contradiction -> Status is CONTRADICTED
        mock_eval.side_effect = [
            make_nli_return(0.05, 0.10, 0.85, "contradiction"),  # chunk 1
            make_nli_return(0.04, 0.10, 0.86, "contradiction"),  # chunk 2
            make_nli_return(0.03, 0.10, 0.87, "contradiction"),  # chunk 3
            make_nli_return(0.02, 0.10, 0.88, "contradiction"),  # chunk 4
            make_nli_return(0.01, 0.10, 0.89, "contradiction"),  # chunk 5
            make_nli_return(0.08, 0.12, 0.80, "contradiction"),  # Comp 2 (least contradiction / highest entailment)
            make_nli_return(0.05, 0.10, 0.85, "contradiction"),  # Comp 3
            make_nli_return(0.03, 0.07, 0.90, "contradiction"),  # Comp 4
        ]

        res_7b = self.verifier.verify(answer=self.sample_answer, retrieved_chunks=self.sample_chunks)
        self.assertEqual(res_7b.status, STATUS_CONTRADICTED)
        self.assertEqual(res_7b.verdict, VERDICT_NOT_ENTAILED)
        self.assertEqual(res_7b.combination_used, "TOP_2")

    @patch("verification_1.verifier._evaluate_pair")
    def test_8_chunks_ranked_by_individual_entailment_prob(self, mock_eval):
        """8. Chunks are ranked by individual entailment probability before concatenation."""
        # Chunk 4 has highest entailment (0.75), Chunk 2 is second (0.60), Chunk 5 is third (0.45)
        mock_eval.side_effect = [
            make_nli_return(0.10, 0.89, 0.01, "neutral"),     # chunk 1
            make_nli_return(0.60, 0.39, 0.01, "neutral"),     # chunk 2 (rank 2)
            make_nli_return(0.20, 0.79, 0.01, "neutral"),     # chunk 3 (rank 4)
            make_nli_return(0.75, 0.24, 0.01, "neutral"),     # chunk 4 (rank 1)
            make_nli_return(0.45, 0.54, 0.01, "neutral"),     # chunk 5 (rank 3)
            make_nli_return(0.95, 0.04, 0.01, "entailment"),  # Comp 2 (C4+C2, i.e. chunks [2, 4])
        ]

        res = self.verifier.verify(answer=self.sample_answer, retrieved_chunks=self.sample_chunks)

        self.assertEqual(res.ranked_chunk_numbers, [4, 2, 5, 3, 1])
        self.assertEqual(res.status, STATUS_SUPPORTED)
        self.assertEqual(res.verdict, VERDICT_ENTAILED_BY_TOP2)
        self.assertEqual(res.combination_used, "TOP_2")
        self.assertEqual(res.selected_chunk_numbers, [2, 4])  # Preserves retrieval order in subset

    @patch("verification_1.verifier._evaluate_pair")
    def test_9_original_chunk_identifiers_and_metadata_preserved(self, mock_eval):
        """9. Original chunk identifiers and evidence metadata remain correct."""
        mock_eval.side_effect = [
            make_nli_return(0.90, 0.09, 0.01, "entailment"),  # chunk 1
            make_nli_return(0.10, 0.89, 0.01, "neutral"),
            make_nli_return(0.05, 0.94, 0.01, "neutral"),
            make_nli_return(0.02, 0.97, 0.01, "neutral"),
            make_nli_return(0.01, 0.98, 0.01, "neutral"),
        ]

        res = self.verifier.verify(answer=self.sample_answer, retrieved_chunks=self.sample_chunks)

        self.assertEqual(len(res.individual_chunk_evaluations), 5)
        self.assertEqual(res.individual_chunk_evaluations[0]["chunk_id"], "c1")
        self.assertEqual(res.individual_chunk_evaluations[0]["section"], "Sec 1")
        self.assertEqual(res.individual_chunk_evaluations[0]["pages"], "10-12")
        self.assertEqual(res.individual_chunk_evaluations[1]["chunk_id"], "c2")
        self.assertEqual(res.individual_chunk_evaluations[1]["pages"], "20-22")
        self.assertEqual(res.selected_chunk_ids, ["c1"])

    def test_10_explicit_abstention_bypasses_nli(self):
        """10. Explicit abstention bypasses NLI (comparison count = 0)."""
        abstention_texts = [
            "Not found in the provided textbook.",
            "Information was not found in the provided textbook.",
            "Not found",
        ]

        for ans in abstention_texts:
            self.assertTrue(is_abstention_answer(ans))
            res = self.verifier.verify(answer=ans, retrieved_chunks=self.sample_chunks)
            self.assertEqual(res.status, STATUS_NOT_FOUND)
            self.assertEqual(res.verdict, VERDICT_ABSTENTION)
            self.assertTrue(res.is_abstention)
            self.assertIsNone(res.combination_used)
            self.assertEqual(len(res.individual_chunk_evaluations), 0)
            self.assertEqual(len(res.progressive_evaluations), 0)
            self.assertEqual(res.timing_breakdown["num_progressive_comparisons"], 0)

    @patch("verification_1.verifier._evaluate_pair")
    def test_11_fewer_than_four_chunks_handled_safely(self, mock_eval):
        """11. Fewer than four chunks are handled safely (e.g. 2 chunks -> max comparisons = 2)."""
        two_chunks = self.sample_chunks[:2]
        mock_eval.side_effect = [
            make_nli_return(0.30, 0.69, 0.01, "neutral"),  # chunk 1
            make_nli_return(0.20, 0.79, 0.01, "neutral"),  # chunk 2
            make_nli_return(0.40, 0.59, 0.01, "neutral"),  # Comp 2 (C1+C2)
        ]

        res = self.verifier.verify(answer=self.sample_answer, retrieved_chunks=two_chunks)

        self.assertEqual(len(res.progressive_evaluations), 2)  # Limited to 2 chunks
        self.assertEqual(res.timing_breakdown["num_progressive_comparisons"], 2)
        self.assertEqual(res.combination_used, "TOP_2")
        self.assertEqual(res.status, STATUS_INSUFFICIENT_EVIDENCE)
        self.assertEqual(res.verdict, VERDICT_NOT_ENTAILED)

    @patch("verification_1.verifier._evaluate_pair")
    def test_12_output_schema_compatibility(self, mock_eval):
        """12. Existing callers continue to receive the expected output schema."""
        mock_eval.side_effect = [
            make_nli_return(0.40, 0.59, 0.01, "neutral"),     # chunk 1
            make_nli_return(0.35, 0.64, 0.01, "neutral"),     # chunk 2
            make_nli_return(0.20, 0.79, 0.01, "neutral"),     # chunk 3
            make_nli_return(0.10, 0.89, 0.01, "neutral"),     # chunk 4
            make_nli_return(0.05, 0.94, 0.01, "neutral"),     # chunk 5
            make_nli_return(0.92, 0.07, 0.01, "entailment"),  # Comp 2
        ]

        res = self.verifier.verify(answer=self.sample_answer, retrieved_chunks=self.sample_chunks)
        d = res.to_dict()

        # Check all expected fields in schema
        expected_keys = [
            "status", "verdict", "is_abstention", "combination_used",
            "entailment_prob", "neutral_prob", "contradiction_prob", "predicted_label",
            "selected_chunk_numbers", "selected_chunk_ids",
            "individual_chunk_evaluations", "ranked_chunk_numbers",
            "top_2_evaluation", "top_3_evaluation", "progressive_evaluations",
            "total_nli_time_sec", "explanation", "timing_breakdown"
        ]
        for k in expected_keys:
            self.assertIn(k, d, f"Missing key '{k}' in VerificationResult.to_dict()")

        # Test top-level verify_answer alias
        mock_eval.side_effect = [
            make_nli_return(0.95, 0.04, 0.01, "entailment"),
            make_nli_return(0.10, 0.89, 0.01, "neutral"),
        ]
        res_alias = verify_answer(answer=self.sample_answer, retrieved_chunks=self.sample_chunks[:2], verifier=self.verifier)
        self.assertEqual(res_alias.status, STATUS_SUPPORTED)


if __name__ == "__main__":
    unittest.main()

