import sys
import json
import time
from pathlib import Path
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from verification_1.verifier import verify_answer, get_verifier
from components.verification_view import render_verification_block


def parse_context_file(filepath: Path):
    import re
    content = filepath.read_text(encoding="utf-8")
    blocks = re.split(r"--- Chunk (\d+) ---", content)
    chunks = []
    for i in range(1, len(blocks), 2):
        cnum = int(blocks[i])
        cbody = blocks[i+1].strip()
        sec_m = re.search(r"Section:\s*(.+)", cbody)
        pages_m = re.search(r"Pages:\s*(.+)", cbody)
        raw_m = re.search(r"Raw Text:\s*\n(.*)", cbody, re.DOTALL)
        chunks.append({
            "chunk_number": cnum,
            "section": sec_m.group(1).strip() if sec_m else "Unknown",
            "pages": pages_m.group(1).strip() if pages_m else "?",
            "text": raw_m.group(1).strip() if raw_m else ""
        })
    return chunks


def test_ui_cases():
    print("=" * 80)
    print("STREAMLIT UI INTEGRATION VALIDATION: 4 REAL TEST CASES")
    print("=" * 80)

    verifier = get_verifier()
    df_sub = pd.read_csv(project_root / "outputs" / "submission.csv")
    with open(project_root / "data" / "queries.json", "r", encoding="utf-8") as f:
        queries = json.load(f)

    # -------------------------------------------------------------
    # TEST 1: Top-2 Supported
    # -------------------------------------------------------------
    print("\n[TEST 1] Top-2 Supported Case")
    q1_text = "What is the scientific method in psychology?"
    q1_ans = str(df_sub.iloc[0]["answer"])
    q1_chunks = parse_context_file(project_root / "outputs" / "retrieved_contexts" / "1.txt")
    
    t0 = time.perf_counter()
    v1 = verifier.verify(answer=q1_ans, retrieved_chunks=q1_chunks, query=q1_text)
    t1 = time.perf_counter() - t0

    print(f"  Question       : {q1_text}")
    print(f"  Status         : {v1.status}")
    print(f"  Verdict        : {v1.verdict}")
    print(f"  Comb Used      : {v1.combination_used}")
    print(f"  Selected Chunks: {v1.selected_chunk_numbers}")
    print(f"  Entailment Prob: {v1.entailment_prob:.4f}")
    print(f"  Verification s : {t1:.2f} s")
    assert v1.status == "SUPPORTED", f"Expected SUPPORTED, got {v1.status}"
    assert v1.combination_used in ["TOP_1", "TOP_2"], \
        f"Expected TOP_1 or TOP_2, got {v1.combination_used}"
    print(f"  -> TEST 1 PASSED: 🟢 Supported by textbook ({v1.combination_used})")

    # -------------------------------------------------------------
    # TEST 2: Top-3 Supported (Recovery)
    # -------------------------------------------------------------
    print("\n[TEST 2] Top-3 Supported Case (Recovery)")
    q41_text = "What is the role of neurotransmitters in mental health?"
    q41_ans = str(df_sub.iloc[40]["answer"])
    q41_chunks = parse_context_file(project_root / "outputs" / "retrieved_contexts" / "41.txt")
    
    t0 = time.perf_counter()
    v41 = verifier.verify(answer=q41_ans, retrieved_chunks=q41_chunks, query=q41_text)
    t2 = time.perf_counter() - t0

    print(f"  Question       : {q41_text}")
    print(f"  Status         : {v41.status}")
    print(f"  Verdict        : {v41.verdict}")
    print(f"  Comb Used      : {v41.combination_used}")
    print(f"  Selected Chunks: {v41.selected_chunk_numbers}")
    print(f"  Entailment Prob: {v41.entailment_prob:.4f}")
    print(f"  Verification s : {t2:.2f} s")
    assert v41.status == "SUPPORTED", f"Expected SUPPORTED, got {v41.status}"
    assert v41.combination_used in ["TOP_1", "TOP_2", "TOP_3"], \
        f"Expected TOP_1, TOP_2, or TOP_3, got {v41.combination_used}"
    print(f"  -> TEST 2 PASSED: 🟢 Supported by textbook ({v41.combination_used})")

    # -------------------------------------------------------------
    # TEST 3: Abstention
    # -------------------------------------------------------------
    print("\n[TEST 3] Explicit Abstention Case")
    q48_text = "What is the difference between mood disorders and personality disorders?"
    q48_ans = str(df_sub.iloc[47]["answer"])
    q48_chunks = parse_context_file(project_root / "outputs" / "retrieved_contexts" / "48.txt")
    
    t0 = time.perf_counter()
    v48 = verifier.verify(answer=q48_ans, retrieved_chunks=q48_chunks, query=q48_text)
    t3 = time.perf_counter() - t0

    print(f"  Question       : {q48_text}")
    print(f"  Status         : {v48.status}")
    print(f"  Verdict        : {v48.verdict}")
    print(f"  Abstention Flag: {v48.is_abstention}")
    print(f"  Comb Used      : {v48.combination_used}")
    print(f"  Verification s : {t3:.4f} s (NLI Bypassed)")
    assert v48.status == "NOT_FOUND", f"Expected NOT_FOUND, got {v48.status}"
    assert v48.is_abstention is True, "Expected is_abstention=True"
    print("  -> TEST 3 PASSED: ⚪ Not found in textbook (Bypassed NLI)")

    # -------------------------------------------------------------
    # TEST 4: Normal RAG Question
    # -------------------------------------------------------------
    print("\n[TEST 4] Normal RAG Question Case")
    q3_text = str(queries[2]["question"])
    q3_ans = str(df_sub.iloc[2]["answer"])
    q3_chunks = parse_context_file(project_root / "outputs" / "retrieved_contexts" / "3.txt")
    
    t0 = time.perf_counter()
    v3 = verifier.verify(answer=q3_ans, retrieved_chunks=q3_chunks, query=q3_text)
    t4 = time.perf_counter() - t0

    print(f"  Question       : {q3_text}")
    print(f"  Status         : {v3.status}")
    print(f"  Verdict        : {v3.verdict}")
    print(f"  Comb Used      : {v3.combination_used}")
    print(f"  Selected Chunks: {v3.selected_chunk_numbers}")
    print(f"  Entailment Prob: {v3.entailment_prob:.4f}")
    print(f"  Verification s : {t4:.2f} s")
    assert v3.status in ["SUPPORTED", "INSUFFICIENT_EVIDENCE"], f"Unexpected status {v3.status}"
    print("  -> TEST 4 PASSED: Standard RAG verification completed seamlessly")

    print("\n" + "=" * 80)
    print("ALL 4 REAL TEST CASES VALIDATED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    test_ui_cases()
