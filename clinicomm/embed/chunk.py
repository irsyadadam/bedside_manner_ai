"""Phase 4: chunk parsed abstracts.

Rules:
  - Structured abstract -> one chunk per labeled section (preserves
    BACKGROUND/METHODS/RESULTS/etc. structure verbatim).
  - Unstructured abstract -> 400-token sliding window with 50-token
    overlap over the single section.
  - Token counts use the embedding model's own tokenizer (so what we
    count here matches what Phase 5 will feed to BGE).

Output: one JSONL file per PMID at db/chunks/<PMID>.jsonl, one Chunk
per line, ordered by position.

Idempotent: skips PMIDs whose chunks file already exists (unless --force).

Run:
  uv run python -m clinicomm.embed.chunk --dry-run
  uv run python -m clinicomm.embed.chunk
  uv run python -m clinicomm.embed.chunk --summarize-only
"""
from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Iterator

from rich.console import Console
from rich.table import Table
from tqdm import tqdm
from transformers import AutoTokenizer

from clinicomm.config import load_config
from clinicomm.logging_setup import setup_logging
from clinicomm.schemas import Chunk, ParsedDocument

log = logging.getLogger("clinicomm.embed.chunk")
console = Console()


def count_tokens(tokenizer, text: str) -> int:
    return len(tokenizer.encode(text, add_special_tokens=False))


def slide_chunks(
    tokenizer, text: str, chunk_size: int, overlap: int
) -> Iterator[tuple[str, int]]:
    """Yield (chunk_text, token_count) pairs covering `text` with a
    sliding window of `chunk_size` tokens and `overlap` tokens of overlap.

    Uses offset_mapping so each yielded text is the exact substring of
    the input that those tokens span — no tokenizer round-trip drift.
    """
    enc = tokenizer(
        text,
        add_special_tokens=False,
        return_offsets_mapping=True,
        truncation=False,
    )
    ids = enc["input_ids"]
    offsets = enc["offset_mapping"]
    if not ids:
        return
    if len(ids) <= chunk_size:
        yield text.strip(), len(ids)
        return
    step = chunk_size - overlap
    if step <= 0:
        raise ValueError(f"overlap ({overlap}) must be < chunk_size ({chunk_size})")
    start = 0
    while start < len(ids):
        end = min(start + chunk_size, len(ids))
        char_start = offsets[start][0]
        char_end = offsets[end - 1][1]
        sub = text[char_start:char_end].strip()
        if sub:
            yield sub, end - start
        if end == len(ids):
            break
        start += step


def chunk_document(
    tokenizer, doc: ParsedDocument, chunk_size: int, overlap: int
) -> list[Chunk]:
    chunks: list[Chunk] = []
    structured = any(s.section_label for s in doc.abstract)
    position = 0
    if structured:
        for section in doc.abstract:
            text = section.text.strip()
            if not text:
                continue
            tok = count_tokens(tokenizer, text)
            if tok <= chunk_size:
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc.pmid}_{position:03d}",
                        pmid=doc.pmid,
                        section_label=section.section_label,
                        position=position,
                        text=text,
                        token_count=tok,
                    )
                )
                position += 1
            else:
                # Section longer than the embedding model's chunk budget —
                # slide within it while keeping the section_label on each
                # sub-chunk, so retrieval still attributes them correctly.
                for sub, sub_tok in slide_chunks(tokenizer, text, chunk_size, overlap):
                    chunks.append(
                        Chunk(
                            chunk_id=f"{doc.pmid}_{position:03d}",
                            pmid=doc.pmid,
                            section_label=section.section_label,
                            position=position,
                            text=sub,
                            token_count=sub_tok,
                        )
                    )
                    position += 1
    else:
        full = " ".join(s.text.strip() for s in doc.abstract if s.text.strip())
        for sub, tok in slide_chunks(tokenizer, full, chunk_size, overlap):
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.pmid}_{position:03d}",
                    pmid=doc.pmid,
                    section_label=None,
                    position=position,
                    text=sub,
                    token_count=tok,
                )
            )
            position += 1
    return chunks


def write_chunks(chunks: list[Chunk], out_path: Path) -> None:
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(c.model_dump_json() + "\n")
    tmp.replace(out_path)  # atomic on POSIX


def load_chunks(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def summarize(chunks_dir: Path, chunk_size: int) -> None:
    files = sorted(chunks_dir.glob("*.jsonl"))
    if not files:
        console.print(f"[red]no chunk files in {chunks_dir}[/red]")
        return

    chunks_per_doc: Counter[int] = Counter()
    token_buckets: Counter[str] = Counter()
    section_labels: Counter[str] = Counter()
    structured_docs = 0
    unstructured_docs = 0
    over_limit = 0
    total_chunks = 0
    longest: tuple[int, str] | None = None  # (token_count, chunk_id)

    for fp in files:
        chunks = load_chunks(fp)
        n = len(chunks)
        chunks_per_doc[n] += 1
        total_chunks += n
        has_label = any(c.get("section_label") for c in chunks)
        if has_label:
            structured_docs += 1
        else:
            unstructured_docs += 1
        for c in chunks:
            lbl = c.get("section_label") or "(unstructured)"
            section_labels[lbl] += 1
            tc = c.get("token_count", 0)
            if longest is None or tc > longest[0]:
                longest = (tc, c.get("chunk_id", "?"))
            if tc > chunk_size:
                over_limit += 1
            if tc <= 50:
                token_buckets["<=50"] += 1
            elif tc <= 100:
                token_buckets["51-100"] += 1
            elif tc <= 200:
                token_buckets["101-200"] += 1
            elif tc <= 400:
                token_buckets["201-400"] += 1
            else:
                token_buckets[">400"] += 1

    console.print(
        f"\n[bold green]Total chunks:[/bold green] {total_chunks} "
        f"across {len(files)} documents"
    )
    console.print(
        f"  structured documents:   {structured_docs}\n"
        f"  unstructured documents: {unstructured_docs}\n"
        f"  chunks exceeding {chunk_size}-token target: {over_limit}\n"
        f"  longest chunk: {longest[0]} tokens ({longest[1]})"
    )

    tbl = Table(title="Chunks per document (distribution)")
    tbl.add_column("chunks")
    tbl.add_column("# docs", justify="right")
    tbl.add_column("bar", no_wrap=True)
    peak = max(chunks_per_doc.values())
    for n in sorted(chunks_per_doc):
        c = chunks_per_doc[n]
        bar = "█" * max(1, int(40 * c / peak))
        tbl.add_row(str(n), str(c), bar)
    console.print(tbl)

    tbl = Table(title="Section labels (top 15)")
    tbl.add_column("label")
    tbl.add_column("count", justify="right")
    for lbl, c in section_labels.most_common(15):
        tbl.add_row(lbl, str(c))
    console.print(tbl)

    tbl = Table(title="Token-count buckets")
    tbl.add_column("range")
    tbl.add_column("count", justify="right")
    for r in ["<=50", "51-100", "101-200", "201-400", ">400"]:
        tbl.add_row(r, str(token_buckets.get(r, 0)))
    console.print(tbl)


def show_examples(chunks_dir: Path, parsed_dir: Path) -> None:
    files = list(chunks_dir.glob("*.jsonl"))
    if not files:
        return
    # Pick one structured (>=2 chunks, all with section_label) and
    # one unstructured (chunks with section_label=None).
    structured: Path | None = None
    unstructured: Path | None = None
    long_unstructured: Path | None = None
    for fp in files:
        chunks = load_chunks(fp)
        if not chunks:
            continue
        all_labeled = all(c.get("section_label") for c in chunks)
        none_labeled = all(c.get("section_label") is None for c in chunks)
        if structured is None and all_labeled and len(chunks) >= 3:
            structured = fp
        if unstructured is None and none_labeled and len(chunks) == 1:
            unstructured = fp
        if long_unstructured is None and none_labeled and len(chunks) >= 2:
            long_unstructured = fp
        if structured and unstructured and long_unstructured:
            break

    for label, fp in [
        ("structured (multi-section)", structured),
        ("unstructured (single window)", unstructured),
        ("unstructured (sliding window, multiple)", long_unstructured),
    ]:
        if fp is None:
            continue
        chunks = load_chunks(fp)
        pmid = chunks[0]["pmid"]
        parsed = json.loads((parsed_dir / f"{pmid}.json").read_text(encoding="utf-8"))
        title = (parsed.get("title") or "").strip()
        console.print(
            f"\n[bold]Example — {label}[/bold]\n"
            f"  PMID:  {pmid}\n"
            f"  Title: {title[:110]}\n"
            f"  Chunks: {len(chunks)}"
        )
        for c in chunks[:6]:
            lbl = c.get("section_label") or "(unlabeled)"
            text = c.get("text", "")
            preview = text[:160] + ("..." if len(text) > 160 else "")
            console.print(
                f"    [{c['position']:02d}] tok={c['token_count']:>3} "
                f"label={lbl!s:<30} {preview}"
            )


def main() -> None:
    p = argparse.ArgumentParser(prog="clinicomm.embed.chunk")
    p.add_argument("--config", default="config/pipeline.yaml")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Tokenize and count, but do not write files.",
    )
    p.add_argument(
        "--summarize-only",
        action="store_true",
        help="Compute stats from existing db/chunks/ without re-chunking.",
    )
    p.add_argument("--limit", type=int, default=None)
    p.add_argument(
        "--force",
        action="store_true",
        help="Re-chunk even if a chunks file already exists.",
    )
    args = p.parse_args()

    cfg = load_config(args.config)
    log_path = setup_logging(
        phase="phase04_chunk",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    parsed_dir = Path(cfg["paths"]["db_parsed"])
    chunks_dir = Path(cfg["paths"]["db_chunks"])
    chunks_dir.mkdir(parents=True, exist_ok=True)

    if args.summarize_only:
        summarize(chunks_dir, cfg["embedding"]["chunk_size_tokens"])
        show_examples(chunks_dir, parsed_dir)
        return

    chunk_size = cfg["embedding"]["chunk_size_tokens"]
    overlap = cfg["embedding"]["chunk_overlap_tokens"]
    model_name = cfg["embedding"]["model"]

    log.info("Loading tokenizer for %s ...", model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    log.info(
        "Tokenizer ready (vocab=%d, fast=%s)",
        tokenizer.vocab_size,
        tokenizer.is_fast,
    )

    parsed_files = sorted(parsed_dir.glob("*.json"))
    if args.limit:
        parsed_files = parsed_files[: args.limit]
    log.info("Parsed docs to chunk: %d", len(parsed_files))

    done = 0
    skipped = 0
    written = 0
    total_chunks = 0
    over_limit = 0
    drop_empty = 0
    for fp in tqdm(parsed_files, desc="chunk", unit="doc"):
        out_path = chunks_dir / f"{fp.stem}.jsonl"
        if out_path.exists() and not args.force:
            skipped += 1
            continue
        try:
            doc = ParsedDocument.model_validate_json(fp.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            log.error("validate failed %s: %s", fp.name, e)
            continue
        chunks = chunk_document(tokenizer, doc, chunk_size, overlap)
        if not chunks:
            drop_empty += 1
            continue
        over_limit += sum(1 for c in chunks if c.token_count > chunk_size)
        total_chunks += len(chunks)
        if not args.dry_run:
            write_chunks(chunks, out_path)
            written += 1
        done += 1

    log.info(
        "Chunking done. processed=%d wrote=%d skipped=%d empty=%d "
        "total_chunks=%d over_limit=%d",
        done,
        written,
        skipped,
        drop_empty,
        total_chunks,
        over_limit,
    )
    console.print(
        f"\n[bold]Chunking summary[/bold]\n"
        f"  docs processed:    {done}\n"
        f"  files written:     {written}\n"
        f"  skipped (existed): {skipped}\n"
        f"  empty (no chunks): {drop_empty}\n"
        f"  total chunks:      {total_chunks}\n"
        f"  over-{chunk_size}-token chunks: {over_limit}"
    )

    if args.dry_run:
        return

    summarize(chunks_dir, chunk_size)
    show_examples(chunks_dir, parsed_dir)


if __name__ == "__main__":
    main()
