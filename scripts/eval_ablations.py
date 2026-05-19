"""Run 4 conditions x 3 transcripts and emit Tables 4 + 5 (md + tex)
plus a `manuscript/data/ablation_metrics.json` for the figure renderer.

Conditions:
  (a) naive            — baseline LLM, free text
  (b) framework_only   — Module IV prompt on hollow profile + empty context
  (c) retrieval_only   — Module I + Module II + stub context + Module IV
  (d) full             — Modules I+II+III+IV

Modes:
  --demo   uses Mock* LLM clients (deterministic, instant)
  (none)   uses VLLMClient against the configured local vLLM server

Metrics produced (see clinicomm/metrics.py):
  citations, cluster_citations, nurse_n, four_habits_n,
  red_flag_addressed, red_flag_in_next_steps, fk_grade, word_count,
  teach_back_present, follow_up_timeframe, provenance_ratio.

Outputs:
  manuscript/tables_draft/table4_pipeline_vs_baseline.{md,tex}
  manuscript/tables_draft/table5_module_ablation.{md,tex}
  manuscript/data/ablation_metrics.json    (raw metrics, all conditions)
"""
from __future__ import annotations

import argparse
import json
import logging
import statistics
from datetime import datetime, timezone
from pathlib import Path

import torch
from rich.console import Console
from sentence_transformers import SentenceTransformer

from clinicomm.ablations import (
    framework_only_response,
    naive_to_patient_response,
    retrieval_only_response,
)
from clinicomm.baseline import NaiveLLMBaseline
from clinicomm.config import load_config
from clinicomm.logging_setup import setup_logging
from clinicomm.metrics import (
    metrics_for_freeform_text,
    metrics_for_structured_response,
    metrics_to_dict,
)
from clinicomm.modules.llm_client import (
    MockBaselineLLM,
    MockLLMClient,
    MockResponseLLM,
    VLLMClient,
)
from clinicomm.pipeline import Pipeline, load_transcript

log = logging.getLogger("clinicomm.eval_ablations")
console = Console()


COLUMNS = [
    ("condition", "Condition", "s"),
    ("citations", "Cit (PMIDs)", "d"),
    ("cluster_citations", "Cit (cls)", "d"),
    ("nurse_n", "NURSE", "d"),
    ("four_habits_n", "4Habits", "d"),
    ("red_flag_addressed", "RF addr", "b"),
    ("red_flag_in_next_steps", "RF first", "b"),
    ("fk_grade", "FK grade", "f"),
    ("word_count", "Words", "d"),
    ("teach_back_present", "Teach-back", "b"),
    ("follow_up_timeframe", "Follow-up", "b"),
    ("provenance_ratio", "Provenance", "f"),
]


def _fmt(value, kind: str) -> str:
    if value is None:
        return "—"
    if kind == "b":
        # Per-transcript: bool. Aggregate row pre-formatted as "k/n".
        if isinstance(value, bool):
            return "✓" if value else "—"
        return str(value)
    if kind == "f":
        return f"{float(value):.1f}"
    # "d" — could be int OR an already-rounded mean float
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def _aggregate(per_transcript: list[dict]) -> dict:
    """Reduce per-transcript metric dicts to mean (numeric) or
    'k/n' string (boolean). Mean is rounded for display."""
    if not per_transcript:
        return {}
    out: dict = {}
    n = len(per_transcript)
    for col, _label, kind in COLUMNS:
        if col == "condition":
            out[col] = per_transcript[0]["condition"]
            continue
        vals = [r[col] for r in per_transcript]
        if kind == "b":
            # Render as "k/n" — much more informative than a proportion.
            k = sum(1 for v in vals if v)
            out[col] = f"{k}/{n}"
        elif kind == "d":
            mean = statistics.fmean(vals) if vals else 0.0
            # Display int-like means without decimals when they are whole numbers.
            out[col] = round(mean, 1) if not float(mean).is_integer() else int(mean)
        else:  # "f"
            out[col] = round(statistics.fmean(vals), 2) if vals else 0.0
    return out


def _table_md(title: str, rows: list[dict]) -> str:
    headers = [label for _, label, _ in COLUMNS]
    out = [f"# {title}", ""]
    out.append(f"_Auto-generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}_")
    out.append("")
    out.append("| " + " | ".join(headers) + " |")
    out.append("|" + "|".join("---" + (":" if kind != "s" else "") for _, _, kind in COLUMNS) + "|")
    for r in rows:
        out.append("| " + " | ".join(_fmt(r.get(col), kind) for col, _, kind in COLUMNS) + " |")
    return "\n".join(out) + "\n"


def _table_tex(title: str, label: str, rows: list[dict]) -> str:
    headers = [label_ for _, label_, _ in COLUMNS]
    align = "l" + "r" * (len(COLUMNS) - 1)
    out: list[str] = []
    out.append(rf"% {title}. Auto-generated.")
    out.append(r"\begin{table*}[t]")
    out.append(r"\centering")
    out.append(rf"\caption{{{title}.}}")
    out.append(rf"\label{{{label}}}")
    out.append(r"\small")
    out.append(rf"\begin{{tabular}}{{{align}}}")
    out.append(r"\toprule")
    out.append(" & ".join(_tex_escape(h) for h in headers) + r" \\")
    out.append(r"\midrule")
    for r in rows:
        cells = []
        for col, _, kind in COLUMNS:
            v = _fmt(r.get(col), kind)
            v = "$\\checkmark$" if v == "✓" else v
            v = "--" if v == "—" else v
            cells.append(_tex_escape(v))
        out.append(" & ".join(cells) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    out.append(r"\end{table*}")
    return "\n".join(out) + "\n"


def _tex_escape(s) -> str:
    if s is None:
        return ""
    s = str(s)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    out = []
    for ch in s:
        if ch == "\\" and "checkmark" in s:
            out.append(ch)
        else:
            out.append(replacements.get(ch, ch))
    return "".join(out).replace("\\textbackslash{}checkmark", r"\checkmark")


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(prog="scripts/eval_ablations.py")
    p.add_argument("--config", default="config/pipeline.yaml")
    p.add_argument("--demo", action="store_true",
                   help="Mock LLM clients (no GPU; deterministic).")
    p.add_argument("--limit-docs", type=int, default=None,
                   help="Cap docs going into Module III in the full pipeline "
                   "(only useful in --no-demo to bound real-LLM time).")
    p.add_argument("--out-dir", type=Path, default=Path("manuscript/tables_draft"))
    p.add_argument("--data-dir", type=Path, default=Path("manuscript/data"))
    p.add_argument(
        "--reuse-traces-from",
        type=Path,
        default=None,
        help="If set, condition (d) full_pipeline is loaded from "
        "<dir>/trace_<id>.json instead of being re-run. Cuts real-LLM "
        "time roughly in half.",
    )
    args = p.parse_args()

    cfg = load_config(args.config)
    log_path = setup_logging(
        phase="phase12_eval_ablations",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    response_prompt = Path(cfg["prompts"]["response_generation"]).read_text(encoding="utf-8")
    intake_prompt = Path(cfg["prompts"]["intake_system"]).read_text(encoding="utf-8")

    # Shared embedding model (used by both Pipeline and ablations).
    device = "cuda" if cfg["embedding"]["use_gpu_if_available"] and torch.cuda.is_available() else "cpu"
    embed_model = SentenceTransformer(cfg["embedding"]["model"], device=device)
    pipeline = (
        Pipeline.with_mocks(cfg, embed_model=embed_model)
        if args.demo
        else Pipeline.with_real_llm(cfg, embed_model=embed_model)
    )

    # Transcripts to evaluate.
    transcripts = sorted(Path(cfg["paths"]["synthetic_patients"]).glob("*.json"))
    runnable: list[tuple[str, str, list[str]]] = []
    for t in transcripts:
        pid, scenario, utts = load_transcript(t)
        if utts:
            runnable.append((pid, scenario, utts))
    if not runnable:
        console.print("[red]No filled-in transcripts found.[/red]")
        return
    console.print(f"Running 4 conditions x {len(runnable)} transcripts ({'mock' if args.demo else 'real'} LLM).")

    # Per-condition LLM clients
    if args.demo:
        baseline_llm_factory = lambda: MockBaselineLLM()
        framework_llm_factory = lambda: MockResponseLLM()
        intake_llm_factory = lambda: MockLLMClient()
        retr_response_llm_factory = lambda: MockResponseLLM()
    else:
        shared_real = VLLMClient(cfg["llm"])
        baseline_llm_factory = lambda: shared_real
        framework_llm_factory = lambda: shared_real
        intake_llm_factory = lambda: shared_real
        retr_response_llm_factory = lambda: shared_real

    per_condition_rows: dict[str, list[dict]] = {
        "(a) naive": [],
        "(b) framework_only": [],
        "(c) retrieval_only": [],
        "(d) full_pipeline": [],
    }

    for pid, scenario, utterances in runnable:
        console.rule(f"[bold]{pid}[/bold]  ({len(utterances)} turns)")

        # ---- (a) Naive baseline -----------------------------------------
        baseline = NaiveLLMBaseline(baseline_llm_factory())
        b_result = baseline.respond(utterances, transcript_id=pid, scenario=scenario,
                                    mode="mock" if args.demo else "real")
        # For (a) we need the profile to score red-flag presence. Either
        # reuse a cached full-pipeline trace, or re-run the full pipeline.
        if args.reuse_traces_from is not None:
            tp = args.reuse_traces_from / f"trace_{pid}.json"
            if not tp.exists():
                console.print(f"[red]--reuse-traces-from given but {tp} missing[/red]")
                return
            td = json.loads(tp.read_text(encoding="utf-8"))
            from clinicomm.schemas import (
                PatientConcernProfile,
                PatientResponse,
                RankedDocumentSet,
                StructuredContextArtifact,
            )
            from clinicomm.pipeline import PipelineResult
            full_result_for_profile = PipelineResult(
                transcript_id=td["transcript_id"],
                scenario=td["scenario"],
                patient_utterances=td["patient_utterances"],
                intake_trace=td["intake_trace"],
                profile=PatientConcernProfile.model_validate(td["profile"]),
                ranked_docs=RankedDocumentSet.model_validate(td["ranked_docs"]),
                structured_context=StructuredContextArtifact.model_validate(td["structured_context"]),
                response=PatientResponse.model_validate(td["response"]),
                mode=td.get("mode", "real"),
                module_timings_ms=td.get("module_timings_ms"),
            )
            console.print(f"  [dim](d) reused cached trace from {tp}[/dim]")
        else:
            full_result_for_profile = pipeline.run(
                utterances, transcript_id=pid, scenario=scenario,
                max_reasoning_docs=args.limit_docs,
            )
        profile = full_result_for_profile.profile
        m_a = metrics_for_freeform_text(
            response_text=b_result.response_text,
            profile=profile,
            condition="(a) naive",
            transcript_id=pid,
        )
        per_condition_rows["(a) naive"].append(metrics_to_dict(m_a))
        console.print(f"  (a) naive            words={m_a.word_count}  fk={m_a.fk_grade:.1f}  rf_addr={m_a.red_flag_addressed}")

        # ---- (b) Framework-only -----------------------------------------
        fo_response = framework_only_response(
            llm=framework_llm_factory(),
            response_prompt=response_prompt,
            patient_utterances=utterances,
            transcript_id=pid,
        )
        m_b = metrics_for_structured_response(
            response=fo_response, profile=profile,
            condition="(b) framework_only", transcript_id=pid,
        )
        per_condition_rows["(b) framework_only"].append(metrics_to_dict(m_b))
        console.print(f"  (b) framework_only   nurse={m_b.nurse_n}  habits={m_b.four_habits_n}  cit={m_b.citations}  prov={m_b.provenance_ratio:.2f}")

        # ---- (c) Retrieval-only -----------------------------------------
        ro_response, _ro_profile, _ro_ranked = retrieval_only_response(
            cfg=cfg,
            intake_llm=intake_llm_factory(),
            response_llm=retr_response_llm_factory(),
            intake_prompt=intake_prompt,
            response_prompt=response_prompt,
            patient_utterances=utterances,
            transcript_id=pid,
            top_n_docs=5,
        )
        m_c = metrics_for_structured_response(
            response=ro_response, profile=profile,
            condition="(c) retrieval_only", transcript_id=pid,
        )
        per_condition_rows["(c) retrieval_only"].append(metrics_to_dict(m_c))
        console.print(f"  (c) retrieval_only   cit={m_c.citations}  nurse={m_c.nurse_n}  prov={m_c.provenance_ratio:.2f}")

        # ---- (d) Full pipeline (already computed for profile) -----------
        m_d = metrics_for_structured_response(
            response=full_result_for_profile.response, profile=profile,
            condition="(d) full_pipeline", transcript_id=pid,
        )
        per_condition_rows["(d) full_pipeline"].append(metrics_to_dict(m_d))
        console.print(f"  (d) full_pipeline    cit={m_d.citations}  nurse={m_d.nurse_n}  habits={m_d.four_habits_n}  prov={m_d.provenance_ratio:.2f}")

    # --------- aggregate ---------
    summary_rows = [_aggregate(rows) for rows in per_condition_rows.values()]

    # --------- write data sidecar ---------
    args.data_dir.mkdir(parents=True, exist_ok=True)
    data_path = args.data_dir / "ablation_metrics.json"
    data_path.write_text(
        json.dumps(
            {
                "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "mode": "mock" if args.demo else "real",
                "per_condition_per_transcript": per_condition_rows,
                "per_condition_mean": summary_rows,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    console.print(f"\nSaved raw metrics to [cyan]{data_path}[/cyan]")

    # --------- Table 4: per-transcript full vs naive ---------
    # The "pipeline vs baseline" table (T4) is the per-transcript view
    # of (a) and (d). We render one row per transcript per condition.
    args.out_dir.mkdir(parents=True, exist_ok=True)
    t4_rows = []
    for tr_idx in range(len(runnable)):
        tid = runnable[tr_idx][0]
        for cond_label, rows in per_condition_rows.items():
            if cond_label not in ("(a) naive", "(d) full_pipeline"):
                continue
            r = dict(rows[tr_idx])
            r["condition"] = f"{cond_label} · {tid}"
            t4_rows.append(r)
    t4_md = _table_md("Table 4 — Pipeline vs. naive LLM baseline (per transcript)", t4_rows)
    t4_tex = _table_tex("Table 4 — Pipeline vs.\\ naive LLM baseline (per transcript)",
                        "tab:pipeline-vs-baseline", t4_rows)
    (args.out_dir / "table4_pipeline_vs_baseline.md").write_text(t4_md, encoding="utf-8")
    (args.out_dir / "table4_pipeline_vs_baseline.tex").write_text(t4_tex, encoding="utf-8")
    console.print(f"Wrote [cyan]{args.out_dir / 'table4_pipeline_vs_baseline.md'}[/cyan]")

    # --------- Table 5: 4-way ablation summary (mean across transcripts) ---
    t5_md = _table_md("Table 5 — Module-level ablation (mean across transcripts)",
                       summary_rows)
    t5_tex = _table_tex("Table 5 — Module-level ablation (mean across transcripts)",
                        "tab:module-ablation", summary_rows)
    (args.out_dir / "table5_module_ablation.md").write_text(t5_md, encoding="utf-8")
    (args.out_dir / "table5_module_ablation.tex").write_text(t5_tex, encoding="utf-8")
    console.print(f"Wrote [cyan]{args.out_dir / 'table5_module_ablation.md'}[/cyan]")


if __name__ == "__main__":
    main()
