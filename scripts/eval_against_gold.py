"""Phase 13 metric driver — consume trace JSONs, emit Tables 8-11 + figure data.

Reads:
  manuscript/traces_external/<dataset>/trace_*.json
    (produced by scripts/eval_on_dataset.py)

Writes:
  manuscript/tables_draft/table8_mts_extraction_accuracy.{md,tex}
  manuscript/tables_draft/table9_aci_response_quality.{md,tex}
  manuscript/tables_draft/table10_cross_dataset.{md,tex}
  manuscript/tables_draft/table11_llm_judge_kappa.{md,tex}    (κ blank until
                                                              human ratings
                                                              are provided)
  manuscript/data/external_metrics_<dataset>.json             (per-transcript
                                                              per-condition
                                                              metrics)
  manuscript/data/calibration_<dataset>.json                  (Fig 15 data)

The script's job is purely consumption + aggregation — it never calls
the pipeline LLM. The optional --llm-judge flag uses a separate, cheap
LLM call per response to score the NURSE/Four-Habits/safety rubric.

Examples
--------
  uv run python scripts/eval_against_gold.py --dataset mts
  uv run python scripts/eval_against_gold.py --dataset aci --llm-judge
  uv run python scripts/eval_against_gold.py --dataset primock57

When run with --dataset all, generates Tables 8-11 across all three
datasets and the cross-dataset rollup (Table 10).
"""
from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from clinicomm.config import load_config
from clinicomm.external_metrics import (
    RUBRIC_ITEMS,
    aggregate_field_f1,
    bertscore_f1,
    cohens_kappa,
    field_extraction_f1_one,
    flatten_response_text,
    hallucination_rate,
    llm_judge_rubric,
    rouge_l,
    safety_audit,
    topic_coverage,
    trust_calibration_bins,
)
from clinicomm.logging_setup import setup_logging
from clinicomm.metrics import _safe_fk  # reuse Flesch-Kincaid helper
from clinicomm.schemas import PatientConcernProfile, PatientResponse

log = logging.getLogger("clinicomm.scripts.eval_against_gold")


DATASET_ALIASES = {
    "mts": "mts_dialog", "mts_dialog": "mts_dialog",
    "primock57": "primock57", "primock": "primock57",
    "aci": "aci_bench", "aci_bench": "aci_bench",
}


# --------------------------------------------------------------------------
# Trace loading
# --------------------------------------------------------------------------


def _load_traces(dataset: str, traces_root: Path) -> list[dict]:
    """Load every trace_*.json under manuscript/traces_external/<dataset>/."""
    path = traces_root / dataset
    if not path.exists():
        log.warning("no traces directory at %s", path)
        return []
    out: list[dict] = []
    for p in sorted(path.glob("trace_*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError as e:
            log.warning("bad trace JSON %s: %s", p, e)
    return out


def _reconstruct_profile(d: dict) -> PatientConcernProfile:
    """Rebuild a sparse PatientConcernProfile from the saved profile_summary.

    The trace JSON serializes a compact profile summary (n_problems +
    field lists) rather than the full structured object, to keep file
    sizes sane on large datasets. We recover what's needed for the
    extraction-F1 / hallucination metrics from those fields.
    """
    if not d:
        return PatientConcernProfile()
    from clinicomm.schemas import Problem
    return PatientConcernProfile(
        problems=[Problem(label=lbl) for lbl in d.get("problems", []) if lbl],
        medications=list(d.get("medications", [])),
        allergies=list(d.get("allergies", [])),
        relevant_history=[],
        red_flags=[],
        emotional_cues=[],
        patient_goals=[],
        unknowns=[],
        completion_status="reconstructed",
    )


def _reconstruct_response(d: dict | None) -> PatientResponse | None:
    if not d:
        return None
    try:
        return PatientResponse.model_validate(d)
    except Exception as e:  # noqa: BLE001
        log.warning("could not validate structured_response: %s", e)
        return None


# --------------------------------------------------------------------------
# Per-condition metric scoring
# --------------------------------------------------------------------------


def _score_record(record: dict, *, embed_model=None) -> dict:
    """For one transcript trace, compute metrics under each condition.

    Returns a dict keyed by condition name, each value containing:
      hallucination, safety_audit, rouge_l (vs gold), topic_coverage,
      profile_field_scores (if MTS gold sections present), fk_grade,
      length_words.

    embed_model — optional SentenceTransformer for the semantic-anchored
    hallucination rate. If None, only the strict (token-overlap) rate
    is reported.
    """
    transcript_text = " ".join(record.get("patient_utterances", []))
    gold_note = record.get("gold_note") or ""
    gold_sections = record.get("gold_sections") or {}

    # Gold reference for ROUGE/BERT: concatenate sections that map to
    # Module IV's output (subjective + assessment + plan), falling back
    # to the full note if those aren't labeled.
    response_relevant_keys = {"SUBJECTIVE", "ASSESSMENT", "PLAN", "ASSESSMENT_PLAN", "HPI", "CC"}
    relevant_gold = "\n\n".join(
        v for k, v in gold_sections.items() if k in response_relevant_keys
    )
    if not relevant_gold:
        relevant_gold = gold_note

    out: dict = {}
    for cond, block in (record.get("conditions") or {}).items():
        if not block or "error" in block:
            out[cond] = {"error": block.get("error", "missing")}
            continue
        response_text = block.get("response_text") or ""
        profile_summary = block.get("profile_summary") or {}
        profile = _reconstruct_profile(profile_summary)
        structured_response = _reconstruct_response(block.get("structured_response"))

        cond_metrics: dict = {
            "length_words": len(response_text.split()),
            "fk_grade": _safe_fk(response_text),
            "hallucination": hallucination_rate(
                profile=profile,
                transcript_text=transcript_text,
                embed_model=embed_model,
            ),
            "safety_audit": safety_audit(
                response_text=response_text,
                profile=profile,
                structured_response=structured_response,
            ).__dict__,
            "rouge_l": rouge_l(response_text, relevant_gold) if relevant_gold else {"available": False, "reason": "no gold"},
            "topic_coverage_overall": topic_coverage(response_text, relevant_gold),
            "topic_coverage_per_section": {
                lbl: topic_coverage(response_text, text)
                for lbl, text in gold_sections.items()
            },
            "pmids_used": list(block.get("pmids_used") or []),
            "n_pmids": len(block.get("pmids_used") or []),
            "nurse_n": len(block.get("nurse_elements_applied") or []),
            "four_habits_n": len(block.get("four_habits_elements_applied") or []),
            # convergent ratio is only meaningful for full pipeline;
            # we'll see how to fill this in if module_timings_ms includes it.
            "convergent_cluster_ratio": 0.0,
        }

        # MTS field F1 — only meaningful when section-labeled gold exists.
        if gold_sections:
            per_section_scores: dict = {}
            for section, gold_text in gold_sections.items():
                score = field_extraction_f1_one(
                    gold_section=section,
                    gold_text=gold_text,
                    profile=profile,
                    context=None,
                )
                per_section_scores[section] = score
            cond_metrics["profile_field_scores"] = per_section_scores

        out[cond] = cond_metrics
    return out


# --------------------------------------------------------------------------
# LLM-judge (optional pass)
# --------------------------------------------------------------------------


def _run_llm_judge(records: list[dict], scored: list[dict], *, conditions: list[str]) -> dict:
    """Run the rubric LLM judge on every (record, condition) response.

    Mutates `scored` in-place to add `llm_judge` per condition, and
    returns the aggregated per-item / per-condition score table.
    """
    from clinicomm.config import load_config
    from clinicomm.modules.llm_client import VLLMClient
    cfg = load_config()
    judge = VLLMClient(cfg["llm"])

    per_item_totals: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))

    for rec, sc in zip(records, scored):
        for cond in conditions:
            block = (rec.get("conditions") or {}).get(cond)
            if not block or "error" in block:
                continue
            text = block.get("response_text") or ""
            if not text.strip():
                continue
            try:
                judged = llm_judge_rubric(response_text=text, llm_client=judge)
            except Exception as e:  # noqa: BLE001
                log.warning("[%s/%s] llm_judge failed: %s", rec.get("transcript_id"), cond, e)
                continue
            if not judged.get("_available", False):
                continue
            sc.setdefault(cond, {})["llm_judge"] = judged
            for item_id, scoring in judged.items():
                if item_id.startswith("_"):
                    continue
                per_item_totals[cond][item_id].append(int(scoring["score"]))

    summary: dict = {}
    for cond, items in per_item_totals.items():
        summary[cond] = {
            item_id: {"mean": (sum(v) / len(v)) if v else 0.0, "n": len(v)}
            for item_id, v in items.items()
        }
    return summary


# --------------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------------


def _per_condition_means(scored: list[dict]) -> dict[str, dict]:
    """Aggregate per-transcript scores into per-condition means."""
    bins: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    safety_bins: dict[str, list[bool]] = defaultdict(list)
    hall_strict_bins: dict[str, list[float]] = defaultdict(list)
    hall_semantic_bins: dict[str, list[float]] = defaultdict(list)
    pmid_bins: dict[str, list[int]] = defaultdict(list)
    n_per_cond: dict[str, int] = defaultdict(int)
    rouge_bins: dict[str, list[float]] = defaultdict(list)
    topic_bins: dict[str, list[float]] = defaultdict(list)

    for tr in scored:
        for cond, m in tr.items():
            if "error" in m:
                continue
            n_per_cond[cond] += 1
            if isinstance(m.get("rouge_l"), dict) and m["rouge_l"].get("available"):
                rouge_bins[cond].append(m["rouge_l"]["f1"])
            topic_bins[cond].append(m.get("topic_coverage_overall", 0.0))
            hall = m.get("hallucination") or {}
            if hall.get("n_atoms"):
                hall_strict_bins[cond].append(hall.get("rate_strict", hall.get("rate", 0.0)))
                # semantic_available=False means we only have strict;
                # don't double-count by feeding strict into the semantic bin.
                if hall.get("semantic_available"):
                    hall_semantic_bins[cond].append(hall.get("rate_semantic", 0.0))
            sa = m.get("safety_audit") or {}
            if "all_pass" in sa:
                safety_bins[cond].append(bool(sa["all_pass"]))
            pmid_bins[cond].append(int(m.get("n_pmids", 0)))
            bins[cond]["nurse_n"].append(m.get("nurse_n", 0))
            bins[cond]["four_habits_n"].append(m.get("four_habits_n", 0))
            bins[cond]["fk_grade"].append(m.get("fk_grade", 0.0))
            bins[cond]["length_words"].append(m.get("length_words", 0))

    def _mean(vs: Iterable[float]) -> float:
        vs = list(vs)
        return statistics.fmean(vs) if vs else 0.0

    out: dict[str, dict] = {}
    for cond in n_per_cond:
        out[cond] = {
            "n": n_per_cond[cond],
            "rouge_l_f1": _mean(rouge_bins[cond]),
            "topic_coverage": _mean(topic_bins[cond]),
            "hallucination_rate_strict": _mean(hall_strict_bins[cond]),
            "hallucination_rate_semantic": _mean(hall_semantic_bins[cond]) if hall_semantic_bins[cond] else float("nan"),
            "hallucination_rate": _mean(hall_strict_bins[cond]),  # backwards-compat alias
            "safety_pass_rate": _mean(1.0 if x else 0.0 for x in safety_bins[cond]),
            "n_pmids_mean": _mean(pmid_bins[cond]),
            "nurse_n_mean": _mean(bins[cond]["nurse_n"]),
            "four_habits_n_mean": _mean(bins[cond]["four_habits_n"]),
            "fk_grade_mean": _mean(bins[cond]["fk_grade"]),
            "length_words_mean": _mean(bins[cond]["length_words"]),
        }
    return out


# --------------------------------------------------------------------------
# Table renderers
# --------------------------------------------------------------------------


CONDITION_DISPLAY = {
    "naive": "Naive baseline",
    "strong_prompt": "Strong-prompt baseline",
    "framework_only": "Framework only",
    "retrieval_only": "Retrieval only",
    "full": "Full pipeline",
}
CONDITION_ORDER = ["naive", "strong_prompt", "framework_only", "retrieval_only", "full"]


def table8_mts_extraction(scored: list[dict], out_dir: Path) -> None:
    """Table 8 — Module I extraction accuracy on MTS-Dialog."""
    by_cond_per_encounter: dict[str, list[dict]] = defaultdict(list)
    for tr in scored:
        for cond, m in tr.items():
            if "error" in m:
                continue
            scores = m.get("profile_field_scores") or {}
            if scores:
                by_cond_per_encounter[cond].append(scores)

    # For Table 8 we report the conditions that actually run Module I:
    # framework_only doesn't (uses raw transcript), naive/strong_prompt don't.
    table_conditions = [c for c in ["retrieval_only", "full"] if c in by_cond_per_encounter]
    if not table_conditions:
        log.info("table8: no conditions with profile_field_scores; skipping")
        return

    md = ["| Section | Strategy | "
          + " | ".join(f"{CONDITION_DISPLAY[c]} P / R / F1 (n)" for c in table_conditions)
          + " |"]
    md.append("|" + "---|" * (2 + len(table_conditions)))

    section_order = ["HPI", "PMH", "MEDICATIONS", "ALLERGIES",
                     "FAMILY_HISTORY", "SOCIAL_HISTORY", "CC",
                     "ASSESSMENT", "ASSESSMENT_PLAN", "PLAN"]

    macro_per_cond: dict[str, list[float]] = defaultdict(list)
    rows_emitted = 0
    for sec in section_order:
        cells = []
        any_data = False
        first_strategy = None
        for cond in table_conditions:
            scores = [s.get(sec) for s in by_cond_per_encounter[cond]]
            valid = [s for s in scores if s is not None]
            if not valid:
                cells.append("—")
                continue
            any_data = True
            n = len(valid)
            p = statistics.fmean(v[0] for v in valid)
            r = statistics.fmean(v[1] for v in valid)
            f = statistics.fmean(v[2] for v in valid)
            strategy = valid[0][3]
            first_strategy = first_strategy or strategy
            macro_per_cond[cond].append(f)
            cells.append(f"{p:.2f} / {r:.2f} / **{f:.2f}** (n={n})")
        if not any_data:
            continue
        md.append(f"| {sec} | {first_strategy or ''} | " + " | ".join(cells) + " |")
        rows_emitted += 1

    if rows_emitted == 0:
        log.info("table8: no section rows had data; skipping write")
        return

    macro_cells = []
    for cond in table_conditions:
        macro = statistics.fmean(macro_per_cond[cond]) if macro_per_cond[cond] else 0.0
        macro_cells.append(f"**{macro:.2f}**")
    md.append("| **Macro F1 (over sections)** | — | " + " | ".join(macro_cells) + " |")

    header = ("# Table 8 — Module I extraction accuracy (MTS-Dialog)\n\n"
              "Per-section precision / recall / F1 of fields extracted by "
              "Module I against MTS-Dialog gold sections. Strategy is "
              "`set` for discrete fields (MEDICATIONS / ALLERGIES) and "
              "`token_overlap` for free-text fields (HPI, PMH, etc.).\n\n")
    (out_dir / "table8_mts_extraction_accuracy.md").write_text(header + "\n".join(md), encoding="utf-8")
    log.info("wrote %s", out_dir / "table8_mts_extraction_accuracy.md")


def table9_aci_response_quality(scored: list[dict], out_dir: Path) -> None:
    """Table 9 — ACI-Bench response quality, all 5 conditions."""
    summary = _per_condition_means(scored)
    if not summary:
        return
    conds = [c for c in CONDITION_ORDER if c in summary]
    md = ["| Condition | n | ROUGE-L F1 | Topic cov. | Halluc.strict ↓ | Halluc.semantic ↓ | Safety pass | NURSE n | 4H n | PMIDs n | FK |"]
    md.append("|" + "---|" * 11)
    for c in conds:
        s = summary[c]
        sem = s.get("hallucination_rate_semantic", float("nan"))
        sem_str = "—" if (sem != sem) else f"{sem:.3f}"
        md.append(
            f"| {CONDITION_DISPLAY[c]} | {s['n']} | "
            f"{s['rouge_l_f1']:.3f} | {s['topic_coverage']:.3f} | "
            f"{s['hallucination_rate_strict']:.3f} | {sem_str} | "
            f"{s['safety_pass_rate']:.2f} | "
            f"{s['nurse_n_mean']:.1f} | {s['four_habits_n_mean']:.1f} | "
            f"{s['n_pmids_mean']:.1f} | {s['fk_grade_mean']:.1f} |"
        )
    header = ("# Table 9 — Response quality on ACI-Bench\n\n"
              "Mean per-condition metrics across encounters. Bolded numbers "
              "in the manuscript are the Full pipeline row. ↓ = lower better.\n\n")
    (out_dir / "table9_aci_response_quality.md").write_text(header + "\n".join(md), encoding="utf-8")
    log.info("wrote %s", out_dir / "table9_aci_response_quality.md")


def table7_per_dataset_headlines(out_dir: Path, data_root: Path) -> None:
    """Table 7 — 5-condition headline per external dataset.

    Reads the per-dataset metric JSONs from data_root (so this can run
    after eval_against_gold has written them) and produces a single MD
    file with one section per dataset, each showing the same 5 conditions
    × 6 headline metrics (safety, autoDx, PMIDs, NURSE, 4H, halluc strict,
    halluc semantic) plus column definitions.
    """
    datasets = [
        ('PriMock57',  'external_metrics_primock57.json'),
        ('MTS-Dialog', 'external_metrics_mts_dialog.json'),
        ('ACI-Bench',  'external_metrics_aci_bench.json'),
    ]
    cond_order = ['naive', 'strong_prompt', 'framework_only', 'retrieval_only', 'full']
    display = {
        'naive':          'Naive baseline',
        'strong_prompt':  'Strong-prompt baseline',
        'framework_only': 'Framework only',
        'retrieval_only': 'Retrieval only',
        'full':           '**Full pipeline**',
    }

    lines: list[str] = []
    lines.append("# Table 7 — Per-dataset 5-condition headline")
    lines.append("")
    lines.append("Mean per-condition metrics on each external dataset. **n** is the "
                 "number of (transcript, condition) cells that produced a valid "
                 "response (small variation across conditions reflects partial-"
                 "failure cases where one condition errored on a transcript that "
                 "otherwise completed).")
    lines.append("")
    lines.append("Higher is better unless marked ↓. Strict-anchor hallucination "
                 "includes legitimate clinical normalizations (e.g. patient says "
                 "\"burning when I pee\" → Module I extracts \"dysuria\"); "
                 "semantic-anchored hallucination filters those out and captures "
                 "only genuine fabrications.")
    lines.append("")

    any_section = False
    for ds_name, ds_fname in datasets:
        ds_path = data_root / ds_fname
        if not ds_path.exists():
            continue
        try:
            d = json.loads(ds_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not d.get("per_condition_summary"):
            continue
        any_section = True

        lines.append(f"## {ds_name} (n={d['n_transcripts']} transcripts)")
        lines.append("")

        items = defaultdict(lambda: defaultdict(list))
        for tr in d.get('per_transcript_scores') or []:
            for cond, m in (tr.get('scores') or {}).items():
                if 'error' in m:
                    continue
                sa = m.get('safety_audit') or {}
                items[cond]['autoDx'].append(1.0 if sa.get('no_autonomous_diagnosis') else 0.0)

        lines.append("| Condition | n | Safety pass | autoDx pass | PMIDs / resp | NURSE n | 4H n | Halluc strict ↓ | Halluc sem ↓ |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for c in cond_order:
            s = d['per_condition_summary'].get(c)
            if not s:
                continue
            autoDx = (
                sum(items[c]['autoDx']) / len(items[c]['autoDx']) * 100
                if items[c]['autoDx'] else 0.0
            )
            sem = s.get('hallucination_rate_semantic', float('nan'))
            sem_str = f"{sem:.3f}" if sem == sem else "—"
            lines.append(
                f"| {display[c]} | {s['n']} | "
                f"{100*s['safety_pass_rate']:.0f}% | {autoDx:.0f}% | "
                f"{s['n_pmids_mean']:.2f} | {s['nurse_n_mean']:.2f} | "
                f"{s['four_habits_n_mean']:.2f} | "
                f"{s['hallucination_rate_strict']:.3f} | {sem_str} |"
            )
        lines.append("")

    if not any_section:
        log.info("table7: no dataset metric JSONs found under %s; skipping", data_root)
        return

    lines.append("## Column definitions")
    lines.append("")
    lines.append("- **Safety pass** — composite pass on the 4-item safety audit "
                 "(escalation when red flag, no autonomous diagnosis, follow-up "
                 "timeframe present, clinician-in-the-loop). All 4 must pass. ↑.")
    lines.append("- **autoDx pass** — pass rate on the no-autonomous-diagnosis item "
                 "alone, broken out as the cleanest single safety signal. ↑.")
    lines.append("- **PMIDs / resp** — mean count of verifiable PubMed citations "
                 "per response (real PMIDs from validated clusters). ↑.")
    lines.append("- **NURSE n** — mean count of NURSE empathy elements applied "
                 "per response (max 5: Name, Understand, Respect, Support, "
                 "Explore). ↑.")
    lines.append("- **4H n** — mean count of Four-Habits Model elements applied "
                 "per response (max 4: Invest in beginning, Elicit patient "
                 "perspective, Demonstrate empathy, Invest in end). ↑.")
    lines.append("- **Halluc strict ↓** — fraction of Module I-extracted atoms "
                 "not anchored in the transcript by verbatim/token-overlap. "
                 "Includes both fabrications AND legitimate clinical "
                 "normalizations. — = no atoms extracted.")
    lines.append("- **Halluc sem ↓** — strict failures that also fail a BGE "
                 "embedding-similarity check vs. transcript sentences. "
                 "Approximates genuine fabrications by filtering out "
                 "normalizations. Manuscript headline.")
    lines.append("")
    lines.append("Reproducible from the per-condition summary JSON files in "
                 "`manuscript/data/`; re-run `scripts/eval_against_gold.py "
                 "--dataset all` to regenerate.")
    lines.append("")

    path = out_dir / "table7_per_dataset_headlines.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    log.info("wrote %s", path)


def table10_cross_dataset(all_summaries: dict[str, dict], out_dir: Path) -> None:
    """Table 10 — cross-dataset rollup for the Full pipeline + Strong baseline."""
    if not all_summaries:
        return
    md = ["| Dataset | Condition | n | ROUGE-L | Topic cov. | Halluc.strict ↓ | Halluc.semantic ↓ | Safety pass | NURSE n | 4H n |"]
    md.append("|" + "---|" * 10)
    for dataset, summary in all_summaries.items():
        for c in ("strong_prompt", "full"):
            s = summary.get(c)
            if not s:
                continue
            sem = s.get("hallucination_rate_semantic", float("nan"))
            sem_str = "—" if (sem != sem) else f"{sem:.3f}"
            md.append(
                f"| {dataset} | {CONDITION_DISPLAY[c]} | {s['n']} | "
                f"{s['rouge_l_f1']:.3f} | {s['topic_coverage']:.3f} | "
                f"{s['hallucination_rate_strict']:.3f} | {sem_str} | "
                f"{s['safety_pass_rate']:.2f} | "
                f"{s['nurse_n_mean']:.1f} | {s['four_habits_n_mean']:.1f} |"
            )
    header = ("# Table 10 — Cross-dataset summary\n\n"
              "Headline metrics for the Full pipeline vs. the Strong-prompt "
              "baseline across PriMock57 / MTS-Dialog / ACI-Bench. Demonstrates "
              "that the framework + retrieval contributions generalize across "
              "dialogue styles and gold-note formats.\n\n")
    (out_dir / "table10_cross_dataset.md").write_text(header + "\n".join(md), encoding="utf-8")
    log.info("wrote %s", out_dir / "table10_cross_dataset.md")


def table11b_per_dataset(out_dir: Path, data_root: Path) -> None:
    """Table 11b — per-dataset rubric scores from LLM judge.

    Mirrors Table 11's pooled view with one section per external dataset.
    Reads each dataset's judge_summary from manuscript/data/external_metrics_*.json
    and renders a 14-row × 5-condition table per dataset.
    """
    datasets = [
        ('PriMock57',  'external_metrics_primock57.json'),
        ('MTS-Dialog', 'external_metrics_mts_dialog.json'),
        ('ACI-Bench',  'external_metrics_aci_bench.json'),
    ]
    cond_order = ['naive', 'strong_prompt', 'framework_only', 'retrieval_only', 'full']
    cond_display = {
        'naive': 'Naive',
        'strong_prompt': 'Strong-prompt',
        'framework_only': 'Framework only',
        'retrieval_only': 'Retrieval only',
        'full': 'Full pipeline',
    }

    lines: list[str] = []
    lines.append("# Table 11b — LLM-judge rubric scoring, per dataset")
    lines.append("")
    lines.append("Per-item mean rubric score broken out by external dataset. "
                 "Reveals the deployment-context dependence of each condition's "
                 "rubric-item performance that Table 11's pooled view averages "
                 "away.")
    lines.append("")

    any_data = False
    for ds_name, ds_fname in datasets:
        ds_path = data_root / ds_fname
        if not ds_path.exists():
            continue
        try:
            d = json.loads(ds_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        js = d.get('judge_summary') or {}
        if not js:
            continue
        any_data = True

        lines.append(f"## {ds_name} (n={d['n_transcripts']} transcripts)")
        lines.append("")
        header = "| Rubric item | Element | "
        header += " | ".join(cond_display[c] for c in cond_order) + " |"
        lines.append(header)
        lines.append("|---|---|" + "---:|" * len(cond_order))

        item_lookup = {it["id"]: it for it in RUBRIC_ITEMS}
        for it in RUBRIC_ITEMS:
            iid = it["id"]
            cells = []
            for c in cond_order:
                entry = js.get(c, {}).get(iid, {})
                mean = entry.get('mean', 0.0)
                n = entry.get('n', 0)
                cells.append(f"{mean:.2f} (n={n})")
            lines.append(f"| `{iid}` | {it['element']} | " + " | ".join(cells) + " |")
        lines.append("")

    if not any_data:
        log.info("table11b: no judge data found across datasets; skipping")
        return

    lines.append("## Reading")
    lines.append("")
    lines.append("- The 0/1 scoring is anchored by positive + negative example "
                 "for each item (see `clinicomm.external_metrics.RUBRIC_ITEMS`). "
                 "Same rubric goes to human raters via "
                 "`scripts/gen_clinician_forms.py`.")
    lines.append("- Each row's column-to-column delta isolates how much that "
                 "condition's design contributes to the rubric item's "
                 "behavior, within that deployment context.")
    lines.append("- Items where ALL conditions score near 1.00 (e.g., "
                 "plain_language) reflect free LLM behavior, not framework "
                 "contribution.")
    lines.append("- Items where the naive baseline scores near 0 but pipeline "
                 "conditions score >0.9 (e.g., teach_back, habits_close on "
                 "PriMock+ACI) are the framework's clearest contributions.")
    lines.append("")
    path = out_dir / "table11b_llm_judge_per_dataset.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    log.info("wrote %s", path)


def table11_llm_judge(judge_summary: dict, out_dir: Path) -> None:
    """Table 11 — LLM-judge mean per rubric item, with κ column placeholder."""
    if not judge_summary:
        return
    item_ids = [it["id"] for it in RUBRIC_ITEMS]
    conds = list(judge_summary.keys())
    md = ["| Rubric item | Framework | Element | "
          + " | ".join(f"{CONDITION_DISPLAY.get(c, c)} (mean)" for c in conds)
          + " | Cohen κ (LLM vs. human) |"]
    md.append("|" + "---|" * (3 + len(conds) + 1))
    item_lookup = {it["id"]: it for it in RUBRIC_ITEMS}
    for iid in item_ids:
        it = item_lookup[iid]
        cells = []
        for c in conds:
            entry = judge_summary[c].get(iid, {})
            mean = entry.get("mean", 0.0)
            n = entry.get("n", 0)
            cells.append(f"{mean:.2f} (n={n})")
        md.append(
            f"| `{iid}` | {it['framework']} | {it['element']} | "
            + " | ".join(cells)
            + " | _pending human ratings_ |"
        )
    header = ("# Table 11 — LLM-as-judge rubric scoring\n\n"
              "Per-item mean rubric score from the LLM judge. Cohen's κ "
              "between LLM ratings and clinician ratings is reported once "
              "the n=20–30 spot-check sample comes back (see "
              "`scripts/gen_clinician_forms.py`).\n\n")
    (out_dir / "table11_llm_judge_kappa.md").write_text(header + "\n".join(md), encoding="utf-8")
    log.info("wrote %s", out_dir / "table11_llm_judge_kappa.md")


# --------------------------------------------------------------------------
# Optional batched BERTScore pass
# --------------------------------------------------------------------------


def _add_bertscore(scored: list[dict], records: list[dict]) -> None:
    """Batched BERTScore for each condition. Heavy — opt-in via --bertscore."""
    # Collect (rec, cond, prediction, reference) tuples.
    triples: list[tuple[int, str, str, str]] = []
    for ti, (rec, sc) in enumerate(zip(records, scored)):
        gold_sections = rec.get("gold_sections") or {}
        relevant_keys = {"SUBJECTIVE", "ASSESSMENT", "PLAN", "ASSESSMENT_PLAN", "HPI", "CC"}
        ref = "\n\n".join(v for k, v in gold_sections.items() if k in relevant_keys) or rec.get("gold_note", "")
        if not ref:
            continue
        for cond, m in sc.items():
            if "error" in m:
                continue
            block = (rec.get("conditions") or {}).get(cond) or {}
            text = block.get("response_text") or ""
            if text.strip():
                triples.append((ti, cond, text, ref))

    if not triples:
        return
    preds = [t[2] for t in triples]
    refs = [t[3] for t in triples]
    result = bertscore_f1(preds, refs)
    if not result.get("available"):
        log.warning("bertscore not available: %s", result.get("reason"))
        return
    # We only stored an aggregate mean above; for per-condition table cells
    # we want per-row scores. Fall back to a recompute below if needed.
    # For now, record the global mean by condition by streaming once more.
    try:
        import bert_score
        P, R, F = bert_score.score(preds, refs, lang="en", verbose=False, batch_size=8)
        F = F.tolist()
    except Exception as e:  # noqa: BLE001
        log.warning("per-pair bertscore failed: %s", e)
        return
    for (ti, cond, _p, _r), f in zip(triples, F):
        scored[ti].setdefault(cond, {})["bertscore_f1"] = float(f)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def _process_one_dataset(
    *,
    dataset: str,
    traces_root: Path,
    tables_out: Path,
    data_out: Path,
    run_llm_judge: bool,
    run_bertscore: bool,
    embed_model=None,
) -> dict | None:
    records = _load_traces(dataset, traces_root)
    if not records:
        log.warning("no traces loaded for dataset=%s", dataset)
        return None
    scored = [_score_record(r, embed_model=embed_model) for r in records]
    if run_bertscore:
        _add_bertscore(scored, records)

    # PRESERVE existing judge_summary from disk when --llm-judge is NOT set.
    # Without this guard, calling eval_against_gold to refresh strict metrics
    # would silently wipe the judge data from a prior --llm-judge run, which
    # is expensive to regenerate (hours of LLM calls).
    judge_summary: dict = {}
    existing_path = data_out / f"external_metrics_{dataset}.json"
    if not run_llm_judge and existing_path.exists():
        try:
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
            judge_summary = existing.get("judge_summary") or {}
            if judge_summary:
                log.info("preserving existing judge_summary (%d conditions) from %s",
                         len(judge_summary), existing_path.name)
        except (json.JSONDecodeError, OSError):
            judge_summary = {}

    if run_llm_judge:
        all_conditions_seen = set()
        for s in scored:
            all_conditions_seen.update(s.keys())
        judge_summary = _run_llm_judge(records, scored, conditions=sorted(all_conditions_seen))

    summary = _per_condition_means(scored)

    if dataset == "mts_dialog":
        table8_mts_extraction(scored, tables_out)
    if dataset == "aci_bench":
        table9_aci_response_quality(scored, tables_out)

    data_out.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset": dataset,
        "n_transcripts": len(records),
        "per_condition_summary": summary,
        "judge_summary": judge_summary,
        "per_transcript_scores": [
            {"transcript_id": r["transcript_id"], "scores": s}
            for r, s in zip(records, scored)
        ],
    }
    (data_out / f"external_metrics_{dataset}.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8"
    )
    log.info("wrote %s", data_out / f"external_metrics_{dataset}.json")

    # Trust calibration: one row per (transcript, "full") with
    # confidence proxy = NURSE+4H coverage / 9 (max), accuracy = safety pass.
    calib_rows = []
    for rec, sc in zip(records, scored):
        full = sc.get("full")
        if not full or "error" in full:
            continue
        nurse_n = full.get("nurse_n", 0)
        habits_n = full.get("four_habits_n", 0)
        conf = (nurse_n + habits_n) / 9.0
        acc = bool(full.get("safety_audit", {}).get("all_pass", False))
        calib_rows.append({"confidence": conf, "all_pass": acc,
                           "n_pmids": full.get("n_pmids", 0)})
    if calib_rows:
        bins = trust_calibration_bins(
            calib_rows, confidence_key="confidence", accuracy_key="all_pass",
        )
        (data_out / f"calibration_{dataset}.json").write_text(
            json.dumps({"dataset": dataset, "bins": bins, "rows": calib_rows}, indent=2),
            encoding="utf-8",
        )
        log.info("wrote %s", data_out / f"calibration_{dataset}.json")

    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 13 metric driver")
    ap.add_argument("--dataset", default="all",
                    choices=["all", "mts", "mts_dialog", "primock57", "primock", "aci", "aci_bench"])
    ap.add_argument("--traces-root", default="manuscript/traces_external")
    ap.add_argument("--tables-out", default="manuscript/tables_draft")
    ap.add_argument("--data-out", default="manuscript/data")
    ap.add_argument("--llm-judge", action="store_true",
                    help="run the rubric LLM judge (one extra LLM call per "
                         "response — heavy)")
    ap.add_argument("--bertscore", action="store_true",
                    help="compute per-pair BERTScore (loads ~2GB model)")
    ap.add_argument("--no-semantic-hallucination", action="store_true",
                    help="skip the BGE-embedding semantic-anchor hallucination "
                         "check (only report the strict token-overlap rate)")
    args = ap.parse_args()

    setup_logging("eval_against_gold")
    traces_root = Path(args.traces_root)
    tables_out = Path(args.tables_out)
    data_out = Path(args.data_out)
    tables_out.mkdir(parents=True, exist_ok=True)
    data_out.mkdir(parents=True, exist_ok=True)

    embed_model = None
    if not args.no_semantic_hallucination:
        try:
            import torch
            from sentence_transformers import SentenceTransformer
            cfg = load_config()
            device = "cuda" if torch.cuda.is_available() and cfg["embedding"].get(
                "use_gpu_if_available", True) else "cpu"
            log.info("loading BGE for semantic hallucination check on %s ...", device)
            embed_model = SentenceTransformer(cfg["embedding"]["model"], device=device)
        except Exception as e:  # noqa: BLE001
            log.warning("could not load embedding model (%s) — falling back to "
                        "strict-only hallucination metric", e)
            embed_model = None

    if args.dataset != "all":
        ds = DATASET_ALIASES[args.dataset]
        summary = _process_one_dataset(
            dataset=ds, traces_root=traces_root, tables_out=tables_out, data_out=data_out,
            run_llm_judge=args.llm_judge, run_bertscore=args.bertscore,
            embed_model=embed_model,
        )
        all_summaries = {ds: summary} if summary else {}
    else:
        all_summaries = {}
        for ds in ("primock57", "mts_dialog", "aci_bench"):
            summary = _process_one_dataset(
                dataset=ds, traces_root=traces_root, tables_out=tables_out, data_out=data_out,
                run_llm_judge=args.llm_judge, run_bertscore=args.bertscore,
                embed_model=embed_model,
            )
            if summary:
                all_summaries[ds] = summary

    table7_per_dataset_headlines(tables_out, data_out)
    table10_cross_dataset(all_summaries, tables_out)

    # Aggregate judge summary across datasets for Table 11 (if any judge run happened).
    judge_data_files = list(data_out.glob("external_metrics_*.json"))
    combined_judge: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for jp in judge_data_files:
        payload = json.loads(jp.read_text(encoding="utf-8"))
        js = payload.get("judge_summary") or {}
        for cond, items in js.items():
            for iid, m in items.items():
                # m has {mean, n}; we approximate the underlying scores by
                # synthesizing n copies of round(mean)
                n = int(m.get("n", 0))
                mean = m.get("mean", 0.0)
                ones = int(round(mean * n))
                combined_judge[cond][iid].extend([1] * ones + [0] * (n - ones))
    if combined_judge:
        judge_summary_combined = {
            cond: {iid: {"mean": (sum(v) / len(v)) if v else 0.0, "n": len(v)}
                   for iid, v in items.items()}
            for cond, items in combined_judge.items()
        }
        table11_llm_judge(judge_summary_combined, tables_out)
        table11b_per_dataset(tables_out, data_out)

    log.info("eval_against_gold done — see %s/", tables_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
