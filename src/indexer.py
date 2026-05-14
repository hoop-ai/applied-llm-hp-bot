"""Builds and persists the two FAISS indices plus a BM25 corpus.

Index A: questions only, used for the fast cache lookup (stage 1).
Index B: every chunk — questions, answers, and raw passages — used to build
LLM context (stage 2).

Both indices use cosine similarity via L2-normalized vectors + inner-product
FAISS index. The BM25 corpus parallels Index B for the hybrid blend.
"""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
INDICES = ROOT / "indices"
INDICES.mkdir(exist_ok=True)

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass
class Bundle:
    """Everything the retriever needs at query time."""
    model: SentenceTransformer
    index_a: faiss.Index            # questions only
    answers_a: list[str]            # parallel to index_a (the stored answer)
    questions_a: list[str]          # parallel to index_a (for debug display)
    index_b: faiss.Index            # everything
    texts_b: list[str]              # parallel to index_b
    bm25: BM25Okapi                 # parallel tokenization of texts_b


def _embed(model: SentenceTransformer, texts: list[str]) -> np.ndarray:
    vecs = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return vecs.astype("float32")


def _faiss_ip(vecs: np.ndarray) -> faiss.Index:
    dim = vecs.shape[1]
    idx = faiss.IndexFlatIP(dim)
    idx.add(vecs)
    return idx


def _tokenize(text: str) -> list[str]:
    # crude but works for BM25
    return [t for t in text.lower().split() if t.isalnum() or any(c.isalnum() for c in t)]


def build() -> Bundle:
    qa = json.loads((DATA / "qa_pairs.json").read_text(encoding="utf-8"))
    passages = json.loads((DATA / "passages.json").read_text(encoding="utf-8"))

    model = SentenceTransformer(EMBED_MODEL)

    # Index A — questions only
    questions = [item["question"] for item in qa]
    answers = [item["answer"] for item in qa]
    vec_a = _embed(model, questions)
    index_a = _faiss_ip(vec_a)

    # Index B — questions + answers + passages, all as searchable chunks
    texts_b: list[str] = []
    for item in qa:
        texts_b.append(f"Q: {item['question']}\nA: {item['answer']}")
    for p in passages:
        texts_b.append(p["text"])
    vec_b = _embed(model, texts_b)
    index_b = _faiss_ip(vec_b)

    bm25 = BM25Okapi([_tokenize(t) for t in texts_b])

    bundle = Bundle(
        model=model,
        index_a=index_a,
        answers_a=answers,
        questions_a=questions,
        index_b=index_b,
        texts_b=texts_b,
        bm25=bm25,
    )
    return bundle


def save(bundle: Bundle) -> None:
    faiss.write_index(bundle.index_a, str(INDICES / "index_a.faiss"))
    faiss.write_index(bundle.index_b, str(INDICES / "index_b.faiss"))
    payload = {
        "answers_a": bundle.answers_a,
        "questions_a": bundle.questions_a,
        "texts_b": bundle.texts_b,
        "bm25_tokens": [_tokenize(t) for t in bundle.texts_b],
    }
    (INDICES / "meta.pkl").write_bytes(pickle.dumps(payload))


def load(model: SentenceTransformer | None = None) -> Bundle:
    if model is None:
        model = SentenceTransformer(EMBED_MODEL)
    index_a = faiss.read_index(str(INDICES / "index_a.faiss"))
    index_b = faiss.read_index(str(INDICES / "index_b.faiss"))
    payload = pickle.loads((INDICES / "meta.pkl").read_bytes())
    bm25 = BM25Okapi(payload["bm25_tokens"])
    return Bundle(
        model=model,
        index_a=index_a,
        answers_a=payload["answers_a"],
        questions_a=payload["questions_a"],
        index_b=index_b,
        texts_b=payload["texts_b"],
        bm25=bm25,
    )


def get_bundle() -> Bundle:
    """Build if missing, else load from disk."""
    if (INDICES / "index_a.faiss").exists() and (INDICES / "meta.pkl").exists():
        return load()
    print("[indexer] building fresh indices ...")
    bundle = build()
    save(bundle)
    print(f"[indexer] saved {len(bundle.questions_a)} Q/A pairs and {len(bundle.texts_b)} chunks")
    return bundle


if __name__ == "__main__":
    bundle = build()
    save(bundle)
    print(f"Built index_a ({len(bundle.questions_a)} questions) and index_b ({len(bundle.texts_b)} chunks).")
