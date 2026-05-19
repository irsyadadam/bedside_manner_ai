"""Quantitative metrics for the pipeline-vs-baseline comparison (Table 4)
and module-level ablation (Table 5).

Inputs are uniform across all conditions:
  - "response_text"        the patient-facing free text
                            (acknowledgment + per-concern + next_steps
                             + teach_back + follow_up, concatenated)
  - "structured_response"  optional — a PatientResponse JSON; absent for
                            the naive baseline, partial for ablations.

Metrics:
  citations               int — len(all_pmids_used) (0 for naive baseline)
  cluster_citations       int — len(all_cluster_ids_used)
  nurse_n                 int — count of NURSE elements applied
  four_habits_n           int — count of Four Habits elements applied
  red_flag_addressed      bool — does the response acknowledge each red
                                 flag from the profile?
  red_flag_in_next_steps  bool — is the first next_steps entry about
                                 the red flag?
  fk_grade                float — Flesch-Kincaid grade level on the full
                                  patient-facing text
  word_count              int
  teach_back_present      bool — non-empty structured field OR keyword in text
  follow_up_timeframe     bool — "<N> days|weeks|months" anywhere in text
  provenance_ratio        float — fraction of concern sections with >=1 citation
                                  (1.0 = fully provenanced, 0.0 = unsupported)
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

import textstat

from clinicomm.schemas import PatientConcernProfile, PatientResponse


# Regexes
_TIMEFRAME_RE = re.compile(
    r"\b(?:in|within|after|over)\s+(?:the\s+)?(?:next\s+)?\d+(?:\s*[-–]\s*\d+)?\s+"
    r"(?:day|days|week|weeks|month|months)\b",
    re.IGNORECASE,
)
_TEACH_BACK_KEYWORDS = (
    "in your own words",
    "tell me what you understood",
    "how you would explain",
    "make sure i explained",
    "summarize",
    "in your words",
)


@dataclass
class ResponseMetrics:
    condition: str
    transcript_id: str
    citations: int = 0
    cluster_citations: int = 0
    nurse_n: int = 0
    four_habits_n: int = 0
    red_flag_addressed: bool = False
    red_flag_in_next_steps: bool = False
    fk_grade: float = 0.0
    word_count: int = 0
    teach_back_present: bool = False
    follow_up_timeframe: bool = False
    provenance_ratio: float = 0.0


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text or ""))


def _safe_fk(text: str) -> float:
    if not text or not text.strip():
        return 0.0
    try:
        return float(textstat.flesch_kincaid_grade(text))
    except Exception:  # noqa: BLE001 — textstat occasionally chokes on short text
        return 0.0


def metrics_for_structured_response(
    *,
    response: PatientResponse,
    profile: PatientConcernProfile,
    condition: str,
    transcript_id: str,
) -> ResponseMetrics:
    """Compute metrics from a Module IV-style structured PatientResponse."""
    full_text = _flatten_response(response)

    red_flag_addressed = False
    red_flag_in_next_steps = False
    if profile.red_flags:
        flag_terms = []
        for rf in profile.red_flags:
            for tok in re.split(r"\W+", rf.flag.lower()):
                if len(tok) >= 4:
                    flag_terms.append(tok)
        full_lower = full_text.lower()
        red_flag_addressed = any(t in full_lower for t in flag_terms)
        if response.next_steps:
            first_step = response.next_steps[0].lower()
            red_flag_in_next_steps = any(t in first_step for t in flag_terms)

    teach_back_present = bool(response.teach_back_prompt and response.teach_back_prompt.strip())
    follow_up_timeframe = bool(
        _TIMEFRAME_RE.search(response.follow_up_invitation or "")
        or _TIMEFRAME_RE.search(" ".join(response.next_steps))
    )
    n_sections = len(response.clinical_information_per_concern)
    n_with_citation = sum(
        1 for s in response.clinical_information_per_concern if s.citations
    )
    provenance_ratio = (n_with_citation / n_sections) if n_sections else 0.0

    return ResponseMetrics(
        condition=condition,
        transcript_id=transcript_id,
        citations=len(response.all_pmids_used),
        cluster_citations=len(response.all_cluster_ids_used),
        nurse_n=len(response.nurse_elements_applied),
        four_habits_n=len(response.four_habits_elements_applied),
        red_flag_addressed=red_flag_addressed,
        red_flag_in_next_steps=red_flag_in_next_steps,
        fk_grade=_safe_fk(full_text),
        word_count=_word_count(full_text),
        teach_back_present=teach_back_present,
        follow_up_timeframe=follow_up_timeframe,
        provenance_ratio=provenance_ratio,
    )


def metrics_for_freeform_text(
    *,
    response_text: str,
    profile: PatientConcernProfile,
    condition: str,
    transcript_id: str,
) -> ResponseMetrics:
    """Compute metrics from a free-text response (naive baseline path).

    NURSE / Four-Habits counts and citations are zero by construction.
    Red-flag handling, FK grade, word count, teach-back keyword check,
    and follow-up timeframe regex still apply.
    """
    lower = (response_text or "").lower()

    red_flag_addressed = False
    red_flag_in_next_steps = False
    if profile.red_flags:
        flag_terms = []
        for rf in profile.red_flags:
            for tok in re.split(r"\W+", rf.flag.lower()):
                if len(tok) >= 4:
                    flag_terms.append(tok)
        red_flag_addressed = any(t in lower for t in flag_terms)
        # For free text we don't have a "next_steps" list; approximate by
        # the first sentence containing an action verb.
        first_sentence = re.split(r"(?<=[.!?])\s+", response_text or "", maxsplit=1)[0]
        red_flag_in_next_steps = any(t in first_sentence.lower() for t in flag_terms)

    teach_back_present = any(k in lower for k in _TEACH_BACK_KEYWORDS)
    follow_up_timeframe = bool(_TIMEFRAME_RE.search(response_text or ""))

    return ResponseMetrics(
        condition=condition,
        transcript_id=transcript_id,
        citations=0,
        cluster_citations=0,
        nurse_n=0,
        four_habits_n=0,
        red_flag_addressed=red_flag_addressed,
        red_flag_in_next_steps=red_flag_in_next_steps,
        fk_grade=_safe_fk(response_text or ""),
        word_count=_word_count(response_text or ""),
        teach_back_present=teach_back_present,
        follow_up_timeframe=follow_up_timeframe,
        provenance_ratio=0.0,
    )


def _flatten_response(r: PatientResponse) -> str:
    parts = [r.acknowledgment]
    for sec in r.clinical_information_per_concern:
        parts.append(sec.explanation)
    parts.extend(r.next_steps)
    parts.append(r.teach_back_prompt)
    parts.append(r.follow_up_invitation)
    return "\n\n".join(p for p in parts if p)


def metrics_to_dict(m: ResponseMetrics) -> dict:
    return asdict(m)
