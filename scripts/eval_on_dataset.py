"""Phase 13 driver — run pipeline + baselines + ablations on an external dataset.

For each transcript in PriMock57 / MTS-Dialog / ACI-Bench, this script
runs five conditions and writes a side-by-side trace plus a compact
JSON record per encounter for downstream metric scoring:

  naive               clinicomm.baseline.NaiveLLMBaseline
  strong_prompt       clinicomm.baseline.StrongPromptLLMBaseline   (Phase 13)
  framework_only      clinicomm.ablations.framework_only_response
  retrieval_only      clinicomm.ablations.retrieval_only_response
  full                clinicomm.pipeline.Pipeline.run

Outputs go to manuscript/traces_external/<dataset>/:
  trace_<id>.md      side-by-side Markdown trace
  trace_<id>.json    structured artifacts for clinicomm.external_metrics

This script is purely the producer. clinicomm.external_metrics +
scripts/eval_against_gold.py (separate driver) consume the JSONs to
emit Tables 8-11 and Figures 13-16.

Examples
--------
  # Smoke test, mocks, 3 transcripts:
  uv run python scripts/eval_on_dataset.py --dataset mts --demo --limit 3

  # Real LLM, full PriMock57 (n=57, ~3h on RTX 6000 Ada):
  uv run python scripts/eval_on_dataset.py --dataset primock57 \\
      --download --max-reasoning-docs 5

  # Real LLM, stratified n=300 of MTS-Dialog:
  uv run python scripts/eval_on_dataset.py --dataset mts \\
      --download --limit 300 --max-reasoning-docs 5

  # Only the strong-prompt baseline (cheapest):
  uv run python scripts/eval_on_dataset.py --dataset aci \\
      --conditions strong_prompt --limit 5

The script is idempotent: if trace_<id>.json already exists and is
non-empty, that transcript is skipped. Re-run after killing to resume.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Iterator

import torch
import yaml
from rich.console import Console

from clinicomm.ablations import (
    framework_only_response,
    naive_to_patient_response,
    retrieval_only_response,
)
from clinicomm.baseline import (
    NaiveLLMBaseline,
    StrongPromptLLMBaseline,
)
from clinicomm.config import load_config
from clinicomm.logging_setup import setup_logging
from clinicomm.modules.llm_client import (
    LLMClient,
    MockLLMClient,
    MockReasoningLLM,
    MockResponseLLM,
    VLLMClient,
)
from clinicomm.pipeline import Pipeline, _load_embed_model
from clinicomm.schemas import PatientConcernProfile, PatientResponse

log = logging.getLogger("clinicomm.scripts.eval_on_dataset")
console = Console()


ALL_CONDITIONS = ["naive", "strong_prompt", "framework_only", "retrieval_only", "full"]


# --------------------------------------------------------------------------
# Dataset dispatch
# --------------------------------------------------------------------------


def _iter_external(dataset: str, *, limit: int | None, cache_dir: Path | None, download: bool):
    """Return an iterator of ExternalTranscript for the named dataset."""
    if dataset in {"mts", "mts_dialog"}:
        from clinicomm.datasets import mts_dialog as mod
        if download:
            mod.download(cache_dir)
        return mod.iter_transcripts(cache_dir=cache_dir, limit=limit)
    if dataset in {"primock57", "primock"}:
        from clinicomm.datasets import primock57 as mod
        if download:
            mod.download(cache_dir)
        return mod.iter_transcripts(cache_dir=cache_dir, limit=limit)
    if dataset in {"aci", "aci_bench"}:
        from clinicomm.datasets import aci_bench as mod
        if download:
            mod.download(cache_dir)
        return mod.iter_transcripts(cache_dir=cache_dir, limit=limit)
    raise ValueError(f"unknown dataset: {dataset!r}")


# --------------------------------------------------------------------------
# Trace MD / JSON writers
# --------------------------------------------------------------------------


def _yaml_pretty(d: dict) -> str:
    return yaml.safe_dump(d, sort_keys=False, default_flow_style=False, width=88, allow_unicode=True)


def _response_to_text(resp: PatientResponse | None) -> str:
    if resp is None:
        return ""
    parts = [resp.acknowledgment or ""]
    for sec in resp.clinical_information_per_concern:
        parts.append(sec.explanation or "")
    parts.extend(resp.next_steps or [])
    parts.append(resp.teach_back_prompt or "")
    parts.append(resp.follow_up_invitation or "")
    return "\n\n".join(p for p in parts if p)


def _profile_summary(profile: PatientConcernProfile | None) -> dict:
    if profile is None:
        return {}
    return {
        "n_problems":     len(profile.problems),
        "n_medications":  len(profile.medications),
        "n_allergies":    len(profile.allergies),
        "n_red_flags":    len(profile.red_flags),
        "n_emotional":    len(profile.emotional_cues),
        "n_goals":        len(profile.patient_goals),
        "problems":       [p.label for p in profile.problems],
        "medications":    list(profile.medications),
        "allergies":      list(profile.allergies),
    }


def _render_trace_md(record: dict) -> str:
    """Render a side-by-side MD comparing all conditions on one transcript."""
    lines: list[str] = []
    lines.append(f"# External-dataset trace — `{record['transcript_id']}`")
    lines.append("")
    lines.append(f"- Dataset: **{record['dataset']}**")
    lines.append(f"- Mode: {record['mode']}")
    lines.append(f"- Speaker strategy: {record['speaker_strategy']}")
    lines.append(f"- # patient utterances: {len(record['patient_utterances'])}")
    if record.get("gold_sections"):
        lines.append(f"- Gold sections: {sorted(record['gold_sections'].keys())}")
    if record.get("gold_note"):
        lines.append(f"- Gold note length: {len(record['gold_note'])} chars")
    lines.append("")

    lines.append("## Patient utterances (first 3)")
    for i, u in enumerate(record["patient_utterances"][:3]):
        lines.append(f"{i+1}. {u}")
    if len(record["patient_utterances"]) > 3:
        lines.append(f"... ({len(record['patient_utterances']) - 3} more)")
    lines.append("")

    if record.get("gold_sections"):
        lines.append("## Gold sections")
        for label, text in record["gold_sections"].items():
            lines.append(f"### {label}")
            lines.append("")
            lines.append(text[:1200] + ("…" if len(text) > 1200 else ""))
            lines.append("")

    for cond in ALL_CONDITIONS:
        block = record.get("conditions", {}).get(cond)
        if not block:
            continue
        lines.append(f"## Condition: `{cond}`")
        lines.append("")
        if "timings_ms" in block:
            lines.append(f"_latency_: {block['timings_ms']:.0f} ms")
            lines.append("")
        if block.get("profile_summary"):
            lines.append("**Extracted profile (summary)**")
            lines.append("```yaml")
            lines.append(_yaml_pretty(block["profile_summary"]).rstrip())
            lines.append("```")
            lines.append("")
        if block.get("response_text"):
            lines.append("**Response**")
            lines.append("")
            lines.append(block["response_text"])
            lines.append("")
        if block.get("pmids_used"):
            lines.append(f"_cited PMIDs_: {block['pmids_used']}")
            lines.append("")
        if block.get("nurse_elements_applied"):
            lines.append(f"_NURSE_: {block['nurse_elements_applied']}")
        if block.get("four_habits_elements_applied"):
            lines.append(f"_Four Habits_: {block['four_habits_elements_applied']}")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Per-condition execution
# --------------------------------------------------------------------------


def _record_for_response(
    cond: str,
    response: PatientResponse,
    profile: PatientConcernProfile | None = None,
    timings_ms: float | None = None,
) -> dict:
    return {
        "condition": cond,
        "timings_ms": timings_ms,
        "response_text": _response_to_text(response),
        "structured_response": response.model_dump(),
        "profile_summary": _profile_summary(profile),
        "pmids_used": list(response.all_pmids_used) if response.all_pmids_used else [],
        "cluster_ids_used": list(response.all_cluster_ids_used) if response.all_cluster_ids_used else [],
        "nurse_elements_applied": list(response.nurse_elements_applied or []),
        "four_habits_elements_applied": list(response.four_habits_elements_applied or []),
    }


def _record_for_baseline(cond: str, response_text: str, timings_ms: float | None) -> dict:
    return {
        "condition": cond,
        "timings_ms": timings_ms,
        "response_text": response_text,
        "structured_response": None,
        "profile_summary": {},
        "pmids_used": [],
        "cluster_ids_used": [],
        "nurse_elements_applied": [],
        "four_habits_elements_applied": [],
    }


def _run_conditions(
    *,
    utterances: list[str],
    transcript_id: str,
    scenario: str,
    conditions: list[str],
    pipeline_real: Pipeline | None,
    pipeline_mock: Pipeline | None,
    cfg: dict,
    llm_for_baselines: LLMClient,
    intake_llm: LLMClient,
    response_llm: LLMClient,
    intake_prompt: str,
    response_prompt: str,
    sentence_model,
    max_reasoning_docs: int | None,
    mode: str,
) -> dict[str, dict]:
    """Run the requested conditions on one transcript. Returns
    {condition_name: record_dict}.

    Each condition is wrapped in try/except so one failure (e.g., an LLM
    timeout on a single transcript) does not kill the run.
    """
    out: dict[str, dict] = {}
    transcript_for_log = transcript_id

    if "naive" in conditions:
        try:
            t0 = time.perf_counter()
            br = NaiveLLMBaseline(llm_for_baselines).respond(
                utterances, transcript_id=transcript_id, scenario=scenario, mode=mode,
            )
            dt = (time.perf_counter() - t0) * 1000
            out["naive"] = _record_for_baseline("naive", br.response_text, dt)
        except Exception as e:  # noqa: BLE001
            log.exception("[%s] naive failed: %s", transcript_for_log, e)
            out["naive"] = {"condition": "naive", "error": str(e)}

    if "strong_prompt" in conditions:
        try:
            t0 = time.perf_counter()
            br = StrongPromptLLMBaseline(llm_for_baselines).respond(
                utterances, transcript_id=transcript_id, scenario=scenario, mode=mode,
            )
            dt = (time.perf_counter() - t0) * 1000
            out["strong_prompt"] = _record_for_baseline("strong_prompt", br.response_text, dt)
        except Exception as e:  # noqa: BLE001
            log.exception("[%s] strong_prompt failed: %s", transcript_for_log, e)
            out["strong_prompt"] = {"condition": "strong_prompt", "error": str(e)}

    if "framework_only" in conditions:
        try:
            t0 = time.perf_counter()
            resp = framework_only_response(
                llm=response_llm,
                response_prompt=response_prompt,
                patient_utterances=utterances,
                transcript_id=transcript_id,
            )
            dt = (time.perf_counter() - t0) * 1000
            out["framework_only"] = _record_for_response("framework_only", resp, profile=None, timings_ms=dt)
        except Exception as e:  # noqa: BLE001
            log.exception("[%s] framework_only failed: %s", transcript_for_log, e)
            out["framework_only"] = {"condition": "framework_only", "error": str(e)}

    if "retrieval_only" in conditions:
        try:
            t0 = time.perf_counter()
            resp, profile, _ranked = retrieval_only_response(
                cfg=cfg,
                intake_llm=intake_llm,
                response_llm=response_llm,
                intake_prompt=intake_prompt,
                response_prompt=response_prompt,
                patient_utterances=utterances,
                transcript_id=transcript_id,
                top_n_docs=5,
                sentence_model=sentence_model,
            )
            dt = (time.perf_counter() - t0) * 1000
            out["retrieval_only"] = _record_for_response("retrieval_only", resp, profile=profile, timings_ms=dt)
        except Exception as e:  # noqa: BLE001
            log.exception("[%s] retrieval_only failed: %s", transcript_for_log, e)
            out["retrieval_only"] = {"condition": "retrieval_only", "error": str(e)}

    if "full" in conditions:
        try:
            pipe = pipeline_real if mode == "real" else pipeline_mock
            assert pipe is not None
            t0 = time.perf_counter()
            res = pipe.run(
                utterances,
                transcript_id=transcript_id,
                scenario=scenario,
                max_reasoning_docs=max_reasoning_docs,
            )
            dt = (time.perf_counter() - t0) * 1000
            out["full"] = _record_for_response(
                "full", res.response, profile=res.profile, timings_ms=dt,
            )
            out["full"]["module_timings_ms"] = res.module_timings_ms
        except Exception as e:  # noqa: BLE001
            log.exception("[%s] full failed: %s", transcript_for_log, e)
            out["full"] = {"condition": "full", "error": str(e)}

    return out


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 13 external-dataset eval driver")
    ap.add_argument(
        "--dataset",
        required=True,
        choices=["mts", "mts_dialog", "primock57", "primock", "aci", "aci_bench"],
    )
    ap.add_argument("--limit", type=int, default=None, help="cap number of transcripts")
    ap.add_argument("--max-reasoning-docs", type=int, default=5,
                    help="cap docs sent to Module III (controls full-pipeline wall-clock)")
    ap.add_argument("--conditions", nargs="+", default=ALL_CONDITIONS,
                    choices=ALL_CONDITIONS,
                    help="which conditions to run")
    ap.add_argument("--demo", action="store_true",
                    help="use mock LLMs (no GPU / no vLLM server)")
    ap.add_argument("--download", action="store_true",
                    help="download dataset files before iterating")
    ap.add_argument("--cache-dir", default=None,
                    help="override db/external/<dataset>/ cache location")
    ap.add_argument("--out-dir", default=None,
                    help="override manuscript/traces_external/<dataset>/ output location")
    ap.add_argument("--speaker-strategy", default="middle",
                    choices=["middle", "patient_only", "interleaved"],
                    help="how to surface clinician turns to the pipeline")
    ap.add_argument("--no-resume", action="store_true",
                    help="re-run transcripts even if trace JSON already exists")
    args = ap.parse_args()

    setup_logging("eval_on_dataset")
    cfg = load_config()

    dataset_canonical = {
        "mts": "mts_dialog", "mts_dialog": "mts_dialog",
        "primock": "primock57", "primock57": "primock57",
        "aci": "aci_bench", "aci_bench": "aci_bench",
    }[args.dataset]

    out_dir = Path(args.out_dir) if args.out_dir else Path(f"manuscript/traces_external/{dataset_canonical}")
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache_dir) if args.cache_dir else None

    mode = "mock" if args.demo else "real"

    # Build pipeline + shared LLM clients once.
    sentence_model = _load_embed_model(cfg)
    if mode == "mock":
        pipeline_mock = Pipeline.with_mocks(cfg, embed_model=sentence_model)
        pipeline_real = None
        llm_for_baselines: LLMClient = MockLLMClient()
        intake_llm: LLMClient = MockLLMClient()
        response_llm: LLMClient = MockResponseLLM()
    else:
        pipeline_mock = None
        pipeline_real = Pipeline.with_real_llm(cfg, embed_model=sentence_model)
        shared_real = VLLMClient(cfg["llm"])
        llm_for_baselines = shared_real
        intake_llm = shared_real
        response_llm = shared_real

    # Re-read prompts so framework_only / retrieval_only can use them.
    intake_prompt = Path(cfg["prompts"]["intake_system"]).read_text(encoding="utf-8")
    response_prompt = Path(cfg["prompts"]["response_generation"]).read_text(encoding="utf-8")

    n_done, n_skipped, n_failed = 0, 0, 0
    t_start = time.time()

    for tr in _iter_external(
        args.dataset, limit=args.limit, cache_dir=cache_dir, download=args.download,
    ):
        json_path = out_dir / f"trace_{tr.id}.json"
        md_path = out_dir / f"trace_{tr.id}.md"

        if not args.no_resume and json_path.exists() and json_path.stat().st_size > 0:
            log.info("[%s] resume: skipping (json exists)", tr.id)
            n_skipped += 1
            continue

        utterances = tr.to_patient_utterances(args.speaker_strategy)
        if not utterances:
            log.warning("[%s] no patient utterances after strategy=%s, skipping",
                        tr.id, args.speaker_strategy)
            n_skipped += 1
            continue

        log.info("[%s] running %d conditions on %d utterances ...",
                 tr.id, len(args.conditions), len(utterances))
        cond_records = _run_conditions(
            utterances=utterances,
            transcript_id=tr.id,
            scenario=tr.scenario,
            conditions=args.conditions,
            pipeline_real=pipeline_real,
            pipeline_mock=pipeline_mock,
            cfg=cfg,
            llm_for_baselines=llm_for_baselines,
            intake_llm=intake_llm,
            response_llm=response_llm,
            intake_prompt=intake_prompt,
            response_prompt=response_prompt,
            sentence_model=sentence_model,
            max_reasoning_docs=args.max_reasoning_docs,
            mode=mode,
        )

        record = {
            "transcript_id": tr.id,
            "dataset": tr.dataset,
            "mode": mode,
            "speaker_strategy": args.speaker_strategy,
            "scenario": tr.scenario,
            "patient_utterances": utterances,
            "gold_note": tr.gold_note,
            "gold_sections": tr.gold_sections,
            "n_patient_turns": tr.n_patient_turns(),
            "n_clinician_turns": tr.n_clinician_turns(),
            "conditions": cond_records,
            "schema_version": "phase13.v1",
        }

        json_path.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
        md_path.write_text(_render_trace_md(record), encoding="utf-8")

        any_error = any("error" in c for c in cond_records.values())
        if any_error:
            n_failed += 1
        else:
            n_done += 1

        elapsed = time.time() - t_start
        log.info(
            "[%s] wrote %s (done=%d skipped=%d failed_partial=%d, %.1f s elapsed)",
            tr.id, json_path.name, n_done, n_skipped, n_failed, elapsed,
        )

    console.print(
        f"[bold green]eval_on_dataset done[/bold green]: "
        f"dataset={dataset_canonical} done={n_done} skipped={n_skipped} "
        f"partial_failures={n_failed} out={out_dir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
