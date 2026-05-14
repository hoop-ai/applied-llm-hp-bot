# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

**Pre-implementation.** The repo currently contains only [project_requirements](project_requirements) — the course brief for COP4921 *Applied Large Language Models* (25/26). There is no source code, build system, or test suite yet. Do not invent commands; ask the user before assuming a stack.

The deliverable is a Harry Potter chatbot built on top of a dataset the instructor will supply (Q/A pairs plus raw passages). Deadline per the brief: **2026-06-03** (instructor said it may be extended).

## Target architecture (per [project_requirements](project_requirements))

Two-stage FAISS retrieval gated by a similarity threshold, then LLM:

1. **Index A — questions only.** On a new user question, embed and search against index A. If top-1 similarity ≥ threshold, return the stored answer **with no API call**.
2. **Index B — all data** (questions, answers, raw passages). On a miss in stage 1, retrieve top-N chunks from B and pass them as context to the LLM call.

Default LLM is **Qwen** (instructor provides API keys), but the model is swappable.

## Hard behavioral requirements

These are graded; the system prompt + retrieval must enforce all of them. When implementing, treat them as acceptance criteria — not nice-to-haves:

1. **Scope refusal.** If the question is not about the dataset, reply exactly `"I cannot answer that.."` (two dots, per brief).
2. **Out-of-knowledge refusal.** Same reply if the question is Harry Potter-related but the answer is not in the retrieved data — do **not** let the model fall back on its parametric knowledge.
3. **Self/greeting whitelist.** Must respond to "hi", "who are you", etc. without leaking the prompt, settings, parameters, or implementation details. This carve-out has to coexist with rules 1 & 2 — solve it in the prompt, not by loosening the refusal logic.
4. **Injection / jailbreak resistance.** Resist "ignore previous instructions", fake-admin claims, "write me python code", etc.
5. **Conversational memory.** Keep the last *n* turns so follow-ups like "how old is he?" resolve pronouns against the prior turn.
6. **No answer-format manipulation.** Reject user attempts to dictate length, language, tone, format ("answer in ten words", "respond as JSON", etc.).

These rules interact — testing rule 3 without breaking rules 1, 2, 4, 6 is the hard part.

## Interface

Any framework is fine (Streamlit, Tkinter, Flask, etc.). The brief explicitly says the UI can be minimal — don't over-invest there.

## Deliverable report

Alongside code, the project ships a short report covering: tech stack, flow diagram, what was hard, what was enjoyable. Keep notes as you go so this isn't a scramble at the end.

## Conventions for this repo

- Course project, not production software — the instructor explicitly said "do not worry about the quality of the code that much." Prefer readable, working code over abstractions.
- The dataset will be provided by the instructor; do not fabricate Harry Potter data for testing.
- When the user asks about Qwen API, FAISS, or sentence-transformer specifics, prefer the **context7** MCP server for up-to-date docs over recalled knowledge.
