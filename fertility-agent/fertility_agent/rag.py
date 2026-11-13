from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from .guidelines import guideline_chunks

EMBEDDING_DIMENSIONS = 384


def _local_embedding(text: str) -> list[float]:
    """Deterministic local feature hashing; needs no external model or network."""
    vector = [0.0] * EMBEDDING_DIMENSIONS
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        slot = int.from_bytes(digest[:4], "little") % EMBEDDING_DIMENSIONS
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[slot] += sign
    norm = sum(value * value for value in vector) ** 0.5
    return [value / norm for value in vector] if norm else vector


class GuidelineRetriever:
    def __init__(self, path: Path):
        import os

        os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
        os.environ.setdefault("OTEL_SDK_DISABLED", "true")
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("Install the project requirements to use local ChromaDB retrieval") from exc
        path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection(
            name="guideline_references",
            metadata={"hnsw:space": "cosine"},
        )
        if self.collection.count() == 0:
            chunks = guideline_chunks()
            self.collection.add(
                ids=[chunk["id"] for chunk in chunks],
                documents=[chunk["text"] for chunk in chunks],
                metadatas=[{key: value for key, value in chunk.items() if key not in {"id", "text"}} for chunk in chunks],
                embeddings=[_local_embedding(chunk["text"]) for chunk in chunks],
            )

    def search(self, query: str, limit: int = 4) -> list[dict[str, Any]]:
        if not query.strip() or limit < 1:
            return []
        result = self.collection.query(
            query_embeddings=[_local_embedding(query)], n_results=min(limit, 5), include=["documents", "metadatas", "distances"]
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadata = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            {"id": identifier, "text": document, "metadata": details or {}, "distance": distance}
            for identifier, document, details, distance in zip(ids, documents, metadata, distances, strict=True)
        ]