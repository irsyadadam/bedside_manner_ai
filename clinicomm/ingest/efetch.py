"""Phase 3: EFetch XML for each PMID, save raw + parsed JSON.

Workflow:
  1. Read PMIDs from db/discovery.jsonl (Phase 2 output).
  2. Skip PMIDs already processed (both raw + parsed present).
  3. EFetch in batches of efetch_batch (50 per config).
  4. For each <PubmedArticle>:
       - Always save db/raw/<PMID>.xml (so re-parsing skips the network).
       - Parse into ParsedDocument. Drop records with no abstract.
       - Write db/parsed/<PMID>.json.
  5. Report retention, show 3 example parsed JSONs.

Flags:
  --dry-run         : list how many would be fetched and exit.
  --reparse-only    : skip network; re-parse all db/raw/*.xml.
  --limit N         : cap PMIDs (testing).
  --summarize-only  : just print stats from db/parsed/.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
from collections import Counter
from pathlib import Path
from typing import Iterable

from lxml import etree
from rich.console import Console
from rich.table import Table
from tqdm import tqdm

from clinicomm.config import load_config
from clinicomm.ingest.eutils import EUtilsClient
from clinicomm.logging_setup import setup_logging
from clinicomm.parse.pubmed_xml import parse_pubmed_articles

log = logging.getLogger("clinicomm.ingest.efetch")
console = Console()


def load_pmids(discovery_path: Path) -> list[str]:
    pmids: list[str] = []
    with discovery_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            pmid = rec.get("pmid") or rec.get("uid")
            if pmid:
                pmids.append(str(pmid))
    return pmids


def chunked(seq: list[str], n: int) -> Iterable[list[str]]:
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def reparse_local(raw_dir: Path, parsed_dir: Path) -> tuple[int, int, Counter]:
    """Re-parse all db/raw/*.xml. Returns (saved, dropped, drop_reasons)."""
    saved = 0
    dropped = 0
    drop_reasons: Counter[str] = Counter()
    xml_files = sorted(raw_dir.glob("*.xml"))
    for xml_path in tqdm(xml_files, desc="reparse"):
        try:
            xml_bytes = xml_path.read_bytes()
        except OSError as e:
            log.error("read failed %s: %s", xml_path, e)
            continue
        # Each raw/<PMID>.xml holds one <PubmedArticle>. Wrap in a fake
        # parent so parse_pubmed_articles can use .iter("PubmedArticle").
        wrapped = b"<PubmedArticleSet>" + xml_bytes + b"</PubmedArticleSet>"
        for pmid, _node, parsed, reason in parse_pubmed_articles(wrapped):
            if parsed is None:
                dropped += 1
                drop_reasons[reason or "unknown"] += 1
                continue
            (parsed_dir / f"{parsed.pmid}.json").write_text(
                parsed.model_dump_json(indent=2), encoding="utf-8"
            )
            saved += 1
    return saved, dropped, drop_reasons


def fetch_and_persist(
    client: EUtilsClient,
    pmids: list[str],
    raw_dir: Path,
    parsed_dir: Path,
    batch_size: int,
) -> tuple[int, int, int, Counter]:
    """Returns (fetched_articles, parsed_saved, dropped, drop_reasons)."""
    fetched = 0
    saved = 0
    dropped = 0
    drop_reasons: Counter[str] = Counter()
    with tqdm(total=len(pmids), desc="EFetch", unit="rec") as bar:
        for batch in chunked(pmids, batch_size):
            try:
                xml_text = client.efetch(
                    db="pubmed", ids=batch, rettype="xml", retmode="xml"
                )
            except Exception as e:  # noqa: BLE001
                log.error("EFetch batch failed (%d ids): %s", len(batch), e)
                bar.update(len(batch))
                continue
            xml_bytes = xml_text.encode("utf-8")
            # Track which PMIDs in the batch were seen so the bar advances
            # correctly even if PubMed silently omits one.
            seen_in_batch: set[str] = set()
            try:
                for pmid, node, parsed, reason in parse_pubmed_articles(xml_bytes):
                    fetched += 1
                    if pmid:
                        seen_in_batch.add(pmid)
                        # Always persist raw, even for dropped records.
                        raw_path = raw_dir / f"{pmid}.xml"
                        raw_path.write_bytes(etree.tostring(node, pretty_print=True))
                    if parsed is None:
                        dropped += 1
                        drop_reasons[reason or "unknown"] += 1
                        continue
                    (parsed_dir / f"{parsed.pmid}.json").write_text(
                        parsed.model_dump_json(indent=2), encoding="utf-8"
                    )
                    saved += 1
            except etree.XMLSyntaxError as e:
                log.error("XML parse failed for batch starting %s: %s", batch[0], e)
            bar.update(len(batch))
            missed = set(batch) - seen_in_batch
            if missed:
                log.warning(
                    "PubMed returned no <PubmedArticle> for %d PMIDs in batch: %s",
                    len(missed),
                    ",".join(sorted(missed)[:5]) + ("..." if len(missed) > 5 else ""),
                )
                dropped += len(missed)
                drop_reasons["not_returned_by_pubmed"] += len(missed)
    return fetched, saved, dropped, drop_reasons


def summarize(parsed_dir: Path, sample_n: int = 3) -> None:
    files = sorted(parsed_dir.glob("*.json"))
    console.print(f"\n[bold green]Parsed JSON count:[/bold green] {len(files)}")

    if not files:
        return

    structured = 0
    pub_type_ct: Counter[str] = Counter()
    abstract_lens: list[int] = []
    issuing_bodies = 0
    mesh_total = 0
    for fp in files:
        rec = json.loads(fp.read_text(encoding="utf-8"))
        sections = rec.get("abstract", [])
        if any(s.get("section_label") for s in sections):
            structured += 1
        abstract_lens.append(sum(len(s["text"]) for s in sections))
        for pt in rec.get("pub_types", []) or []:
            pub_type_ct[pt] += 1
        if rec.get("issuing_body"):
            issuing_bodies += 1
        mesh_total += len(rec.get("mesh_headings", []) or [])

    n = len(files)
    avg_len = sum(abstract_lens) / n if n else 0
    console.print(
        f"  structured abstracts: {structured} ({100 * structured / n:.1f}%)\n"
        f"  mean abstract length (chars): {avg_len:,.0f}\n"
        f"  records with issuing_body (collective author): {issuing_bodies}\n"
        f"  mean MeSH headings per record: {mesh_total / n:.1f}"
    )

    tbl = Table(title="Pub-type tallies (parsed corpus)")
    tbl.add_column("pubtype")
    tbl.add_column("count", justify="right")
    for pt, c in pub_type_ct.most_common(10):
        tbl.add_row(pt, str(c))
    console.print(tbl)

    # Show 3 examples — pick one structured, one unstructured, one guideline if available
    structured_ex = next(
        (
            f
            for f in files
            if any(
                s.get("section_label")
                for s in json.loads(f.read_text(encoding="utf-8")).get("abstract", [])
            )
        ),
        None,
    )
    unstructured_ex = next(
        (
            f
            for f in files
            if not any(
                s.get("section_label")
                for s in json.loads(f.read_text(encoding="utf-8")).get("abstract", [])
            )
        ),
        None,
    )
    guideline_ex = next(
        (
            f
            for f in files
            if "Practice Guideline"
            in (json.loads(f.read_text(encoding="utf-8")).get("pub_types") or [])
            or "Guideline"
            in (json.loads(f.read_text(encoding="utf-8")).get("pub_types") or [])
        ),
        None,
    )

    picks = []
    for label, path in [
        ("structured abstract example", structured_ex),
        ("unstructured abstract example", unstructured_ex),
        ("guideline example", guideline_ex),
    ]:
        if path is not None and path not in [p for _, p in picks]:
            picks.append((label, path))
    while len(picks) < sample_n and len(files) > len(picks):
        cand = random.choice(files)
        if cand not in [p for _, p in picks]:
            picks.append(("random pick", cand))

    for label, path in picks[:sample_n]:
        rec = json.loads(path.read_text(encoding="utf-8"))
        console.print(
            f"\n[bold]Example — {label}[/bold]  ({path.name})\n"
            f"  PMID:        {rec.get('pmid')}\n"
            f"  Title:       {(rec.get('title') or '')[:120]}\n"
            f"  Journal:     {rec.get('journal')}\n"
            f"  Pub date:    {rec.get('pub_date')}\n"
            f"  Pub types:   {rec.get('pub_types')}\n"
            f"  DOI:         {rec.get('doi')}\n"
            f"  Issuing:     {rec.get('issuing_body')}\n"
            f"  # authors:   {len(rec.get('authors') or [])}\n"
            f"  # MeSH:      {len(rec.get('mesh_headings') or [])}\n"
            f"  Abstract sections ({len(rec.get('abstract') or [])}):"
        )
        for s in (rec.get("abstract") or [])[:6]:
            lbl = s.get("section_label") or "(unlabeled)"
            txt = s.get("text", "")
            console.print(f"    [{lbl}] {txt[:200]}{'...' if len(txt) > 200 else ''}")


def main() -> None:
    p = argparse.ArgumentParser(prog="clinicomm.ingest.efetch")
    p.add_argument("--config", default="config/pipeline.yaml")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Report how many PMIDs would be fetched and exit.",
    )
    p.add_argument(
        "--reparse-only",
        action="store_true",
        help="Skip network. Re-parse db/raw/*.xml into db/parsed/.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap PMIDs processed (testing).",
    )
    p.add_argument(
        "--summarize-only",
        action="store_true",
        help="Skip network. Compute stats from existing db/parsed/.",
    )
    args = p.parse_args()

    cfg = load_config(args.config)
    log_path = setup_logging(
        phase="phase03_efetch",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    raw_dir = Path(cfg["paths"]["db_raw"])
    parsed_dir = Path(cfg["paths"]["db_parsed"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    parsed_dir.mkdir(parents=True, exist_ok=True)
    discovery_path = Path(cfg["paths"]["discovery"])

    if args.summarize_only:
        summarize(parsed_dir)
        return

    if args.reparse_only:
        saved, dropped, reasons = reparse_local(raw_dir, parsed_dir)
        log.info("Reparse: saved=%d dropped=%d", saved, dropped)
        if reasons:
            console.print("[bold]Drop reasons:[/bold]")
            for k, v in reasons.most_common():
                console.print(f"  {k}: {v}")
        summarize(parsed_dir)
        return

    if not discovery_path.exists():
        console.print(
            f"[red]Phase 2 output missing: {discovery_path}. Run phase 2 first.[/red]"
        )
        return

    pmids = load_pmids(discovery_path)
    log.info("Loaded %d PMIDs from %s", len(pmids), discovery_path)

    already = {p.stem for p in raw_dir.glob("*.xml")} & {
        p.stem for p in parsed_dir.glob("*.json")
    }
    todo_pmids = [p for p in pmids if p not in already]
    log.info(
        "Skipping %d already processed (raw+parsed present); to-do = %d",
        len(already),
        len(todo_pmids),
    )

    if args.limit:
        todo_pmids = todo_pmids[: args.limit]
        log.info("--limit=%d", args.limit)

    if args.dry_run:
        console.print(
            f"\n[bold]Dry run:[/bold] would fetch {len(todo_pmids)} PMIDs "
            f"(already done: {len(already)})."
        )
        return

    pubmed_cfg = cfg["pubmed"]
    api_key = os.environ.get(pubmed_cfg["api_key_env"]) or None
    rate = (
        pubmed_cfg["rate_limit_with_key"] if api_key else pubmed_cfg["rate_limit_no_key"]
    )
    log.info("NCBI rate limit %s req/s (api_key=%s)", rate, bool(api_key))

    email = os.environ.get(pubmed_cfg.get("email_env", "NCBI_EMAIL")) or pubmed_cfg["email"]
    client = EUtilsClient(
        tool="clinicomm",
        email=email,
        api_key=api_key,
        rate_per_sec=rate,
    )

    fetched, saved, dropped, reasons = fetch_and_persist(
        client=client,
        pmids=todo_pmids,
        raw_dir=raw_dir,
        parsed_dir=parsed_dir,
        batch_size=pubmed_cfg["efetch_batch"],
    )
    total_attempted = len(todo_pmids)
    retention = saved / total_attempted if total_attempted else 0.0
    log.info(
        "EFetch done. attempted=%d fetched_articles=%d saved_json=%d dropped=%d retention=%.3f",
        total_attempted,
        fetched,
        saved,
        dropped,
        retention,
    )
    console.print(
        f"\n[bold]EFetch complete[/bold]\n"
        f"  attempted PMIDs: {total_attempted}\n"
        f"  articles in XML: {fetched}\n"
        f"  parsed JSON saved: {saved}\n"
        f"  dropped: {dropped}\n"
        f"  retention rate: {retention:.1%}"
    )
    if reasons:
        console.print("[bold]Drop reasons:[/bold]")
        for k, v in reasons.most_common():
            console.print(f"  {k}: {v}")

    summarize(parsed_dir)


if __name__ == "__main__":
    main()
