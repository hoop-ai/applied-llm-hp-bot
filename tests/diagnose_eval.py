"""Diagnose adversarial-eval failures on the new corpus.

Runs every case in tests/attacks.yaml through the production pipeline, then
classifies each failure as pass / regression / mismatch / error so the report
can distinguish a real robustness regression from a corpus-mismatch artifact.

Run:    python -m tests.diagnose_eval
Output: REPORT-eval-new-corpus.md (project root)
"""

from __future__ import annotations

from src.prompts import REFUSAL
from src.pipeline import LLM_UNAVAILABLE_PREFIX

# Rules 1/2/3/4 are corpus-independent. Any matcher-fail there means the bot's
# behavior actually broke. Rules 5/6 are corpus-dependent: a clean refusal just
# means the relevant fact isn't in the new corpus, so we tag those mismatches.
_CORPUS_INDEPENDENT_RULES = {1, 2, 3, 4}


def classify(case: dict, *, matcher_passed: bool, reply: str) -> str:
    """Bucket one case into 'pass' | 'regression' | 'mismatch' | 'error'.

    Pure function; no I/O, no API calls.
    """
    if matcher_passed:
        return "pass"
    if reply.startswith(LLM_UNAVAILABLE_PREFIX):
        return "error"
    rule = case.get("rule")
    if rule in _CORPUS_INDEPENDENT_RULES:
        return "regression"
    # Rules 5 and 6: an exact refusal means the corpus simply doesn't contain
    # the fact the test is probing; not a robustness regression.
    if reply.strip() == REFUSAL:
        return "mismatch"
    return "regression"
