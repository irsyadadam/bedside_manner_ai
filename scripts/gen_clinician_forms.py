"""Generate clinician rubric forms + compute κ vs. the LLM judge.

Phase 13 dual-track human evaluation. The LLM judge in
`clinicomm.external_metrics.llm_judge_rubric()` scores every response
under the same rubric a human rater will use. This script does two
jobs:

  (1) emit-forms  — stratified-sample n=20–30 responses across
                    {datasets} × {conditions}, write one human-friendly
                    Markdown form per sample to
                    manuscript/clinician_forms/<rater_code>/form_<id>.md
                    The form is blinded (no condition / no PMIDs shown)
                    so the rater scores the response on its own merits.

  (2) score-forms — once the rater fills in the forms (writes "1" or
                    "0" in the score blank for each item), this command
                    parses the forms, looks up the LLM judge score for
                    the same response from
                    manuscript/data/external_metrics_*.json, and reports
                    per-item Cohen's κ + overall κ for Table 11.

Examples
--------
  uv run python scripts/gen_clinician_forms.py emit-forms \\
      --n-per-dataset 10 --rater-code R1

  # … rater fills in manuscript/clinician_forms/R1/form_*.md …

  uv run python scripts/gen_clinician_forms.py score-forms \\
      --rater-code R1

The script intentionally does NOT shuffle responses across raters; each
rater gets its own deterministic stratified sample so two raters can
independently score the same set if you want Cohen's κ between humans
too (for inter-clinician baseline).
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

from clinicomm.external_metrics import RUBRIC_ITEMS, cohens_kappa

log = logging.getLogger("clinicomm.scripts.gen_clinician_forms")


CONDITION_DISPLAY = {
    "naive": "Response A",
    "strong_prompt": "Response B",
    "framework_only": "Response C",
    "retrieval_only": "Response D",
    "full": "Response E",
}


# --------------------------------------------------------------------------
# Form rendering
# --------------------------------------------------------------------------


FORM_HEADER = """\
# Clinician rubric scoring — form `{form_id}`

**Rater code:** {rater_code}
**Form ID:** `{form_id}`

Please rate the response below against each rubric item. Score **1** if the
response satisfies the item, **0** if it does not. Use the positive and
negative anchor examples as the boundary. Optional one-line comment per
item explains your reasoning.

This form is blinded: you cannot see which condition produced the response,
or what PMIDs were cited. Score it on the response text alone.

---

## Patient context (transcript excerpt)

{patient_context}

## Response text to score

```
{response_text}
```

---

## Rubric

"""

FORM_ITEM = """\
### {n}. {framework} — {element}

**Definition:** {definition}

**Positive anchor:** {pos}
**Negative anchor:** {neg}

**Score [0 or 1]:** ___

**Comment (optional):**

---

"""

FORM_FOOTER = """\
## Overall qualitative comment (optional)

> Anything that didn't fit the per-item boxes — concerning content,
> standout phrasing, anything you'd want flagged for follow-up:

___
"""


def _render_form(*, form_id: str, rater_code: str, patient_context: str, response_text: str) -> str:
    body = FORM_HEADER.format(
        form_id=form_id,
        rater_code=rater_code,
        patient_context=patient_context,
        response_text=response_text.strip(),
    )
    for i, it in enumerate(RUBRIC_ITEMS, start=1):
        body += FORM_ITEM.format(
            n=i,
            framework=it["framework"],
            element=it["element"],
            definition=it["definition"],
            pos=it["positive_anchor"],
            neg=it["negative_anchor"],
        )
    body += FORM_FOOTER
    return body


# --------------------------------------------------------------------------
# Sampling
# --------------------------------------------------------------------------


def _collect_candidates(traces_root: Path) -> list[dict]:
    """Walk traces_external/* and emit one (dataset, transcript_id, condition,
    response_text, patient_context) record per usable response."""
    out: list[dict] = []
    for ds_dir in sorted(traces_root.iterdir()):
        if not ds_dir.is_dir():
            continue
        for tp in sorted(ds_dir.glob("trace_*.json")):
            try:
                rec = json.loads(tp.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            patient = "\n\n".join(
                f"P{i+1}: {u}" for i, u in enumerate(rec.get("patient_utterances", [])[:4])
            )
            for cond, block in (rec.get("conditions") or {}).items():
                if not block or "error" in block:
                    continue
                text = (block.get("response_text") or "").strip()
                if len(text.split()) < 30:
                    continue
                out.append({
                    "dataset": rec.get("dataset"),
                    "transcript_id": rec.get("transcript_id"),
                    "condition": cond,
                    "response_text": text,
                    "patient_context": patient,
                })
    return out


def emit_forms(args: argparse.Namespace) -> int:
    traces_root = Path(args.traces_root)
    if not traces_root.exists():
        log.error("traces root not found: %s", traces_root)
        return 2

    candidates = _collect_candidates(traces_root)
    if not candidates:
        log.error("no candidate responses found under %s", traces_root)
        return 2

    # Stratified sample: at most --n-per-dataset per (dataset, condition).
    by_strata: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for c in candidates:
        by_strata[(c["dataset"], c["condition"])].append(c)

    rng = random.Random(args.seed)
    sampled: list[dict] = []
    for stratum, cs in by_strata.items():
        n = min(args.n_per_stratum, len(cs))
        sampled.extend(rng.sample(cs, n))

    out_dir = Path(args.out_dir) / args.rater_code
    out_dir.mkdir(parents=True, exist_ok=True)

    # Index keeps the unblinding mapping so score-forms can recover the
    # (dataset, transcript_id, condition) tuple per form_id.
    index: dict[str, dict] = {}
    for i, c in enumerate(sampled, start=1):
        form_id = f"{args.rater_code}-{i:03d}"
        path = out_dir / f"form_{form_id}.md"
        path.write_text(
            _render_form(
                form_id=form_id,
                rater_code=args.rater_code,
                patient_context=c["patient_context"][:1500],
                response_text=c["response_text"][:4500],
            ),
            encoding="utf-8",
        )
        index[form_id] = {
            "dataset": c["dataset"],
            "transcript_id": c["transcript_id"],
            "condition": c["condition"],
        }

    (out_dir / "_index.json").write_text(
        json.dumps(index, indent=2), encoding="utf-8",
    )
    log.info("wrote %d forms to %s (rater=%s, seed=%d)",
             len(sampled), out_dir, args.rater_code, args.seed)
    print(f"\nWrote {len(sampled)} forms to {out_dir}/")
    print(f"Hand these to clinician '{args.rater_code}'. When they're done, run:")
    print(f"  uv run python scripts/gen_clinician_forms.py score-forms --rater-code {args.rater_code}\n")
    return 0


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------


SCORE_LINE_RE = re.compile(
    r"^\*\*Score\s*\[0\s*or\s*1\][:]\*\*\s*(?P<score>[01])\b",
    re.MULTILINE | re.IGNORECASE,
)


def _parse_form(path: Path) -> dict[str, int]:
    """Extract per-item scores from a filled form.

    The form lays out items in the same order as RUBRIC_ITEMS. We index
    by position rather than re-parsing the item titles (which the rater
    may have edited).
    """
    text = path.read_text(encoding="utf-8")
    scores: dict[str, int] = {}
    matches = list(SCORE_LINE_RE.finditer(text))
    for i, it in enumerate(RUBRIC_ITEMS):
        if i < len(matches):
            scores[it["id"]] = int(matches[i].group("score"))
    return scores


def _load_llm_judge_scores(data_root: Path) -> dict[tuple[str, str, str], dict[str, int]]:
    """Build lookup {(dataset, transcript_id, condition) -> {item_id: 0/1}}.

    Reads from per-transcript_scores in external_metrics_<dataset>.json.
    """
    out: dict[tuple[str, str, str], dict[str, int]] = {}
    for f in data_root.glob("external_metrics_*.json"):
        payload = json.loads(f.read_text(encoding="utf-8"))
        ds = payload.get("dataset")
        for tr in payload.get("per_transcript_scores") or []:
            tid = tr.get("transcript_id")
            for cond, m in (tr.get("scores") or {}).items():
                judge = m.get("llm_judge") or {}
                if not judge.get("_available"):
                    continue
                out[(ds, tid, cond)] = {
                    iid: int(judge[iid]["score"])
                    for iid in judge
                    if not iid.startswith("_")
                }
    return out


def score_forms(args: argparse.Namespace) -> int:
    forms_dir = Path(args.out_dir) / args.rater_code
    index_path = forms_dir / "_index.json"
    if not index_path.exists():
        log.error("missing %s — run emit-forms first?", index_path)
        return 2
    index = json.loads(index_path.read_text(encoding="utf-8"))

    llm_judge = _load_llm_judge_scores(Path(args.data_root))
    if not llm_judge:
        log.error("no LLM-judge scores found under %s — run "
                  "eval_against_gold.py --llm-judge first.", args.data_root)
        return 2

    # Collect per-item paired vectors across all forms.
    pair_vecs: dict[str, tuple[list[int], list[int]]] = {
        it["id"]: ([], []) for it in RUBRIC_ITEMS
    }
    n_forms_paired = 0
    for fp in sorted(forms_dir.glob("form_*.md")):
        m = re.match(r"form_(.+)\.md", fp.name)
        if not m:
            continue
        form_id = m.group(1)
        meta = index.get(form_id)
        if not meta:
            continue
        key = (meta["dataset"], meta["transcript_id"], meta["condition"])
        llm = llm_judge.get(key)
        if not llm:
            log.warning("no LLM judge entry for %s", key)
            continue
        human = _parse_form(fp)
        if not human:
            log.warning("no scores parsed from %s (rater hasn't filled it in?)", fp)
            continue
        n_forms_paired += 1
        for iid in pair_vecs:
            if iid in human and iid in llm:
                pair_vecs[iid][0].append(human[iid])
                pair_vecs[iid][1].append(llm[iid])

    if n_forms_paired == 0:
        log.error("no forms had parseable scores for rater %s", args.rater_code)
        return 2

    # Per-item κ + overall κ (flattened across all items).
    flat_h: list[int] = []
    flat_l: list[int] = []
    rows = []
    for iid in (it["id"] for it in RUBRIC_ITEMS):
        h, l = pair_vecs[iid]
        if h:
            kappa = cohens_kappa(h, l)
            agree = sum(1 for a, b in zip(h, l) if a == b) / len(h)
            rows.append({"item_id": iid, "n": len(h), "agreement": agree, "kappa": kappa})
            flat_h.extend(h)
            flat_l.extend(l)
    overall_k = cohens_kappa(flat_h, flat_l)

    payload = {
        "rater_code": args.rater_code,
        "n_forms_paired": n_forms_paired,
        "overall_kappa": overall_k,
        "per_item": rows,
    }
    out_path = Path(args.data_root) / f"clinician_kappa_{args.rater_code}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log.info("wrote %s", out_path)

    print(f"\nκ summary for rater {args.rater_code} (n={n_forms_paired} forms):")
    print(f"  overall κ = {overall_k:+.3f}")
    print("  per-item κ:")
    for r in rows:
        print(f"    {r['item_id']:>28}  n={r['n']:3d}  agree={r['agreement']:.2f}  κ={r['kappa']:+.3f}")
    print(f"\nWritten to {out_path}.")
    print("Once you have ratings from a second clinician, re-run this command "
          "with that rater code to populate Table 11 for both.\n")
    return 0


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description="Clinician rubric form generator / scorer")
    sp = ap.add_subparsers(dest="cmd", required=True)

    emit = sp.add_parser("emit-forms", help="generate blinded forms for a rater")
    emit.add_argument("--rater-code", required=True, help="e.g. R1, R2 (used in form IDs)")
    emit.add_argument("--n-per-stratum", type=int, default=4,
                      help="forms per (dataset × condition) cell (default 4 → ~60 forms total)")
    emit.add_argument("--seed", type=int, default=42)
    emit.add_argument("--traces-root", default="manuscript/traces_external")
    emit.add_argument("--out-dir", default="manuscript/clinician_forms")
    emit.set_defaults(func=emit_forms)

    score = sp.add_parser("score-forms", help="compute κ between this rater and the LLM judge")
    score.add_argument("--rater-code", required=True)
    score.add_argument("--out-dir", default="manuscript/clinician_forms")
    score.add_argument("--data-root", default="manuscript/data")
    score.set_defaults(func=score_forms)

    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
