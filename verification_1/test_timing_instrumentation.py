"""
verification_1: Validation Script for Diagnostic Timing Instrumentation (Task 11)

Tests:
1. API attempt & retry tracking in src/generate.py.
2. Timing breakdown and workload fields in verification_1/verifier.py.
3. Diagnostic JSONL logger in verification_1/diagnostic_logger.py.
"""

import sys
import json
import time
from pathlib import Path
from unittest.mock import MagicMock

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.generate import call_nvidia_api, generate_answer
from verification_1.verifier import verify_answer, is_abstention_answer
from verification_1.diagnostic_logger import build_diagnostic_record, log_diagnostic_record


def test_api_attempt_instrumentation():
    print("Test 1: API Attempt & Retry Tracking...")
    
    # Mock client simulating a 429 rate limit on attempt 1, and success on attempt 2
    mock_client = MagicMock()
    
    class FakeUsage:
        prompt_tokens = 250
        completion_tokens = 45
        total_tokens = 295

    class FakeChoice:
        message = MagicMock(content="Classical conditioning is an associative learning process.")

    class FakeResponse:
        choices = [FakeChoice()]
        usage = FakeUsage()

    call_count = 0
    def mock_create(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Rate limit exceeded 429")
        return FakeResponse()

    mock_client.chat.completions.create = mock_create

    # Override time.sleep in generate for fast testing
    import src.generate as gen_mod
    orig_sleep = gen_mod.time.sleep
    gen_mod.time.sleep = lambda s: None

    try:
        sample_chunks = [{
            "chunk_id": "c1",
            "section": "6.2 Classical Conditioning",
            "section_path": "learning/classical_conditioning",
            "chapter": "Chapter 6",
            "page_start": 200,
            "page_end": 201,
            "pages": [200, 201],
            "text": "Ivan Pavlov discovered classical conditioning in dogs."
        }]

        result = generate_answer(
            client=mock_client,
            query_id="smoke_test_q1",
            question="What is classical conditioning?",
            retrieved_chunks=sample_chunks
        )

        assert "api_metrics" in result, "api_metrics missing from generate_answer result"
        api_metrics = result["api_metrics"]
        assert api_metrics["total_attempts"] == 2, f"Expected 2 attempts, got {api_metrics['total_attempts']}"
        assert api_metrics["attempts"][0]["success"] is False, "Attempt 1 should be marked failed"
        assert "429" in api_metrics["attempts"][0]["error_category"], "Attempt 1 should record 429 error category"
        assert api_metrics["attempts"][0]["retry_occurred"] is True, "Attempt 1 should record retry_occurred=True"
        assert api_metrics["attempts"][0]["retry_sleep_sec"] == 30.0, "Attempt 1 should record 30s sleep"
        assert api_metrics["attempts"][1]["success"] is True, "Attempt 2 should be marked success"
        print("  ✓ API metrics recorded properly with retry breakdown!")
    finally:
        gen_mod.time.sleep = orig_sleep


def test_verification_timing_instrumentation():
    print("Test 2: Verification Timing & Workload Breakdown...")

    # Fast test with abstention to verify timing_breakdown structure
    abstention_answer = "Not found in the provided textbook."
    v_res_abstain = verify_answer(
        answer=abstention_answer,
        retrieved_chunks=[],
        query="Out of scope question"
    )

    assert v_res_abstain.timing_breakdown is not None, "timing_breakdown missing from VerificationResult"
    assert v_res_abstain.timing_breakdown["num_retrieved_chunks"] == 0
    assert v_res_abstain.timing_breakdown["num_individual_evaluations"] == 0
    print("  ✓ Abstention verification timing breakdown verified!")


def test_diagnostic_logger():
    print("Test 3: Diagnostic Structured Logger (JSONL Output)...")
    
    test_log_path = project_root / "verification_1" / "output" / "diagnostic_timing_log.jsonl"
    
    sample_record = build_diagnostic_record(
        query_id="test_diag_001",
        question="What is classical conditioning?",
        answer="Classical conditioning is an associative learning process.",
        total_wall_clock_sec=14.523,
        retrieval_sec=0.125,
        generation_sec=8.341,
        citation_sec=0.012,
        verification_sec=6.012,
        snapshot_sec=0.033,
        api_metrics={
            "total_attempts": 1,
            "total_generation_time_sec": 8.341,
            "total_api_wait_sec": 8.340,
            "total_retry_sleep_sec": 0.0,
            "attempts": [{
                "attempt_number": 1,
                "duration_sec": 8.340,
                "success": True,
                "error_category": None,
                "retry_occurred": False,
                "retry_sleep_sec": 0.0,
                "prompt_tokens": 2850,
                "completion_tokens": 145,
                "total_tokens": 2995
            }]
        },
        verification_data={
            "status": "SUPPORTED",
            "verdict": "ENTAILED_BY_TOP2",
            "is_abstention": False,
            "total_nli_time_sec": 6.012,
            "timing_breakdown": {
                "model_load_time_sec": 0.0,
                "num_retrieved_chunks": 7,
                "num_individual_evaluations": 7,
                "individual_eval_time_sec": 4.821,
                "individual_chunk_token_counts": [350, 420, 390, 500, 460, 380, 410],
                "ran_top2": True,
                "top2_eval_time_sec": 1.191,
                "top2_token_count": 820,
                "ran_top3": False,
                "top3_eval_time_sec": 0.0,
                "top3_token_count": 0,
                "total_nli_time_sec": 6.012
            }
        },
        retrieved_chunks=[{"chunk_id": f"c{i}"} for i in range(1, 8)]
    )

    out_path = log_diagnostic_record(sample_record, test_log_path)
    assert out_path.exists(), f"Log file not created at {out_path}"

    # Verify JSON Line parsing
    with open(out_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
        last_record = json.loads(lines[-1])
        assert last_record["query_id"] == "test_diag_001"
        assert "timings" in last_record
        assert "api_telemetry" in last_record
        assert "verification_telemetry" in last_record
        assert "workload_metrics" in last_record
        assert last_record["timings"]["total_wall_clock_sec"] == 14.523

    print(f"  ✓ Diagnostic JSONL log written and verified at: {out_path}")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING TASK 11 INSTRUMENTATION TESTS")
    print("=" * 60)
    test_api_attempt_instrumentation()
    test_verification_timing_instrumentation()
    test_diagnostic_logger()
    print("=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
