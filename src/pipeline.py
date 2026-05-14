"""End-to-end request pipeline.

guard → stage A (question cache) → stage B (hybrid retrieval) → LLM.
Used by both the Streamlit app and the evaluation harness so behavior is
identical between the two.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .guard import guard
from .indexer import get_bundle, Bundle
from .llm import call as llm_call
from .memory import Memory
from .retriever import stage_a, stage_b


@dataclass
class PipelineResult:
    answer: str
    source: str                       # "guard" | "cache" | "llm"
    debug: dict[str, Any] = field(default_factory=dict)


_BUNDLE: Bundle | None = None


def get_pipeline_bundle() -> Bundle:
    global _BUNDLE
    if _BUNDLE is None:
        _BUNDLE = get_bundle()
    return _BUNDLE


def answer(user_message: str, memory: Memory | None = None) -> PipelineResult:
    """Run one user turn through the full pipeline."""
    memory = memory or Memory()
    bundle = get_pipeline_bundle()

    # 1. Heuristic prefilter
    blocked = guard(user_message)
    if blocked is not None:
        return PipelineResult(answer=blocked, source="guard", debug={"reason": "jailbreak_pattern"})

    # 2. Stage A — exact-question cache
    a_hit = stage_a(user_message, bundle)
    if a_hit is not None:
        return PipelineResult(
            answer=a_hit.answer,
            source="cache",
            debug={
                "matched_question": a_hit.matched_question,
                "similarity": a_hit.similarity,
            },
        )

    # 3. Stage B — hybrid retrieval → LLM
    b_hit = stage_b(user_message, bundle)
    context = "\n\n---\n\n".join(b_hit.texts)
    history = memory.render()
    response = llm_call(user_message=user_message, context=context, history=history)
    return PipelineResult(
        answer=response,
        source="llm",
        debug={
            "retrieved_chunks": b_hit.texts,
            "dense_scores": b_hit.dense_scores,
            "bm25_scores": b_hit.bm25_scores,
            "blended_scores": b_hit.blended_scores,
        },
    )
