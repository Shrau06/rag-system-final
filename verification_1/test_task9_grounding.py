# verification_1/test_task9_grounding.py

import sys
import os
import json
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root and src to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from embed_index import load_chunks, load_chroma_collection, load_embed_model
from retrieve import load_or_build_bm25, retrieve
from generate import init_client, generate_answer
from verification_1.verifier import verify_answer

def run_experiment():
    print("=" * 80)
    print("TASK 9: TESTING STRICT TEXTBOOK-GROUNDED PROMPT (3 RUNS)")
    print("=" * 80)

    # Load components
    chunks = load_chunks("cache/chunks.json")
    collection = load_chroma_collection()
    model = load_embed_model()
    bm25 = load_or_build_bm25(chunks)
    client = init_client()

    question = "How does short-term memory work?"
    print(f"\nQuestion: '{question}'")

    # Retrieve chunks once (frozen retrieval)
    retrieved = retrieve(
        query=question,
        collection=collection,
        model=model,
        bm25=bm25,
        chunks=chunks,
        top_k=7
    )

    print(f"\nRetrieved {len(retrieved)} chunks:")
    for idx, c in enumerate(retrieved[:3]):
        print(f"  [Chunk {idx+1}] Section: {c.get('section')}, Pages: {c.get('page_start')}-{c.get('page_end')}")
        print(f"    Preview: {c.get('text', '')[:160]}...")

    results = []

    for run_idx in range(1, 4):
        print(f"\n" + "-" * 60)
        print(f"RUN {run_idx} / 3: Generating Answer & Verifying...")
        print("-" * 60)

        t0_gen = time.perf_counter()
        gen_res = generate_answer(
            client=client,
            query_id=f"task9_stm_run_{run_idx}",
            question=question,
            retrieved_chunks=retrieved,
            answer_style="Standard (2-5 Sentences)"
        )
        t_gen = time.perf_counter() - t0_gen
        answer_text = gen_res["answer"]

        t0_v = time.perf_counter()
        v_res = verify_answer(
            answer=answer_text,
            retrieved_chunks=retrieved,
            query=question
        )
        t_v = time.perf_counter() - t0_v

        run_data = {
            "run": run_idx,
            "answer": answer_text,
            "status": v_res.status,
            "verdict": v_res.verdict,
            "combination_used": v_res.combination_used,
            "selected_chunks": v_res.selected_chunk_numbers,
            "entailment_prob": v_res.entailment_prob,
            "neutral_prob": v_res.neutral_prob,
            "contradiction_prob": v_res.contradiction_prob,
            "gen_time_sec": t_gen,
            "verif_time_sec": t_v
        }
        results.append(run_data)

        print(f"\n[Run {run_idx} Answer]:\n{answer_text}")
        print(f"\n[Verification Result]:")
        print(f"  Status          : {v_res.status}")
        print(f"  Verdict         : {v_res.verdict}")
        print(f"  Combination Used: {v_res.combination_used}")
        print(f"  Selected Chunks : {v_res.selected_chunk_numbers}")
        print(f"  Entailment Prob : {v_res.entailment_prob:.4f}")
        print(f"  Neutral Prob    : {v_res.neutral_prob:.4f}")
        print(f"  Contra Prob     : {v_res.contradiction_prob:.4f}")
        print(f"  Gen Time        : {t_gen:.2f}s | Verif Time: {t_v:.2f}s")

        # Small pause between API calls
        time.sleep(2)

    # Save results to output
    out_path = project_root / "verification_1" / "output" / "task9_grounding_experiment.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print("TASK 9 EXPERIMENT COMPLETED")
    print(f"Results saved to: {out_path}")
    print("=" * 80)

if __name__ == "__main__":
    run_experiment()
