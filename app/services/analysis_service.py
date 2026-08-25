"""
In-memory document store and simple analysis service.

For the MVP, documents are kept in a module-level dict:
    { doc_id: {"file_name": ..., "chunks": [...str]} }

Production upgrade path:
  - Replace the in-memory store with a vector DB (pgvector, Pinecone, Azure AI Search …)
  - Replace the heuristic keyword search with semantic similarity search.
  - Replace the local summariser with an LLM call (OpenAI, Azure OpenAI, etc.)
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any

from app.utils.file_helpers import chunk_text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory store  { doc_id -> { "file_name": str, "chunks": list[str], "mime_type": str } }
# ---------------------------------------------------------------------------
_store: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Store helpers
# ---------------------------------------------------------------------------

def store_document(doc_id: str, file_name: str, mime_type: str, text: str) -> int:
    """Chunk *text* and persist it. Returns number of chunks created."""
    chunks = chunk_text(text)
    _store[doc_id] = {
        "file_name": file_name,
        "mime_type": mime_type,
        "chunks": chunks,
    }
    return len(chunks)


def get_all_doc_ids() -> list[str]:
    return list(_store.keys())


def document_exists(doc_id: str) -> bool:
    return doc_id in _store


def get_document(doc_id: str) -> dict[str, Any] | None:
    return _store.get(doc_id)


def clear_store() -> None:
    """Remove all ingested documents (useful for testing)."""
    _store.clear()


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def summarize(doc_id: str, max_length: int = 300) -> str:
    """
    MVP summariser: concatenate the first few chunks and truncate.
    Replace with an LLM call in production.
    """
    doc = _store.get(doc_id)
    if doc is None:
        return f"[Document '{doc_id}' not found in store]"

    chunks = doc["chunks"]
    combined = " ".join(chunks[:3])  # take up to 3 chunks
    if len(combined) <= max_length:
        return combined.strip()

    # Truncate at the last sentence boundary within max_length
    truncated = combined[:max_length]
    last_period = max(truncated.rfind("."), truncated.rfind("!"), truncated.rfind("?"))
    if last_period > max_length // 2:
        return truncated[: last_period + 1].strip()
    return truncated.strip() + "…"


def answer_question(question: str, doc_ids: list[str] | None, top_k: int = 5) -> tuple[str, list[str]]:
    """
    MVP Q&A: keyword-based chunk retrieval.
    Returns (answer_text, [doc_ids used]).
    Replace with semantic search + LLM in production.
    """
    target_ids = doc_ids if doc_ids else list(_store.keys())
    if not target_ids:
        return "No documents have been ingested yet. Please run /documents/ingest first.", []

    # Tokenise question
    keywords = set(re.findall(r"\w+", question.lower())) - _STOPWORDS

    scored: list[tuple[float, str, str]] = []  # (score, doc_id, chunk)
    for doc_id in target_ids:
        doc = _store.get(doc_id)
        if not doc:
            continue
        for chunk in doc["chunks"]:
            words = re.findall(r"\w+", chunk.lower())
            word_freq = Counter(words)
            score = sum(word_freq.get(kw, 0) for kw in keywords)
            if score > 0:
                scored.append((score, doc_id, chunk))

    if not scored:
        return (
            f"No relevant content found for the question: '{question}'. "
            "Try rephrasing or ingest more documents.",
            [],
        )

    scored.sort(key=lambda x: x[0], reverse=True)
    top_results = scored[:top_k]
    used_doc_ids = list({doc_id for _, doc_id, _ in top_results})

    answer_parts = []
    for rank, (score, doc_id, chunk) in enumerate(top_results, start=1):
        file_name = _store[doc_id]["file_name"]
        answer_parts.append(f"[{rank}] (from '{file_name}')\n{chunk.strip()}")

    answer = "\n\n".join(answer_parts)
    return answer, used_doc_ids


# ---------------------------------------------------------------------------
# Stopwords (basic English + Spanish)
# ---------------------------------------------------------------------------

_STOPWORDS: set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "can", "could", "that", "this", "these",
    "those", "it", "its", "i", "we", "you", "he", "she", "they",
    # Spanish
    "el", "la", "los", "las", "un", "una", "de", "del", "en", "que",
    "y", "o", "por", "para", "con", "se", "no", "al", "le", "su",
    "es", "son", "fue", "ser", "si", "como",
}
