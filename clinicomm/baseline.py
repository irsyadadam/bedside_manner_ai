"""Naive LLM baseline — the manuscript's control condition.

This represents what a clinician-LLM would produce *without* our four-
module pipeline: no intake extraction, no literature retrieval, no
assertion clustering, no structured NURSE/Four Habits scaffolding, no
per-claim provenance. Just: concatenate the patient's turns, ask the
LLM to respond, return free text.

Module IV's `PatientResponse` cites cluster_ids and PMIDs; this
baseline cites nothing. Phase 12's comparison MD highlights the gap.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from clinicomm.modules.llm_client import LLMClient

log = logging.getLogger("clinicomm.baseline")


BASELINE_SYSTEM_PROMPT = (
    "You are a primary-care clinician. A patient has just described their "
    "concerns to you across several turns of dialogue. Write an empathetic, "
    "clinically appropriate written response addressed to the patient. Use "
    "plain language. Keep it to one or two short paragraphs. Do not use "
    "JSON, do not use markdown headings, do not cite sources — just speak "
    "to the patient as a clinician would."
)


@dataclass
class BaselineResult:
    """Output of the naive baseline. Deliberately unstructured to mirror
    what an unsteered LLM would produce."""
    transcript_id: str
    scenario: str
    patient_utterances: list[str]
    system_prompt: str
    response_text: str
    mode: str = "real"  # "real" or "mock"


class NaiveLLMBaseline:
    """Single LLM call, single text output. No pipeline."""

    def __init__(self, llm_client: LLMClient, system_prompt: str = BASELINE_SYSTEM_PROMPT) -> None:
        self.llm = llm_client
        self.system_prompt = system_prompt

    def respond(
        self,
        patient_utterances: list[str],
        *,
        transcript_id: str = "(unknown)",
        scenario: str = "",
        mode: str = "real",
    ) -> BaselineResult:
        transcript = "\n\n".join(f"Patient: {u}" for u in patient_utterances)
        log.info(
            "baseline.respond transcript=%s turns=%d",
            transcript_id,
            len(patient_utterances),
        )
        text = self.llm.complete(
            system=self.system_prompt,
            user=transcript,
            response_format_json=False,
        )
        return BaselineResult(
            transcript_id=transcript_id,
            scenario=scenario,
            patient_utterances=patient_utterances,
            system_prompt=self.system_prompt,
            response_text=text.strip(),
            mode=mode,
        )
