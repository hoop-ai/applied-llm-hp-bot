"""Two-stage retrieval with hybrid dense+BM25 blend on stage 2.

Stage 1 — exact-question cache: embed query, search Index A (questions only).
If top-1 cosine similarity >= THRESHOLD_A, return the stored answer directly.
No LLM call.

Stage 2 — passages for the LLM: blend dense (cosine) and BM25 scores into a
single ranking, return top-K texts as the context block.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np

from .indexer import Bundle, _embed, _tokenize


@dataclass
class StageAHit:
    answer: str
    matched_question: str
    similarity: float


@dataclass
class StageBHit:
    texts: list[str]
    dense_scores: list[float]
    bm25_scores: list[float]
    blended_scores: list[float]


def stage_a(query: str, bundle: Bundle, threshold: float | None = None) -> StageAHit | None:
    if threshold is None:
        threshold = float(os.getenv("THRESHOLD_A", "0.85"))
    vec = _embed(bundle.model, [query])
    scores, idx = bundle.index_a.search(vec, k=1)
    top_score = float(scores[0][0])
    top_idx = int(idx[0][0])
    if top_score >= threshold:
        return StageAHit(
            answer=bundle.answers_a[top_idx],
            matched_question=bundle.questions_a[top_idx],
            similarity=top_score,
        )
    return None


def _normalize(arr: np.ndarray) -> np.ndarray:
    """Min-max scale into [0, 1]. Flat arrays become zeros."""
    if arr.size == 0:
        return arr
    lo, hi = float(arr.min()), float(arr.max())
    if hi - lo < 1e-9:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)


def stage_b(query: str, bundle: Bundle, top_k: int | None = None, alpha: float = 0.7) -> StageBHit:
    """Hybrid retrieval. alpha weights dense vs BM25 (alpha=1 → dense only)."""
    if top_k is None:
        top_k = int(os.getenv("TOP_K_B", "5"))

    n = len(bundle.texts_b)
    fetch = min(n, top_k * 4)  # over-fetch then re-rank

    # Dense
    vec = _embed(bundle.model, [query])
    dense_scores, dense_idx = bundle.index_b.search(vec, k=fetch)
    dense_scores = dense_scores[0]
    dense_idx = dense_idx[0]

    # BM25 over the same corpus
    bm25_all = np.array(bundle.bm25.get_scores(_tokenize(query)), dtype="float32")

    # Build a per-document score: dense for the fetched indices, BM25 for all.
    dense_full = np.full(n, fill_value=float("-inf"), dtype="float32")
    for s, i in zip(dense_scores, dense_idx):
        dense_full[int(i)] = float(s)
    # Replace -inf with the minimum of the fetched dense scores so normalize works
    if np.isfinite(dense_full).any():
        min_finite = dense_full[np.isfinite(dense_full)].min()
        dense_full[~np.isfinite(dense_full)] = min_finite

    dense_norm = _normalize(dense_full)
    bm25_norm = _normalize(bm25_all)
    blended = alpha * dense_norm + (1 - alpha) * bm25_norm

    order = np.argsort(-blended)[:top_k]
    return StageBHit(
        texts=[bundle.texts_b[int(i)] for i in order],
        dense_scores=[float(dense_full[int(i)]) for i in order],
        bm25_scores=[float(bm25_all[int(i)]) for i in order],
        blended_scores=[float(blended[int(i)]) for i in order],
    )
