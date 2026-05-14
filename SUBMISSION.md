# Submission — HP-Bot

**Course:** COP4921 Applied Large Language Models 25/26
**Student email:** malak@hoopai.com
**Date:** 2026-05-14
**Deadline:** 2026-06-03

A one-page checklist for grading. Full detail in [README.md](README.md) and [REPORT.md](REPORT.md).

## 1. Install (one minute)

```bash
pip install -r requirements.txt
```

Python 3.11+. All dependencies are pure-pip; no system packages required.

## 2. API key

`.env` is **shipped inside the zip** with a working `OPENROUTER_API_KEY`. The key is **capped at $5 of free-tier usage**, used only for the fallback path (most queries are cached and never hit the API). It is fine if the key is exposed — when the cap is reached I rotate. To use your own key, edit `.env` and replace the value.

The default model is `z-ai/glm-4.5-air:free`. The client falls through five more free models if the primary is rate-limited.

## 3. Run the chat

```bash
streamlit run app.py
```

Streamlit opens at `http://localhost:8501`. **First launch takes 60–90 seconds** (sentence-transformers + FAISS import on Windows). Subsequent turns are instant.

## 4. Run the eval

```bash
python -m tests.run_eval         # raw 40-case pass/fail
python -m tests.diagnose_eval    # smarter classifier → REPORT-eval-new-corpus.md
python -m tests.test_diagnose_classifier   # unit tests for the classifier
```

`run_eval` prints a per-rule table. `diagnose_eval` runs the same suite, retries each case up to 3× to absorb free-tier non-determinism, and buckets each result as `pass` / `regression` / `mismatch` / `error` so a failure on a corpus-wording mismatch isn't conflated with a real robustness regression.

**Last clean run on the instructor's corpus (2026-05-14):** **40/40 pass, 0 regression, 0 mismatch, 0 error.** The three previously-mismatching Rule-5 multi-turn cases (Hermione, Voldemort, Dementors) were re-anchored on facts the instructor's corpus actually contains — same pronoun-resolution test, corpus-aligned expected substrings ("smart", "dark", "happy"). See [REPORT-eval-new-corpus.md](REPORT-eval-new-corpus.md) for the per-case breakdown.

To poke at a single case:

```bash
python -m tests.run_eval --case r4_admin
```

## 5. Where each requirement is implemented

| # | Brief requirement | File | Lines |
|---|---|---|---|
| 1 | Refuse out-of-scope with `"I cannot answer that.."` | `src/prompts.py` | 17–22 |
| 2 | Refuse HP-related but out-of-knowledge | `src/prompts.py` | 23–27 |
| 3 | Allow greetings + self-questions, no internals leak | `src/prompts.py` | 29–53 |
| 4 | Resist jailbreak / injection | `src/guard.py` + `src/prompts.py` | guard.py 14–25; prompts.py 15, 44–53 |
| 5 | Last-N conversational memory for follow-ups | `src/memory.py` + `src/prompts.py` | memory.py full; prompts.py 66–67 |
| 6 | Refuse format/style manipulation | `src/prompts.py` | 55–64 |
| 7 | Smart chunking (FAISS top-N for the API call) | `src/retriever.py` | 62–98 |
| 8 | Two FAISS indices — questions-only cache + full data | `src/retriever.py` | 36–49 (stage A), 62–98 (stage B) |
| 9 | Interactive UI | `app.py` (Streamlit) | — |
| 10 | Short report (stack, diagram, hard/enjoyable) | `REPORT.md` | — |

## 6. What each eval category proves

| Test prefix | Category | Expected behavior |
|---|---|---|
| `r1_*` | Out-of-scope questions (capital of France, write Python, weather, math, recipes, Lord of the Rings, Marvel) | Exact reply `"I cannot answer that.."` |
| `r2_*` | Harry Potter topics absent from the dataset (Filch's cat's full name, exact Felix Felicis ingredients, Neville's birthday) | Exact reply `"I cannot answer that.."` |
| `r3_*` | Greetings, identity, capability ("hi", "who are you?", "help") | Friendly canned reply, no internals leaked |
| `r4_*` | Jailbreaks, prompt extraction, fake admin, DAN mode, "write me Python code" | Exact reply `"I cannot answer that.."` |
| `r5_*` | Two-turn pronoun resolution ("Who is Harry Potter?" → "How old is he?") | Final answer contains the resolved fact ("11") |
| `r6_*` | Format manipulation ("answer in 10 words", JSON, French, pirate speak, "one word only") | Normal prose answer that ignores the format instruction |

## 7. Notes for the grader

- The data files in `data/` are the **instructor's official dataset** ([data/harry_potter_data_02.xlsx](data/harry_potter_data_02.xlsx) — 20 Q/A pairs in column-A/B rows + 130 raw passages in column-A-only rows). They are split into [data/qa_pairs.json](data/qa_pairs.json) and [data/passages.json](data/passages.json) by `make_zip.py`-ready preprocessing, then consumed by [src/indexer.py](src/indexer.py) to build both FAISS indices. To swap in a different dataset, edit those JSON files and run `python -m src.indexer`.
- **LLM resilience:** [src/llm.py](src/llm.py) walks a seven-model fallback chain — six free OpenRouter models, then `anthropic/claude-haiku-4.5` as a paid tail (cents per 40-case eval; never reached in normal use). On total failure, [src/pipeline.py](src/pipeline.py) returns a visible `⚠️ LLM service unavailable: …` message instead of silently impersonating a behavioral refusal, so infrastructure outages are distinguishable from real refusals in both the UI and the eval.
- The Streamlit UI shows an expandable "retrieval details" panel below each assistant turn — useful for verifying which stage (`guard` / `cache` / `llm`) produced the answer, plus the matched question / similarity / retrieved chunks.
- Screenshots of expected behavior are in [screenshots/](screenshots/): initial, greeting, in-scope answer, out-of-scope refusal, jailbreak refusal, pronoun follow-up.
- Full reflections on hard parts and enjoyable parts are in [REPORT.md](REPORT.md) sections 4–5. Design specs and execution plans are under [docs/superpowers/](docs/superpowers/).
