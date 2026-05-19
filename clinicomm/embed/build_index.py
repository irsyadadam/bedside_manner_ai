"""Phase 5a: embed every chunk with BGE-large-en-v1.5 and upsert into
a persistent Chroma collection at index/chroma/.

Metadata stored per chunk (everything Module II will need for rerank):
  pmid, position, section_label, token_count,
  title, journal, pub_date, pub_year, pub_types, issuing_body

Chroma metadata values must be scalar — `pub_types` is stored as a
pipe-delimited string ("Journal Article|Systematic Review|...").

Idempotent: uses collection.upsert keyed by chunk_id, so re-running
replaces existing rows in place. To rebuild from scratch, pass --rebuild.

Run:
  uv run python -m clinicomm.embed.build_index --dry-run
  uv run python -m clinicomm.embed.build_index
  uv run python -m clinicomm.embed.build_index --rebuild
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
from pathlib import Path
from typing import Iterator

import torch
from rich.console import Console
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from clinicomm.config import load_config
from clinicomm.index.chroma_store import open_collection
from clinicomm.logging_setup import setup_logging

log = logging.getLogger("clinicomm.embed.build_index")
console = Console()


def iter_chunks_with_meta(
    chunks_dir: Path, parsed_dir: Path
) -> Iterator[tuple[dict, dict]]:
    """Yield (chunk, doc_meta) — doc_meta is the parsed-doc fields we
    want copied into Chroma metadata."""
    for fp in sorted(chunks_dir.glob("*.jsonl")):
        pmid = fp.stem
        parsed_path = parsed_dir / f"{pmid}.json"
        if not parsed_path.exists():
            continue
        doc = json.loads(parsed_path.read_text(encoding="utf-8"))
        pub_date = doc.get("pub_date") or ""
        pub_year = int(pub_date[:4]) if pub_date[:4].isdigit() else 0
        meta = {
            "pmid": pmid,
            "title": (doc.get("title") or "")[:512],
            "journal": doc.get("journal") or "",
            "pub_date": pub_date,
            "pub_year": pub_year,
            "pub_types": "|".join(doc.get("pub_types") or []),
            "issuing_body": doc.get("issuing_body") or "",
        }
        with fp.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line), meta


def batched(items, n: int):
    buf = []
    for it in items:
        buf.append(it)
        if len(buf) >= n:
            yield buf
            buf = []
    if buf:
        yield buf


def main() -> None:
    p = argparse.ArgumentParser(prog="clinicomm.embed.build_index")
    p.add_argument("--config", default="config/pipeline.yaml")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Load model + count chunks; do not write to Chroma.",
    )
    p.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete index/chroma/ before building.",
    )
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()

    cfg = load_config(args.config)
    log_path = setup_logging(
        phase="phase05_build_index",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    chunks_dir = Path(cfg["paths"]["db_chunks"])
    parsed_dir = Path(cfg["paths"]["db_parsed"])
    persist_dir = Path(cfg["index"]["persist_dir"])

    if args.rebuild and persist_dir.exists():
        log.warning("--rebuild: removing %s", persist_dir)
        shutil.rmtree(persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    model_name = cfg["embedding"]["model"]
    batch_size = cfg["embedding"]["batch_size"]
    use_gpu = cfg["embedding"]["use_gpu_if_available"] and torch.cuda.is_available()
    device = "cuda" if use_gpu else "cpu"
    log.info(
        "Loading SentenceTransformer model=%s device=%s batch=%d",
        model_name,
        device,
        batch_size,
    )
    model = SentenceTransformer(model_name, device=device)
    log.info(
        "Model ready. dim=%d max_seq_len=%d",
        model.get_sentence_embedding_dimension(),
        model.max_seq_length,
    )

    # Collect chunks
    pairs = list(iter_chunks_with_meta(chunks_dir, parsed_dir))
    if args.limit:
        pairs = pairs[: args.limit]
    log.info("Chunks to index: %d", len(pairs))

    if args.dry_run:
        # Encode a small sample so we exercise the pipeline
        sample = [c["text"] for c, _ in pairs[:8]]
        emb = model.encode(sample, normalize_embeddings=True, batch_size=batch_size)
        log.info(
            "Dry-run: encoded %d sample texts, embedding shape %s",
            len(sample),
            tuple(emb.shape),
        )
        console.print(
            f"[bold]Dry run:[/bold] would index {len(pairs)} chunks into "
            f"{persist_dir}/ (collection={cfg['index']['collection_name']})"
        )
        return

    coll = open_collection(persist_dir, cfg["index"]["collection_name"])
    log.info(
        "Collection '%s' opened. existing count=%d",
        cfg["index"]["collection_name"],
        coll.count(),
    )

    # Index in batches of `batch_size` so we never hold all embeddings in RAM.
    total_added = 0
    with tqdm(total=len(pairs), desc="embed+upsert", unit="chunk") as bar:
        for batch in batched(pairs, batch_size):
            ids = [c["chunk_id"] for c, _ in batch]
            texts = [c["text"] for c, _ in batch]
            metas = []
            for c, doc_meta in batch:
                m = dict(doc_meta)
                m["position"] = int(c.get("position", 0))
                m["section_label"] = c.get("section_label") or ""
                m["token_count"] = int(c.get("token_count", 0))
                metas.append(m)
            embeddings = model.encode(
                texts,
                normalize_embeddings=True,
                batch_size=len(texts),
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            coll.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings.tolist(),
                metadatas=metas,
            )
            total_added += len(batch)
            bar.update(len(batch))

    final_count = coll.count()
    log.info(
        "Indexing done. upserted=%d collection_count_now=%d",
        total_added,
        final_count,
    )
    console.print(
        f"\n[bold]Index summary[/bold]\n"
        f"  chunks upserted: {total_added}\n"
        f"  Chroma collection count: {final_count}\n"
        f"  persist dir: {persist_dir}\n"
        f"  embedding dim: {model.get_sentence_embedding_dimension()}\n"
        f"  device: {device}"
    )


if __name__ == "__main__":
    main()
