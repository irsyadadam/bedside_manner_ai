"""Mechanical provenance audit for Table 6.

For every ResponseCitation in every saved trace, check whether the
cited cluster's primary_assertion.evidence_quote actually appears in
the source abstract (db/parsed/<PMID>.json → abstract sections).

Classification (per claim):
  supported       — evidence_quote (whitespace-normalized) is a substring
                    of the source abstract (verbatim).
  paraphrased     — token overlap ≥ paraphrase_threshold (default 0.55)
                    of the assertion's tokens appear in the abstract.
  unsupported     — neither verbatim nor sufficient token overlap.

Outputs:
  manuscript/tables_draft/table6_provenance_audit.{md,tex}
  manuscript/data/provenance_audit.json   (raw per-claim classification)

Note: this is a mechanical lower bound. A claim that paraphrases the
abstract while preserving meaning may still score "unsupported" if its
vocabulary is too far from the source. A reviewer-grade audit needs
human judgment; this script gives you a defensible automated baseline
on which to overlay manual review.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.table import Table

from clinicomm.config import load_config
from clinicomm.logging_setup import setup_logging

log = logging.getLogger("clinicomm.provenance_audit")
console = Console()


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _tokenize(s: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", (s or "").lower()) if len(t) >= 3]


def _classify(evidence_quote: str, source_text: str, threshold: float) -> str:
    """Return 'supported', 'paraphrased', or 'unsupported'."""
    quote = _normalize(evidence_quote)
    source = _normalize(source_text)
    if not quote or not source:
        return "unsupported"
    if quote in source:
        return "supported"
    q_tokens = _tokenize(evidence_quote)
    s_tokens = set(_tokenize(source_text))
    if not q_tokens:
        return "unsupported"
    overlap = sum(1 for t in q_tokens if t in s_tokens) / len(q_tokens)
    if overlap >= threshold:
        return "paraphrased"
    return "unsupported"


def _load_source(parsed_dir: Path, pmid: str) -> str:
    p = parsed_dir / f"{pmid}.json"
    if not p.exists():
        return ""
    doc = json.loads(p.read_text(encoding="utf-8"))
    pieces = []
    for s in doc.get("abstract", []) or []:
        if s.get("text"):
            pieces.append(s["text"])
    return "\n\n".join(pieces)


def audit_trace(
    trace_json: Path, parsed_dir: Path, threshold: float
) -> list[dict]:
    """Returns one row per (cluster_id, claim) entry."""
    td = json.loads(trace_json.read_text(encoding="utf-8"))
    sc_clusters = {c["cluster_id"]: c for c in td["structured_context"]["clusters"]}
    rows: list[dict] = []
    for sec in td["response"]["clinical_information_per_concern"]:
        for cite in sec.get("citations") or []:
            cid = cite["cluster_id"]
            cluster = sc_clusters.get(cid)
            if cluster is None:
                # Cited cluster not in artifact — flag as orphan
                rows.append(
                    {
                        "trace": td["transcript_id"],
                        "cluster_id": cid,
                        "primary_assertion_id": cite.get("primary_assertion_id"),
                        "concern": sec.get("profile_path"),
                        "pmids": cite.get("pmids") or [],
                        "classification": "orphan_cluster",
                        "overlap_score": None,
                    }
                )
                continue
            primary = cluster["primary_assertion"]
            evidence = primary.get("evidence_quote", "")
            pmid = primary.get("source_pmid", "")
            source_text = _load_source(parsed_dir, pmid)
            kind = _classify(evidence, source_text, threshold)
            q_tokens = _tokenize(evidence)
            s_tokens = set(_tokenize(source_text))
            overlap = (
                sum(1 for t in q_tokens if t in s_tokens) / len(q_tokens)
                if q_tokens
                else 0.0
            )
            rows.append(
                {
                    "trace": td["transcript_id"],
                    "cluster_id": cid,
                    "primary_assertion_id": primary.get("assertion_id"),
                    "concern": sec.get("profile_path"),
                    "pmids": cite.get("pmids") or [],
                    "classification": kind,
                    "overlap_score": round(overlap, 3),
                }
            )
    return rows


def _tex_escape(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    replacements = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
                    "_": r"\_", "{": r"\{", "}": r"\}"}
    return "".join(replacements.get(ch, ch) for ch in s)


def main() -> None:
    p = argparse.ArgumentParser(prog="scripts/provenance_audit.py")
    p.add_argument("--config", default="config/pipeline.yaml")
    p.add_argument("--traces-dir", type=Path, default=Path("manuscript/traces"))
    p.add_argument("--out-dir", type=Path, default=Path("manuscript/tables_draft"))
    p.add_argument("--data-dir", type=Path, default=Path("manuscript/data"))
    p.add_argument("--paraphrase-threshold", type=float, default=0.55,
                   help="Token-overlap fraction at which a non-verbatim "
                   "claim counts as 'paraphrased' rather than 'unsupported'.")
    args = p.parse_args()

    cfg = load_config(args.config)
    log_path = setup_logging(
        phase="phase12_provenance_audit",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    parsed_dir = Path(cfg["paths"]["db_parsed"])
    trace_files = sorted(args.traces_dir.glob("trace_*.json"))
    if not trace_files:
        console.print(f"[red]No trace_*.json under {args.traces_dir}[/red]")
        return

    all_rows: list[dict] = []
    for tf in trace_files:
        rows = audit_trace(tf, parsed_dir, args.paraphrase_threshold)
        all_rows.extend(rows)
        ct = Counter(r["classification"] for r in rows)
        console.print(
            f"  {tf.name}: {len(rows)} claims  "
            + " ".join(f"{k}={v}" for k, v in ct.items())
        )

    # Aggregate
    total = len(all_rows)
    overall_ct: Counter[str] = Counter(r["classification"] for r in all_rows)
    by_trace: dict[str, Counter[str]] = defaultdict(Counter)
    for r in all_rows:
        by_trace[r["trace"]][r["classification"]] += 1

    # Save raw data
    args.data_dir.mkdir(parents=True, exist_ok=True)
    (args.data_dir / "provenance_audit.json").write_text(
        json.dumps(
            {
                "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "paraphrase_threshold": args.paraphrase_threshold,
                "n_claims_total": total,
                "overall": dict(overall_ct),
                "by_trace": {k: dict(v) for k, v in by_trace.items()},
                "per_claim": all_rows,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # ---- Markdown table ----
    md: list[str] = []
    md.append("# Table 6 — Provenance audit (mechanical)")
    md.append("")
    md.append(
        f"_Auto-generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}; "
        f"paraphrase-threshold = {args.paraphrase_threshold:.2f}_"
    )
    md.append("")
    md.append(
        "Each clinical claim in a generated `PatientResponse` cites a "
        "`cluster_id`; that cluster's `primary_assertion.evidence_quote` "
        "is checked against the source abstract."
    )
    md.append("")
    md.append("## Overall")
    md.append("")
    md.append("| Classification | Count | Share |")
    md.append("|---|---:|---:|")
    for kind in ("supported", "paraphrased", "unsupported", "orphan_cluster"):
        c = overall_ct.get(kind, 0)
        pct = (c / total * 100) if total else 0.0
        md.append(f"| {kind} | {c} | {pct:.1f}% |")
    md.append(f"| **total** | **{total}** | 100% |")
    md.append("")
    md.append("## By trace")
    md.append("")
    md.append("| Trace | Supported | Paraphrased | Unsupported | Orphan |")
    md.append("|---|---:|---:|---:|---:|")
    for tid, ct in by_trace.items():
        md.append(
            f"| {tid} | {ct.get('supported',0)} | {ct.get('paraphrased',0)} "
            f"| {ct.get('unsupported',0)} | {ct.get('orphan_cluster',0)} |"
        )
    md.append("")
    md.append(
        "**Definitions.**  *supported* = evidence quote appears verbatim "
        "(whitespace-normalized) in the source abstract.  *paraphrased* = "
        "≥ paraphrase-threshold of evidence-quote tokens occur in the "
        "abstract.  *unsupported* = neither.  *orphan_cluster* = the "
        "response cited a `cluster_id` that does not exist in the "
        "structured-context artifact (a regression to investigate)."
    )
    md.append("")
    md.append(
        "**Limitations.** Token overlap is a lower bound on faithfulness "
        "— a semantically faithful paraphrase using different vocabulary "
        "may score *unsupported* mechanically. Human review on a subsample "
        "is recommended."
    )
    (args.out_dir / "table6_provenance_audit.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )

    # ---- LaTeX ----
    tex: list[str] = []
    tex.append(r"% Table 6 — Provenance audit. Auto-generated.")
    tex.append(r"\begin{table}[t]")
    tex.append(r"\centering")
    tex.append(r"\caption{Mechanical provenance audit of pipeline-generated clinical claims.}")
    tex.append(r"\label{tab:provenance-audit}")
    tex.append(r"\small")
    tex.append(r"\begin{tabular}{lrr}")
    tex.append(r"\toprule")
    tex.append(r"Classification & Count & Share \\")
    tex.append(r"\midrule")
    for kind in ("supported", "paraphrased", "unsupported", "orphan_cluster"):
        c = overall_ct.get(kind, 0)
        pct = (c / total * 100) if total else 0.0
        tex.append(rf"{_tex_escape(kind)} & {c} & {pct:.1f}\% \\")
    tex.append(rf"\textbf{{total}} & \textbf{{{total}}} & 100\% \\")
    tex.append(r"\bottomrule")
    tex.append(r"\end{tabular}")
    tex.append(r"\end{table}")
    (args.out_dir / "table6_provenance_audit.tex").write_text(
        "\n".join(tex) + "\n", encoding="utf-8"
    )

    # ---- Console summary ----
    tbl = Table(title="Provenance audit summary")
    tbl.add_column("classification")
    tbl.add_column("count", justify="right")
    tbl.add_column("share", justify="right")
    for kind, c in overall_ct.most_common():
        pct = (c / total * 100) if total else 0.0
        tbl.add_row(kind, str(c), f"{pct:.1f}%")
    console.print(tbl)
    console.print(f"\nSaved table6_provenance_audit.md / .tex to {args.out_dir}/")
    console.print(f"Saved raw audit to {args.data_dir / 'provenance_audit.json'}")


if __name__ == "__main__":
    main()
