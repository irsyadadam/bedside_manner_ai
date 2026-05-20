"""MTS-Dialog (MEDIQA-Chat 2023) adapter.

Source: https://github.com/abachaa/MTS-Dialog
Citation: Ben Abacha et al. 2023, "An Empirical Study of Clinical Note
Generation from Doctor-Patient Encounters."

Schema (CSV, per row):
  ID, section_header, section_text, dialogue

A given dialogue can appear in multiple rows when its reference note has
multiple labeled sections (HPI, PMH, MEDICATIONS, ALLERGIES, ASSESSMENT,
etc.). We group rows by normalized dialogue text and assemble one
ExternalTranscript per unique dialogue, with `gold_sections` carrying
every section the gold note covers for that encounter.

Why this dataset is the linchpin for Phase 13:
Its section labels map almost 1:1 to PatientConcernProfile fields, which
unlocks Table 8 (Module I extraction precision/recall/F1) with no human
annotation effort. See CLAUDE.md §"Phase 13" for the full mapping.
"""
from __future__ import annotations

import csv
import hashlib
import logging
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Iterator

from clinicomm.datasets.base import (
    ExternalTranscript,
    Turn,
    canonical_role,
    default_cache_dir,
)

log = logging.getLogger(__name__)


# Raw-CSV URLs on GitHub. Pinned to main; if upstream renames a file
# the download() will fail with a clear error and the user can drop the
# CSVs manually into cache_dir.
DATASET_URLS = {
    "train":   "https://raw.githubusercontent.com/abachaa/MTS-Dialog/main/Main-Dataset/MTS-Dialog-TrainingSet.csv",
    "val":     "https://raw.githubusercontent.com/abachaa/MTS-Dialog/main/Main-Dataset/MTS-Dialog-ValidationSet.csv",
    "test_1":  "https://raw.githubusercontent.com/abachaa/MTS-Dialog/main/Main-Dataset/MTS-Dialog-TestSet-1-MEDIQA-Chat-2023.csv",
    "test_2":  "https://raw.githubusercontent.com/abachaa/MTS-Dialog/main/Main-Dataset/MTS-Dialog-TestSet-2-MEDIQA-Sum-2023.csv",
}

# Section header normalization. MTS uses a few capitalization variants.
# The canonical form is uppercase + underscores; consumers (external_metrics)
# match against these.
_SECTION_NORMALIZE = {
    "HISTORY OF PRESENT ILLNESS": "HPI",
    "HISTORY_OF_PRESENT_ILLNESS": "HPI",
    "HPI": "HPI",
    "GENHX": "HPI",                       # MTS abbreviation
    "CHIEF COMPLAINT": "CC",
    "CC": "CC",
    "PAST MEDICAL HISTORY": "PMH",
    "PMH": "PMH",
    "PASTMEDICALHX": "PMH",
    "MEDICATIONS": "MEDICATIONS",
    "CURRENT MEDICATIONS": "MEDICATIONS",
    "MEDICATIONS_HX": "MEDICATIONS",
    "ALLERGIES": "ALLERGIES",
    "FAMILY HISTORY": "FAMILY_HISTORY",
    "FAMILY_HISTORY": "FAMILY_HISTORY",
    "FAMILY/SOCIAL HISTORY": "FAMILY_HISTORY",
    "FAMHX": "FAMILY_HISTORY",
    "SOCIAL HISTORY": "SOCIAL_HISTORY",
    "SOCIAL_HISTORY": "SOCIAL_HISTORY",
    "SOCHX": "SOCIAL_HISTORY",
    "REVIEW OF SYSTEMS": "ROS",
    "ROS": "ROS",
    "PHYSICAL EXAM": "PHYSICAL_EXAM",
    "PHYSICAL_EXAM": "PHYSICAL_EXAM",
    "EXAM": "PHYSICAL_EXAM",
    "ASSESSMENT": "ASSESSMENT",
    "ASSESSMENT AND PLAN": "ASSESSMENT_PLAN",
    "PLAN": "PLAN",
    "DIAGNOSIS": "DIAGNOSIS",
    "EDCOURSE": "ED_COURSE",
    "DISPOSITION": "DISPOSITION",
    "PASTSURGICAL": "PAST_SURGICAL",
    "OTHER_HISTORY": "OTHER_HISTORY",
    "IMMUNIZATIONS": "IMMUNIZATIONS",
    "LABS": "LABS",
    "IMAGING": "IMAGING",
    "PROCEDURES": "PROCEDURES",
}


# MTS turn prefix patterns. The dataset usually formats turns one per line:
#   Doctor: blah
#   Patient: blah
# Sometimes "D:" / "P:", sometimes "Guest_family:" for accompanying family.
_TURN_RE = re.compile(
    r"^\s*(Doctor|Patient|Guest_family|Guest|Nurse|D|P|GP|Doc|Pt|Clinician)\s*[:.\-]\s*(.*)$",
    re.IGNORECASE,
)


def _normalize_section_label(raw: str) -> str:
    """Map a raw MTS section header to the canonical label set."""
    if not raw:
        return ""
    k = raw.strip().upper().replace(" ", "_").replace("/", "_").replace(",", "_")
    return _SECTION_NORMALIZE.get(k) or _SECTION_NORMALIZE.get(raw.strip().upper()) or k


def _dialogue_id(text: str) -> str:
    """Stable short hash of the (whitespace-normalized) dialogue."""
    norm = re.sub(r"\s+", " ", (text or "").strip()).lower()
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]


def _parse_dialogue(raw: str) -> list[Turn]:
    """Parse MTS's free-text dialogue into [Turn(role, text, raw_role)].

    Handles common edge cases: multi-line patient utterances (lines without
    a speaker prefix are appended to the previous turn), and stray empty
    lines. Lines with no speaker prefix at the start of the dialogue
    default to 'other' (rare).
    """
    turns: list[Turn] = []
    current: Turn | None = None
    for line in (raw or "").splitlines():
        line = line.rstrip()
        if not line.strip():
            continue
        m = _TURN_RE.match(line)
        if m:
            raw_role = m.group(1)
            body = m.group(2).strip()
            current = Turn(role=canonical_role(raw_role), text=body, raw_role=raw_role)
            turns.append(current)
        else:
            # Continuation of the prior turn.
            if current is not None:
                current.text = (current.text + " " + line.strip()).strip()
            else:
                turns.append(Turn(role="other", text=line.strip(), raw_role=""))
    return turns


# --------------------------------------------------------------------------
# Download
# --------------------------------------------------------------------------


def download(cache_dir: Path | None = None, *, force: bool = False) -> Path:
    """Fetch the 4 MTS-Dialog CSVs into `cache_dir`. Idempotent.

    Returns the cache directory. Network-free if files already present.
    """
    cache_dir = Path(cache_dir) if cache_dir else default_cache_dir("mts_dialog")
    cache_dir.mkdir(parents=True, exist_ok=True)
    for name, url in DATASET_URLS.items():
        dst = cache_dir / f"{name}.csv"
        if dst.exists() and not force and dst.stat().st_size > 0:
            log.info("mts_dialog: %s already cached", dst.name)
            continue
        log.info("mts_dialog: downloading %s -> %s", url, dst)
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                dst.write_bytes(r.read())
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(
                f"failed to download {url}: {e}.\n"
                f"You can also place the CSV manually at {dst} "
                "and re-run."
            ) from e
    return cache_dir


# --------------------------------------------------------------------------
# Iteration
# --------------------------------------------------------------------------


def _read_rows(cache_dir: Path, splits: list[str]) -> Iterator[dict]:
    """Yield raw CSV rows from the requested splits. Raises if a split file
    is missing — caller should call download() first."""
    for split in splits:
        p = cache_dir / f"{split}.csv"
        if not p.exists():
            raise FileNotFoundError(
                f"{p} not found. Run clinicomm.datasets.mts_dialog.download() first."
            )
        with p.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                row["_split"] = split
                yield row


def iter_transcripts(
    *,
    splits: list[str] | None = None,
    cache_dir: Path | None = None,
    limit: int | None = None,
    min_patient_turns: int = 2,
) -> Iterator[ExternalTranscript]:
    """Yield one ExternalTranscript per unique dialogue.

    splits           : subset of {'train','val','test_1','test_2'}.
                       Default = ['val','test_1'] (smaller, stable for paper).
    cache_dir        : where the CSVs live (default db/external/mts_dialog/).
    limit            : cap number of transcripts yielded.
    min_patient_turns: skip dialogues with too few patient turns to be useful
                       (degenerate single-turn rows are common).
    """
    cache_dir = Path(cache_dir) if cache_dir else default_cache_dir("mts_dialog")
    splits = splits or ["val", "test_1"]

    # Group rows by dialogue hash. Each row contributes one section to the
    # gold_sections dict of its dialogue's ExternalTranscript.
    grouped: dict[str, dict] = {}
    for row in _read_rows(cache_dir, splits):
        dialogue = row.get("dialogue") or row.get("Dialogue") or ""
        dialogue = dialogue.strip()
        if not dialogue:
            continue
        did = _dialogue_id(dialogue)
        section_raw = (
            row.get("section_header")
            or row.get("Section_header")
            or row.get("Section")
            or ""
        ).strip()
        section_text = (
            row.get("section_text") or row.get("Section_text") or ""
        ).strip()
        if did not in grouped:
            row_id = (row.get("ID") or row.get("id") or "").strip()
            split = row.get("_split", "")
            grouped[did] = {
                "id": f"mts_{split}_{row_id or did}",
                "dialogue": dialogue,
                "split": split,
                "gold_sections": {},
                "first_section": section_raw,
            }
        if section_raw:
            label = _normalize_section_label(section_raw)
            # If multiple rows share the same dialogue + section, concatenate.
            if label in grouped[did]["gold_sections"]:
                grouped[did]["gold_sections"][label] += "\n" + section_text
            else:
                grouped[did]["gold_sections"][label] = section_text

    n_yielded = 0
    for did, bundle in grouped.items():
        turns = _parse_dialogue(bundle["dialogue"])
        if sum(1 for t in turns if t.role == "patient") < min_patient_turns:
            continue
        scenario = ""
        # First gold section provides a scenario hint (the first sentence of HPI/CC).
        if bundle["gold_sections"]:
            first_key = next(iter(bundle["gold_sections"]))
            first_val = bundle["gold_sections"][first_key]
            scenario = first_val.split(".")[0][:140].strip()
        t = ExternalTranscript(
            id=bundle["id"],
            dataset="mts_dialog",
            scenario=scenario,
            turns=turns,
            gold_note="",       # MTS doesn't ship a single concatenated note
            gold_sections=bundle["gold_sections"],
            raw_format="csv",
        )
        yield t
        n_yielded += 1
        if limit is not None and n_yielded >= limit:
            return


# --------------------------------------------------------------------------
# CLI (smoke test)
# --------------------------------------------------------------------------


def _cli() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="MTS-Dialog adapter smoke test")
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--download", action="store_true", help="fetch CSVs from GitHub")
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--splits", nargs="+", default=["val", "test_1"])
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    cache = Path(args.cache_dir) if args.cache_dir else None

    if args.download:
        download(cache)

    n = 0
    for t in iter_transcripts(cache_dir=cache, splits=args.splits, limit=args.limit):
        n += 1
        print(f"\n=== {t.id} ({t.n_patient_turns()} pt / {t.n_clinician_turns()} cl turns) ===")
        print(f"  scenario:       {t.scenario[:100]}")
        print(f"  gold sections:  {sorted(t.gold_sections.keys())}")
        first = t.turns[:2]
        for turn in first:
            print(f"  [{turn.role:>9}] {turn.text[:90]}")
        utts = t.to_patient_utterances("middle")
        print(f"  -> {len(utts)} patient utterances (middle strategy)")
        if utts:
            print(f"     ex: {utts[0][:120]}")
    print(f"\nyielded {n} transcripts.")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
