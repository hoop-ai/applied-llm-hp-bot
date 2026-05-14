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
python -m tests.run_eval
```

Prints a per-rule pass/fail table. Last clean run: **40/40 on 2026-05-14**. Exit code 0 only if every case passes.

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

- The data files (`data/qa_pairs.json`, `data/passages.json`) are a **small synthetic stub** — the instructor's official dataset has not been distributed yet. The pipeline is dataset-agnostic; dropping the real files in `data/` and rerunning `python -m src.indexer` rebuilds both indices.
- The Streamlit UI shows an expandable "retrieval details" panel below each assistant turn — useful for verifying which stage (`guard` / `cache` / `llm`) produced the answer, plus the matched question / similarity / retrieved chunks.
- Screenshots of expected behavior are in [screenshots/](screenshots/): initial, greeting, in-scope answer, out-of-scope refusal, jailbreak refusal, pronoun follow-up.
- Full reflections on hard parts and enjoyable parts are in [REPORT.md](REPORT.md) sections 4–5.
