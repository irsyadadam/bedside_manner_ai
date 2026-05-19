"""Phase 5b: run the spec's 5 hard-coded sanity queries against the
Chroma index. Print top-5 per query and persist the raw results to
logs/sanity_query_<UTC>.json for Phase 12 (appendix table).

Usage:
  uv run python scripts/sanity_query.py
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import torch
from rich.console import Console
from rich.table import Table
from sentence_transformers import SentenceTransformer

from clinicomm.config import load_config
from clinicomm.index.chroma_store import open_collection
from clinicomm.logging_setup import setup_logging

log = logging.getLogger("clinicomm.sanity_query")
console = Console()

QUERIES = [
    "patient with fatigue and weight loss",
    "managing hypertension in primary care",
    "communicating bad news to patients",
    "screening for depression adult",
    "evaluating chronic cough",
]


def main() -> None:
    cfg = load_config()
    log_path = setup_logging(
        phase="phase05_sanity_query",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    device = (
        "cuda"
        if (cfg["embedding"]["use_gpu_if_available"] and torch.cuda.is_available())
        else "cpu"
    )
    log.info("Loading SentenceTransformer %s on %s", cfg["embedding"]["model"], device)
    model = SentenceTransformer(cfg["embedding"]["model"], device=device)

    coll = open_collection(
        cfg["index"]["persist_dir"],
        cfg["index"]["collection_name"],
        create_if_missing=False,
    )
    log.info("Chroma collection size: %d", coll.count())

    embeddings = model.encode(
        QUERIES, normalize_embeddings=True, convert_to_numpy=True
    ).tolist()

    results_payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model": cfg["embedding"]["model"],
        "collection": cfg["index"]["collection_name"],
        "collection_size": coll.count(),
        "queries": [],
    }

    for query, emb in zip(QUERIES, embeddings):
        res = coll.query(
            query_embeddings=[emb],
            n_results=5,
            include=["documents", "metadatas", "distances"],
        )
        ids = res["ids"][0]
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]
        per_query = {
            "query": query,
            "results": [
                {
                    "rank": i + 1,
                    "chunk_id": ids[i],
                    "pmid": metas[i].get("pmid"),
                    "section_label": metas[i].get("section_label"),
                    "title": metas[i].get("title"),
                    "journal": metas[i].get("journal"),
                    "pub_date": metas[i].get("pub_date"),
                    "pub_types": metas[i].get("pub_types"),
                    # Chroma returns cosine *distance* (1 - cos). Lower=better.
                    "cosine_distance": float(dists[i]),
                    "similarity": 1.0 - float(dists[i]),
                    "text": docs[i],
                }
                for i in range(len(ids))
            ],
        }
        results_payload["queries"].append(per_query)

        tbl = Table(title=f"Query: \"{query}\"")
        tbl.add_column("#", justify="right")
        tbl.add_column("sim", justify="right")
        tbl.add_column("PMID")
        tbl.add_column("section")
        tbl.add_column("journal")
        tbl.add_column("year")
        tbl.add_column("title (truncated)")
        for r in per_query["results"]:
            year = (r["pub_date"] or "")[:4]
            tbl.add_row(
                str(r["rank"]),
                f"{r['similarity']:.3f}",
                r["pmid"],
                (r["section_label"] or "")[:14],
                (r["journal"] or "")[:28],
                year,
                (r["title"] or "")[:60],
            )
        console.print(tbl)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = Path(cfg["paths"]["logs"]) / f"sanity_query_{ts}.json"
    out_path.write_text(json.dumps(results_payload, indent=2), encoding="utf-8")
    log.info("Wrote %s", out_path)
    console.print(f"\nPersisted raw results to [cyan]{out_path}[/cyan]")


if __name__ == "__main__":
    main()
