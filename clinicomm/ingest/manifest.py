"""Phase 6: corpus manifest + README summary.

Outputs:
  - db/manifest.jsonl     : one line per parsed PMID with full provenance
  - README.md             : refreshes a marker-delimited block with corpus
                            stats (idempotent — replaces in place if present)

Run:
  uv run python -m clinicomm.ingest.manifest
  uv run python -m clinicomm.ingest.manifest --dry-run    # no writes
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

from clinicomm.config import load_config
from clinicomm.index.chroma_store import open_collection
from clinicomm.logging_setup import setup_logging

log = logging.getLogger("clinicomm.ingest.manifest")
console = Console()

README_BEGIN = "<!-- BEGIN AUTO-CORPUS-SUMMARY -->"
README_END = "<!-- END AUTO-CORPUS-SUMMARY -->"


def _read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def build_manifest(cfg: dict) -> tuple[list[dict], dict]:
    """Build the per-doc manifest list and a summary dict."""
    parsed_dir = Path(cfg["paths"]["db_parsed"])
    chunks_dir = Path(cfg["paths"]["db_chunks"])
    raw_dir = Path(cfg["paths"]["db_raw"])

    parsed_files = sorted(parsed_dir.glob("*.json"))
    rows: list[dict] = []

    # Aggregators for the summary
    pub_types_ct: Counter[str] = Counter()
    journals_ct: Counter[str] = Counter()
    mesh_ct: Counter[str] = Counter()
    year_ct: Counter[int] = Counter()
    n_structured = 0
    total_chunks = 0
    total_tokens = 0
    docs_with_doi = 0
    docs_with_issuing = 0

    for fp in parsed_files:
        doc = json.loads(fp.read_text(encoding="utf-8"))
        pmid = doc["pmid"]
        chunks_path = chunks_dir / f"{pmid}.jsonl"
        chunks = _read_jsonl(chunks_path) if chunks_path.exists() else []
        n_chunks = len(chunks)
        chunk_tokens = sum(c.get("token_count", 0) for c in chunks)
        structured = any(s.get("section_label") for s in doc.get("abstract") or [])
        mesh_names = [
            mh["descriptor"]
            for mh in (doc.get("mesh_headings") or [])
            if mh.get("descriptor")
        ]
        pub_date = doc.get("pub_date") or ""
        pub_year = int(pub_date[:4]) if pub_date[:4].isdigit() else None

        row = {
            "pmid": pmid,
            "doi": doc.get("doi"),
            "title": doc.get("title"),
            "journal": doc.get("journal"),
            "pub_date": pub_date or None,
            "pub_year": pub_year,
            "pub_types": doc.get("pub_types") or [],
            "issuing_body": doc.get("issuing_body"),
            "n_authors": len(doc.get("authors") or []),
            "mesh_descriptors": mesh_names,
            "n_mesh_headings": len(mesh_names),
            "abstract_structured": structured,
            "abstract_section_count": len(doc.get("abstract") or []),
            "abstract_total_chars": sum(
                len(s.get("text", "")) for s in doc.get("abstract") or []
            ),
            "n_chunks": n_chunks,
            "chunk_token_total": chunk_tokens,
            "provenance": {
                "raw_xml": str(raw_dir / f"{pmid}.xml"),
                "parsed_json": str(fp),
                "chunks_jsonl": str(chunks_path) if chunks_path.exists() else None,
            },
        }
        rows.append(row)

        # Update aggregators
        for pt in row["pub_types"]:
            pub_types_ct[pt] += 1
        if row["journal"]:
            journals_ct[row["journal"]] += 1
        for d in mesh_names:
            mesh_ct[d] += 1
        if pub_year is not None:
            year_ct[pub_year] += 1
        if structured:
            n_structured += 1
        total_chunks += n_chunks
        total_tokens += chunk_tokens
        if row["doi"]:
            docs_with_doi += 1
        if row["issuing_body"]:
            docs_with_issuing += 1

    # Chroma vector count
    chroma_count = 0
    try:
        coll = open_collection(
            cfg["index"]["persist_dir"],
            cfg["index"]["collection_name"],
            create_if_missing=False,
        )
        chroma_count = coll.count()
    except Exception as e:  # noqa: BLE001
        log.warning("Could not open Chroma collection: %s", e)

    # Discovery + raw counts
    discovery_path = Path(cfg["paths"]["discovery"])
    n_discovery = sum(1 for _ in discovery_path.open()) if discovery_path.exists() else 0
    n_raw = len(list(raw_dir.glob("*.xml")))
    n_parsed = len(parsed_files)

    years = sorted(year_ct.keys())
    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "discovery_pmids": n_discovery,
        "raw_xml_count": n_raw,
        "parsed_doc_count": n_parsed,
        "chunk_count": total_chunks,
        "chroma_vector_count": chroma_count,
        "structured_abstract_count": n_structured,
        "docs_with_doi": docs_with_doi,
        "docs_with_issuing_body": docs_with_issuing,
        "year_min": years[0] if years else None,
        "year_max": years[-1] if years else None,
        "median_year": years[len(years) // 2] if years else None,
        "total_chunk_tokens": total_tokens,
        "pub_types_top": pub_types_ct.most_common(),
        "journals_top20": journals_ct.most_common(20),
        "mesh_top30": mesh_ct.most_common(30),
        "years_distribution": dict(sorted(year_ct.items())),
        "embedding": {
            "model": cfg["embedding"]["model"],
            "dim": 1024,  # BGE-large-en-v1.5
            "max_seq_len": 512,
            "chunk_size_tokens": cfg["embedding"]["chunk_size_tokens"],
            "chunk_overlap_tokens": cfg["embedding"]["chunk_overlap_tokens"],
        },
        "index": {
            "backend": cfg["index"]["backend"],
            "persist_dir": cfg["index"]["persist_dir"],
            "collection_name": cfg["index"]["collection_name"],
            "distance": "cosine",
        },
        "pubmed_query": cfg["pubmed"]["query"].strip(),
    }
    return rows, summary


def render_readme_block(summary: dict) -> str:
    lines: list[str] = []
    a = lines.append
    a(README_BEGIN)
    a("")
    a(f"_Last refreshed: {summary['generated_utc']}_")
    a("")
    a("### Pipeline state")
    a("```")
    a(f"  Discovery PMIDs (Phase 2):   {summary['discovery_pmids']}")
    a(f"  Raw XML records (Phase 3):   {summary['raw_xml_count']}")
    a(f"  Parsed documents (Phase 3):  {summary['parsed_doc_count']}")
    a(f"  Total chunks (Phase 4):      {summary['chunk_count']}")
    a(f"  Indexed vectors (Phase 5):   {summary['chroma_vector_count']}")
    a(
        f"  Structured abstracts:        {summary['structured_abstract_count']} "
        f"({100 * summary['structured_abstract_count'] / max(1, summary['parsed_doc_count']):.1f}%)"
    )
    a(f"  Records with DOI:            {summary['docs_with_doi']}")
    a(
        f"  Records with issuing_body:   {summary['docs_with_issuing_body']} "
        f"(guideline collective authors)"
    )
    a(f"  Total chunk tokens:          {summary['total_chunk_tokens']:,}")
    a("```")
    a("")

    a("### Date range")
    a("```")
    a(f"  Earliest year: {summary['year_min']}")
    a(f"  Latest year:   {summary['year_max']}")
    a(f"  Median year:   {summary['median_year']}")
    a("")
    yd = summary["years_distribution"]
    peak = max(yd.values()) if yd else 1
    for y in sorted(yd):
        n = yd[y]
        bar = "#" * max(1, int(40 * n / peak))
        a(f"  {y}: {n:>4}  {bar}")
    a("```")
    a("")

    a("### Pub-type breakdown")
    a("```")
    for pt, c in summary["pub_types_top"]:
        a(f"  {pt:<48} {c:>5}")
    a("```")
    a("")

    a("### Top 20 journals")
    a("```")
    for j, c in summary["journals_top20"]:
        a(f"  {j[:64]:<64} {c:>4}")
    a("```")
    a("")

    a("### Top 30 MeSH descriptors")
    a("```")
    for d, c in summary["mesh_top30"]:
        a(f"  {d[:48]:<48} {c:>5}")
    a("```")
    a("")

    e = summary["embedding"]
    i = summary["index"]
    a("### Embedding + index")
    a("```")
    a(f"  Embedding model:  {e['model']}")
    a(f"  Dimension:        {e['dim']}")
    a(f"  Max seq length:   {e['max_seq_len']}")
    a(
        f"  Chunk size / overlap (tokens): {e['chunk_size_tokens']} / "
        f"{e['chunk_overlap_tokens']}"
    )
    a(f"  Index backend:    {i['backend']} ({i['distance']})")
    a(f"  Persist dir:      {i['persist_dir']}")
    a(f"  Collection name:  {i['collection_name']}")
    a("```")
    a("")

    a("### PubMed query used (verbatim from config/pipeline.yaml)")
    a("```")
    for line in summary["pubmed_query"].splitlines():
        a("  " + line)
    a("```")
    a("")

    a("### Data lineage")
    a("```")
    a("  db/discovery.jsonl          Phase 2 — ESummary metadata per PMID")
    a("  db/raw/<PMID>.xml           Phase 3 — raw EFetch XML")
    a("  db/parsed/<PMID>.json       Phase 3 — normalized JSON (ParsedDocument)")
    a("  db/chunks/<PMID>.jsonl      Phase 4 — one Chunk per line")
    a("  index/chroma/               Phase 5 — Chroma persistent collection")
    a("  db/manifest.jsonl           Phase 6 — per-doc provenance index")
    a("  logs/sanity_query_*.json    Phase 5 — sanity-query persisted results")
    a("  logs/<phase>_<UTC>.log      every phase — per-run audit log")
    a("```")
    a("")
    a(README_END)
    return "\n".join(lines)


def upsert_readme_block(readme_path: Path, new_block: str) -> tuple[bool, bool]:
    """Insert or replace the auto-summary block. Returns (replaced, written)."""
    old = readme_path.read_text(encoding="utf-8")
    pat = re.compile(
        re.escape(README_BEGIN) + r".*?" + re.escape(README_END), re.DOTALL
    )
    if pat.search(old):
        new = pat.sub(new_block, old)
        replaced = True
    else:
        if not old.endswith("\n"):
            old = old + "\n"
        new = (
            old
            + "\n"
            + "================================================================================\n"
            + "CORPUS SUMMARY (Phase 6, auto-generated — refreshed by\n"
            + "`uv run python -m clinicomm.ingest.manifest`)\n"
            + "================================================================================\n\n"
            + new_block
            + "\n"
        )
        replaced = False
    readme_path.write_text(new, encoding="utf-8")
    return replaced, True


def main() -> None:
    p = argparse.ArgumentParser(prog="clinicomm.ingest.manifest")
    p.add_argument("--config", default="config/pipeline.yaml")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--readme", default="README.md")
    args = p.parse_args()

    cfg = load_config(args.config)
    log_path = setup_logging(
        phase="phase06_manifest",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    rows, summary = build_manifest(cfg)
    manifest_path = Path(cfg["paths"]["manifest"])
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        console.print(
            f"[bold]Dry run.[/bold] would write {len(rows)} rows to {manifest_path}"
        )
    else:
        tmp = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        tmp.replace(manifest_path)
        log.info("Wrote %s (%d rows)", manifest_path, len(rows))

    block = render_readme_block(summary)
    readme_path = Path(args.readme)
    if args.dry_run:
        console.print(
            f"[bold]Dry run.[/bold] would refresh corpus-summary block in {readme_path}"
        )
    else:
        replaced, _ = upsert_readme_block(readme_path, block)
        log.info(
            "README %s: %s",
            readme_path,
            "replaced existing block" if replaced else "appended new block",
        )

    tbl = Table(title="Corpus at a glance")
    tbl.add_column("metric")
    tbl.add_column("value", justify="right")
    tbl.add_row("Discovery PMIDs", str(summary["discovery_pmids"]))
    tbl.add_row("Raw XML", str(summary["raw_xml_count"]))
    tbl.add_row("Parsed docs", str(summary["parsed_doc_count"]))
    tbl.add_row("Chunks", str(summary["chunk_count"]))
    tbl.add_row("Chroma vectors", str(summary["chroma_vector_count"]))
    tbl.add_row(
        "Year range",
        f"{summary['year_min']}–{summary['year_max']} (median {summary['median_year']})",
    )
    tbl.add_row("Structured abstracts", str(summary["structured_abstract_count"]))
    tbl.add_row("DOIs", str(summary["docs_with_doi"]))
    tbl.add_row("Issuing bodies", str(summary["docs_with_issuing_body"]))
    tbl.add_row("Total chunk tokens", f"{summary['total_chunk_tokens']:,}")
    console.print(tbl)


if __name__ == "__main__":
    main()
