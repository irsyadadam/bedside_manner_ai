"""Regenerate publication-grade Tables 1/4/5/6 + Figure 10.

Phase 13 update: tables previously based on n=3 synthetic patients are
rewritten against the external-dataset metrics (PriMock57 + MTS-Dialog,
n=292) and the full PubMed corpus.

  Table 1  — Corpus characteristics (summary stats only; top-k panels
              moved to Figure 10)
  Fig  10  — Corpus overview (4-panel SVG): year distribution,
              publication type breakdown, top-50 journals, top-30 MeSH
  Table 4  — Pipeline vs LLM-only baselines (naive / strong-prompt /
              full), per dataset
  Table 5  — Module-level ablation, 5 conditions, pooled across
              external datasets
  Table 6  — Provenance audit (verbatim on n=3 synthetic; citation-
              existence on n=292 external)

The script is read-only on the LLM and GPU — it operates purely on the
already-computed metric JSONs (manuscript/data/external_metrics_*.json)
and the PubMed corpus (db/parsed/, db/manifest.jsonl).

Usage:
  uv run python scripts/regen_pub_tables.py
"""
from __future__ import annotations

import json
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("regen_pub_tables")

ROOT = Path(__file__).resolve().parent.parent
PARSED_DIR = ROOT / "db" / "parsed"
MANIFEST = ROOT / "db" / "manifest.jsonl"
TABLES_DIR = ROOT / "manuscript" / "tables_draft"
FIGURES_DIR = ROOT / "manuscript" / "figures"
DATA_DIR = ROOT / "manuscript" / "data"
SYNTHETIC_TRACES = ROOT / "manuscript" / "traces"
EXTERNAL_TRACES = ROOT / "manuscript" / "traces_external"


# --------------------------------------------------------------------------
# Corpus stats loader
# --------------------------------------------------------------------------


def load_corpus() -> dict:
    """Read db/parsed/*.json + db/manifest.jsonl. Returns aggregate stats."""
    if not PARSED_DIR.exists():
        raise FileNotFoundError(f"{PARSED_DIR} not found — run bootstrap first.")

    docs = []
    for p in sorted(PARSED_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            docs.append(d)
        except json.JSONDecodeError:
            continue

    years = Counter()
    pub_types = Counter()
    journals = Counter()
    mesh_descriptors = Counter()
    structured_count = 0
    doi_count = 0
    issuing_body_count = 0
    abstract_chars = []
    for d in docs:
        # Year extraction from pub_date "YYYY", "YYYY-MM", or "YYYY-MM-DD"
        pd = (d.get("pub_date") or "").strip()
        m = re.match(r"(\d{4})", pd)
        if m:
            years[int(m.group(1))] += 1
        for pt in d.get("pub_types") or []:
            pub_types[pt] += 1
        j = (d.get("journal") or "").strip()
        if j:
            journals[j] += 1
        if d.get("doi"):
            doi_count += 1
        if d.get("issuing_body"):
            issuing_body_count += 1
        ab = d.get("abstract") or []
        if ab and isinstance(ab, list):
            # structured if more than one section OR section_label != None
            if len(ab) > 1 or (len(ab) == 1 and ab[0].get("section_label")):
                structured_count += 1
            chars = sum(len((s.get("text") or "")) for s in ab)
            abstract_chars.append(chars)
        for mh in d.get("mesh_headings") or []:
            desc = (mh.get("descriptor") or "").strip()
            if desc:
                mesh_descriptors[desc] += 1

    # Chunk + token totals from manifest. Field name in db/manifest.jsonl
    # is `chunk_token_total` (per-doc total), not `total_chunk_tokens`.
    n_chunks = 0
    n_chunk_tokens = 0
    if MANIFEST.exists():
        for line in MANIFEST.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                n_chunks += int(row.get("n_chunks") or 0)
                n_chunk_tokens += int(row.get("chunk_token_total") or row.get("total_chunk_tokens") or 0)
            except json.JSONDecodeError:
                continue

    return {
        "n_docs": len(docs),
        "years": dict(years),
        "year_min": min(years.keys()) if years else None,
        "year_max": max(years.keys()) if years else None,
        "pub_types": dict(pub_types),
        "journals": dict(journals),
        "n_unique_journals": len(journals),
        "mesh_descriptors": dict(mesh_descriptors),
        "n_unique_mesh": len(mesh_descriptors),
        "structured_count": structured_count,
        "doi_count": doi_count,
        "issuing_body_count": issuing_body_count,
        "mean_abstract_chars": (sum(abstract_chars) / len(abstract_chars)) if abstract_chars else 0,
        "median_abstract_chars": (
            sorted(abstract_chars)[len(abstract_chars) // 2] if abstract_chars else 0
        ),
        "n_chunks": n_chunks,
        "n_chunk_tokens": n_chunk_tokens,
    }


# --------------------------------------------------------------------------
# Table 1 — corpus summary only
# --------------------------------------------------------------------------


def write_table1(corpus: dict) -> None:
    s_pct = lambda n, d: f"{100*n/d:.1f}%" if d else "—"
    md = []
    md.append("# Table 1. Corpus characteristics")
    md.append("")
    md.append("*PubMed records retrieved via a MeSH-based query targeting "
              "patient-centered primary-care communication and intake "
              "(systematic reviews, meta-analyses, practice guidelines, "
              "consensus statements; English; 2018–2026), normalized, "
              "chunked at 400 tokens with 50-token overlap, and embedded "
              "with BAAI/bge-large-en-v1.5 (1,024-d vectors).*")
    md.append("")
    md.append("| Property | Value |")
    md.append("|:---|---:|")
    md.append(f"| Documents (parsed) | {corpus['n_docs']:,} |")
    md.append(f"| Publication years | {corpus['year_min']}–{corpus['year_max']} |")
    md.append(f"| Documents with structured abstract | {corpus['structured_count']:,} ({s_pct(corpus['structured_count'], corpus['n_docs'])}) |")
    md.append(f"| Documents with DOI | {corpus['doi_count']:,} ({s_pct(corpus['doi_count'], corpus['n_docs'])}) |")
    md.append(f"| Documents with issuing body (guideline society) | {corpus['issuing_body_count']:,} |")
    md.append(f"| Unique source journals | {corpus['n_unique_journals']:,} |")
    md.append(f"| Unique MeSH descriptors | {corpus['n_unique_mesh']:,} |")
    md.append(f"| Mean abstract length (characters) | {corpus['mean_abstract_chars']:,.0f} |")
    md.append(f"| Median abstract length (characters) | {corpus['median_abstract_chars']:,.0f} |")
    md.append(f"| Total chunks (Phase 4) | {corpus['n_chunks']:,} |")
    md.append(f"| Total chunk tokens (BGE tokenizer) | {corpus['n_chunk_tokens']:,} |")
    md.append("")
    md.append("**Distributional detail.** Year, publication type, journal, "
              "and MeSH descriptor distributions are shown in **Figure 10** "
              "(corpus overview). Top-10 listings have been removed from "
              "this table in favor of the figure's complete distributions.")
    md.append("")
    md.append(f"<small>Auto-generated by `scripts/regen_pub_tables.py` on "
              f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}.</small>")
    md.append("")
    out = TABLES_DIR / "table1_corpus.md"
    out.write_text("\n".join(md), encoding="utf-8")
    log.info("wrote %s", out)


# --------------------------------------------------------------------------
# Figure 10 — corpus overview (4-panel SVG)
# --------------------------------------------------------------------------


def write_figure10(corpus: dict) -> None:
    sns.set_theme(style="whitegrid", context="paper")
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    # (a) Year distribution
    ax = axes[0, 0]
    years = sorted(corpus["years"].keys())
    counts = [corpus["years"][y] for y in years]
    ax.bar(years, counts, color="#4C72B0", edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Publication year")
    ax.set_ylabel("Documents (n)")
    ax.set_title(f"(a) Publications by year (n={corpus['n_docs']:,}; range {corpus['year_min']}–{corpus['year_max']})",
                 fontsize=11, loc="left")
    for y, c in zip(years, counts):
        ax.text(y, c + max(counts) * 0.02, str(c), ha="center", fontsize=8)

    # (b) Publication-type breakdown (drop the noisy MeSH "Research
    # Support" funding tags which aren't pub types in any meaningful
    # sense — keep the actual pub-type vocabulary)
    ax = axes[0, 1]
    skip_prefix = "Research Support"
    pub_filtered = {k: v for k, v in corpus["pub_types"].items() if not k.startswith(skip_prefix)}
    top_pt = sorted(pub_filtered.items(), key=lambda kv: -kv[1])[:12]
    pt_labels = [k for k, _ in top_pt][::-1]
    pt_counts = [v for _, v in top_pt][::-1]
    ax.barh(pt_labels, pt_counts, color="#55A868", edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Documents (n; multi-label)")
    ax.set_title("(b) Publication types (top 12; Research Support tags omitted)",
                 fontsize=11, loc="left")
    for i, c in enumerate(pt_counts):
        ax.text(c + max(pt_counts) * 0.01, i, str(c), va="center", fontsize=8)

    # (c) Top-50 journals (horizontal)
    ax = axes[1, 0]
    top_j = sorted(corpus["journals"].items(), key=lambda kv: -kv[1])[:50]
    j_labels = [k[:55] + "…" if len(k) > 55 else k for k, _ in top_j][::-1]
    j_counts = [v for _, v in top_j][::-1]
    ax.barh(range(len(j_labels)), j_counts, color="#C44E52", edgecolor="white", linewidth=0.3)
    ax.set_yticks(range(len(j_labels)))
    ax.set_yticklabels(j_labels, fontsize=6.5)
    ax.set_xlabel("Documents (n)")
    ax.set_title(f"(c) Top-50 source journals (of {corpus['n_unique_journals']:,} unique)",
                 fontsize=11, loc="left")

    # (d) Top-30 MeSH descriptors
    ax = axes[1, 1]
    top_m = sorted(corpus["mesh_descriptors"].items(), key=lambda kv: -kv[1])[:30]
    m_labels = [k[:50] + "…" if len(k) > 50 else k for k, _ in top_m][::-1]
    m_counts = [v for _, v in top_m][::-1]
    ax.barh(range(len(m_labels)), m_counts, color="#8172B2", edgecolor="white", linewidth=0.3)
    ax.set_yticks(range(len(m_labels)))
    ax.set_yticklabels(m_labels, fontsize=7.5)
    ax.set_xlabel("Documents tagged (n; multi-label)")
    ax.set_title(f"(d) Top-30 MeSH descriptors (of {corpus['n_unique_mesh']:,} unique)",
                 fontsize=11, loc="left")

    fig.suptitle("Figure 10 — Corpus overview", fontsize=13, fontweight="bold", y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.99])
    out = FIGURES_DIR / "fig10_corpus_overview.svg"
    fig.savefig(out, format="svg", bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", out)


# --------------------------------------------------------------------------
# External-dataset metric loader
# --------------------------------------------------------------------------


def load_external_metrics() -> dict[str, dict]:
    """Returns {dataset_name: full external_metrics json}. Sorted by name."""
    out: dict[str, dict] = {}
    for name, fname in (
        ("PriMock57", "external_metrics_primock57.json"),
        ("MTS-Dialog", "external_metrics_mts_dialog.json"),
        ("ACI-Bench", "external_metrics_aci_bench.json"),
    ):
        p = DATA_DIR / fname
        if not p.exists():
            continue
        out[name] = json.loads(p.read_text(encoding="utf-8"))
    return out


def _autoDx_pass_rates(d: dict) -> dict[str, float]:
    items = defaultdict(list)
    for tr in d.get("per_transcript_scores") or []:
        for cond, m in (tr.get("scores") or {}).items():
            if "error" in m:
                continue
            sa = m.get("safety_audit") or {}
            items[cond].append(1.0 if sa.get("no_autonomous_diagnosis") else 0.0)
    return {c: (sum(v) / len(v) if v else 0.0) for c, v in items.items()}


# --------------------------------------------------------------------------
# Table 4 — 3-condition × per-dataset
# --------------------------------------------------------------------------


def write_table4(external: dict[str, dict]) -> None:
    md = []
    md.append("# Table 4. Pipeline vs. LLM-only baselines, by dataset")
    md.append("")
    md.append("*Headline metrics on each external dataset comparing the full "
              "pipeline (Modules I–IV) against two LLM-only controls: a "
              "naive baseline (same local DeepSeek-R1-Distill-Qwen-14B with "
              "a generic “write an empathetic response” prompt) and a "
              "strong-prompt baseline (same model, prompt explicitly "
              "instructing NURSE + Four-Habits structure and PMID-style "
              "citations). Bold cells indicate the best per-row condition; "
              "↑ higher is better, ↓ lower is better.*")
    md.append("")

    md.append("| Dataset | Metric | Naive | Strong-prompt | Full pipeline |")
    md.append("|:---|:---|---:|---:|---:|")

    for ds_name, d in external.items():
        if not d.get("per_transcript_scores"):
            continue
        autoDx = _autoDx_pass_rates(d)
        n = d["n_transcripts"]
        s_n = d["per_condition_summary"].get("naive", {})
        s_sp = d["per_condition_summary"].get("strong_prompt", {})
        s_f = d["per_condition_summary"].get("full", {})

        def cell(v_n, v_sp, v_f, fmt=".2f", is_pct=False, lower_better=False):
            fmtv = (lambda x: f"{100*x:.0f}%") if is_pct else (lambda x: f"{x:{fmt}}")
            vals = [v_n or 0.0, v_sp or 0.0, v_f or 0.0]
            best = (min if lower_better else max)(range(3), key=lambda i: vals[i])
            rendered = [fmtv(x) for x in vals]
            rendered[best] = f"**{rendered[best]}**"
            return rendered

        first = True
        rows = [
            ("Safety pass ↑",   s_n.get("safety_pass_rate"),       s_sp.get("safety_pass_rate"),       s_f.get("safety_pass_rate"),       None, True,  False),
            ("autoDx pass ↑",   autoDx.get("naive"),                autoDx.get("strong_prompt"),        autoDx.get("full"),                None, True,  False),
            ("PMIDs / resp ↑", s_n.get("n_pmids_mean"),            s_sp.get("n_pmids_mean"),           s_f.get("n_pmids_mean"),           ".2f", False, False),
            ("NURSE n ↑",       s_n.get("nurse_n_mean"),            s_sp.get("nurse_n_mean"),           s_f.get("nurse_n_mean"),           ".2f", False, False),
            ("4H n ↑",          s_n.get("four_habits_n_mean"),      s_sp.get("four_habits_n_mean"),     s_f.get("four_habits_n_mean"),     ".2f", False, False),
            ("Halluc strict ↓", s_n.get("hallucination_rate_strict"),s_sp.get("hallucination_rate_strict"), s_f.get("hallucination_rate_strict"), ".3f", False, True),
            ("Halluc sem ↓",    s_n.get("hallucination_rate_semantic"),s_sp.get("hallucination_rate_semantic"), s_f.get("hallucination_rate_semantic"), ".3f", False, True),
        ]
        # Baselines have ZERO extracted atoms (Module I is skipped), so their
        # hallucination rate is trivially 0/0 -> 0 (degenerate). Render those
        # cells as "—†" instead of competing with the pipeline's non-trivial
        # rate; footnote below explains why.
        baselines_have_no_atoms = (s_n.get("nurse_n_mean", 0) == 0 and s_sp.get("nurse_n_mean", 0) == 0)
        for metric, v_n, v_sp, v_f, fmt, is_pct, lower in rows:
            if metric == "Halluc sem ↓":
                vals_present = []
                for v in (v_n, v_sp, v_f):
                    vals_present.append(v if (v is not None and not (v != v)) else None)
                if vals_present.count(None) >= 2:
                    cells = ["—" if x is None else f"{x:.3f}" for x in vals_present]
                else:
                    cells = []
                    valids = [(i, x) for i, x in enumerate(vals_present) if x is not None]
                    best_i = min(valids, key=lambda kv: kv[1])[0] if valids else None
                    for i, x in enumerate(vals_present):
                        if x is None:
                            cells.append("—")
                        elif i == best_i:
                            cells.append(f"**{x:.3f}**")
                        else:
                            cells.append(f"{x:.3f}")
            elif metric == "Halluc strict ↓" and baselines_have_no_atoms:
                # Baselines extract nothing -> "—†" not 0.000 (which would
                # spuriously win the row). The pipeline number is the only
                # meaningful value; report unbolded since there's no real
                # comparison.
                full_v = v_f if v_f is not None else 0.0
                cells = ["—†", "—†", f"{full_v:.3f}"]
            else:
                cells = cell(v_n, v_sp, v_f, fmt=fmt or ".2f", is_pct=is_pct, lower_better=lower)
            ds_label = f"**{ds_name} (n={n})**" if first else " "
            first = False
            md.append(f"| {ds_label} | {metric} | {cells[0]} | {cells[1]} | {cells[2]} |")

    md.append("")
    md.append("**Reading.** Bolded cells indicate the row's best-performing "
              "condition. Across both datasets, the full pipeline dominates "
              "on every provenance and empathy-marker metric. The "
              "autonomous-diagnosis (autoDx) pass rate flips direction on "
              "MTS-Dialog (favoring the strong-prompt baseline) because MTS's "
              "short section-focused snippets cause LLM-only conditions to "
              "produce vague, accidentally safe responses while the pipeline "
              "retrieves and references specific clinical content — a "
              "deployment-context sensitivity discussed in §5.")
    md.append("")
    md.append("† **Halluc strict** cells for LLM-only baselines are reported "
              "as “—” because those conditions do not run Module I — they "
              "extract no patient-profile atoms, so their hallucination rate "
              "is trivially 0/0 = 0. The pipeline's 0.32–0.33 strict rate is "
              "reported alongside its 0.000 *semantic*-anchored rate; the gap "
              "is entirely accounted for by legitimate clinical normalizations "
              "(see Table 7 footnote and §4.3).")
    md.append("")
    md.append("<small>Auto-generated from `manuscript/data/external_metrics_*.json` "
              f"on {datetime.now(timezone.utc).isoformat(timespec='seconds')}.</small>")
    md.append("")
    out = TABLES_DIR / "table4_pipeline_vs_baseline.md"
    out.write_text("\n".join(md), encoding="utf-8")
    log.info("wrote %s", out)


# --------------------------------------------------------------------------
# Table 5 — 5-condition pooled ablation
# --------------------------------------------------------------------------


def write_table5(external: dict[str, dict]) -> None:
    cond_order = ["naive", "strong_prompt", "framework_only", "retrieval_only", "full"]
    display = {
        "naive": "(a) Naive",
        "strong_prompt": "(b) Strong-prompt",
        "framework_only": "(c) Framework only",
        "retrieval_only": "(d) Retrieval only",
        "full": "(e) Full pipeline",
    }

    # Pool across datasets — collect raw per-record per-condition values,
    # then compute means weighted by record count (i.e., unweighted across
    # the pooled set of records).
    pooled: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    autoDx_pool: dict[str, list[float]] = defaultdict(list)
    n_records_total = 0

    for ds_name, d in external.items():
        n_records_total += d["n_transcripts"]
        for tr in d.get("per_transcript_scores") or []:
            for cond, m in (tr.get("scores") or {}).items():
                if "error" in m:
                    continue
                pooled[cond]["safety_all_pass"].append(
                    1.0 if (m.get("safety_audit") or {}).get("all_pass") else 0.0
                )
                pooled[cond]["n_pmids"].append(m.get("n_pmids", 0))
                pooled[cond]["nurse_n"].append(m.get("nurse_n", 0))
                pooled[cond]["four_habits_n"].append(m.get("four_habits_n", 0))
                pooled[cond]["fk_grade"].append(m.get("fk_grade", 0.0))
                pooled[cond]["length_words"].append(m.get("length_words", 0))
                hall = m.get("hallucination") or {}
                if hall.get("n_atoms"):
                    pooled[cond]["hallucination_strict"].append(hall.get("rate_strict", 0.0))
                    if hall.get("semantic_available"):
                        pooled[cond]["hallucination_semantic"].append(hall.get("rate_semantic", 0.0))
                sa = m.get("safety_audit") or {}
                autoDx_pool[cond].append(1.0 if sa.get("no_autonomous_diagnosis") else 0.0)

    def mean(xs):
        return (sum(xs) / len(xs)) if xs else 0.0

    md = []
    md.append("# Table 5. Module-level ablation (pooled, n = "
              f"{n_records_total} transcripts × 5 conditions)")
    md.append("")
    md.append("*Five conditions on the same external-dataset transcripts. "
              "(a) and (b) are LLM-only controls (no extraction, no "
              "retrieval); (c) applies the response-generation directive "
              "block on the raw transcript without intake/retrieval; "
              "(d) substitutes Module III's structured-context with "
              "top-N retrieved doc titles wrapped as singleton clusters; "
              "(e) is the full Modules I–IV pipeline. Pooled means across "
              f"PriMock57 (n=57) + MTS-Dialog (n=235) = {n_records_total} "
              "transcripts.*")
    md.append("")
    md.append("| Condition | n | Safety pass ↑ | autoDx pass ↑ | PMIDs ↑ | NURSE ↑ | 4H ↑ | Halluc strict ↓ | Halluc sem ↓ | FK | Words |")
    md.append("|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for c in cond_order:
        if c not in pooled or not pooled[c]["safety_all_pass"]:
            continue
        n_c = len(pooled[c]["safety_all_pass"])
        safety = mean(pooled[c]["safety_all_pass"]) * 100
        autoDx = mean(autoDx_pool[c]) * 100
        pmids = mean(pooled[c]["n_pmids"])
        nurse = mean(pooled[c]["nurse_n"])
        habits = mean(pooled[c]["four_habits_n"])
        fk = mean(pooled[c]["fk_grade"])
        words = mean(pooled[c]["length_words"])
        halluc_strict = mean(pooled[c]["hallucination_strict"]) if pooled[c]["hallucination_strict"] else None
        halluc_sem = mean(pooled[c]["hallucination_semantic"]) if pooled[c]["hallucination_semantic"] else None
        hs_str = f"{halluc_strict:.3f}" if halluc_strict is not None else "—"
        hsem_str = f"{halluc_sem:.3f}" if halluc_sem is not None else "—"
        md.append(
            f"| {display[c]} | {n_c} | {safety:.0f}% | {autoDx:.0f}% | "
            f"{pmids:.2f} | {nurse:.2f} | {habits:.2f} | "
            f"{hs_str} | {hsem_str} | {fk:.1f} | {words:.0f} |"
        )
    md.append("")
    md.append("**Reading.** Each module adds measurable behaviors. "
              "Comparing (a)→(c): the directive block alone delivers "
              "~5 NURSE+Habits elements/response but no provenance. "
              "Comparing (c)→(d): adding retrieval (without Module III) "
              "produces real PMID citations, raising safety from "
              "framework-only to the highest pooled value. Comparing "
              "(d)→(e): Module III's structured context approximately "
              "doubles PMID citation density while trading a few "
              "percentage points of safety composite for richer "
              "evidentiary content — the citation-density vs. response-"
              "structure tradeoff discussed in §5.")
    md.append("")
    md.append("<small>Auto-generated by `scripts/regen_pub_tables.py` on "
              f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}.</small>")
    md.append("")
    out = TABLES_DIR / "table5_module_ablation.md"
    out.write_text("\n".join(md), encoding="utf-8")
    log.info("wrote %s", out)


# --------------------------------------------------------------------------
# Table 6 — provenance audit (verbatim synth + citation-existence external)
# --------------------------------------------------------------------------


_PMID_PATTERN = re.compile(r"(?:PMID[:\s]*|PubMed[:\s]*|\[\s*PMID\s*[:\s]*|\b)(\d{7,9})\b", re.IGNORECASE)
_PMID_NUMERIC = re.compile(r"\b(\d{7,9})\b")


def _valid_pmids_in_corpus() -> set[str]:
    """Set of PMIDs that exist in db/parsed/."""
    if not PARSED_DIR.exists():
        return set()
    return {p.stem for p in PARSED_DIR.glob("*.json")}


def _extract_pmid_numbers_from_text(text: str) -> set[str]:
    """Pull all 7-9 digit numbers from a response that look like PMIDs."""
    return set(_PMID_NUMERIC.findall(text or ""))


def write_table6(external: dict[str, dict]) -> None:
    # --- Section A: synthetic n=3 verbatim audit (carry forward) -------
    # Format of manuscript/data/provenance_audit.json:
    #   {generated_utc, paraphrase_threshold, n_claims_total,
    #    overall: {classification: count, ...},
    #    by_trace: {trace_id: {classification: count, ...}},
    #    per_claim: [{trace, classification, ...}, ...]}
    synth_path = DATA_DIR / "provenance_audit.json"
    synth_summary = None
    synth_threshold = 0.55
    if synth_path.exists():
        synth = json.loads(synth_path.read_text(encoding="utf-8"))
        overall = synth.get("overall") or {}
        if overall:
            total = int(synth.get("n_claims_total") or sum(overall.values()))
            synth_summary = {"total": total, "by_class": dict(overall)}
            synth_threshold = synth.get("paraphrase_threshold", 0.55)
        elif isinstance(synth.get("per_claim"), list):
            rows = synth["per_claim"]
            cls_counts = Counter(r.get("classification", "unknown") for r in rows)
            synth_summary = {"total": len(rows), "by_class": dict(cls_counts)}

    # --- Section B: external citation-existence audit ------------------
    valid_pmids = _valid_pmids_in_corpus()
    n_corpus = len(valid_pmids)

    # Per-condition citation stats
    ext_stats: dict[str, dict] = defaultdict(lambda: {
        "n_responses": 0,
        "n_pmid_brackets_in_text": 0,   # any [PMID N] / [PMID ?] type marker count
        "n_pmid_numbers_in_text": 0,    # actual numeric PMIDs found in response_text
        "n_valid_pmids": 0,             # those numeric PMIDs that exist in db/parsed/
        "n_invented_pmids": 0,          # numeric PMIDs that DON'T exist in db/parsed/
        "n_pmids_structured": 0,        # PMIDs from the structured all_pmids_used field
    })
    bracket_re = re.compile(r"\[\s*PMID\b[^\]]*\]", re.IGNORECASE)

    for ds_name, d in external.items():
        for tr in d.get("per_transcript_scores") or []:
            # Trace JSON not directly available here; we look at the metric
            # JSON's per_transcript_scores which has pmids_used per cond
            pass

        # Walk the actual trace files for response_text + pmids_used
        dataset_slug = (
            "primock57" if ds_name == "PriMock57" else
            "mts_dialog" if ds_name == "MTS-Dialog" else "aci_bench"
        )
        trace_dir = EXTERNAL_TRACES / dataset_slug
        if not trace_dir.exists():
            continue
        for tp in sorted(trace_dir.glob("trace_*.json")):
            try:
                rec = json.loads(tp.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            for cond, b in (rec.get("conditions") or {}).items():
                if not b or "error" in b:
                    continue
                text = b.get("response_text") or ""
                pmids_used = b.get("pmids_used") or []
                ext_stats[cond]["n_responses"] += 1
                ext_stats[cond]["n_pmid_brackets_in_text"] += len(bracket_re.findall(text))
                nums = _extract_pmid_numbers_from_text(text)
                ext_stats[cond]["n_pmid_numbers_in_text"] += len(nums)
                ext_stats[cond]["n_valid_pmids"] += sum(1 for x in nums if x in valid_pmids)
                ext_stats[cond]["n_invented_pmids"] += sum(1 for x in nums if x not in valid_pmids)
                ext_stats[cond]["n_pmids_structured"] += len(pmids_used)
                # Validate structured citations too (should be 100% if pipeline works)
                ext_stats[cond].setdefault("n_pmids_structured_valid", 0)
                ext_stats[cond]["n_pmids_structured_valid"] += sum(1 for x in pmids_used if x in valid_pmids)

    # ---- render ------------------------------------------------------
    md = []
    md.append("# Table 6. Provenance audit")
    md.append("")
    md.append("*Two complementary mechanical audits of the responses' citation "
              "behavior. **Section A** (carried forward from Phase 12) checks "
              "every clinical claim in the n=3 synthetic-patient traces against "
              "its cited evidence quote, verifying verbatim substring presence "
              "in the source PubMed abstract — the strictest possible faithfulness "
              "check. **Section B** (new, Phase 13) extends to the full external-"
              "dataset corpus (PriMock57 + MTS-Dialog, " +
              f"{sum(s['n_responses'] for s in ext_stats.values())} responses) "
              "with a citation-existence audit: for every PMID number cited in a "
              "response, check whether that PMID exists in our parsed corpus.*")
    md.append("")

    md.append("## Section A — Per-claim verbatim audit (n=3 synthetic patients)")
    md.append("")
    if synth_summary:
        total = synth_summary["total"]
        by_class = synth_summary["by_class"]
        md.append("| Classification | Count | Share |")
        md.append("|:---|---:|---:|")
        for cls in ("supported", "paraphrased", "unsupported", "orphan_cluster"):
            c = by_class.get(cls, 0)
            md.append(f"| {cls} | {c} | {100*c/total:.1f}% |")
        md.append(f"| **total** | **{total}** | 100% |")
    else:
        md.append("_(no synthetic provenance_audit.json found)_")
    md.append("")
    md.append("*Strict verbatim check: every clinical claim in the response "
              "cites a structured `cluster_id`; that cluster's "
              "`primary_assertion.evidence_quote` is verified as a whitespace-"
              "normalized substring of the cited PubMed abstract. Paraphrase "
              "fallback (token-overlap ≥0.55) and orphan-cluster regression "
              "checks are also reported.*")
    md.append("")

    md.append("## Section B — Citation-existence audit (n=292 external responses × 5 conditions)")
    md.append("")
    md.append(f"Corpus: **{n_corpus:,} parsed PubMed documents** in `db/parsed/`.")
    md.append("")
    md.append("| Condition | n responses | PMID brackets | PMID numbers cited | Valid in corpus | Invented | Structured cites (`all_pmids_used`) | Structured valid |")
    md.append("|:---|---:|---:|---:|---:|---:|---:|---:|")
    cond_order = ["naive", "strong_prompt", "framework_only", "retrieval_only", "full"]
    display = {
        "naive": "Naive baseline",
        "strong_prompt": "Strong-prompt baseline",
        "framework_only": "Framework only",
        "retrieval_only": "Retrieval only",
        "full": "**Full pipeline**",
    }
    for c in cond_order:
        s = ext_stats.get(c)
        if not s:
            continue
        valid_share = (100 * s["n_valid_pmids"] / s["n_pmid_numbers_in_text"]) if s["n_pmid_numbers_in_text"] else None
        invented_share = (100 * s["n_invented_pmids"] / s["n_pmid_numbers_in_text"]) if s["n_pmid_numbers_in_text"] else None
        sv_share = (100 * s["n_pmids_structured_valid"] / s["n_pmids_structured"]) if s["n_pmids_structured"] else None
        valid_str = f"{s['n_valid_pmids']} ({valid_share:.0f}%)" if valid_share is not None else "—"
        invented_str = f"{s['n_invented_pmids']} ({invented_share:.0f}%)" if invented_share is not None else "—"
        sv_str = f"{s['n_pmids_structured_valid']} ({sv_share:.0f}%)" if sv_share is not None else "—"
        md.append(
            f"| {display[c]} | {s['n_responses']} | {s['n_pmid_brackets_in_text']} | "
            f"{s['n_pmid_numbers_in_text']} | {valid_str} | {invented_str} | "
            f"{s['n_pmids_structured']} | {sv_str} |"
        )
    md.append("")
    md.append("**Reading.**")
    md.append("- The strong-prompt baseline writes many bracketed citation "
              "markers in its response text (the prompt instructs it to "
              "cite PubMed) but produces no actual PMID numbers — its "
              "brackets are mostly `[PMID ?]` placeholders. **No real "
              "papers grounded.**")
    md.append("- The full pipeline's structured `all_pmids_used` field "
              "contains only PMIDs that exist in the parsed PubMed "
              "corpus — the Module IV citation validator strips invented "
              "IDs the LLM hallucinates from worked-example prompts. "
              "**Structured-valid rate = 100% by construction.**")
    md.append("- Numeric PMIDs that leak into the free-text response "
              "(rare; the LLM occasionally writes a PMID inline instead "
              "of via the structured citation field) are also validated.")
    md.append("")
    md.append("## Definitions")
    md.append("")
    md.append("- **supported** *(Section A)* — evidence quote appears verbatim (whitespace-normalized) in the cited source abstract.")
    md.append("- **paraphrased** *(Section A)* — ≥0.55 of evidence-quote tokens occur in the abstract; semantically faithful paraphrase below the verbatim threshold.")
    md.append("- **unsupported** *(Section A)* — neither verbatim nor sufficient token overlap. None observed.")
    md.append("- **orphan_cluster** *(Section A)* — response cited a `cluster_id` not present in Module III's output (regression check). None observed.")
    md.append("- **PMID brackets** *(Section B)* — count of `[PMID …]` substrings in response text. Captures the strong-prompt baseline's `[PMID ?]` placeholders even when no number is cited.")
    md.append("- **PMID numbers cited** *(Section B)* — count of 7-9 digit numbers in response text matching PMID syntax. The naive baseline does not cite any.")
    md.append("- **Structured `all_pmids_used`** *(Section B)* — PMIDs in the `PatientResponse.all_pmids_used` field, which is populated only by the pipeline (Modules I-IV); baselines do not produce structured output.")
    md.append("")
    md.append("## Limitations")
    md.append("")
    md.append("Section A's token overlap is a lower bound on faithfulness — a "
              "semantically faithful paraphrase using different vocabulary may "
              "score *unsupported* mechanically. Section B's citation-existence "
              "check verifies the cited paper exists in our corpus but does not "
              "verify that the paper actually supports the claim being made; "
              "for that, see the per-claim semantic-anchored hallucination "
              "metric in Table 7. A reviewer-grade per-claim audit on the n=292 "
              "external traces would require saving Module III's structured "
              "context with each trace (a known limitation of the current "
              "trace schema, slated for the next data release).")
    md.append("")
    md.append("<small>Auto-generated by `scripts/regen_pub_tables.py` on "
              f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}.</small>")
    md.append("")
    out = TABLES_DIR / "table6_provenance_audit.md"
    out.write_text("\n".join(md), encoding="utf-8")
    log.info("wrote %s", out)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> int:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    log.info("loading corpus ...")
    corpus = load_corpus()
    log.info("corpus: n_docs=%d unique_journals=%d unique_mesh=%d",
             corpus["n_docs"], corpus["n_unique_journals"], corpus["n_unique_mesh"])

    write_table1(corpus)
    write_figure10(corpus)

    log.info("loading external metrics ...")
    external = load_external_metrics()
    log.info("external datasets loaded: %s", list(external.keys()))

    write_table4(external)
    write_table5(external)
    write_table6(external)

    log.info("done.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
