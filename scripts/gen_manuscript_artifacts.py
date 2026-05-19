"""Phase 12 entrypoint — refresh manuscript artifacts from pipeline state.

What this script does (in order):

  1. ASCII figures (manuscript/figures_ascii/fig{1..6}_*.txt + .notes.md)
     are written by hand into the file (see those files), NOT regenerated
     here. We only verify they're present and report.

  2. Auto-generated tables (manuscript/tables_draft/):
       table1_corpus.{md,tex}              ← from db/manifest.jsonl
       table2_directives.{md,tex}          ← from DIRECTIVES block in
                                              config/prompts/response_generation.txt
       table3_retrieval_sanity.{md,tex}    ← from latest
                                              logs/sanity_query_*.json

  3. Per-patient pipeline traces:
       manuscript/traces/trace_<id>.{md,json}   ← from Phase 11 run

     If any synthetic transcript is still a TODO stub, it is SKIPPED
     and the patient_id is reported. We never invent transcript content.

  4. Naive-LLM baseline + comparison (NEW; user request):
       manuscript/traces/baseline_<id>.md       ← single naive LLM call
       manuscript/traces/comparison_<id>.md     ← side-by-side w/ pipeline

     The comparison MD highlights what the structured pipeline adds
     (citations, NURSE/Four Habits tracking, red-flag detection,
     glossary substitution, etc.).

Run:
  uv run python scripts/gen_manuscript_artifacts.py --demo
      # mocked end-to-end; reuses traces from scripts/run_demo.py

  uv run python scripts/gen_manuscript_artifacts.py
      # requires vLLM server; produces real pipeline + baseline outputs
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from rich.console import Console

from clinicomm.baseline import NaiveLLMBaseline
from clinicomm.config import load_config
from clinicomm.logging_setup import setup_logging
from clinicomm.modules.llm_client import MockBaselineLLM, VLLMClient
from clinicomm.pipeline import Pipeline, PipelineResult, is_stub_transcript, load_transcript

log = logging.getLogger("clinicomm.gen_manuscript_artifacts")
console = Console()


# --------------------------------------------------------------------------
# Table 1 — corpus
# --------------------------------------------------------------------------


def _read_manifest(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def table1_corpus_md_tex(cfg: dict) -> tuple[str, str] | None:
    manifest_path = Path(cfg["paths"]["manifest"])
    rows = _read_manifest(manifest_path)
    if not rows:
        log.warning("table1: manifest missing or empty (%s) — skipping", manifest_path)
        return None

    total = len(rows)
    structured = sum(1 for r in rows if r.get("abstract_structured"))
    structured_pct = (structured / total * 100) if total else 0.0
    pub_year_set = [r.get("pub_year") for r in rows if r.get("pub_year")]
    year_min = min(pub_year_set) if pub_year_set else "—"
    year_max = max(pub_year_set) if pub_year_set else "—"
    abs_chars = [r.get("abstract_total_chars") or 0 for r in rows]
    mean_chars = sum(abs_chars) / total if total else 0
    docs_with_doi = sum(1 for r in rows if r.get("doi"))
    docs_with_issuing = sum(1 for r in rows if r.get("issuing_body"))
    total_chunks = sum(r.get("n_chunks") or 0 for r in rows)
    total_tokens = sum(r.get("chunk_token_total") or 0 for r in rows)

    pubtype_ct: Counter[str] = Counter()
    journal_ct: Counter[str] = Counter()
    mesh_ct: Counter[str] = Counter()
    for r in rows:
        for pt in r.get("pub_types") or []:
            pubtype_ct[pt] += 1
        if r.get("journal"):
            journal_ct[r["journal"]] += 1
        for d in r.get("mesh_descriptors") or []:
            mesh_ct[d] += 1
    pubtypes_top = pubtype_ct.most_common(10)
    journals_top = journal_ct.most_common(10)
    mesh_top = mesh_ct.most_common(10)

    # -------- Markdown --------
    md: list[str] = []
    md.append("# Table 1 — Corpus")
    md.append("")
    md.append(f"_Auto-generated from `{manifest_path}` "
              f"({datetime.now(timezone.utc).isoformat(timespec='seconds')})_")
    md.append("")
    md.append("## Top-level counts")
    md.append("")
    md.append("| Metric | Value |")
    md.append("|---|---|")
    md.append(f"| Total documents | {total} |")
    md.append(f"| Date range (publication year) | {year_min}–{year_max} |")
    md.append(f"| Structured abstracts | {structured} ({structured_pct:.1f}%) |")
    md.append(f"| Mean abstract length (characters) | {mean_chars:,.0f} |")
    md.append(f"| Documents with DOI | {docs_with_doi} |")
    md.append(f"| Documents with issuing-body (collective author) | {docs_with_issuing} |")
    md.append(f"| Total chunks | {total_chunks:,} |")
    md.append(f"| Total chunk tokens | {total_tokens:,} |")
    md.append("")
    md.append("## Publication types (top 10)")
    md.append("")
    md.append("| Pub type | Count |")
    md.append("|---|---:|")
    for pt, c in pubtypes_top:
        md.append(f"| {pt} | {c} |")
    md.append("")
    md.append("## Journals (top 10)")
    md.append("")
    md.append("| Journal | Count |")
    md.append("|---|---:|")
    for j, c in journals_top:
        md.append(f"| {j} | {c} |")
    md.append("")
    md.append("## MeSH descriptors (top 10)")
    md.append("")
    md.append("| Descriptor | Count |")
    md.append("|---|---:|")
    for d, c in mesh_top:
        md.append(f"| {d} | {c} |")
    md_text = "\n".join(md) + "\n"

    # -------- LaTeX (booktabs) --------
    tex: list[str] = []
    tex.append(r"% Table 1 — Corpus. Auto-generated; do not edit by hand.")
    tex.append(r"\begin{table}[t]")
    tex.append(r"\centering")
    tex.append(r"\caption{Corpus summary.}")
    tex.append(r"\label{tab:corpus}")
    tex.append(r"\small")
    tex.append(r"\begin{tabular}{lr}")
    tex.append(r"\toprule")
    tex.append(r"Metric & Value \\")
    tex.append(r"\midrule")
    tex.append(rf"Total documents & {total} \\")
    tex.append(rf"Date range (publication year) & {year_min}--{year_max} \\")
    tex.append(rf"Structured abstracts & {structured} ({structured_pct:.1f}\%) \\")
    tex.append(rf"Mean abstract length (characters) & {mean_chars:,.0f} \\")
    tex.append(rf"Documents with DOI & {docs_with_doi} \\")
    tex.append(rf"Documents with issuing-body & {docs_with_issuing} \\")
    tex.append(rf"Total chunks & {total_chunks:,} \\")
    tex.append(rf"Total chunk tokens & {total_tokens:,} \\")
    tex.append(r"\bottomrule")
    tex.append(r"\end{tabular}")
    tex.append("")
    tex.append(r"\bigskip")
    tex.append(r"\begin{tabular}{lr}")
    tex.append(r"\toprule")
    tex.append(r"Publication type (top 10) & Count \\")
    tex.append(r"\midrule")
    for pt, c in pubtypes_top:
        tex.append(rf"{_tex_escape(pt)} & {c} \\")
    tex.append(r"\bottomrule")
    tex.append(r"\end{tabular}")
    tex.append("")
    tex.append(r"\bigskip")
    tex.append(r"\begin{tabular}{lr}")
    tex.append(r"\toprule")
    tex.append(r"Journal (top 10) & Count \\")
    tex.append(r"\midrule")
    for j, c in journals_top:
        tex.append(rf"{_tex_escape(j)} & {c} \\")
    tex.append(r"\bottomrule")
    tex.append(r"\end{tabular}")
    tex.append("")
    tex.append(r"\bigskip")
    tex.append(r"\begin{tabular}{lr}")
    tex.append(r"\toprule")
    tex.append(r"MeSH descriptor (top 10) & Count \\")
    tex.append(r"\midrule")
    for d, c in mesh_top:
        tex.append(rf"{_tex_escape(d)} & {c} \\")
    tex.append(r"\bottomrule")
    tex.append(r"\end{tabular}")
    tex.append(r"\end{table}")
    tex_text = "\n".join(tex) + "\n"

    return md_text, tex_text


# --------------------------------------------------------------------------
# Table 2 — DIRECTIVES (parsed from response_generation.txt)
# --------------------------------------------------------------------------


def _parse_directives_block(text: str) -> list[dict]:
    """Parse the block between DIRECTIVES_START and DIRECTIVES_END.
    Returns a list of {framework, element, trigger, rule}."""
    m = re.search(r"^DIRECTIVES_START\s*$.+?^DIRECTIVES_END\s*$", text, re.S | re.M)
    if not m:
        return []
    block = m.group(0)
    out: list[dict] = []
    # Each row begins with "- framework: <value>".
    for chunk in re.split(r"\n(?=- framework:)", block):
        if "framework:" not in chunk:
            continue
        fw = re.search(r"framework:\s*(.+)", chunk)
        el = re.search(r"element:\s*(.+)", chunk)
        tr = re.search(r"trigger:\s*(.+)", chunk)
        ru = re.search(r"rule:\s*(.+(?:\n\s{4,}.+)*)", chunk)
        if not (fw and el and tr and ru):
            continue
        out.append(
            {
                "framework": fw.group(1).strip(),
                "element": el.group(1).strip(),
                "trigger": tr.group(1).strip(),
                "rule": " ".join(ru.group(1).strip().split()),
            }
        )
    return out


def table2_directives_md_tex(cfg: dict) -> tuple[str, str] | None:
    prompt_path = Path(cfg["prompts"]["response_generation"])
    if not prompt_path.exists():
        log.warning("table2: prompt missing (%s) — skipping", prompt_path)
        return None
    text = prompt_path.read_text(encoding="utf-8")
    rows = _parse_directives_block(text)
    if not rows:
        log.warning("table2: DIRECTIVES_START/END block empty — skipping")
        return None

    md: list[str] = []
    md.append("# Table 2 — Communication directives")
    md.append("")
    md.append(f"_Auto-generated from `{prompt_path}` "
              f"({datetime.now(timezone.utc).isoformat(timespec='seconds')})_")
    md.append("")
    md.append("| Framework | Element | Trigger condition | Generation rule |")
    md.append("|---|---|---|---|")
    for r in rows:
        md.append(
            f"| {_md_escape(r['framework'])} | {_md_escape(r['element'])} | "
            f"{_md_escape(r['trigger'])} | {_md_escape(r['rule'])} |"
        )
    md_text = "\n".join(md) + "\n"

    tex: list[str] = []
    tex.append(r"% Table 2 — Communication directives. Auto-generated.")
    tex.append(r"\begin{table*}[t]")
    tex.append(r"\centering")
    tex.append(r"\caption{Communication directives applied by Module IV.}")
    tex.append(r"\label{tab:directives}")
    tex.append(r"\small")
    tex.append(r"\begin{tabular}{llp{4.5cm}p{6cm}}")
    tex.append(r"\toprule")
    tex.append(r"Framework & Element & Trigger condition & Generation rule \\")
    tex.append(r"\midrule")
    for r in rows:
        tex.append(
            rf"{_tex_escape(r['framework'])} & {_tex_escape(r['element'])} "
            rf"& {_tex_escape(r['trigger'])} & {_tex_escape(r['rule'])} \\"
        )
    tex.append(r"\bottomrule")
    tex.append(r"\end{tabular}")
    tex.append(r"\end{table*}")
    tex_text = "\n".join(tex) + "\n"

    return md_text, tex_text


# --------------------------------------------------------------------------
# Table 3 — retrieval sanity (latest logs/sanity_query_*.json)
# --------------------------------------------------------------------------


def table3_retrieval_sanity_md_tex(cfg: dict) -> tuple[str, str] | None:
    logs_dir = Path(cfg["paths"]["logs"])
    candidates = sorted(logs_dir.glob("sanity_query_*.json"))
    if not candidates:
        log.warning("table3: no sanity_query_*.json in %s — skipping", logs_dir)
        return None
    latest = candidates[-1]
    data = json.loads(latest.read_text(encoding="utf-8"))

    md: list[str] = []
    md.append("# Table 3 — Retrieval sanity (appendix)")
    md.append("")
    md.append(f"_Auto-generated from `{latest}` "
              f"({datetime.now(timezone.utc).isoformat(timespec='seconds')})_")
    md.append("")
    md.append(f"Model: `{data.get('model')}`  ·  "
              f"collection: `{data.get('collection')}` "
              f"(size {data.get('collection_size')}).")
    md.append("")

    for q in data.get("queries") or []:
        md.append(f"## Query: \"{q['query']}\"")
        md.append("")
        md.append("| Rank | PMID | Sim | Title |")
        md.append("|---:|---|---:|---|")
        for r in q.get("results") or []:
            title = (r.get("title") or "")[:90].replace("|", "\\|")
            md.append(
                f"| {r['rank']} | {r['pmid']} | {r['similarity']:.3f} | {title} |"
            )
        md.append("")
    md_text = "\n".join(md) + "\n"

    tex: list[str] = []
    tex.append(r"% Table 3 — Retrieval sanity. Auto-generated. Appendix.")
    tex.append(r"\begin{table*}[t]")
    tex.append(r"\centering")
    tex.append(r"\caption{Retrieval sanity check — top-5 documents for each of "
               r"five fixed primary-care queries.}")
    tex.append(r"\label{tab:retrieval-sanity}")
    tex.append(r"\small")
    tex.append(r"\begin{tabular}{lllrl}")
    tex.append(r"\toprule")
    tex.append(r"Query & Rank & PMID & Sim & Title \\")
    tex.append(r"\midrule")
    for q in data.get("queries") or []:
        for i, r in enumerate(q.get("results") or []):
            q_label = _tex_escape(q["query"]) if i == 0 else ""
            tex.append(
                rf"{q_label} & {r['rank']} & {r['pmid']} & "
                rf"{r['similarity']:.3f} & {_tex_escape((r.get('title') or '')[:80])} \\"
            )
        tex.append(r"\midrule")
    # Replace the trailing midrule with a bottomrule.
    if tex and tex[-1] == r"\midrule":
        tex[-1] = r"\bottomrule"
    else:
        tex.append(r"\bottomrule")
    tex.append(r"\end{tabular}")
    tex.append(r"\end{table*}")
    tex_text = "\n".join(tex) + "\n"

    return md_text, tex_text


# --------------------------------------------------------------------------
# Baseline + comparison MD
# --------------------------------------------------------------------------


def _comparison_md(
    pipeline_result: PipelineResult,
    baseline_text: str,
    baseline_system_prompt: str,
) -> str:
    r = pipeline_result
    resp = r.response

    n_problems = len(r.profile.problems)
    n_goals = len(r.profile.patient_goals)
    n_cues = len(r.profile.emotional_cues)
    n_redflags = len(r.profile.red_flags)
    n_pmids = len(resp.all_pmids_used)
    n_clusters = len(resp.all_cluster_ids_used)
    n_glossary = len(resp.glossary_substitutions)
    nurse = ", ".join(resp.nurse_elements_applied) or "—"
    habits = ", ".join(resp.four_habits_elements_applied) or "—"

    # Compose the verbatim emotional cue used (if any) for the comparison row.
    verbatim_cue = "—"
    for ec in r.profile.emotional_cues:
        if ec.evidence_quote and ec.evidence_quote in resp.acknowledgment:
            verbatim_cue = f"\"{ec.evidence_quote[:120]}\""
            break

    # Compose a list of red flags actually surfaced.
    red_summary = "—"
    if r.profile.red_flags:
        red_summary = "; ".join(rf.flag for rf in r.profile.red_flags)

    lines: list[str] = []
    lines.append(f"# Comparison: pipeline vs. naive LLM baseline — `{r.transcript_id}`")
    lines.append("")
    lines.append(f"_Mode: **{r.mode}**  ·  generated: "
                 f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}_")
    lines.append("")
    if r.scenario:
        lines.append("## Scenario")
        lines.append("")
        lines.append(r.scenario)
        lines.append("")

    lines.append("## Patient transcript (input to both systems)")
    lines.append("")
    for i, u in enumerate(r.patient_utterances):
        lines.append(f"**Turn {i+1}**")
        lines.append("")
        lines.append(f"> {u}")
        lines.append("")

    lines.append("## (A) Naive LLM baseline — single call, no pipeline")
    lines.append("")
    lines.append("_System prompt to the model:_")
    lines.append("")
    lines.append("> " + baseline_system_prompt.replace("\n", " "))
    lines.append("")
    lines.append("_Model's reply:_")
    lines.append("")
    lines.append("> " + baseline_text.replace("\n", "\n> "))
    lines.append("")

    lines.append("## (B) Pipeline output (Modules I–IV)")
    lines.append("")
    lines.append("**Acknowledgment**")
    lines.append("")
    lines.append(f"> {resp.acknowledgment}")
    lines.append("")
    lines.append("**Clinical information, per concern (with provenance):**")
    lines.append("")
    for sec in resp.clinical_information_per_concern:
        pmid_set: list[str] = []
        for cite in sec.citations:
            for p in cite.pmids:
                if p not in pmid_set:
                    pmid_set.append(p)
        markers = " " + " ".join(f"[PMID {p}]" for p in pmid_set[:5]) if pmid_set else ""
        lines.append(f"- **{sec.concern_label}** (`{sec.profile_path}`){markers}")
        lines.append(f"    > {sec.explanation}")
    lines.append("")
    lines.append("**Next steps:**")
    lines.append("")
    for i, s in enumerate(resp.next_steps):
        lines.append(f"{i+1}. {s}")
    lines.append("")
    lines.append("**Teach-back:**")
    lines.append("")
    lines.append(f"> {resp.teach_back_prompt}")
    lines.append("")
    lines.append("**Follow-up invitation:**")
    lines.append("")
    lines.append(f"> {resp.follow_up_invitation}")
    lines.append("")

    lines.append("## What the pipeline adds")
    lines.append("")
    lines.append("| Dimension | Naive LLM (A) | Pipeline (B) |")
    lines.append("|---|---|---|")
    lines.append(f"| Citations to literature | none | "
                 f"{n_pmids} PMIDs across {n_clusters} cluster(s) |")
    lines.append(f"| Per-claim provenance | unverifiable | "
                 f"every clinical claim links to cluster\\_id → PMID |")
    lines.append(f"| NURSE elements (tracked) | implicit | {nurse} |")
    lines.append(f"| Four Habits elements (tracked) | implicit | {habits} |")
    lines.append(f"| Verbatim emotional cue used | not applicable | {verbatim_cue} |")
    lines.append(f"| Red-flag screen | implicit / may miss | explicit; flagged: {red_summary} |")
    lines.append(f"| Structured patient profile | none | "
                 f"{n_problems} problems · {n_goals} goals · "
                 f"{n_cues} emotional cues · {n_redflags} red flags |")
    lines.append(f"| Plain-language guarantee | model discretion | "
                 f"post-gen glossary pass ({n_glossary} substitutions) |")
    lines.append(f"| Audit trail | none | full intermediate artifacts at `logs/`, "
                 f"`manuscript/traces/` |")
    lines.append(f"| Reproducibility | model-state-dependent | "
                 f"deterministic given same inputs |")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "_Generated by `scripts/gen_manuscript_artifacts.py`. The naive "
        "baseline is a single LLM call against the patient transcript "
        "with no intake extraction, no retrieval, no reasoning, and no "
        "framework directives — by design, to represent the control "
        "condition for the manuscript._"
    )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _tex_escape(s: str) -> str:
    if s is None:
        return ""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "<": r"\textless{}",
        ">": r"\textgreater{}",
    }
    out = []
    for ch in s:
        out.append(replacements.get(ch, ch))
    return "".join(out)


def _md_escape(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _report_figures(fig_dir: Path) -> list[str]:
    expected = [
        "fig1_architecture",
        "fig2_intake_state_machine",
        "fig3_schema_illustration",
        "fig4_retrieval",
        "fig5_reasoning",
        "fig6_end_to_end_trace",
    ]
    missing: list[str] = []
    for stem in expected:
        txt = fig_dir / f"{stem}.txt"
        notes = fig_dir / f"{stem}.notes.md"
        if not txt.exists():
            missing.append(str(txt))
        if not notes.exists():
            missing.append(str(notes))
    return missing


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(prog="scripts/gen_manuscript_artifacts.py")
    p.add_argument("--config", default="config/pipeline.yaml")
    p.add_argument(
        "--demo",
        action="store_true",
        help="Use mock LLM clients (pipeline + baseline). No vLLM server needed.",
    )
    p.add_argument(
        "--skip-traces",
        action="store_true",
        help="Don't (re-)run the pipeline; only refresh figures/tables/comparisons "
        "based on existing traces.",
    )
    args = p.parse_args()

    cfg = load_config(args.config)
    log_path = setup_logging(
        phase="phase12_gen_manuscript",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    fig_dir = Path(cfg["paths"]["figures_ascii"])
    tab_dir = Path(cfg["paths"]["tables_draft"])
    trace_dir = Path(cfg["paths"]["traces"])

    # ---- 1. ASCII figures: verify ------------------------------------
    console.rule("[bold]ASCII figures[/bold]")
    missing = _report_figures(fig_dir)
    if missing:
        for m in missing:
            console.print(f"  [yellow]MISSING[/yellow] {m}")
    else:
        console.print(f"  All 6 figures present in {fig_dir}/")

    # ---- 2. Tables ----------------------------------------------------
    console.rule("[bold]Tables[/bold]")
    for label, fn, stem in [
        ("table1_corpus", table1_corpus_md_tex, "table1_corpus"),
        ("table2_directives", table2_directives_md_tex, "table2_directives"),
        ("table3_retrieval_sanity", table3_retrieval_sanity_md_tex, "table3_retrieval_sanity"),
    ]:
        try:
            result = fn(cfg)
        except Exception as e:  # noqa: BLE001
            console.print(f"  [red]ERROR[/red] {label}: {e}")
            continue
        if result is None:
            console.print(f"  [yellow]SKIP[/yellow] {label} (no source data)")
            continue
        md_text, tex_text = result
        _write(tab_dir / f"{stem}.md", md_text)
        _write(tab_dir / f"{stem}.tex", tex_text)
        console.print(f"  [green]OK[/green] {label} -> {stem}.md / {stem}.tex")

    # ---- 3. Pipeline traces ------------------------------------------
    console.rule("[bold]Pipeline traces[/bold]")
    transcripts = sorted(Path(cfg["paths"]["synthetic_patients"]).glob("*.json"))
    runnable = [t for t in transcripts if not is_stub_transcript(t)]
    skipped = [t for t in transcripts if is_stub_transcript(t)]
    for s in skipped:
        console.print(f"  [yellow]SKIP (all-TODO)[/yellow] {s.name}")

    if not runnable:
        console.print("  [red]No filled-in transcripts.[/red] Phase 11 + 12 cannot "
                      "produce per-patient traces. Use scripts/run_demo.py "
                      "--demo --fallback at minimum.")
    else:
        if args.skip_traces:
            console.print(f"  [dim]--skip-traces: reusing existing trace JSONs[/dim]")
        else:
            # Build the pipeline once.
            pipeline = (
                Pipeline.with_mocks(cfg) if args.demo else Pipeline.with_real_llm(cfg)
            )
            for tp in runnable:
                pid, scenario, utterances = load_transcript(tp)
                console.print(f"  running pipeline on {pid} ({len(utterances)} turns) ...")
                result = pipeline.run(
                    utterances,
                    transcript_id=pid,
                    scenario=scenario,
                )
                # Save the trace JSON (the MD report is written by
                # scripts/run_demo.py; in --skip-traces we just reuse it,
                # so we always need the JSON here too).
                trace_dir.mkdir(parents=True, exist_ok=True)
                _write(
                    trace_dir / f"trace_{pid}.json",
                    json.dumps(
                        {
                            "transcript_id": result.transcript_id,
                            "scenario": result.scenario,
                            "patient_utterances": result.patient_utterances,
                            "intake_trace": result.intake_trace,
                            "profile": result.profile.model_dump(),
                            "ranked_docs": result.ranked_docs.model_dump(),
                            "structured_context": result.structured_context.model_dump(),
                            "response": result.response.model_dump(),
                            "mode": result.mode,
                        },
                        indent=2,
                        ensure_ascii=False,
                    ),
                )
                # Also write the MD by importing render_markdown — keeps
                # behavior identical to scripts/run_demo.py.
                from scripts.run_demo import render_markdown  # local import to avoid circular
                _write(trace_dir / f"trace_{pid}.md", render_markdown(result))
                console.print(f"    [green]OK[/green] trace_{pid}.{{md,json}}")

    # ---- 4. Baseline + comparison ------------------------------------
    console.rule("[bold]Baseline + comparison[/bold]")
    baseline_llm = MockBaselineLLM() if args.demo else VLLMClient(cfg["llm"])
    baseline = NaiveLLMBaseline(baseline_llm)
    for tp in runnable:
        pid, scenario, utterances = load_transcript(tp)
        # Run baseline
        b = baseline.respond(
            utterances,
            transcript_id=pid,
            scenario=scenario,
            mode="mock" if args.demo else "real",
        )
        _write(
            trace_dir / f"baseline_{pid}.md",
            "# Naive LLM baseline — `" + pid + "`\n\n"
            f"_Mode: **{b.mode}**  ·  generated: "
            f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}_\n\n"
            "## System prompt\n\n"
            f"> {b.system_prompt}\n\n"
            "## Patient transcript\n\n"
            + "\n\n".join(f"> {u}" for u in utterances)
            + "\n\n## Model response\n\n"
            f"> {b.response_text.replace(chr(10), chr(10) + '> ')}\n",
        )
        console.print(f"  [green]OK[/green] baseline_{pid}.md")

        # Load the pipeline trace JSON we just wrote (or reuse existing).
        trace_json = trace_dir / f"trace_{pid}.json"
        if not trace_json.exists():
            console.print(
                f"  [yellow]SKIP comparison ({pid})[/yellow] — no pipeline trace JSON; "
                "rerun without --skip-traces"
            )
            continue
        td = json.loads(trace_json.read_text(encoding="utf-8"))
        # Rehydrate a PipelineResult-ish for the comparison.
        from clinicomm.schemas import (
            PatientConcernProfile,
            PatientResponse,
            RankedDocumentSet,
            StructuredContextArtifact,
        )

        rehydrated = PipelineResult(
            transcript_id=td["transcript_id"],
            scenario=td["scenario"],
            patient_utterances=td["patient_utterances"],
            intake_trace=td["intake_trace"],
            profile=PatientConcernProfile.model_validate(td["profile"]),
            ranked_docs=RankedDocumentSet.model_validate(td["ranked_docs"]),
            structured_context=StructuredContextArtifact.model_validate(td["structured_context"]),
            response=PatientResponse.model_validate(td["response"]),
            mode=td["mode"],
        )
        cmp_md = _comparison_md(rehydrated, b.response_text, baseline.system_prompt)
        _write(trace_dir / f"comparison_{pid}.md", cmp_md)
        console.print(f"  [green]OK[/green] comparison_{pid}.md")

    console.rule("[bold]Done[/bold]")
    console.print(f"All artifacts under:\n"
                  f"  • figures: {fig_dir}/\n"
                  f"  • tables:  {tab_dir}/\n"
                  f"  • traces:  {trace_dir}/")


if __name__ == "__main__":
    main()
