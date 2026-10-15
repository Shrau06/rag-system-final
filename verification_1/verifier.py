"""
verification_1: Production-Ready ModernCE Complete-Answer Multi-Chunk Verifier

Evaluates whether a complete generated RAG answer is supported by retrieved textbook
evidence using long-context ModernBERT cross-encoder NLI (dleemiller/ModernCE-base-nli)
with ranked, progressive evidence concatenation.

Architecture:
  Generated Answer + Retrieved Chunks
  1. Check for explicit abstention ("Not found in textbook") -> return NOT_FOUND status.
  2. Score individual chunks against complete answer via ModernCE.
  3. Rank chunks by entailment probability descending (tie-broken stably).
  4. Progressive Evidence Concatenation:
     - Comparison 1: C1
     - Comparison 2: C1 + C2
     - Comparison 3: C1 + C2 + C3
     - Comparison 4: C1 + C2 + C3 + C4
  5. If any comparison predicts ENTAILMENT -> immediately return SUPPORTED (ENTAILED_BY_TOP{k}).
  6. If no comparison predicts ENTAILMENT -> select the best non-entailment result across
     comparisons 1..M according to explicit score rule (neutral preferred over contradiction,
     higher entailment probability, lower contradiction probability).
"""

import sys
import time
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure project root is in sys.path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from verification_1.modern_nli_matcher import (
    MODERN_NLI_MODEL_NAME,
    MODERN_NLI_ID2LABEL,
    MODERN_NLI_LABEL_MAP,
    DEFAULT_MAX_LENGTH,
    get_modern_nli_model,
    get_last_model_load_time_sec,
)

# ─────────────────────────────────────────────
# CONSTANTS & CONCEPTUAL STATUSES
# ─────────────────────────────────────────────

# User-facing conceptual verification statuses
STATUS_SUPPORTED = "SUPPORTED"
STATUS_INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
STATUS_CONTRADICTED = "CONTRADICTED"
STATUS_NOT_FOUND = "NOT_FOUND"

# Internal/detailed NLI verdicts
VERDICT_ENTAILED_BY_TOP1 = "ENTAILED_BY_TOP1"
VERDICT_ENTAILED_BY_TOP2 = "ENTAILED_BY_TOP2"
VERDICT_ENTAILED_BY_TOP3 = "ENTAILED_BY_TOP3"
VERDICT_ENTAILED_BY_TOP4 = "ENTAILED_BY_TOP4"
VERDICT_NOT_ENTAILED = "NOT_ENTAILED"
VERDICT_ABSTENTION = "ABSTENTION"


# ─────────────────────────────────────────────
# STRUCTURED DATA MODELS
# ─────────────────────────────────────────────

@dataclass
class ChunkScore:
    """Evaluation result for an individual retrieved evidence chunk."""
    chunk_number: int
    chunk_id: str
    section: str = "Unknown"
    pages: str = "?"
    hybrid_score: float = 0.0
    token_count: int = 0
    is_truncated: bool = False
    entailment_prob: float = 0.0
    neutral_prob: float = 0.0
    contradiction_prob: float = 0.0
    predicted_label: str = "neutral"
    eval_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MultiChunkScore:
    """Evaluation result for a combined multi-chunk premise."""
    combination_type: str  # "TOP_1", "TOP_2", "TOP_3", "TOP_4"
    selected_chunk_numbers: List[int]
    selected_chunk_ids: List[str]
    token_count: int = 0
    is_truncated: bool = False
    entailment_prob: float = 0.0
    neutral_prob: float = 0.0
    contradiction_prob: float = 0.0
    predicted_label: str = "neutral"
    eval_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationResult:
    """
    Complete structured verification output returned to callers.
    """
    status: str  # SUPPORTED, INSUFFICIENT_EVIDENCE, CONTRADICTED, NOT_FOUND
    verdict: str  # ENTAILED_BY_TOP1..4, NOT_ENTAILED, ABSTENTION
    is_abstention: bool = False
    combination_used: Optional[str] = None  # "TOP_1", "TOP_2", "TOP_3", "TOP_4", or None
    entailment_prob: float = 0.0
    neutral_prob: float = 0.0
    contradiction_prob: float = 0.0
    predicted_label: str = "neutral"
    selected_chunk_numbers: List[int] = field(default_factory=list)
    selected_chunk_ids: List[str] = field(default_factory=list)
    individual_chunk_evaluations: List[Dict[str, Any]] = field(default_factory=list)
    ranked_chunk_numbers: List[int] = field(default_factory=list)
    top_2_evaluation: Optional[Dict[str, Any]] = None
    top_3_evaluation: Optional[Dict[str, Any]] = None
    progressive_evaluations: List[Dict[str, Any]] = field(default_factory=list)
    total_nli_time_sec: float = 0.0
    explanation: str = ""
    timing_breakdown: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def is_abstention_answer(answer_text: str) -> bool:
    """
    Detects whether an answer is an explicit abstention.
    Matches standard textbook out-of-scope response phrasings.
    """
    if not answer_text or not isinstance(answer_text, str):
        return False
    norm = answer_text.strip().lower()
    if "not found in the provided textbook" in norm:
        return True
    if len(answer_text.strip()) < 50 and "not found" in norm:
        return True
    return False


def _normalize_chunk(chunk: Any, index: int) -> Dict[str, Any]:
    """
    Normalizes a chunk object from various dictionary formats (ChromaDB, parsed txt, etc.)
    into a consistent dictionary.
    """
    if isinstance(chunk, str):
        return {
            "chunk_number": index + 1,
            "chunk_id": f"chunk_{index + 1}",
            "section": "Unknown",
            "pages": "?",
            "hybrid_score": 0.0,
            "text": chunk.strip()
        }

    if not isinstance(chunk, dict):
        return {
            "chunk_number": index + 1,
            "chunk_id": f"chunk_{index + 1}",
            "section": "Unknown",
            "pages": "?",
            "hybrid_score": 0.0,
            "text": str(chunk)
        }

    chunk_num = chunk.get("chunk_number")
    if chunk_num is None:
        chunk_num = index + 1

    chunk_id = chunk.get("chunk_id") or chunk.get("id") or f"chunk_{chunk_num}"
    section = chunk.get("section") or chunk.get("section_path") or "Unknown"
    
    pages = chunk.get("pages")
    if pages is None:
        p_start = chunk.get("page_start")
        p_end = chunk.get("page_end")
        if p_start is not None and p_end is not None:
            pages = f"{p_start}-{p_end}" if p_start != p_end else str(p_start)
        else:
            pages = "?"

    hybrid_score = float(chunk.get("hybrid_score") or chunk.get("rrf_score") or chunk.get("score") or 0.0)
    raw_text = chunk.get("text") or chunk.get("raw_text") or chunk.get("content") or ""

    return {
        "chunk_number": int(chunk_num),
        "chunk_id": str(chunk_id),
        "section": str(section),
        "pages": str(pages),
        "hybrid_score": round(hybrid_score, 4),
        "text": raw_text.strip()
    }


def _evaluate_pair(
    premise: str,
    hypothesis: str,
    tokenizer: Any,
    model: Any,
    label_map: Dict[str, int],
    max_length: int = DEFAULT_MAX_LENGTH,
) -> Dict[str, Any]:
    """Evaluates NLI for a single premise-hypothesis pair using ModernBERT."""
    import torch
    import numpy as np

    t0 = time.perf_counter()
    encoded = tokenizer(
        premise,
        hypothesis,
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )

    token_count = int(encoded["input_ids"].shape[1])
    is_truncated = token_count >= max_length

    device = next(model.parameters()).device
    encoded = {k: v.to(device) for k, v in encoded.items()}

    with torch.no_grad():
        outputs = model(**encoded)
        logits = outputs.logits[0].cpu().numpy()
        probs = torch.softmax(outputs.logits[0], dim=-1).cpu().numpy()

    eval_time = time.perf_counter() - t0

    contra_idx = label_map["contradiction"]
    entail_idx = label_map["entailment"]
    neutral_idx = label_map["neutral"]

    contra_p = float(probs[contra_idx])
    entail_p = float(probs[entail_idx])
    neutral_p = float(probs[neutral_idx])

    pred_idx = int(np.argmax(probs))
    pred_label = MODERN_NLI_ID2LABEL.get(pred_idx, "unknown")

    return {
        "token_count": token_count,
        "is_truncated": is_truncated,
        "raw_logits": [round(float(x), 4) for x in logits],
        "entailment_prob": round(entail_p, 4),
        "neutral_prob": round(neutral_p, 4),
        "contradiction_prob": round(contra_p, 4),
        "predicted_label": pred_label,
        "eval_time_sec": round(eval_time, 4),
    }


def _non_entailment_score(comp: MultiChunkScore) -> Tuple[int, float, float]:
    """
    Score key for selecting the best non-entailment comparison across progressive stages:
    1. Label priority: Prefer 'neutral' (INSUFFICIENT_EVIDENCE, score 1) over 'contradiction' (CONTRADICTED, score 0).
       (A lack of sufficient evidence is considered a better/closer state to support than active factual contradiction).
    2. Entailment probability: Higher entailment_prob represents closer alignment to full evidence support.
    3. Contradiction probability: Lower contradiction_prob (-contradiction_prob) breaks ties in favor of lower conflict.
    """
    label_priority = 1 if comp.predicted_label == "neutral" else 0
    return (label_priority, comp.entailment_prob, -comp.contradiction_prob)


# ─────────────────────────────────────────────
# MAIN VERIFIER CLASS
# ─────────────────────────────────────────────

class ModernCEVerifier:
    """
    Production verifier that uses ModernBERT Cross-Encoder NLI on complete generated answers
    and ranked, progressive multi-chunk evidence aggregation (up to 4 stages).
    """

    def __init__(
        self,
        model_bundle: Optional[Tuple[Any, Any, Dict[str, int]]] = None,
        max_length: int = DEFAULT_MAX_LENGTH,
    ):
        self.max_length = max_length
        if model_bundle is None:
            self.tokenizer, self.model, self.label_map = get_modern_nli_model()
        else:
            self.tokenizer, self.model, self.label_map = model_bundle

    def is_abstention(self, answer: str) -> bool:
        """Exposes abstention detection logic."""
        return is_abstention_answer(answer)

    def verify(
        self,
        answer: str,
        retrieved_chunks: List[Any],
        query: Optional[str] = None,
    ) -> VerificationResult:
        """
        Verifies a generated answer against retrieved evidence chunks using
        ranked, progressive evidence concatenation.

        Args:
            answer: The complete original generated answer string.
            retrieved_chunks: List of retrieved chunk dictionaries or strings (typically 5-7 chunks).
            query: Optional user question for logging/context.

        Returns:
            Structured VerificationResult object.
        """
        t0_total = time.perf_counter()

        # -------------------------------------------------------------
        # 1. Check for Explicit Abstention
        # -------------------------------------------------------------
        if self.is_abstention(answer):
            total_time = time.perf_counter() - t0_total
            timing_info = {
                "model_load_time_sec": get_last_model_load_time_sec(),
                "num_retrieved_chunks": len(retrieved_chunks) if retrieved_chunks else 0,
                "num_individual_evaluations": 0,
                "individual_eval_time_sec": 0.0,
                "individual_chunk_token_counts": [],
                "num_progressive_comparisons": 0,
                "progressive_evaluations": [],
                "ran_top1": False,
                "ran_top2": False,
                "ran_top3": False,
                "ran_top4": False,
                "total_nli_time_sec": round(total_time, 4),
            }
            return VerificationResult(
                status=STATUS_NOT_FOUND,
                verdict=VERDICT_ABSTENTION,
                is_abstention=True,
                combination_used=None,
                entailment_prob=0.0,
                neutral_prob=0.0,
                contradiction_prob=0.0,
                predicted_label="abstention",
                selected_chunk_numbers=[],
                selected_chunk_ids=[],
                individual_chunk_evaluations=[],
                ranked_chunk_numbers=[],
                top_2_evaluation=None,
                top_3_evaluation=None,
                progressive_evaluations=[],
                total_nli_time_sec=round(total_time, 4),
                explanation="Answer explicitly states that information was not found in the textbook. NLI verification against retrieved chunks was safely bypassed.",
                timing_breakdown=timing_info
            )

        # -------------------------------------------------------------
        # 2. Validate Retrieved Chunks
        # -------------------------------------------------------------
        if not retrieved_chunks:
            total_time = time.perf_counter() - t0_total
            timing_info = {
                "model_load_time_sec": get_last_model_load_time_sec(),
                "num_retrieved_chunks": 0,
                "num_individual_evaluations": 0,
                "individual_eval_time_sec": 0.0,
                "individual_chunk_token_counts": [],
                "num_progressive_comparisons": 0,
                "progressive_evaluations": [],
                "ran_top1": False,
                "ran_top2": False,
                "ran_top3": False,
                "ran_top4": False,
                "total_nli_time_sec": round(total_time, 4),
            }
            return VerificationResult(
                status=STATUS_INSUFFICIENT_EVIDENCE,
                verdict=VERDICT_NOT_ENTAILED,
                is_abstention=False,
                combination_used=None,
                entailment_prob=0.0,
                neutral_prob=1.0,
                contradiction_prob=0.0,
                predicted_label="neutral",
                selected_chunk_numbers=[],
                selected_chunk_ids=[],
                individual_chunk_evaluations=[],
                ranked_chunk_numbers=[],
                top_2_evaluation=None,
                top_3_evaluation=None,
                progressive_evaluations=[],
                total_nli_time_sec=round(total_time, 4),
                explanation="No retrieved evidence chunks were provided for verification.",
                timing_breakdown=timing_info
            )

        normalized_chunks = [_normalize_chunk(c, i) for i, c in enumerate(retrieved_chunks)]

        # -------------------------------------------------------------
        # 3. Individual Chunk Evaluations & Ranking (Step 1)
        # -------------------------------------------------------------
        individual_scores: List[ChunkScore] = []
        total_nli_time = 0.0

        for chunk in normalized_chunks:
            res = _evaluate_pair(
                premise=chunk["text"],
                hypothesis=answer,
                tokenizer=self.tokenizer,
                model=self.model,
                label_map=self.label_map,
                max_length=self.max_length,
            )
            total_nli_time += res["eval_time_sec"]

            c_score = ChunkScore(
                chunk_number=chunk["chunk_number"],
                chunk_id=chunk["chunk_id"],
                section=chunk["section"],
                pages=chunk["pages"],
                hybrid_score=chunk["hybrid_score"],
                token_count=res["token_count"],
                is_truncated=res["is_truncated"],
                entailment_prob=res["entailment_prob"],
                neutral_prob=res["neutral_prob"],
                contradiction_prob=res["contradiction_prob"],
                predicted_label=res["predicted_label"],
                eval_time_sec=res["eval_time_sec"],
            )
            individual_scores.append(c_score)

        indiv_eval_total_sec = sum(c.eval_time_sec for c in individual_scores)
        indiv_token_counts = [c.token_count for c in individual_scores]

        # Rank chunks by entailment_prob descending (stable tie-break by chunk_number)
        ranked_chunks = sorted(
            individual_scores,
            key=lambda x: (x.entailment_prob, -x.chunk_number),
            reverse=True,
        )
        ranked_chunk_nums = [c.chunk_number for c in ranked_chunks]

        # -------------------------------------------------------------
        # 4. Progressive Verification Loop (Step 2)
        # -------------------------------------------------------------
        # Stages: Comparison 1 (C1), Comparison 2 (C1+C2), Comparison 3 (C1+C2+C3), Comparison 4 (C1+C2+C3+C4)
        max_stages = min(4, len(ranked_chunks))
        progressive_scores: List[MultiChunkScore] = []
        found_entailment = False
        winning_comp: Optional[MultiChunkScore] = None
        winning_k = 0

        model_load_dur = get_last_model_load_time_sec()

        for k in range(1, max_stages + 1):
            candidates = ranked_chunks[:k]
            # Preserve original retrieval order for narrative coherence
            ordered_candidates = sorted(candidates, key=lambda x: x.chunk_number)
            nums = [c.chunk_number for c in ordered_candidates]
            ids = [c.chunk_id for c in ordered_candidates]

            if k == 1:
                # Comparison 1: Single top-ranked chunk (reusing individual forward pass)
                top1_c = candidates[0]
                comp_score = MultiChunkScore(
                    combination_type="TOP_1",
                    selected_chunk_numbers=[top1_c.chunk_number],
                    selected_chunk_ids=[top1_c.chunk_id],
                    token_count=top1_c.token_count,
                    is_truncated=top1_c.is_truncated,
                    entailment_prob=top1_c.entailment_prob,
                    neutral_prob=top1_c.neutral_prob,
                    contradiction_prob=top1_c.contradiction_prob,
                    predicted_label=top1_c.predicted_label,
                    eval_time_sec=top1_c.eval_time_sec,
                )
            else:
                texts = []
                for c in ordered_candidates:
                    ch_raw = next(ch["text"] for ch in normalized_chunks if ch["chunk_number"] == c.chunk_number)
                    texts.append(ch_raw)
                premise = "\n\n".join(texts)

                res_k = _evaluate_pair(
                    premise=premise,
                    hypothesis=answer,
                    tokenizer=self.tokenizer,
                    model=self.model,
                    label_map=self.label_map,
                    max_length=self.max_length,
                )
                total_nli_time += res_k["eval_time_sec"]

                comp_score = MultiChunkScore(
                    combination_type=f"TOP_{k}",
                    selected_chunk_numbers=nums,
                    selected_chunk_ids=ids,
                    token_count=res_k["token_count"],
                    is_truncated=res_k["is_truncated"],
                    entailment_prob=res_k["entailment_prob"],
                    neutral_prob=res_k["neutral_prob"],
                    contradiction_prob=res_k["contradiction_prob"],
                    predicted_label=res_k["predicted_label"],
                    eval_time_sec=res_k["eval_time_sec"],
                )

            progressive_scores.append(comp_score)

            # Check for ENTAILMENT -> Immediate early stopping
            if comp_score.predicted_label == "entailment":
                found_entailment = True
                winning_comp = comp_score
                winning_k = k
                break

        # -------------------------------------------------------------
        # 5. Formulate Final Verdict & Result
        # -------------------------------------------------------------
        top2_dict = next((s.to_dict() for s in progressive_scores if s.combination_type == "TOP_2"), None)
        top3_dict = next((s.to_dict() for s in progressive_scores if s.combination_type == "TOP_3"), None)
        prog_dicts = [s.to_dict() for s in progressive_scores]

        if found_entailment and winning_comp is not None:
            final_status = STATUS_SUPPORTED
            final_verdict = f"ENTAILED_BY_TOP{winning_k}"
            explanation = f"Generated answer is strongly supported by Top-{winning_k} retrieved chunks {winning_comp.selected_chunk_numbers} (Entailment: {winning_comp.entailment_prob:.4f})."
            selected_comp = winning_comp
        else:
            # If no comparison predicts entailment, select best result across comparisons 1..max_stages
            best_comp = max(progressive_scores, key=_non_entailment_score)
            selected_comp = best_comp
            if best_comp.predicted_label == "contradiction":
                final_status = STATUS_CONTRADICTED
                final_verdict = VERDICT_NOT_ENTAILED
                explanation = f"Generated answer conflicts with retrieved evidence in Top-{len(best_comp.selected_chunk_numbers)} chunks {best_comp.selected_chunk_numbers} (Contradiction: {best_comp.contradiction_prob:.4f})."
            else:
                final_status = STATUS_INSUFFICIENT_EVIDENCE
                final_verdict = VERDICT_NOT_ENTAILED
                explanation = f"Retrieved evidence across progressive comparisons (best: Top-{len(best_comp.selected_chunk_numbers)} chunks {best_comp.selected_chunk_numbers}) is insufficient to fully entail the answer (Neutral: {best_comp.neutral_prob:.4f}, Entailment: {best_comp.entailment_prob:.4f})."

        timing_info = {
            "model_load_time_sec": model_load_dur,
            "num_retrieved_chunks": len(normalized_chunks),
            "num_individual_evaluations": len(individual_scores),
            "individual_eval_time_sec": round(indiv_eval_total_sec, 4),
            "individual_chunk_token_counts": indiv_token_counts,
            "num_progressive_comparisons": len(progressive_scores),
            "progressive_evaluations": prog_dicts,
            "ran_top1": any(s.combination_type == "TOP_1" for s in progressive_scores),
            "ran_top2": any(s.combination_type == "TOP_2" for s in progressive_scores),
            "ran_top3": any(s.combination_type == "TOP_3" for s in progressive_scores),
            "ran_top4": any(s.combination_type == "TOP_4" for s in progressive_scores),
            "total_nli_time_sec": round(total_nli_time, 4),
        }

        return VerificationResult(
            status=final_status,
            verdict=final_verdict,
            is_abstention=False,
            combination_used=selected_comp.combination_type,
            entailment_prob=selected_comp.entailment_prob,
            neutral_prob=selected_comp.neutral_prob,
            contradiction_prob=selected_comp.contradiction_prob,
            predicted_label=selected_comp.predicted_label,
            selected_chunk_numbers=selected_comp.selected_chunk_numbers,
            selected_chunk_ids=selected_comp.selected_chunk_ids,
            individual_chunk_evaluations=[c.to_dict() for c in individual_scores],
            ranked_chunk_numbers=ranked_chunk_nums,
            top_2_evaluation=top2_dict,
            top_3_evaluation=top3_dict,
            progressive_evaluations=prog_dicts,
            total_nli_time_sec=round(total_nli_time, 4),
            explanation=explanation,
            timing_breakdown=timing_info
        )


# Global singleton verifier instance
_GLOBAL_VERIFIER: Optional[ModernCEVerifier] = None


def get_verifier() -> ModernCEVerifier:
    """Returns a shared, lazily-initialized ModernCEVerifier instance."""
    global _GLOBAL_VERIFIER
    if _GLOBAL_VERIFIER is None:
        _GLOBAL_VERIFIER = ModernCEVerifier()
    return _GLOBAL_VERIFIER


def verify_answer(
    answer: str,
    retrieved_chunks: List[Any],
    query: Optional[str] = None,
    verifier: Optional[ModernCEVerifier] = None,
) -> VerificationResult:
    """
    Convenience function to verify a generated answer against retrieved chunks.
    """
    if verifier is None:
        verifier = get_verifier()
    return verifier.verify(answer=answer, retrieved_chunks=retrieved_chunks, query=query)


# Alias for verify_answer matching standard functional signatures
verify = verify_answer

