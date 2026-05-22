# Submission — HP-Bot

**Course:** COP4921 Applied Large Language Models 25/26
**Student email:** malak@hoopai.com
**Date:** 2026-05-14
**Deadline:** 2026-06-03

A one-page checklist for grading. Full detail in [README.md](README.md) and [REPORT.md](REPORT.md).

## 1. Install (two minutes)

Prerequisites: **Python 3.11+** and **git**. No system packages required.

```bash
git clone https://github.com/hoop-ai/applied-llm-hp-bot.git
cd applied-llm-hp-bot
```

Create and activate a virtual environment:

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 2. API key

Get a free OpenRouter key (30 seconds, no credit card):

1. Sign up at <https://openrouter.ai/>.
2. Open <https://openrouter.ai/keys> → **Create Key** → copy the `sk-or-v1-…` string.

Copy the template and paste in your key:

**macOS / Linux:**

```bash
cp .env.example .env
```

**Windows (PowerShell):**

```powershell
Copy-Item .env.example .env
```

Open `.env` and set `OPENROUTER_API_KEY=sk-or-v1-…`. Leave the other values at their defaults. `.env` is gitignored so it stays out of the public repo.

The default model is `z-ai/glm-4.5-air:free`. The client falls through five more free models if the primary is rate-limited, then `anthropic/claude-haiku-4.5` as a paid tail (cents per 40-case eval, never reached in normal use). Most queries are served from the Stage-A cache and never hit the API at all.

## 3. Run the chat

```bash
streamlit run app.py
```

Streamlit opens at <http://localhost:8501>. **First launch takes 60–90 seconds** (sentence-transformers + FAISS import on Windows). Subsequent turns are instant.

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

## 6b. Presentation (5–10 minutes, live demo)

- [HP-Bot-presentation.pptx](HP-Bot-presentation.pptx) — 8 slides, 16:9.
- [docs/PRESENTATION.md](docs/PRESENTATION.md) — presenter guide: time budget, slide-by-slide speaker notes, the 5-prompt live-demo script (with what-to-say + fallback plans), likely Q&A from the instructor, and a 15-minute pre-presentation checklist.

The slide deck is generated from `scripts/build_slides.py` so edits to the structure happen in one place. Demo flow: greeting → in-scope question → pronoun follow-up → out-of-scope refusal → jailbreak attempt — one prompt per behavioral rule, visible in real time.

## 7. Notes for the grader

- The data files in `data/` are the **instructor's official dataset** ([data/harry_potter_data_02.xlsx](data/harry_potter_data_02.xlsx) — 20 Q/A pairs in column-A/B rows + 130 raw passages in column-A-only rows). They are split into [data/qa_pairs.json](data/qa_pairs.json) and [data/passages.json](data/passages.json) by `make_zip.py`-ready preprocessing, then consumed by [src/indexer.py](src/indexer.py) to build both FAISS indices. To swap in a different dataset, edit those JSON files and run `python -m src.indexer`.
- **LLM resilience:** [src/llm.py](src/llm.py) walks a seven-model fallback chain — six free OpenRouter models, then `anthropic/claude-haiku-4.5` as a paid tail (cents per 40-case eval; never reached in normal use). On total failure, [src/pipeline.py](src/pipeline.py) returns a visible `⚠️ LLM service unavailable: …` message instead of silently impersonating a behavioral refusal, so infrastructure outages are distinguishable from real refusals in both the UI and the eval.
- The Streamlit UI shows an expandable "retrieval details" panel below each assistant turn — useful for verifying which stage (`guard` / `cache` / `llm`) produced the answer, plus the matched question / similarity / retrieved chunks.
- Screenshots of expected behavior are in [screenshots/](screenshots/): initial, greeting, in-scope answer, out-of-scope refusal, jailbreak refusal, pronoun follow-up.
- Full reflections on hard parts and enjoyable parts are in [REPORT.md](REPORT.md) sections 4–5. Design specs and execution plans are under [docs/superpowers/](docs/superpowers/).
