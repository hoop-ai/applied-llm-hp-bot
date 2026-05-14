# Adversarial Eval — New Corpus Report

Generated: 2026-05-14 21:05:21

## Summary (by rule × bucket)

| Rule | Pass | Regression | Mismatch | Error |
| --- | --- | --- | --- | --- |
| 1 | 8 | 0 | 0 | 0
| 2 | 6 | 0 | 0 | 0
| 3 | 6 | 0 | 0 | 0
| 4 | 10 | 0 | 0 | 0
| 5 | 5 | 0 | 0 | 0
| 6 | 5 | 0 | 0 | 0
| **TOTAL** | **40** | **0** | **0** | **0**

## Regressions (0)

Cases where the bot's behavior actually broke. These are corpus-independent (rules 1-4) or are non-refusal responses on rules 5-6 that miss the expected keyword.

_None._

## Corpus mismatches (0)

Cases where the bot correctly refused on rule 5 or 6 because the asked fact isn't in the new instructor corpus. Not a robustness regression — the test's expected keyword no longer applies.

_None._

## Errors (0)

Cases where the LLM layer failed twice in a row (every fallback model errored). Infrastructure, not behavior.

_None._

## Verdict

All 40 adversarial cases pass on the new corpus. The six graded behavioral rules hold.
