"""Thin wrapper around chromadb's PersistentClient.

Centralizes collection name + distance metric so the indexer and the
query-side code agree without duplicating constants.
"""
from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings


def open_collection(
    persist_dir: str | Path,
    name: str,
    create_if_missing: bool = True,
) -> Collection:
    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False),
    )
    if create_if_missing:
        return client.get_or_create_collection(
            name=name,
            # Cosine for normalized embeddings — BGE outputs are L2-normalized.
            metadata={"hnsw:space": "cosine"},
        )
    return client.get_collection(name=name)
