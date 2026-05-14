# 📚 HP-Bot

A retrieval-augmented Harry Potter chatbot built for **COP4921 Applied Large Language Models 25/26**. Two-stage FAISS retrieval gates an LLM call so common questions answer instantly from cache and out-of-scope questions never reach the model.

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| UI | Streamlit |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector index | FAISS (CPU), cosine via inner-product on L2-normalized vectors |
| Sparse retrieval | `rank-bm25` (hybrid blend, 0.7 dense / 0.3 BM25) |
| LLM | OpenRouter — `z-ai/glm-4.5-air:free` default, six-model fallback chain |
| Eval | YAML cases + custom runner (`tests/run_eval.py`) |

## How it works

A user message first hits a regex prefilter that catches obvious jailbreaks ("ignore previous instructions", "I am the admin", etc.) and returns the refusal without an API call. Surviving messages are embedded and searched against **Index A** (questions only). If the top match exceeds the threshold (default 0.85 cosine), the stored answer is returned — still no LLM call. Otherwise the query goes to **Index B** (every Q/A pair plus raw passages), which uses a hybrid dense+BM25 blend to pick the top-5 chunks. Those chunks, the last N conversation turns, and the system prompt are sent to OpenRouter at temperature 0. The system prompt is the behavioral contract — every rule below lives there.

## Brief requirements

| # | Requirement | Status | Where it's enforced |
|---|---|---|---|
| 1 | Refuse out-of-scope questions with `"I cannot answer that.."` | done | [src/prompts.py:17–22](src/prompts.py#L17) |
| 2 | Refuse HP questions whose answer is not in the data | done | [src/prompts.py:23–27](src/prompts.py#L23) |
| 3 | Answer greetings + self questions without leaking internals | done | [src/prompts.py:29–53](src/prompts.py#L29) |
| 4 | Resist injection / jailbreak attempts | done | [src/guard.py:14–25](src/guard.py#L14) + [src/prompts.py:15](src/prompts.py#L15) + [src/prompts.py:44–53](src/prompts.py#L44) |
| 5 | Conversation memory for follow-ups ("how old is he?") | done | [src/memory.py](src/memory.py) + [src/prompts.py:66–67](src/prompts.py#L66) |
| 6 | Reject format/style manipulation ("answer in 10 words") | done | [src/prompts.py:55–64](src/prompts.py#L55) |
| 7 | Smart chunking (FAISS, top-N for the API call) | done | [src/retriever.py:62–98](src/retriever.py#L62) |
| 8 | Two-stage FAISS — questions-only cache + full index | done | [src/retriever.py:36–49](src/retriever.py#L36) (stage A), [src/retriever.py:62–98](src/retriever.py#L62) (stage B) |
| 9 | Interactive UI | done | [app.py](app.py) (Streamlit) |
| 10 | Short report (stack, flow diagram, hard/enjoyable parts) | done | [REPORT.md](REPORT.md) |

## Quickstart

```bash
pip install -r requirements.txt
streamlit run app.py
```

First launch downloads the embedding model (~80 MB) and builds the FAISS indices — expect 60–90 seconds on Windows. After that, `st.cache_resource` keeps the bundle warm and turns are instant.

## Run the eval

```bash
python -m tests.run_eval                  # full suite (40 cases)
python -m tests.run_eval --case r4_admin  # single case
```

The runner prints a per-rule pass/fail table. Exit code is 0 only on a clean sweep. Last run on 2026-05-14: 40/40 — see [REPORT.md](REPORT.md#6-evaluation-results).

## Project structure

```
.
├── app.py                  Streamlit chat UI
├── src/
│   ├── prompts.py          System prompt — the entire behavioral contract
│   ├── guard.py            Regex jailbreak prefilter
│   ├── indexer.py          Builds + persists FAISS indices and BM25 corpus
│   ├── retriever.py        Stage A (question cache) + Stage B (hybrid)
│   ├── memory.py           Last-N-turn buffer with rolling summary
│   ├── llm.py              OpenRouter client + model fallback chain
│   └── pipeline.py         guard → A → B → LLM orchestration
├── tests/
│   ├── attacks.yaml        40 adversarial cases, labeled by rule
│   └── run_eval.py         Eval harness
├── data/
│   ├── qa_pairs.json       Q/A pairs (synthetic stub — see REPORT.md)
│   └── passages.json       Raw passages
├── indices/                FAISS indices + pickle metadata (rebuilt on demand)
├── REPORT.md               Tech stack, flow diagram, reflections, eval table
├── SUBMISSION.md           One-page grading checklist for the instructor
└── requirements.txt
```

## Configuration

All knobs live in `.env` (shipped) — copy `.env.example` if needed:

| Key | Default | Meaning |
|---|---|---|
| `OPENROUTER_API_KEY` | *(set)* | OpenRouter key. The shipped one is $5-capped — see [SUBMISSION.md](SUBMISSION.md) |
| `OPENROUTER_MODEL` | `z-ai/glm-4.5-air:free` | Primary model; the client falls back through five more free models on failure |
| `THRESHOLD_A` | `0.85` | Stage-A cache hit threshold (cosine similarity) |
| `TOP_K_B` | `5` | Stage-B passages retrieved as context |
| `MEMORY_TURNS` | `5` | Prior turns kept verbatim before rolling summary kicks in |

## Rebuilding indices

The indices are committed for reproducibility. After editing `data/`, rebuild with:

```bash
python -m src.indexer
```

Or delete the `indices/` folder — the next launch rebuilds automatically.
