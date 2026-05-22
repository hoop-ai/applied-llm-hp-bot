# 📚 HP-Bot

A retrieval-augmented Harry Potter chatbot built for **COP4921 Applied Large Language Models 25/26**. Two-stage FAISS retrieval gates the LLM call so common questions answer instantly from cache, out-of-scope questions never reach the model, and every behavioral rule from the brief is enforced in the system prompt.

> **For the instructor:** start with [SUBMISSION.md](SUBMISSION.md) — one-page grading checklist with `Where each requirement is implemented` line numbers. Last clean eval run: **40/40 pass, 0 regression, 0 mismatch, 0 error** on the instructor's corpus ([REPORT-eval-new-corpus.md](REPORT-eval-new-corpus.md)).

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| UI | Streamlit |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector index | FAISS (CPU), cosine via inner-product on L2-normalized vectors |
| Sparse retrieval | `rank-bm25` (hybrid blend, 0.7 dense / 0.3 BM25) |
| LLM | OpenRouter — `z-ai/glm-4.5-air:free` default → six free fallbacks → `anthropic/claude-haiku-4.5` paid tail |
| Eval | YAML cases + custom runner (`tests/run_eval.py`) + classifier (`tests/diagnose_eval.py`) |

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env          # then open .env and paste your OpenRouter key
streamlit run app.py
```

Get a free OpenRouter key at <https://openrouter.ai/keys>. The default model `z-ai/glm-4.5-air:free` works on the free tier; the client falls through six more free models, then `anthropic/claude-haiku-4.5` as a paid tail.

First launch downloads the embedding model (~80 MB) and builds the FAISS indices — expect 60–90 seconds on Windows. After that, `st.cache_resource` keeps the bundle warm and turns are instant. Most queries hit the Stage-A cache and never spend an API credit.

## How it works

A user message first hits a regex prefilter that catches obvious jailbreaks ("ignore previous instructions", "I am the admin", etc.) and returns the refusal without an API call. Surviving messages are embedded and searched against **Index A** (questions only). If the top match exceeds the threshold (default 0.85 cosine), the stored answer is returned — still no LLM call. Otherwise the query goes to **Index B** (every Q/A pair plus raw passages), which uses a hybrid dense+BM25 blend to pick the top-5 chunks. Those chunks, the last N conversation turns, and the system prompt are sent to OpenRouter at temperature 0. The system prompt is the behavioral contract — every rule below lives there. Full flow diagram in [REPORT.md §2](REPORT.md).

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

## Run the eval

```bash
python -m tests.run_eval                    # raw 40-case pass/fail
python -m tests.diagnose_eval               # smarter classifier → REPORT-eval-new-corpus.md
python -m tests.test_diagnose_classifier    # 10 unit tests for the classifier
python -m tests.e2e_playwright              # 5-step Streamlit smoke test (requires playwright)
```

`run_eval` prints a per-rule pass/fail table. `diagnose_eval` runs the same suite, retries each case up to 3× to absorb free-tier provider non-determinism, and buckets each result as `pass` / `regression` / `mismatch` / `error` — useful when the corpus changes (a corpus-wording mismatch is not a robustness regression). Last clean run on the instructor's corpus (2026-05-14): **40/40** — see [REPORT.md §6](REPORT.md) and [REPORT-eval-new-corpus.md](REPORT-eval-new-corpus.md).

## Project structure

```
.
├── app.py                              Streamlit chat UI
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

`indices/` (FAISS files) and `HP-Bot.zip` are gitignored — both regenerate on demand from `python -m src.indexer` and `python make_zip.py` respectively.

## Configuration

All knobs live in `.env` — copy [.env.example](.env.example) to `.env` and fill in your key:

| Key | Default | Meaning |
|---|---|---|
| `OPENROUTER_API_KEY` | *(required)* | Your own OpenRouter key — get one free at <https://openrouter.ai/keys>. `.env` is gitignored so it won't leak. |
| `OPENROUTER_MODEL` | `z-ai/glm-4.5-air:free` | Primary model; the client falls back through six more models on failure (final tail: `anthropic/claude-haiku-4.5`, paid but cheap) |
| `THRESHOLD_A` | `0.85` | Stage-A cache hit threshold (cosine similarity) |
| `TOP_K_B` | `5` | Stage-B passages retrieved as context |
| `MEMORY_TURNS` | `5` | Prior turns kept verbatim before rolling summary kicks in |

## Rebuilding indices

After editing the JSON files in `data/`, rebuild with:

```bash
python -m src.indexer
```

Or delete the `indices/` folder — the next launch rebuilds automatically.

## Documentation

- [SUBMISSION.md](SUBMISSION.md) — grading checklist
- [REPORT.md](REPORT.md) — full project report (tech stack, flow diagram, hard parts, enjoyable parts, eval results, limitations)
- [REPORT-eval-new-corpus.md](REPORT-eval-new-corpus.md) — generated per-case diagnostic
- [docs/PRESENTATION.md](docs/PRESENTATION.md) — presenter guide for the 5–10 min live demo (slides outline, speaker notes, demo script, Q&A prep, pre-presentation checklist)
- [HP-Bot-presentation.pptx](HP-Bot-presentation.pptx) — slide deck (regenerate via `python scripts/build_slides.py`)
- [docs/superpowers/specs/](docs/superpowers/specs/) — design specs (chatbot architecture + adversarial-eval pass)
- [docs/superpowers/plans/](docs/superpowers/plans/) — implementation plan
