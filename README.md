# 📚 HP-Bot

> A retrieval-augmented Harry Potter chatbot built for **COP4921 Applied Large Language Models 25/26**.

Two-stage FAISS retrieval gates the LLM call: common questions answer instantly from cache, out-of-scope questions never reach the model, and every behavioral rule from the brief is enforced in the system prompt.

**Last clean eval run: 40/40 pass, 0 regression, 0 mismatch, 0 error** on the instructor's corpus — see [REPORT-eval-new-corpus.md](REPORT-eval-new-corpus.md).

> **For the instructor:** the one-page grading checklist with per-requirement source lines is in [SUBMISSION.md](SUBMISSION.md).

![HP-Bot Streamlit UI](screenshots/presentation/01_initial_ui.png)

---

## Table of contents

- [Getting started](#getting-started)
- [How it works](#how-it-works)
- [Brief requirements](#brief-requirements)
- [Running the eval](#running-the-eval)
- [Configuration](#configuration)
- [Project structure](#project-structure)
- [Rebuilding indices](#rebuilding-indices)
- [Documentation](#documentation)

---

## Getting started

A clean clone to running chat in about **3 minutes**. Prerequisites: **Python 3.11+** and **git**.

### 1. Clone the repo

```bash
git clone https://github.com/hoop-ai/applied-llm-hp-bot.git
cd applied-llm-hp-bot
```

### 2. Create a virtual environment

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

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get a free OpenRouter API key

1. Sign up at <https://openrouter.ai/> — Google or GitHub login works in one click.
2. Open <https://openrouter.ai/keys> → **Create Key** → copy the `sk-or-v1-…` string.

No credit card required. The default model (`z-ai/glm-4.5-air:free`) runs on OpenRouter's free tier.

### 5. Set up your `.env`

Copy the template to a local `.env` file (gitignored — your key never leaves your machine):

**macOS / Linux:**

```bash
cp .env.example .env
```

**Windows (PowerShell):**

```powershell
Copy-Item .env.example .env
```

Open `.env` in any editor and paste your key into the first line:

```dotenv
# OpenRouter API key — paste yours here (https://openrouter.ai/keys)
OPENROUTER_API_KEY=sk-or-v1-PASTE-YOUR-KEY-HERE

# Model id. Any OpenRouter-supported model.
OPENROUTER_MODEL=z-ai/glm-4.5-air:free

# Stage-A similarity threshold (0..1).
THRESHOLD_A=0.85

# Stage-B top-K passages to retrieve as context.
TOP_K_B=5

# How many prior turns to keep in conversation memory.
MEMORY_TURNS=5
```

Leave everything except `OPENROUTER_API_KEY` at the defaults.

### 6. Run the app

```bash
streamlit run app.py
```

Streamlit opens at <http://localhost:8501>.

> **First launch takes 60–90 seconds** — it downloads the MiniLM embedding model (~80 MB) and builds both FAISS indices. After that, `st.cache_resource` keeps everything warm and turns are instant. Most queries hit the Stage-A cache and never spend an API credit.

### Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError` on first run | Confirm the venv is activated (your prompt should show `(.venv)`) and re-run `pip install -r requirements.txt`. |
| `OPENROUTER_API_KEY not set` | Make sure `.env` lives in the repo root and the value starts with `sk-or-v1-`. No quotes around the value. |
| Streamlit page hangs on first turn | Cold start of MiniLM + FAISS. Give it 60–90 seconds. Subsequent turns are instant. |
| `429` / rate-limit messages | OpenRouter free models are shared. The client auto-fails-over through six more free models and a paid Claude Haiku tail; just retry the turn. |
| Want to start fresh | Delete the `indices/` folder; it rebuilds on next launch. |

---

## How it works

A user message first hits a regex prefilter that catches obvious jailbreaks ("ignore previous instructions", "I am the admin", etc.) and returns the refusal without an API call. Surviving messages are embedded and searched against **Index A** (questions only). If the top match exceeds the threshold (default 0.85 cosine), the stored answer is returned — still no LLM call. Otherwise the query goes to **Index B** (every Q/A pair plus raw passages), which uses a hybrid dense + BM25 blend to pick the top-5 chunks. Those chunks, the last N conversation turns, and the system prompt are sent to OpenRouter at temperature 0. The system prompt is the behavioral contract — every rule below lives there.

```text
                       ┌────────────────────────────┐
                       │   user message (Streamlit) │
                       └──────────────┬─────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────┐
                       │   guard.py heuristic     │
                       │   regex jailbreak filter │
                       └────────────┬─────────────┘
                                    │
                       tripped ─────┴───── pass
                          │                 │
                          ▼                 ▼
                  ┌──────────────┐  ┌─────────────────────┐
                  │ refusal      │  │  embed(query)       │
                  │ (no API call)│  │  MiniLM-L6-v2       │
                  └──────────────┘  └──────┬──────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────┐
                              │  Index A (questions)    │
                              │  FAISS cosine top-1     │
                              └───────────┬─────────────┘
                                          │
                            score ≥ 0.85 ─┴── score < 0.85
                                   │                │
                                   ▼                ▼
                          ┌─────────────────┐  ┌────────────────────────┐
                          │ cached answer   │  │ Index B (all chunks)   │
                          │ (no LLM call)   │  │ hybrid: 0.7·dense      │
                          └─────────────────┘  │       + 0.3·BM25       │
                                               │ top-5 chunks           │
                                               └──────────┬─────────────┘
                                                          │
                                                          ▼
                                          ┌──────────────────────────────┐
                                          │ build prompt:                │
                                          │  system rules                │
                                          │  + retrieved context         │
                                          │  + memory.render()           │
                                          │  + user message              │
                                          │  + final reminder            │
                                          └──────────────┬───────────────┘
                                                         │
                                                         ▼
                                          ┌──────────────────────────────┐
                                          │ OpenRouter chat completion   │
                                          │ (temperature 0)              │
                                          └──────────────┬───────────────┘
                                                         │
                                                         ▼
                                          ┌──────────────────────────────┐
                                          │ render in Streamlit          │
                                          │ append to Memory             │
                                          └──────────────────────────────┘
```

### Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| UI | Streamlit |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector index | FAISS (CPU), cosine via inner-product on L2-normalized vectors |
| Sparse retrieval | `rank-bm25` (hybrid blend, 0.7 dense / 0.3 BM25) |
| LLM | OpenRouter — `z-ai/glm-4.5-air:free` default → six free fallbacks → `anthropic/claude-haiku-4.5` paid tail |
| Eval | YAML cases + custom runner (`tests/run_eval.py`) + classifier (`tests/diagnose_eval.py`) |

---

## Brief requirements

| # | Requirement | Status | Where it's enforced |
|---|---|---|---|
| 1 | Refuse out-of-scope questions with `"I cannot answer that.."` | ✓ | [src/prompts.py:17–22](src/prompts.py#L17) |
| 2 | Refuse HP questions whose answer is not in the data | ✓ | [src/prompts.py:23–27](src/prompts.py#L23) |
| 3 | Answer greetings + self questions without leaking internals | ✓ | [src/prompts.py:29–53](src/prompts.py#L29) |
| 4 | Resist injection / jailbreak attempts | ✓ | [src/guard.py:14–25](src/guard.py#L14) + [src/prompts.py:15](src/prompts.py#L15) + [src/prompts.py:44–53](src/prompts.py#L44) |
| 5 | Conversation memory for follow-ups ("how old is he?") | ✓ | [src/memory.py](src/memory.py) + [src/prompts.py:66–67](src/prompts.py#L66) |
| 6 | Reject format/style manipulation ("answer in 10 words") | ✓ | [src/prompts.py:55–64](src/prompts.py#L55) |
| 7 | Smart chunking (FAISS, top-N for the API call) | ✓ | [src/retriever.py:62–98](src/retriever.py#L62) |
| 8 | Two-stage FAISS — questions-only cache + full index | ✓ | [src/retriever.py:36–49](src/retriever.py#L36) (stage A), [src/retriever.py:62–98](src/retriever.py#L62) (stage B) |
| 9 | Interactive UI | ✓ | [app.py](app.py) (Streamlit) |
| 10 | Short report (stack, flow diagram, hard/enjoyable parts) | ✓ | [REPORT.md](REPORT.md) |

---

## Running the eval

```bash
python -m tests.run_eval                    # raw 40-case pass/fail
python -m tests.diagnose_eval               # smarter classifier → REPORT-eval-new-corpus.md
python -m tests.test_diagnose_classifier    # 10 unit tests for the classifier
python -m tests.e2e_playwright              # 5-step Streamlit smoke test (requires playwright)
```

`run_eval` prints a per-rule pass/fail table. `diagnose_eval` runs the same suite, retries each case up to 3× to absorb free-tier provider non-determinism, and buckets each result as `pass` / `regression` / `mismatch` / `error` — useful when the corpus changes (a corpus-wording mismatch is not a robustness regression). Last clean run on the instructor's corpus (2026-05-14): **40/40** — see [REPORT.md §6](REPORT.md) and [REPORT-eval-new-corpus.md](REPORT-eval-new-corpus.md).

---

## Configuration

All knobs live in `.env` — copy [.env.example](.env.example) to `.env` and fill in your key:

| Key | Default | Meaning |
|---|---|---|
| `OPENROUTER_API_KEY` | *(required)* | Your own OpenRouter key — get one free at <https://openrouter.ai/keys>. `.env` is gitignored so it won't leak. |
| `OPENROUTER_MODEL` | `z-ai/glm-4.5-air:free` | Primary model; the client falls back through six more models on failure (final tail: `anthropic/claude-haiku-4.5`, paid but cheap) |
| `THRESHOLD_A` | `0.85` | Stage-A cache hit threshold (cosine similarity) |
| `TOP_K_B` | `5` | Stage-B passages retrieved as context |
| `MEMORY_TURNS` | `5` | Prior turns kept verbatim before rolling summary kicks in |

---

## Project structure

```text
.
├── app.py                              Streamlit chat UI
├── .env.example                        Template — copy to .env and add your key
├── src/
│   ├── prompts.py                      System prompt — the behavioral contract
│   ├── guard.py                        Regex jailbreak prefilter
│   ├── indexer.py                      Builds + persists FAISS indices and BM25 corpus
│   ├── retriever.py                    Stage A (question cache) + Stage B (hybrid)
│   ├── memory.py                       Last-N-turn buffer with rolling summary
│   ├── llm.py                          OpenRouter client + 7-model fallback chain
│   └── pipeline.py                     guard → A → B → LLM orchestration
├── tests/
│   ├── attacks.yaml                    40 adversarial cases, labeled by rule
│   ├── run_eval.py                     Raw pass/fail eval harness
│   ├── diagnose_eval.py                Smarter classifier + retry + markdown report
│   ├── test_diagnose_classifier.py     Unit tests for the classifier (10/10 pass)
│   └── e2e_playwright.py               UI smoke test (5/5 pass)
├── data/
│   ├── harry_potter_data_02.xlsx       Instructor's official dataset
│   ├── qa_pairs.json                   20 Q/A pairs (split from the xlsx)
│   └── passages.json                   130 raw passages (split from the xlsx)
├── docs/superpowers/
│   ├── specs/                          Design specs (architecture + eval-on-new-corpus)
│   └── plans/                          Implementation plan
├── screenshots/                        e2e captures of every chat state
├── REPORT.md                           Tech stack, flow diagram, reflections, eval table
├── REPORT-eval-new-corpus.md           Per-case diagnostic report
├── SUBMISSION.md                       One-page grading checklist for the instructor
├── make_zip.py                         Builds HP-Bot.zip (the shipping artifact)
└── requirements.txt
```

`.env`, `indices/` (FAISS files), and `HP-Bot.zip` are gitignored — `indices/` regenerates from `python -m src.indexer`, the zip from `python make_zip.py`.

---

## Rebuilding indices

After editing the JSON files in `data/`, rebuild with:

```bash
python -m src.indexer
```

Or delete the `indices/` folder — the next launch rebuilds automatically.

---

## Documentation

- [SUBMISSION.md](SUBMISSION.md) — one-page grading checklist
- [REPORT.md](REPORT.md) — full project report (tech stack, flow diagram, hard parts, enjoyable parts, eval results, limitations)
- [REPORT-eval-new-corpus.md](REPORT-eval-new-corpus.md) — generated per-case eval diagnostic
- [docs/PRESENTATION.md](docs/PRESENTATION.md) — presenter guide for the 5–10 min live demo (slides outline, speaker notes, demo script, Q&A prep, pre-presentation checklist)
- [HP-Bot-presentation.pptx](HP-Bot-presentation.pptx) — slide deck (regenerate via `python scripts/build_slides.py`)
- [docs/superpowers/specs/](docs/superpowers/specs/) — design specs (chatbot architecture + adversarial-eval pass)
- [docs/superpowers/plans/](docs/superpowers/plans/) — implementation plan
