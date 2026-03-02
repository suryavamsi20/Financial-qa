from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]


def _norm(counter: Counter[str]) -> float:
    return math.sqrt(sum(value * value for value in counter.values()))


@dataclass
class SearchResult:
    text: str
    score: float
    metadata: dict


class SimpleVectorStore:
    """
    Lightweight lexical retrieval store.
    Uses normalized term-frequency cosine similarity.
    """

    def __init__(self) -> None:
        self._entries: list[dict] = []

    def add_texts(self, texts: list[str], metadatas: list[dict] | None = None) -> None:
        metadatas = metadatas or [{} for _ in texts]
        if len(texts) != len(metadatas):
            raise ValueError("texts and metadatas must have same length")

        for text, metadata in zip(texts, metadatas):
            tokens = _tokenize(text)
            tf = Counter(tokens)
            self._entries.append(
                {
                    "text": text,
                    "metadata": metadata,
                    "tf": dict(tf),
                    "norm": _norm(tf),
                }
            )

    def similarity_search(self, query: str, k: int = 4) -> list[SearchResult]:
        if not self._entries:
            return []

        query_tf = Counter(_tokenize(query))
        query_norm = _norm(query_tf) or 1.0

        scored: list[SearchResult] = []
        for entry in self._entries:
            entry_tf = Counter(entry["tf"])
            dot = sum(query_tf[token] * entry_tf[token] for token in query_tf.keys())
            denom = query_norm * (entry["norm"] or 1.0)
            score = dot / denom if denom else 0.0
            if score > 0:
                scored.append(
                    SearchResult(
                        text=entry["text"],
                        score=score,
                        metadata=entry["metadata"],
                    )
                )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[: max(1, k)]

    def save(self, path: str | Path) -> None:
        payload = [{"text": e["text"], "metadata": e["metadata"]} for e in self._entries]
        Path(path).write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "SimpleVectorStore":
        raw = Path(path).read_text(encoding="utf-8")
        data = json.loads(raw)
        store = cls()
        store.add_texts([item["text"] for item in data], [item.get("metadata", {}) for item in data])
        return store
