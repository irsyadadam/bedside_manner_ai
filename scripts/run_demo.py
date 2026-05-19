"""Phase 11 entrypoint — run the full pipeline on a synthetic patient
transcript JSON and write a Markdown report to manuscript/traces/.

Examples
--------
    # Real LLM (requires vLLM server running):
    uv run python scripts/run_demo.py \\
        demos/synthetic_patients/p001_fatigue_weightloss.json

    # Offline mocks (no GPU / no server needed):
    uv run python scripts/run_demo.py --demo \\
        demos/synthetic_patients/p001_fatigue_weightloss.json

    # All filled-in transcripts in demos/synthetic_patients/:
    uv run python scripts/run_demo.py --demo --all

    # Fallback: no transcripts filled in -> hard-coded example
    uv run python scripts/run_demo.py --demo --fallback

Report layout (per spec):
  - Transcript (dialogue format)
  - Final PatientConcernProfile (YAML)
  - Top 5 retrieved documents
  - StructuredContextArtifact (clusters with provenance)
  - Final PatientResponse with [PMID] markers
  - Provenance appendix
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from rich.console import Console

from clinicomm.config import load_config
from clinicomm.logging_setup import setup_logging
from clinicomm.pipeline import (
    Pipeline,
    PipelineResult,
    is_stub_transcript,
    load_transcript,
)

log = logging.getLogger("clinicomm.run_demo")
console = Console()


# --------------------------------------------------------------------------
# Hard-coded fallback (per spec: "If transcripts are still stubs, run on
# a single hard-coded example transcript embedded in scripts/run_demo.py
# so we have at least one real pipeline trace available for Phase 12")
# --------------------------------------------------------------------------

FALLBACK_TRANSCRIPT_ID = "fallback_fatigue_weightloss"
FALLBACK_SCENARIO = (
    "Hard-coded demo: 52M contractor with new fatigue + ~12-lb "
    "unintentional weight loss, father with colon cancer, openly afraid."
)
FALLBACK_UTTERANCES = [
    "I've been so tired the past month, and I've lost about 12 pounds without "
    "trying. My wife is convinced it's cancer and honestly I am too. I just want "
    "to know what's going on so I can keep working.",
    "It started about a month ago. Some days I feel a 7 out of 10 tired — I can "
    "barely get through my shifts. I'm taking ibuprofen sometimes for headaches "
    "but nothing for the fatigue itself.",
    "No chest pain, no shortness of breath, nothing like that. But I have been "
    "getting these dull headaches in the morning, almost every day.",
    "I'm on lisinopril 10 mg once a day. No allergies that I know of. My dad had "
    "colon cancer at 55 and I'd really like to rule that out — I want to feel "
    "safe again.",
]


# --------------------------------------------------------------------------
# Markdown writer
# --------------------------------------------------------------------------


def _yaml_pretty(model_dump: dict) -> str:
    return yaml.safe_dump(
        model_dump,
        sort_keys=False,
        default_flow_style=False,
        width=80,
        allow_unicode=True,
    )


def render_markdown(result: PipelineResult, transcript_turns_meta: list[dict] | None = None) -> str:
    r = result
    lines: list[str] = []

    # ---- header --------------------------------------------------------
    lines.append(f"# Pipeline trace — `{r.transcript_id}`")
    lines.append("")
    lines.append(f"_Mode: **{r.mode}**  ·  Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}_")
    lines.append("")
    if r.scenario:
        lines.append("## Scenario")
        lines.append("")
        lines.append(r.scenario)
        lines.append("")

    # ---- transcript ----------------------------------------------------
    lines.append("## Transcript")
    lines.append("")
    for i, utt in enumerate(r.patient_utterances):
        agent_prompt = ""
        if i < len(r.intake_trace):
            agent_prompt = r.intake_trace[i].get("agent_prompt") or ""
        # Prefer the agent prompt the IntakeAgent actually picked over
        # the transcript's elicited_by hint (which is informational only).
        lines.append(f"**Turn {i + 1}** — *agent (templated):*")
        if agent_prompt:
            lines.append("")
            lines.append(f"> {agent_prompt}")
        lines.append("")
        lines.append("**Patient:**")
        lines.append("")
        lines.append(f"> {utt}")
        lines.append("")

    # ---- intake completion summary -------------------------------------
    last_complete = r.intake_trace[-1]["complete"] if r.intake_trace else False
    lines.append(
        f"_Intake completion at last turn: **{last_complete}** "
        f"(status: `{r.profile.completion_status}`)_"
    )
    lines.append("")

    # ---- profile -------------------------------------------------------
    lines.append("## Final `PatientConcernProfile`")
    lines.append("")
    lines.append("```yaml")
    lines.append(_yaml_pretty(r.profile.model_dump()).rstrip())
    lines.append("```")
    lines.append("")

    # ---- top retrieved docs --------------------------------------------
    lines.append("## Top 5 retrieved documents (Module II)")
    lines.append("")
    lines.append(
        f"Sub-queries decomposed: **{len(r.ranked_docs.sub_queries)}**.  "
        f"top_k chunks/sub-query: **{r.ranked_docs.top_k_chunks_per_query}**.  "
        f"Graph expansion: `{r.ranked_docs.expansion_used}`.  "
        f"Rerank weights: `{r.ranked_docs.rerank_weights}`."
    )
    lines.append("")
    lines.append("| Rank | PMID | Year | Journal | sem | rec | aut | cov | total | Title |")
    lines.append("|---:|---|---:|---|---:|---:|---:|---:|---:|---|")
    for i, d in enumerate(r.ranked_docs.documents[:5]):
        title = (d.title or "").replace("|", "\\|")[:100]
        journal = (d.journal or "")[:50].replace("|", "\\|")
        lines.append(
            f"| {i + 1} | {d.pmid} | {d.pub_year or '—'} | {journal} | "
            f"{d.semantic_similarity:.3f} | {d.recency_score:.2f} | "
            f"{d.authority_score:.2f} | {d.coverage_bonus:.2f} | "
            f"{d.total_score:.3f} | {title} |"
        )
    lines.append("")

    # ---- structured context --------------------------------------------
    sc = r.structured_context
    lines.append("## `StructuredContextArtifact` (Module III)")
    lines.append("")
    lines.append(
        f"- Documents processed: **{sc.n_documents_processed}**  "
        f"· Assertions extracted: **{sc.n_assertions_extracted}**  "
        f"· Clusters: **{sc.n_clusters}** "
        f"(convergent={sc.n_convergent_clusters}, "
        f"divergent={sc.n_divergent_clusters})  "
        f"· Similarity threshold: **{sc.cluster_similarity_threshold:.2f}**"
    )
    lines.append("")

    for i, c in enumerate(sc.clusters):
        kind = "CONVERGENT" if c.convergent else "DIVERGENT"
        lines.append(
            f"### Cluster {i + 1} · {kind} · `{c.assertion_type}` · "
            f"addresses=`{c.addresses_concern or '(global)'}` · "
            f"confidence={c.confidence:.2f}"
        )
        lines.append("")
        p = c.primary_assertion
        lines.append(
            f"**Primary** (`{p.assertion_id}`, conf={p.confidence:.2f}): "
            f"{p.assertion_text}"
        )
        if p.evidence_quote:
            lines.append("")
            lines.append(f"> _evidence_: {p.evidence_quote[:300]}")
        if c.alternative_assertions:
            lines.append("")
            lines.append(f"**Alternatives ({len(c.alternative_assertions)}):**")
            for a in c.alternative_assertions[:4]:
                lines.append(
                    f"- `{a.assertion_id}` (conf={a.confidence:.2f}) — {a.assertion_text[:160]}"
                )
            if len(c.alternative_assertions) > 4:
                lines.append(f"- ... and {len(c.alternative_assertions) - 4} more")
        if c.resolution_rule:
            lines.append("")
            lines.append(
                f"_Resolution rule: **{c.resolution_rule}** — {c.resolution_rationale}_"
            )
        lines.append("")
        pmid_list = ", ".join(c.supporting_pmids[:10]) + (
            "..." if len(c.supporting_pmids) > 10 else ""
        )
        lines.append(f"Supporting PMIDs ({len(c.supporting_pmids)}): {pmid_list}")
        lines.append("")

    if sc.notes:
        lines.append("**Limitations recorded by Module III:**")
        for n in sc.notes:
            lines.append(f"- {n}")
        lines.append("")

    # ---- patient response ----------------------------------------------
    resp = r.response
    lines.append("## Final `PatientResponse` (Module IV)")
    lines.append("")
    lines.append("### Acknowledgment")
    lines.append("")
    lines.append(f"> {resp.acknowledgment}")
    lines.append("")

    lines.append("### Clinical information, per concern")
    lines.append("")
    for sec in resp.clinical_information_per_concern:
        markers = ""
        if sec.citations:
            pmid_set: list[str] = []
            for cite in sec.citations:
                for p in cite.pmids:
                    if p not in pmid_set:
                        pmid_set.append(p)
            markers = " " + " ".join(f"[PMID {p}]" for p in pmid_set[:6])
            if len(pmid_set) > 6:
                markers += " [...]"
        lines.append(f"**{sec.concern_label}** (`{sec.profile_path}`){markers}")
        lines.append("")
        lines.append(f"> {sec.explanation}")
        if sec.citations:
            cite_bits = []
            for cite in sec.citations:
                cite_bits.append(
                    f"`{cite.cluster_id}` → primary `{cite.primary_assertion_id}` "
                    f"(supports: {', '.join(cite.pmids[:4])}"
                    f"{'...' if len(cite.pmids) > 4 else ''})"
                )
            lines.append("")
            lines.append("Citations:")
            for b in cite_bits:
                lines.append(f"- {b}")
        lines.append("")

    lines.append("### Next steps")
    lines.append("")
    for i, s in enumerate(resp.next_steps):
        lines.append(f"{i + 1}. {s}")
    lines.append("")

    lines.append("### Teach-back prompt")
    lines.append("")
    lines.append(f"> {resp.teach_back_prompt}")
    lines.append("")

    lines.append("### Follow-up invitation")
    lines.append("")
    lines.append(f"> {resp.follow_up_invitation}")
    lines.append("")

    # ---- annotations / appendix ---------------------------------------
    lines.append("## Provenance appendix")
    lines.append("")
    lines.append("### Framework elements applied")
    lines.append("")
    lines.append(f"- **NURSE** elements applied: {resp.nurse_elements_applied or '—'}")
    lines.append(f"- **Four Habits** elements applied: {resp.four_habits_elements_applied or '—'}")
    lines.append("")

    lines.append("### Cluster → PMIDs used in the response")
    lines.append("")
    used_clusters = {c.cluster_id: c for c in sc.clusters if c.cluster_id in resp.all_cluster_ids_used}
    if not used_clusters:
        lines.append("_(no clusters were cited in the response)_")
    else:
        for cid, c in used_clusters.items():
            pmid_set = ", ".join(c.supporting_pmids[:10]) + (
                "..." if len(c.supporting_pmids) > 10 else ""
            )
            lines.append(
                f"- `{cid}` · `{c.assertion_type}` · "
                f"addresses=`{c.addresses_concern or '(global)'}` · "
                f"primary `{c.primary_assertion.assertion_id}` · "
                f"PMIDs: {pmid_set}"
            )
    lines.append("")

    lines.append("### All PMIDs cited (deduped)")
    lines.append("")
    if resp.all_pmids_used:
        for p in resp.all_pmids_used:
            lines.append(f"- {p}")
    else:
        lines.append("_(no PMIDs were cited)_")
    lines.append("")

    if resp.glossary_substitutions:
        lines.append("### Post-generation glossary substitutions")
        lines.append("")
        lines.append("| Field | Original | Plain | Count |")
        lines.append("|---|---|---|---:|")
        for g in resp.glossary_substitutions:
            lines.append(f"| {g.field} | {g.original} | {g.plain} | {g.count} |")
        lines.append("")
    else:
        lines.append("_No glossary substitutions were needed (LLM produced plain language directly)._")
        lines.append("")

    # ---- footer --------------------------------------------------------
    lines.append("---")
    lines.append("")
    lines.append(
        f"_Generated by `scripts/run_demo.py` · mode `{r.mode}` · "
        f"transcript `{r.transcript_id}`_"
    )

    return "\n".join(lines)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _run_one(
    pipeline: Pipeline,
    transcript_path: Path,
    out_dir: Path,
) -> tuple[Path, PipelineResult]:
    pid, scenario, utterances = load_transcript(transcript_path)
    if not utterances:
        raise RuntimeError(
            f"{transcript_path} has no non-TODO patient_utterances; "
            "use --fallback to run the hard-coded example."
        )
    result = pipeline.run(
        utterances,
        transcript_id=pid,
        scenario=scenario,
    )
    md = render_markdown(result)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"trace_{pid}.md"
    out_path.write_text(md, encoding="utf-8")
    # Also persist the result as JSON for downstream Phase 12 use.
    json_path = out_dir / f"trace_{pid}.json"
    json_path.write_text(
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
        encoding="utf-8",
    )
    return out_path, result


def main() -> None:
    p = argparse.ArgumentParser(prog="scripts/run_demo.py")
    p.add_argument("transcript", type=Path, nargs="?", help="Path to a transcript JSON.")
    p.add_argument(
        "--demo",
        action="store_true",
        help="Use mock LLM clients (no vLLM server needed).",
    )
    p.add_argument(
        "--all",
        action="store_true",
        help="Run on every JSON in demos/synthetic_patients/ that has non-TODO utterances.",
    )
    p.add_argument(
        "--fallback",
        action="store_true",
        help="Use the hard-coded fallback transcript (per spec when stubs are unfilled).",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("manuscript/traces"),
        help="Where to write trace_<id>.md (default: manuscript/traces/).",
    )
    p.add_argument("--config", default="config/pipeline.yaml")
    args = p.parse_args()

    cfg = load_config(args.config)
    log_path = setup_logging(
        phase="phase11_run_demo",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    # Build pipeline once and reuse across transcripts.
    if args.demo:
        pipeline = Pipeline.with_mocks(cfg)
    else:
        pipeline = Pipeline.with_real_llm(cfg)
    console.print(f"[bold]Pipeline mode:[/bold] {pipeline.mode}")

    targets: list[Path] = []
    if args.fallback:
        # Run the hard-coded fallback regardless of stub state.
        log.info("Running hard-coded fallback transcript.")
        result = pipeline.run(
            FALLBACK_UTTERANCES,
            transcript_id=FALLBACK_TRANSCRIPT_ID,
            scenario=FALLBACK_SCENARIO,
        )
        md = render_markdown(result)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        out_path = args.out_dir / f"trace_{FALLBACK_TRANSCRIPT_ID}.md"
        out_path.write_text(md, encoding="utf-8")
        console.print(f"Wrote [cyan]{out_path}[/cyan]")
        return

    if args.all:
        for f in sorted(Path("demos/synthetic_patients").glob("*.json")):
            if is_stub_transcript(f):
                console.print(f"[yellow]skip (all-TODO):[/yellow] {f}")
                continue
            targets.append(f)
        if not targets:
            console.print(
                "[yellow]No filled-in transcripts found in demos/synthetic_patients/. "
                "Falling back to hard-coded example.[/yellow]"
            )
            result = pipeline.run(
                FALLBACK_UTTERANCES,
                transcript_id=FALLBACK_TRANSCRIPT_ID,
                scenario=FALLBACK_SCENARIO,
            )
            md = render_markdown(result)
            args.out_dir.mkdir(parents=True, exist_ok=True)
            (args.out_dir / f"trace_{FALLBACK_TRANSCRIPT_ID}.md").write_text(md, encoding="utf-8")
            console.print(
                f"Wrote [cyan]{args.out_dir / f'trace_{FALLBACK_TRANSCRIPT_ID}.md'}[/cyan]"
            )
            return
    else:
        if not args.transcript:
            console.print(
                "[red]No transcript given. Pass a path, --all, or --fallback.[/red]"
            )
            sys.exit(2)
        targets.append(args.transcript)

    for tp in targets:
        out_path, result = _run_one(pipeline, tp, args.out_dir)
        console.print(
            f"Wrote [cyan]{out_path}[/cyan]  "
            f"(problems={len(result.profile.problems)}, "
            f"clusters={result.structured_context.n_clusters}, "
            f"pmids={len(result.response.all_pmids_used)})"
        )


if __name__ == "__main__":
    main()
