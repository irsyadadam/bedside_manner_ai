"""Phase 2: PubMed discovery (ESearch + ESummary).

Workflow:
  1. ESearch with the configured query and usehistory="y".
  2. Print total count. If > esearch_retmax, STOP (refine query or --force).
  3. ESummary in batches via WebEnv/QueryKey, append to db/discovery.jsonl.
  4. Report total count, date distribution, top 10 journals, 10 sample titles.

Idempotent: re-running skips PMIDs already in discovery.jsonl.

Run:
  uv run python -m clinicomm.ingest.discovery --dry-run
  uv run python -m clinicomm.ingest.discovery
  uv run python -m clinicomm.ingest.discovery --summarize-only
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from collections import Counter
from pathlib import Path
from typing import Iterator

from rich.console import Console
from rich.table import Table
from tqdm import tqdm

from clinicomm.config import load_config
from clinicomm.ingest.eutils import EUtilsClient
from clinicomm.logging_setup import setup_logging

log = logging.getLogger("clinicomm.ingest.discovery")
console = Console()


def existing_pmids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    pmids: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                pmid = rec.get("pmid") or rec.get("uid")
                if pmid:
                    pmids.add(str(pmid))
            except json.JSONDecodeError:
                continue
    return pmids


def stream_summaries(
    client: EUtilsClient,
    webenv: str,
    query_key: str,
    total: int,
    batch_size: int,
) -> Iterator[dict]:
    """Yield one ESummary record dict per PMID."""
    for retstart in range(0, total, batch_size):
        size = min(batch_size, total - retstart)
        try:
            result = client.esummary(
                db="pubmed",
                webenv=webenv,
                query_key=query_key,
                retstart=retstart,
                retmax=size,
            )
        except Exception as e:  # noqa: BLE001 — log and continue across batches
            log.error("ESummary failed at retstart=%d size=%d: %s", retstart, size, e)
            continue
        uids = result.get("uids", [])
        for uid in uids:
            rec = result.get(uid)
            if not rec:
                continue
            yield {"pmid": str(uid), **rec}


def summarize(discovery_path: Path) -> None:
    if not discovery_path.exists():
        console.print(f"[red]discovery file not found: {discovery_path}[/red]")
        return

    records: list[dict] = []
    with discovery_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    console.print(f"\n[bold green]Total records:[/bold green] {len(records)}")

    # Year distribution from sortpubdate ("YYYY/MM/DD ...") or pubdate.
    years: Counter[str] = Counter()
    for r in records:
        s = r.get("sortpubdate") or r.get("pubdate") or ""
        if len(s) >= 4 and s[:4].isdigit():
            years[s[:4]] += 1

    if years:
        tbl = Table(title="Date distribution (by year)", show_lines=False)
        tbl.add_column("year")
        tbl.add_column("count", justify="right")
        tbl.add_column("bar", no_wrap=True)
        peak = max(years.values())
        for y in sorted(years):
            n = years[y]
            bar = "█" * max(1, int(40 * n / peak))
            tbl.add_row(y, str(n), bar)
        console.print(tbl)

    journals: Counter[str] = Counter()
    for r in records:
        j = (r.get("fulljournalname") or r.get("source") or "(unknown)").strip()
        journals[j] += 1
    tbl = Table(title="Top 10 journals")
    tbl.add_column("journal")
    tbl.add_column("count", justify="right")
    for j, c in journals.most_common(10):
        tbl.add_row(j, str(c))
    console.print(tbl)

    pub_types: Counter[str] = Counter()
    for r in records:
        for pt in r.get("pubtype", []) or []:
            pub_types[pt] += 1
    if pub_types:
        tbl = Table(title="Publication type counts")
        tbl.add_column("pubtype")
        tbl.add_column("count", justify="right")
        for pt, c in pub_types.most_common():
            tbl.add_row(pt, str(c))
        console.print(tbl)

    tbl = Table(title="Sample titles (first 10)")
    tbl.add_column("PMID", style="cyan")
    tbl.add_column("title")
    for r in records[:10]:
        title = (r.get("title") or "").strip()
        if len(title) > 110:
            title = title[:107] + "..."
        tbl.add_row(str(r.get("pmid", "?")), title)
    console.print(tbl)


def main() -> None:
    p = argparse.ArgumentParser(prog="clinicomm.ingest.discovery")
    p.add_argument("--config", default="config/pipeline.yaml")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Run ESearch only; print total count and exit (no ESummary).",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Proceed past the esearch_retmax cap.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap the number of summaries fetched (for testing).",
    )
    p.add_argument(
        "--summarize-only",
        action="store_true",
        help="Skip network. Compute stats from existing discovery.jsonl.",
    )
    args = p.parse_args()

    cfg = load_config(args.config)

    log_path = setup_logging(
        phase="phase02_discovery",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    discovery_path = Path(cfg["paths"]["discovery"])
    discovery_path.parent.mkdir(parents=True, exist_ok=True)

    if args.summarize_only:
        summarize(discovery_path)
        return

    pubmed_cfg = cfg["pubmed"]
    api_key = os.environ.get(pubmed_cfg["api_key_env"]) or None
    rate = (
        pubmed_cfg["rate_limit_with_key"] if api_key else pubmed_cfg["rate_limit_no_key"]
    )
    log.info(
        "NCBI rate limit: %s req/s (NCBI_API_KEY present: %s)", rate, bool(api_key)
    )

    email = os.environ.get(pubmed_cfg.get("email_env", "NCBI_EMAIL")) or pubmed_cfg["email"]
    client = EUtilsClient(
        tool="clinicomm",
        email=email,
        api_key=api_key,
        rate_per_sec=rate,
    )

    log.info("ESearch starting (db=pubmed, usehistory=y) ...")
    result = client.esearch(
        db="pubmed",
        term=pubmed_cfg["query"],
        retmax=pubmed_cfg["esearch_retmax"],
        use_history=pubmed_cfg["use_history"],
    )
    total = int(result["count"])
    webenv = result["webenv"]
    query_key = result["querykey"]
    log.info(
        "ESearch returned total=%d webenv=%s... query_key=%s",
        total,
        webenv[:12],
        query_key,
    )
    console.print(f"\n[bold green]ESearch total count:[/bold green] {total}")

    cap = pubmed_cfg["esearch_retmax"]
    if total > cap and not args.force:
        console.print(
            f"\n[yellow]STOP:[/yellow] total {total} exceeds esearch_retmax={cap}.\n"
            "  - Refine the query in config/pipeline.yaml, or\n"
            "  - re-run with --force to fetch all summaries via WebEnv pagination."
        )
        return

    if args.dry_run:
        console.print("\n[bold]--dry-run set; not fetching ESummary.[/bold]")
        return

    todo = min(args.limit, total) if args.limit else total

    existing = existing_pmids(discovery_path)
    log.info("Existing records in %s: %d", discovery_path, len(existing))

    new_count = 0
    skipped = 0
    batch_size = pubmed_cfg["esummary_batch"]
    with discovery_path.open("a", encoding="utf-8") as out, tqdm(
        total=todo, desc="ESummary", unit="rec"
    ) as bar:
        for record in stream_summaries(client, webenv, query_key, todo, batch_size):
            bar.update(1)
            if record["pmid"] in existing:
                skipped += 1
                continue
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            existing.add(record["pmid"])
            new_count += 1

    log.info("ESummary done. wrote=%d skipped=%d", new_count, skipped)
    console.print(
        f"\n[bold]ESummary complete[/bold]: wrote {new_count}, skipped {skipped} existing.\n"
    )
    summarize(discovery_path)


if __name__ == "__main__":
    main()
