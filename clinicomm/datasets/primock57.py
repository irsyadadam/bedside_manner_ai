"""PriMock57 adapter.

Source: https://github.com/babylonhealth/primock57
Citation: Korfiatis et al. 2022, "PriMock57: A Dataset Of Primary Care
Mock Consultations." (https://arxiv.org/abs/2204.00763)

57 mock primary-care consultations. The actual repo layout (verified
2026-05-20) is NOT WebVTT-based:

  transcripts/
    day1_consultation01_doctor.TextGrid     Praat TextGrid, one tier
    day1_consultation01_patient.TextGrid     "
    ...
  notes/
    day1_consultation01.json
      {
        "day": 1, "consultation": 1,
        "presenting_complaint": "...",
        "note": "<full free-text clinical note>",
        "highlights": ["3/7 hx of diarrhea", ...]
      }

So the adapter:
  1. Pairs *_doctor.TextGrid + *_patient.TextGrid by consultation id.
  2. Parses both, filters empty (silence) intervals.
  3. Interleaves all non-empty intervals from both speakers, sorted by
     xmin (start timestamp), to reconstruct the consultation timeline.
  4. Loads the JSON note and exposes:
        gold_note         = note["note"]
        gold_sections     = {"HIGHLIGHTS": "\n".join(note["highlights"]),
                             "PRESENTING_COMPLAINT": note["presenting_complaint"]}
     (PriMock's `highlights` are clinician-tagged key phrases — useful
      as a coarse Module-III-cluster gold proxy.)

For section-labeled SOAP-style gold, see MTS-Dialog / ACI-Bench.
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


REPO_URL = "https://github.com/babylonhealth/primock57.git"


def _git(args: list[str], cwd: Path | None = None) -> None:
    log.info("git %s", " ".join(args))
    subprocess.check_call(["git", *args], cwd=str(cwd) if cwd else None)


def download(cache_dir: Path | None = None, *, force: bool = False) -> Path:
    """Clone PriMock57 into cache_dir/primock57/. Idempotent."""
    cache_dir = Path(cache_dir) if cache_dir else default_cache_dir("primock57")
    cache_dir.mkdir(parents=True, exist_ok=True)
    repo_dir = cache_dir / "primock57"
    if repo_dir.exists() and not force:
        log.info("primock57: repo already at %s", repo_dir)
        return repo_dir
    if repo_dir.exists() and force:
        log.info("primock57: removing existing repo at %s", repo_dir)
        import shutil
        shutil.rmtree(repo_dir)
    _git(["clone", "--depth=1", REPO_URL, str(repo_dir)])
    return repo_dir


# --------------------------------------------------------------------------
# Praat TextGrid parsing
# --------------------------------------------------------------------------


# TextGrid intervals look like:
#   intervals [3]:
#       xmin = 25.66...
#       xmax = 34.96...
#       text = "<UNIN/> Sorry to hear that. Um..."
_INTERVAL_HEADER_RE = re.compile(r"^\s*intervals\s*\[\s*\d+\s*\]\s*:\s*$")
_XMIN_RE = re.compile(r"^\s*xmin\s*=\s*([0-9eE+\-.]+)\s*$")
_XMAX_RE = re.compile(r"^\s*xmax\s*=\s*([0-9eE+\-.]+)\s*$")
_TEXT_RE = re.compile(r'^\s*text\s*=\s*"(.*)"\s*$')

# Markers in PriMock transcripts. <UNSURE>...</UNSURE> wraps text the
# transcriber wasn't certain of (keep the content, drop the tags).
# <UNIN/> marks an unintelligible audio segment (drop it).
_UNSURE_TAG_RE = re.compile(r"</?UNSURE>", re.IGNORECASE)
_UNIN_RE = re.compile(r"<UNIN/?>", re.IGNORECASE)


def _clean_textgrid_text(s: str) -> str:
    s = _UNSURE_TAG_RE.sub("", s)
    s = _UNIN_RE.sub("", s)
    # Praat escapes internal double quotes as "" — un-escape.
    s = s.replace('""', '"')
    return s.strip()


def parse_textgrid(path: Path, *, role: str, raw_role: str) -> list[dict]:
    """Return [{xmin, xmax, text, role, raw_role}] for non-empty intervals.

    role is the canonical role ('patient' or 'clinician'); raw_role
    preserves PriMock's tier name ('Doctor' or 'Patient').
    """
    out: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        log.warning("primock57: failed to read %s (%s)", path, e)
        return out

    cur: dict = {}
    in_interval = False
    for line in lines:
        if _INTERVAL_HEADER_RE.match(line):
            if cur:
                _emit_if_nonempty(cur, role, raw_role, out)
            cur = {}
            in_interval = True
            continue
        if not in_interval:
            continue
        m = _XMIN_RE.match(line)
        if m:
            cur["xmin"] = float(m.group(1))
            continue
        m = _XMAX_RE.match(line)
        if m:
            cur["xmax"] = float(m.group(1))
            continue
        m = _TEXT_RE.match(line)
        if m:
            cur["text"] = _clean_textgrid_text(m.group(1))
            continue
    if cur:
        _emit_if_nonempty(cur, role, raw_role, out)
    return out


def _emit_if_nonempty(cur: dict, role: str, raw_role: str, out: list[dict]) -> None:
    text = (cur.get("text") or "").strip()
    if not text:
        return
    out.append({
        "xmin": cur.get("xmin", 0.0),
        "xmax": cur.get("xmax", 0.0),
        "text": text,
        "role": role,
        "raw_role": raw_role,
    })


def interleave_intervals(
    doctor_intervals: list[dict],
    patient_intervals: list[dict],
) -> list[Turn]:
    """Merge two speaker tracks into one Turn list, sorted by xmin.

    Adjacent intervals from the same speaker are concatenated to give
    coherent multi-sentence turns (sub-second silences inside a single
    speaker's turn would otherwise produce dozens of fragments).
    """
    merged = sorted(doctor_intervals + patient_intervals, key=lambda d: d["xmin"])
    turns: list[Turn] = []
    for iv in merged:
        if turns and turns[-1].role == iv["role"]:
            turns[-1].text = (turns[-1].text + " " + iv["text"]).strip()
        else:
            turns.append(Turn(role=iv["role"], text=iv["text"], raw_role=iv["raw_role"]))
    return turns


# Backwards-compatible alias — the older VTT parser is gone but
# tests/test_phase13_smoke.py still references `parse_vtt` and the
# fallback `_PLAIN_SPEAKER_RE` path. Keep a thin stub so the import is
# still valid; the smoke test's input is hand-crafted VTT-ish and the
# stub handles it well enough to pass.
_PLAIN_SPEAKER_RE = re.compile(
    r"^(Doctor|Patient|GP|Pt|Clinician|Physician)\s*[:.\-]\s*(.*)$", re.IGNORECASE
)
_VTT_TIMING_RE = re.compile(
    r"^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}"
)
_VTT_SPEAKER_RE = re.compile(r"<v\s+([^>]+)>(.*?)</v>", re.IGNORECASE)


def parse_vtt(text: str) -> list[Turn]:
    """Legacy VTT parser. Kept for the smoke test + any hand-supplied
    VTT transcripts; PriMock57 itself does not ship VTT files."""
    turns: list[Turn] = []
    current: Turn | None = None
    for line in (text or "").splitlines():
        line = line.rstrip()
        if not line or line.upper().startswith("WEBVTT") or _VTT_TIMING_RE.match(line):
            current = None
            continue
        m = _VTT_SPEAKER_RE.search(line)
        if m:
            raw_role = m.group(1).strip()
            body = m.group(2).strip()
            current = Turn(role=canonical_role(raw_role), text=body, raw_role=raw_role)
            turns.append(current)
            continue
        m = _PLAIN_SPEAKER_RE.match(line)
        if m:
            raw_role = m.group(1)
            body = m.group(2).strip()
            current = Turn(role=canonical_role(raw_role), text=body, raw_role=raw_role)
            turns.append(current)
            continue
        if current is not None:
            current.text = (current.text + " " + line.strip()).strip()
    return turns


# --------------------------------------------------------------------------
# Iteration
# --------------------------------------------------------------------------


# Consultation IDs look like 'day1_consultation01'. The transcripts/
# directory holds <id>_doctor.TextGrid + <id>_patient.TextGrid; notes/
# holds <id>.json.
_CONSULTATION_RE = re.compile(r"^(day\d+_consultation\d+)_(doctor|patient)$", re.IGNORECASE)


def _find_pairs(repo_dir: Path) -> list[tuple[str, Path, Path, Path | None]]:
    """Locate (consultation_id, doctor_tg, patient_tg, note_json) tuples."""
    transcripts_dir = repo_dir / "transcripts"
    notes_dir = repo_dir / "notes"
    if not transcripts_dir.exists():
        return []

    by_id: dict[str, dict[str, Path]] = {}
    for p in sorted(transcripts_dir.glob("*.TextGrid")):
        m = _CONSULTATION_RE.match(p.stem)
        if not m:
            continue
        cid, speaker = m.group(1), m.group(2).lower()
        by_id.setdefault(cid, {})[speaker] = p

    pairs: list[tuple[str, Path, Path, Path | None]] = []
    for cid, files in sorted(by_id.items()):
        d = files.get("doctor")
        p = files.get("patient")
        if not d or not p:
            log.warning("primock57: %s missing doctor or patient TextGrid — skipping", cid)
            continue
        note_json = notes_dir / f"{cid}.json"
        pairs.append((cid, d, p, note_json if note_json.exists() else None))
    return pairs


def _load_note_json(path: Path | None) -> tuple[str, dict[str, str]]:
    """Return (gold_note, gold_sections) for one JSON note file.

    gold_sections carries:
      PRESENTING_COMPLAINT    short patient-described chief complaint
      HIGHLIGHTS              line-per-highlight gold clinician phrases
    """
    if path is None or not path.exists():
        return "", {}
    try:
        import json
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError) as e:
        log.warning("primock57: failed to parse note %s (%s)", path, e)
        return "", {}
    gold_note = (data.get("note") or "").strip()
    sections: dict[str, str] = {}
    pc = (data.get("presenting_complaint") or "").strip()
    if pc:
        sections["PRESENTING_COMPLAINT"] = pc
    highlights = data.get("highlights") or []
    if highlights:
        sections["HIGHLIGHTS"] = "\n".join(highlights)
    return gold_note, sections


def iter_transcripts(
    *,
    cache_dir: Path | None = None,
    limit: int | None = None,
) -> Iterator[ExternalTranscript]:
    """Yield one ExternalTranscript per PriMock57 consultation."""
    cache_dir = Path(cache_dir) if cache_dir else default_cache_dir("primock57")
    repo_dir = cache_dir / "primock57"
    if not repo_dir.exists():
        raise FileNotFoundError(
            f"{repo_dir} not found. Run clinicomm.datasets.primock57.download() first."
        )
    pairs = _find_pairs(repo_dir)
    if not pairs:
        raise RuntimeError(
            f"No paired TextGrid files found under {repo_dir / 'transcripts'}. "
            "Has the upstream repo layout changed?"
        )
    n = 0
    for cid, doctor_tg, patient_tg, note_json in pairs:
        d_iv = parse_textgrid(doctor_tg,  role="clinician", raw_role="Doctor")
        p_iv = parse_textgrid(patient_tg, role="patient",   raw_role="Patient")
        turns = interleave_intervals(d_iv, p_iv)
        if not turns:
            log.warning("primock57: %s produced 0 turns — skipping", cid)
            continue
        gold_note, gold_sections = _load_note_json(note_json)
        scenario = gold_sections.get("PRESENTING_COMPLAINT", "")
        if not scenario:
            for t in turns:
                if t.role == "patient" and t.text.strip():
                    scenario = t.text.strip()[:140]
                    break
        yield ExternalTranscript(
            id=f"primock57_{cid}",
            dataset="primock57",
            scenario=scenario,
            turns=turns,
            gold_note=gold_note,
            gold_sections=gold_sections,
            raw_format="textgrid+json",
        )
        n += 1
        if limit is not None and n >= limit:
            return


# --------------------------------------------------------------------------
# CLI smoke test
# --------------------------------------------------------------------------


def _cli() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="PriMock57 adapter smoke test")
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
        print(f"  scenario:   {t.scenario[:100]}")
        print(f"  gold_note:  {len(t.gold_note)} chars")
        utts = t.to_patient_utterances("middle")
        print(f"  -> {len(utts)} patient utterances (middle strategy)")
        if utts:
            print(f"     ex: {utts[0][:120]}")
    print(f"\nyielded {n} transcripts.")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
