"""Common shape for every external dataset adapter.

ExternalTranscript is the bridge from "raw dataset record" to
"something Pipeline.run() accepts." The pipeline expects a list[str]
of patient utterances (one per turn); real-world datasets carry both
clinician and patient turns, so each adapter is responsible for
deciding which turns to surface.

Speaker-handling policy (default = "middle"):

  patient_only  : strip clinician turns, return only patient text.
                  Loses disambiguating context for short answers
                  ("yes" / "no" / "about a week").

  middle        : default. Return patient turns, but inline the
                  immediately preceding clinician turn as bracketed
                  context: "[Clinician asked: '...'] <patient text>".
                  Existing intake prompt parses these gracefully without
                  any prompt change — R1-distill treats bracketed
                  preambles as context, not as patient speech.

  interleaved   : emit alternating clinician/patient turns as separate
                  utterances. NOT recommended — the intake state machine
                  in m1_intake.py expects each utterance to add patient
                  information.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path


_SPEAKER_PATTERNS = {
    "patient": re.compile(r"^(patient|pt|guest_family|family)\b[:\s]?", re.IGNORECASE),
    "clinician": re.compile(
        r"^(doctor|doc|clinician|provider|physician|nurse|practitioner|gp)\b[:\s]?",
        re.IGNORECASE,
    ),
}


def _canonical_role(raw_role: str) -> str:
    """Map a free-text speaker label to {'patient', 'clinician', 'other'}.

    Datasets use different conventions (Doctor/Patient, GP/PT, role_1/role_2).
    We canonicalize so downstream code doesn't have to special-case.
    """
    if not raw_role:
        return "other"
    s = raw_role.strip().lower()
    if _SPEAKER_PATTERNS["patient"].match(s):
        return "patient"
    if _SPEAKER_PATTERNS["clinician"].match(s):
        return "clinician"
    return "other"


@dataclass
class Turn:
    """One dialogue turn. role is the canonical {'patient', 'clinician', 'other'}.

    raw_role preserves the dataset's original label for trace-back.
    """
    role: str
    text: str
    raw_role: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExternalTranscript:
    """One encounter, normalized across PriMock57 / MTS-Dialog / ACI-Bench.

    Fields:
      id            : stable ID within the dataset (use {dataset}_{native_id})
      dataset       : 'primock57' | 'mts_dialog' | 'aci_bench'
      scenario      : short free-text scenario label, used in trace MD
      turns         : ordered list of Turn objects
      gold_note     : full reference clinician note (free text). May be empty
                      for datasets that only ship section-labeled summaries.
      gold_sections : dict[section_label, text]. Populated by adapters whose
                      gold is section-labeled (MTS-Dialog primarily, partial
                      for ACI-Bench's SOAP). Empty for PriMock57.
      raw_format    : provenance — 'vtt+csv' | 'jsonl' | 'csv' etc.

    The `to_patient_utterances()` helper is what Pipeline.run() consumes.
    """
    id: str
    dataset: str
    scenario: str = ""
    turns: list[Turn] = field(default_factory=list)
    gold_note: str = ""
    gold_sections: dict[str, str] = field(default_factory=dict)
    raw_format: str = ""

    # ---- consumers ------------------------------------------------------

    def to_patient_utterances(self, strategy: str = "middle") -> list[str]:
        """Return the list[str] of patient utterances Pipeline.run() expects.

        See module docstring for strategy semantics. Default is 'middle'
        (preceding clinician question inlined as bracketed context).
        """
        if strategy == "patient_only":
            return [t.text for t in self.turns if t.role == "patient" and t.text.strip()]

        if strategy == "middle":
            out: list[str] = []
            last_clinician: str | None = None
            for t in self.turns:
                if t.role == "clinician":
                    last_clinician = t.text.strip()
                elif t.role == "patient":
                    body = t.text.strip()
                    if not body:
                        continue
                    if last_clinician:
                        # Compact the question — most are short already, but
                        # cap to keep the user payload manageable.
                        q = last_clinician[:300]
                        out.append(f"[Clinician asked: \"{q}\"] {body}")
                        last_clinician = None
                    else:
                        out.append(body)
            return out

        if strategy == "interleaved":
            out = []
            for t in self.turns:
                if t.role in ("patient", "clinician") and t.text.strip():
                    prefix = "[Patient]" if t.role == "patient" else "[Clinician]"
                    out.append(f"{prefix} {t.text.strip()}")
            return out

        raise ValueError(f"unknown speaker strategy: {strategy!r}")

    def n_patient_turns(self) -> int:
        return sum(1 for t in self.turns if t.role == "patient")

    def n_clinician_turns(self) -> int:
        return sum(1 for t in self.turns if t.role == "clinician")

    # ---- I/O ------------------------------------------------------------

    def to_json(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "dataset": self.dataset,
                "scenario": self.scenario,
                "turns": [t.to_dict() for t in self.turns],
                "gold_note": self.gold_note,
                "gold_sections": self.gold_sections,
                "raw_format": self.raw_format,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, s: str) -> "ExternalTranscript":
        d = json.loads(s)
        d["turns"] = [Turn(**t) for t in d.get("turns", [])]
        return cls(**d)

    def save(self, path: Path | str) -> None:
        Path(path).write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: Path | str) -> "ExternalTranscript":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


def default_cache_dir(dataset: str) -> Path:
    """Where adapters cache downloaded raw files."""
    return Path("db/external") / dataset


# Re-exported so adapters can keep canonicalization centralized.
canonical_role = _canonical_role
