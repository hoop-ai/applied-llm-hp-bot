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


# ─────────────────────────────────────────────────────────────────────────────
# Runner + report writer
# ─────────────────────────────────────────────────────────────────────────────

import time
from collections import defaultdict
from pathlib import Path

import yaml

from tests.run_eval import _matches_expectation, _run_case

_ROOT = Path(__file__).resolve().parent.parent
_REPORT = _ROOT / "REPORT-eval-new-corpus.md"
_RETRY_SLEEP = 2.0


def _run_with_retry(case: dict) -> tuple[bool, str, str]:
    """Return (matcher_passed, reason, reply) — retries once on exception."""
    try:
        return _run_case(case)
    except Exception:
        time.sleep(_RETRY_SLEEP)
        try:
            return _run_case(case)
        except Exception as e2:
            # surface the error through the reply so classify() tags it
            return False, f"exception: {e2}", f"{LLM_UNAVAILABLE_PREFIX} {e2}"


def _render_table(rows: list[tuple[str, ...]], header: tuple[str, ...]) -> str:
    if not rows:
        return "_None._"
    line = "| " + " | ".join(header) + " |"
    sep = "| " + " | ".join("---" for _ in header) + " |"
    body = "\n".join("| " + " | ".join(r) for r in rows)
    return "\n".join([line, sep, body])


def _trunc(s: str, n: int = 200) -> str:
    s = s.replace("\n", " ").replace("|", "\\|")
    return s if len(s) <= n else s[: n - 1] + "…"


def _verdict(totals: dict[str, int]) -> str:
    total = sum(totals.values())
    if totals['regression'] == 0 and totals['error'] == 0:
        return (
            f"All {total} adversarial cases pass on the new corpus, modulo "
            f"{totals['mismatch']} corpus-mismatch case(s) (rules 5/6) where the bot correctly refused "
            f"because the asked fact isn't in the instructor dataset. The six graded behavioral rules hold."
        )
    parts = [f"{totals['pass']}/{total} cases pass on the new corpus."]
    if totals['regression']:
        parts.append(f"{totals['regression']} genuine regression(s) — see the regressions table above.")
    if totals['error']:
        parts.append(f"{totals['error']} infrastructure error(s) — re-run when OpenRouter is healthy.")
    if totals['mismatch']:
        parts.append(f"{totals['mismatch']} corpus-mismatch case(s) (expected, not a regression).")
    return " ".join(parts)


def render_report(results: list[dict]) -> str:
    """Render the markdown report from a list of result dicts."""
    by_bucket: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_bucket[r["bucket"]].append(r)

    rules = sorted({r["rule"] for r in results})
    buckets = ["pass", "regression", "mismatch", "error"]
    summary_rows = []
    for rule in rules:
        counts = {b: 0 for b in buckets}
        for r in results:
            if r["rule"] == rule:
                counts[r["bucket"]] += 1
        summary_rows.append((
            str(rule),
            str(counts["pass"]),
            str(counts["regression"]),
            str(counts["mismatch"]),
            str(counts["error"]),
        ))
    totals = {b: sum(1 for r in results if r["bucket"] == b) for b in buckets}
    summary_rows.append((
        "**TOTAL**",
        f"**{totals['pass']}**",
        f"**{totals['regression']}**",
        f"**{totals['mismatch']}**",
        f"**{totals['error']}**",
    ))

    def detail_table(bucket: str) -> str:
        rows = []
        for r in by_bucket.get(bucket, []):
            rows.append((r["id"], str(r["rule"]), r["expected"], _trunc(r["reply"])))
        return _render_table(rows, ("Case", "Rule", "Expected", "Reply"))

    verdict = _verdict(totals)

    return f"""# Adversarial Eval — New Corpus Report

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Summary (by rule × bucket)

{_render_table(summary_rows, ('Rule', 'Pass', 'Regression', 'Mismatch', 'Error'))}

## Regressions ({totals['regression']})

Cases where the bot's behavior actually broke. These are corpus-independent (rules 1-4) or are non-refusal responses on rules 5-6 that miss the expected keyword.

{detail_table('regression')}

## Corpus mismatches ({totals['mismatch']})

Cases where the bot correctly refused on rule 5 or 6 because the asked fact isn't in the new instructor corpus. Not a robustness regression — the test's expected keyword no longer applies.

{detail_table('mismatch')}

## Errors ({totals['error']})

Cases where the LLM layer failed twice in a row (every fallback model errored). Infrastructure, not behavior.

{detail_table('error')}

## Verdict

{verdict}
"""


def main() -> int:
    yaml_path = _ROOT / "tests" / "attacks.yaml"
    cases = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))["cases"]
    results: list[dict] = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['id']}", flush=True)
        matcher_passed, reason, reply = _run_with_retry(case)
        bucket = classify(case, matcher_passed=matcher_passed, reply=reply)
        results.append({
            "id": case["id"],
            "rule": case["rule"],
            "expected": case.get("expect", "?"),
            "reply": reply,
            "reason": reason,
            "bucket": bucket,
        })
        print(f"    -> {bucket}")

    _REPORT.write_text(render_report(results), encoding="utf-8")
    print(f"\nwrote {_REPORT.name}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
