"""Unit tests for the diagnose_eval classifier (pure function, no API calls).

Run:  python -m tests.test_diagnose_classifier
Exits non-zero if any assertion fails. Matches the project's existing
plain-Python test style (see tests/run_eval.py, tests/e2e_playwright.py).
"""

from __future__ import annotations

import sys
import traceback

from src.prompts import REFUSAL
from src.pipeline import LLM_UNAVAILABLE_PREFIX
from tests.diagnose_eval import classify


def _case(rule: int, expect: str = "refuse", value: str | None = None) -> dict:
    c = {"id": f"r{rule}_x", "rule": rule, "expect": expect}
    if value is not None:
        c["value"] = value
    return c


def test_pass_is_pass_regardless_of_rule():
    for rule in range(1, 7):
        assert classify(_case(rule), matcher_passed=True, reply="anything") == "pass"


def test_rules_1_through_4_failures_are_always_regression():
    for rule in (1, 2, 3, 4):
        assert classify(_case(rule), matcher_passed=False, reply="I made something up") == "regression"
        # even when the bot refused (still a regression here — there's nothing to mismatch)
        assert classify(_case(rule), matcher_passed=False, reply=REFUSAL) == "regression"


def test_rule_5_refusal_is_mismatch():
    case = _case(5, expect="contains", value="11")
    assert classify(case, matcher_passed=False, reply=REFUSAL) == "mismatch"


def test_rule_5_non_refusal_missing_keyword_is_regression():
    case = _case(5, expect="contains", value="11")
    assert classify(case, matcher_passed=False, reply="Harry is a young wizard.") == "regression"


def test_rule_6_refusal_is_mismatch():
    case = _case(6, expect="contains", value="Hagrid")
    assert classify(case, matcher_passed=False, reply=REFUSAL) == "mismatch"


def test_rule_6_non_refusal_compliance_is_regression():
    case = _case(6, expect="contains", value="Hagrid")
    assert classify(case, matcher_passed=False, reply="oui, Hagrid is large") == "regression"


def test_unavailable_marker_is_error_for_any_rule():
    for rule in range(1, 7):
        reply = f"{LLM_UNAVAILABLE_PREFIX} OpenRouter 503"
        assert classify(_case(rule), matcher_passed=False, reply=reply) == "error"


def main() -> int:
    tests = [
        test_pass_is_pass_regardless_of_rule,
        test_rules_1_through_4_failures_are_always_regression,
        test_rule_5_refusal_is_mismatch,
        test_rule_5_non_refusal_missing_keyword_is_regression,
        test_rule_6_refusal_is_mismatch,
        test_rule_6_non_refusal_compliance_is_regression,
        test_unavailable_marker_is_error_for_any_rule,
    ]
    failures = 0
    for fn in tests:
        try:
            fn()
            print(f"  [PASS] {fn.__name__}")
        except AssertionError:
            failures += 1
            print(f"  [FAIL] {fn.__name__}")
            traceback.print_exc()
    total = len(tests)
    print(f"\n{total - failures}/{total} passed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
