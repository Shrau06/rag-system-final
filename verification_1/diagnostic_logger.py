"""
verification_1: Diagnostic Timing & Workload Logger

Records granular, structured timing and workload telemetry per query to investigate
variable latency across retrieval, LLM generation, API retries, and ModernCE verification.
"""

import os
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

DEFAULT_DIAGNOSTIC_LOG_PATH = Path(__file__).resolve().parent / "output" / "diagnostic_timing_log.jsonl"


def build_diagnostic_record(
    query_id: str,
    question: str,
    answer: str,
    total_wall_clock_sec: float,
    retrieval_sec: float,
    generation_sec: float,
    citation_sec: float,
    verification_sec: float,
    snapshot_sec: float,
    api_metrics: Optional[Dict[str, Any]] = None,
    verification_data: Optional[Dict[str, Any]] = None,
    retrieved_chunks: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """
    Builds a standardized diagnostic record containing stage durations,
    API retry details, verification workload counts, and token counts.
    """
    # Safe preview (avoiding large textbook passages)
    q_preview = question.strip()
    if len(q_preview) > 120:
        q_preview = q_preview[:117] + "..."

    # Extract API telemetry
    api_info = api_metrics or {}
    attempts_list = api_info.get("attempts", [])
    total_attempts = api_info.get("total_attempts", len(attempts_list) if attempts_list else 1)
    total_api_wait = api_info.get("total_api_wait_sec", generation_sec)
    total_retry_sleep = api_info.get("total_retry_sleep_sec", 0.0)

    # Extract verification telemetry
    v_data = verification_data or {}
    t_breakdown = v_data.get("timing_breakdown") or {}

    num_retrieved = len(retrieved_chunks) if retrieved_chunks is not None else v_data.get("num_retrieved_chunks", 0)
    indiv_eval_time = t_breakdown.get("individual_eval_time_sec", 0.0)
    top2_eval_time = t_breakdown.get("top2_eval_time_sec", 0.0)
    top3_eval_time = t_breakdown.get("top3_eval_time_sec", 0.0)
    model_load_time = t_breakdown.get("model_load_time_sec", 0.0)
    total_nli_inference = v_data.get("total_nli_time_sec", t_breakdown.get("total_nli_time_sec", 0.0))

    # Compute prompt / completion token metrics from last successful API attempt if available
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    for att in attempts_list:
        if att.get("success"):
            prompt_tokens = att.get("prompt_tokens", 0)
            completion_tokens = att.get("completion_tokens", 0)
            total_tokens = att.get("total_tokens", prompt_tokens + completion_tokens)

    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "query_id": str(query_id),
        "question_preview": q_preview,
        "timings": {
            "total_wall_clock_sec": round(float(total_wall_clock_sec), 4),
            "retrieval_sec": round(float(retrieval_sec), 4),
            "generation_sec": round(float(generation_sec), 4),
            "citation_sec": round(float(citation_sec), 4),
            "verification_sec": round(float(verification_sec), 4),
            "snapshot_sec": round(float(snapshot_sec), 4),
        },
        "api_telemetry": {
            "total_attempts": int(total_attempts),
            "total_api_wait_sec": round(float(total_api_wait), 4),
            "total_retry_sleep_sec": round(float(total_retry_sleep), 4),
            "attempts": attempts_list,
        },
        "verification_telemetry": {
            "model_name": "dleemiller/ModernCE-base-nli",
            "device": "cpu",
            "model_load_time_sec": round(float(model_load_time), 4),
            "num_retrieved_chunks": int(num_retrieved),
            "num_individual_evaluations": int(t_breakdown.get("num_individual_evaluations", 0)),
            "individual_eval_total_sec": round(float(indiv_eval_time), 4),
            "individual_chunk_token_counts": t_breakdown.get("individual_chunk_token_counts", []),
            "ran_top2": bool(t_breakdown.get("ran_top2", False)),
            "top2_eval_sec": round(float(top2_eval_time), 4),
            "top2_token_count": int(t_breakdown.get("top2_token_count", 0)),
            "ran_top3": bool(t_breakdown.get("ran_top3", False)),
            "top3_eval_sec": round(float(top3_eval_time), 4),
            "top3_token_count": int(t_breakdown.get("top3_token_count", 0)),
            "total_nli_inference_sec": round(float(total_nli_inference), 4),
            "final_status": v_data.get("status", "UNKNOWN"),
            "final_verdict": v_data.get("verdict", "UNKNOWN"),
            "is_abstention": bool(v_data.get("is_abstention", False)),
        },
        "workload_metrics": {
            "answer_char_length": len(answer) if answer else 0,
            "answer_completion_tokens": int(completion_tokens),
            "prompt_tokens": int(prompt_tokens),
            "total_tokens": int(total_tokens),
        },
    }

    return record


def log_diagnostic_record(
    record: Dict[str, Any],
    log_path: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Appends one structured JSONL record to the diagnostic log file.
    Creates parent directories automatically.
    """
    target_path = Path(log_path).resolve() if log_path else DEFAULT_DIAGNOSTIC_LOG_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with open(target_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return target_path
