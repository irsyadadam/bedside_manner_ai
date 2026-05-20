"""ACI-Bench adapter.

Source: https://github.com/wyim/aci-bench
Citation: Yim et al. 2023, "ACI-Bench: a Novel Ambient Clinical
Intelligence Dataset for Benchmarking Automatic Visit Note Generation."

207 doctor-patient encounters paired with full SOAP / sectioned
clinician notes. Used in Phase 13 for Module IV response-quality
evaluation (Table 9): ROUGE-L + BERTScore + topic-coverage of the
generated PatientResponse vs. the reference note's
SUBJECTIVE+ASSESSMENT+PLAN sections (Module IV does not produce an
OBJECTIVE/exam section, so OBJECTIVE is excluded from the comparison).

Repo layout (as of late 2024):
  data/challenge_data/{train,valid,test1,test2}/<split>.csv
with columns: encounter_id, dataset, dialogue, note (and a few others).
This adapter is tolerant of column-name variation.
"""
from __future__ import annotations

import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterator

from clinicomm.datasets.base import (
    ExternalTranscript,
    Turn,
    canonical_role,
    default_cache_dir,
)

log = logging.getLogger(__name__)


REPO_URL = "https://github.com/wyim/aci-bench.git"


# ACI-Bench section headers. Some notes use SOAP, some use CC/HPI style.
_SECTION_HEADER_RE = re.compile(
    r"^(?P<header>[A-Z][A-Z _/&\-]{2,})\s*$",
    re.MULTILINE,
)

# Canonical section names — see mts_dialog for the full key set.
_SECTION_NORMALIZE = {
    "SUBJECTIVE": "SUBJECTIVE",
    "OBJECTIVE": "OBJECTIVE",
    "ASSESSMENT": "ASSESSMENT",
    "PLAN": "PLAN",
    "ASSESSMENT_AND_PLAN": "ASSESSMENT_PLAN",
    "ASSESSMENT & PLAN": "ASSESSMENT_PLAN",
    "A/P": "ASSESSMENT_PLAN",
    "CHIEF_COMPLAINT": "CC",
    "CC": "CC",
    "HISTORY_OF_PRESENT_ILLNESS": "HPI",
    "HPI": "HPI",
    "PAST_MEDICAL_HISTORY": "PMH",
    "PMH": "PMH",
    "MEDICATIONS": "MEDICATIONS",
    "ALLERGIES": "ALLERGIES",
    "FAMILY_HISTORY": "FAMILY_HISTORY",
    "SOCIAL_HISTORY": "SOCIAL_HISTORY",
    "REVIEW_OF_SYSTEMS": "ROS",
    "PHYSICAL_EXAM": "PHYSICAL_EXAM",
    "EXAM": "PHYSICAL_EXAM",
    "RESULTS": "RESULTS",
    "VITALS": "VITALS",
}


def _norm_header(h: str) -> str:
    k = h.strip().upper().replace(" ", "_").replace("/", "_").replace("&", "AND")
    return _SECTION_NORMALIZE.get(k, k)


def parse_soap_note(note: str) -> dict[str, str]:
    """Split an ACI-Bench reference note into {section_label: text}.

    Notes use ALL-CAPS section headers on their own line. Text between
    a header and the next header (or EOF) is the section body. If the
    note has no recognizable headers, returns {'UNSTRUCTURED': note}.
    """
    if not note:
        return {}
    # Collect (start_index, end_index, normalized_header) for each match.
    matches = list(_SECTION_HEADER_RE.finditer(note))
    if not matches:
        return {"UNSTRUCTURED": note.strip()}
    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        raw_header = m.group("header").strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(note)
        body = note[start:end].strip()
        if not body:
            continue
        label = _norm_header(raw_header)
        # Concatenate if the same canonical label appears more than once.
        if label in out:
            out[label] += "\n" + body
        else:
            out[label] = body
    return out


_TURN_RE = re.compile(
    # Accepts: 'Doctor: text', '[Doctor] text', 'Doctor - text'. The
    # separator after the speaker label is optional ONLY when the label
    # is bracketed; bare 'Doctor What...' would otherwise eat any word
    # starting with a capitalized speaker name.
    r"^\s*(?:"
    r"\[(?P<bracket>Doctor|Patient|Doc|Pt|Clinician|Physician|GP|D|P|Guest_family|Guest)\]\s*[:.\-]?\s*"
    r"|"
    r"(?P<bare>Doctor|Patient|Doc|Pt|Clinician|Physician|GP|D|P|Guest_family|Guest)\s*[:.\-]\s*"
    r")(?P<body>.*)$",
    re.IGNORECASE,
)


def parse_dialogue(raw: str) -> list[Turn]:
    """Parse an ACI-Bench dialogue field into Turns."""
    turns: list[Turn] = []
    current: Turn | None = None
    for line in (raw or "").splitlines():
        line = line.rstrip()
        if not line.strip():
            continue
        m = _TURN_RE.match(line)
        if m:
            raw_role = m.group("bracket") or m.group("bare") or ""
            body = (m.group("body") or "").strip()
            current = Turn(role=canonical_role(raw_role), text=body, raw_role=raw_role)
            turns.append(current)
        elif current is not None:
            current.text = (current.text + " " + line.strip()).strip()
    return turns


# --------------------------------------------------------------------------
# Download
# --------------------------------------------------------------------------


def download(cache_dir: Path | None = None, *, force: bool = False) -> Path:
    """Clone aci-bench into cache_dir/aci-bench/. Idempotent."""
    cache_dir = Path(cache_dir) if cache_dir else default_cache_dir("aci_bench")
    cache_dir.mkdir(parents=True, exist_ok=True)
    repo_dir = cache_dir / "aci-bench"
    if repo_dir.exists() and not force:
        log.info("aci_bench: repo already at %s", repo_dir)
        return repo_dir
    if repo_dir.exists() and force:
        import shutil
        shutil.rmtree(repo_dir)
    log.info("aci_bench: cloning %s into %s", REPO_URL, repo_dir)
    subprocess.check_call(["git", "clone", "--depth=1", REPO_URL, str(repo_dir)])
    return repo_dir


# --------------------------------------------------------------------------
# Iteration
# --------------------------------------------------------------------------


def _locate_csvs(repo_dir: Path) -> list[Path]:
    """Find all challenge-data CSVs in the repo. ACI-Bench has shipped
    these under several path variants over time; we glob defensively."""
    candidates: list[Path] = []
    for p in repo_dir.rglob("*.csv"):
        if "challenge_data" in p.as_posix() or p.name in {
            "train.csv", "valid.csv", "test1.csv", "test2.csv",
            "train_clean.csv", "valid_clean.csv",
        }:
            candidates.append(p)
    return sorted(candidates)


def _read_csv_rows(path: Path) -> Iterator[dict]:
    import csv
    with path.open("r", encoding="utf-8", newline="") as fh:
        # Some ACI files use a quote-heavy schema; csv.DictReader handles it.
        reader = csv.DictReader(fh)
        for row in reader:
            yield row


def iter_transcripts(
    *,
    cache_dir: Path | None = None,
    limit: int | None = None,
    splits: list[str] | None = None,
) -> Iterator[ExternalTranscript]:
    """Yield one ExternalTranscript per ACI-Bench encounter.

    splits: optional filter on the 'dataset' column (e.g. ['valid','test1']).
            If None, all encounters are yielded.
    """
    cache_dir = Path(cache_dir) if cache_dir else default_cache_dir("aci_bench")
    repo_dir = cache_dir / "aci-bench"
    if not repo_dir.exists():
        raise FileNotFoundError(
            f"{repo_dir} not found. Run clinicomm.datasets.aci_bench.download() first."
        )
    csvs = _locate_csvs(repo_dir)
    if not csvs:
        raise RuntimeError(f"No CSV files found under {repo_dir}.")
    n = 0
    seen_ids: set[str] = set()
    for csv_path in csvs:
        split_hint = csv_path.stem
        try:
            for row in _read_csv_rows(csv_path):
                dialogue = (
                    row.get("dialogue")
                    or row.get("Dialogue")
                    or row.get("conversation")
                    or ""
                )
                note = (
                    row.get("note")
                    or row.get("Note")
                    or row.get("reference_note")
                    or ""
                )
                if not dialogue.strip():
                    continue
                eid = (
                    row.get("encounter_id")
                    or row.get("id")
                    or row.get("ID")
                    or row.get("encounter")
                    or f"{split_hint}_{n}"
                ).strip()
                if eid in seen_ids:
                    continue
                seen_ids.add(eid)
                split_label = (row.get("dataset") or row.get("split") or split_hint).strip()
                if splits and split_label not in splits:
                    continue
                turns = parse_dialogue(dialogue)
                if not turns:
                    continue
                gold_sections = parse_soap_note(note)
                scenario = ""
                for t in turns:
                    if t.role == "patient" and t.text.strip():
                        scenario = t.text.strip()[:140]
                        break
                yield ExternalTranscript(
                    id=f"aci_{split_label}_{eid}",
                    dataset="aci_bench",
                    scenario=scenario,
                    turns=turns,
                    gold_note=note.strip(),
                    gold_sections=gold_sections,
                    raw_format="csv",
                )
                n += 1
                if limit is not None and n >= limit:
                    return
        except (FileNotFoundError, OSError) as e:
            log.warning("aci_bench: skipping %s (%s)", csv_path, e)


# --------------------------------------------------------------------------
# CLI smoke test
# --------------------------------------------------------------------------


def _cli() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="ACI-Bench adapter smoke test")
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--limit", type=int, default=3)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    cache = Path(args.cache_dir) if args.cache_dir else None
    if args.download:
        download(cache)
    n = 0
    for t in iter_transcripts(cache_dir=cache, limit=args.limit):
        n += 1
        print(f"\n=== {t.id} ({t.n_patient_turns()} pt / {t.n_clinician_turns()} cl turns) ===")
        print(f"  scenario:       {t.scenario[:100]}")
        print(f"  gold_note:      {len(t.gold_note)} chars")
        print(f"  gold sections:  {sorted(t.gold_sections.keys())}")
        utts = t.to_patient_utterances("middle")
        print(f"  -> {len(utts)} patient utterances (middle strategy)")
    print(f"\nyielded {n} transcripts.")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
