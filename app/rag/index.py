from __future__ import annotations

import json
import math
import re
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.rag.chunking import chunk_text


TOKEN_PATTERN = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


@dataclass
class Chunk:
    id: str
    document_id: str
    title: str
    text: str
    position: int
    created_at: str
    token_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class SearchResult:
    chunk_id: str
    document_id: str
    title: str
    text: str
    score: float
    position: int


class KnowledgeIndex:
    def __init__(self, index_path: Path):
        self.index_path = index_path
        self.chunks: list[Chunk] = []
        self.document_titles: dict[str, str] = {}
        self._load()

    def add_document(self, title: str, text: str) -> dict[str, Any]:
        document_id = str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat()
        chunks = chunk_text(text)

        for position, chunk in enumerate(chunks):
            self.chunks.append(
                Chunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    title=title,
                    text=chunk,
                    position=position,
                    created_at=created_at,
                    token_counts=dict(Counter(tokenize(chunk))),
                )
            )

        self.document_titles[document_id] = title
        self.save()
        return {"document_id": document_id, "title": title, "chunks": len(chunks)}

    def list_documents(self) -> list[dict[str, Any]]:
        totals: Counter[str] = Counter(chunk.document_id for chunk in self.chunks)
        return [
            {"document_id": document_id, "title": title, "chunks": totals[document_id]}
            for document_id, title in sorted(self.document_titles.items(), key=lambda item: item[1])
        ]

    def clear(self) -> None:
        self.chunks = []
        self.document_titles = {}
        self.save()

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        query_tokens = Counter(tokenize(query))
        if not query_tokens:
            return []

        doc_count = max(1, len(self.chunks))
        document_frequency: Counter[str] = Counter()
        for chunk in self.chunks:
            document_frequency.update(chunk.token_counts.keys())

        query_vector = _tf_idf_vector(query_tokens, document_frequency, doc_count)
        scored: list[SearchResult] = []

        for chunk in self.chunks:
            chunk_vector = _tf_idf_vector(Counter(chunk.token_counts), document_frequency, doc_count)
            score = _cosine_similarity(query_vector, chunk_vector)
            if score > 0:
                scored.append(
                    SearchResult(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        title=chunk.title,
                        text=chunk.text,
                        score=round(score, 4),
                        position=chunk.position,
                    )
                )

        return sorted(scored, key=lambda result: result.score, reverse=True)[:top_k]

    def save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "documents": self.document_titles,
            "chunks": [chunk.__dict__ for chunk in self.chunks],
        }
        self.index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self) -> None:
        if not self.index_path.exists():
            return
        payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        self.document_titles = dict(payload.get("documents", {}))
        self.chunks = [Chunk(**item) for item in payload.get("chunks", [])]


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for match in TOKEN_PATTERN.findall(text.lower()):
        if len(match) <= 1 and not ("\u4e00" <= match <= "\u9fff"):
            continue
        if _looks_like_cjk(match):
            tokens.extend(_cjk_ngrams(match))
        else:
            tokens.append(match)
    return tokens


def _looks_like_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _cjk_ngrams(text: str) -> list[str]:
    chars = [char for char in text if "\u4e00" <= char <= "\u9fff" or char.isalnum()]
    if len(chars) <= 2:
        return ["".join(chars)] if chars else []
    return ["".join(chars[index : index + 2]) for index in range(len(chars) - 1)]


def _tf_idf_vector(
    counts: Counter[str],
    document_frequency: Counter[str],
    doc_count: int,
) -> dict[str, float]:
    vector: dict[str, float] = {}
    total = max(1, sum(counts.values()))
    for token, count in counts.items():
        tf = count / total
        idf = math.log((doc_count + 1) / (document_frequency[token] + 1)) + 1
        vector[token] = tf * idf
    return vector


def _cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    shared = set(left).intersection(right)
    numerator = sum(left[token] * right[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
