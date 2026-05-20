"""Two LLM-only baselines — the manuscript's control conditions.

NaiveLLMBaseline
    What a clinician-LLM produces with NO pipeline scaffolding: a
    generic "respond empathetically to the patient" prompt with no
    structure, no retrieval, no provenance directives.

StrongPromptLLMBaseline (Phase 13)
    Same model, but with a smart prompt: instructs the LLM to follow
    NURSE / Four-Habits structure, cite PMID-style sources when stating
    clinical claims, end with a teach-back. No retrieval — the model
    invents its citations. This is the baseline that answers reviewer
    #2's "wouldn't smarter prompting alone close the gap?" question.
    If our pipeline still beats this on provenance + hallucination,
    that is the strongest claim we can make without a cloud API.

Both return BaselineResult; downstream metrics (clinicomm.metrics +
clinicomm.external_metrics) treat them identically.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from clinicomm.modules.llm_client import LLMClient

log = logging.getLogger("clinicomm.baseline")


# DeepSeek-R1-Distill emits chain-of-thought before the actual response.
# Sometimes it wraps the thinking in <think>...</think>; other times the
# opening tag is dropped and only the closing </think> survives. Either
# leak inflates word count + FK grade and pollutes hallucination metrics,
# so we strip both forms before returning the response text.
_THINK_FULL_RE = re.compile(r"<think>.*?</think>", flags=re.DOTALL | re.IGNORECASE)
_THINK_CLOSE_ONLY_RE = re.compile(r"^.*?</think>", flags=re.DOTALL | re.IGNORECASE)


def _strip_reasoning(text: str) -> str:
    """Remove R1-distill reasoning preamble from a raw LLM response.

    Handles two cases:
      1. Complete <think>...</think> block — common.
      2. Missing opening tag, only trailing </think> — R1 quirk; strip
         everything up to and including that closing tag.
    """
    if not text:
        return ""
    s = _THINK_FULL_RE.sub("", text)
    if "</think>" in s.lower():
        s = _THINK_CLOSE_ONLY_RE.sub("", s, count=1)
    return s.strip()


BASELINE_SYSTEM_PROMPT = (
    "You are a primary-care clinician. A patient has just described their "
    "concerns to you across several turns of dialogue. Write an empathetic, "
    "clinically appropriate written response addressed to the patient. Use "
    "plain language. Keep it to one or two short paragraphs. Do not use "
    "JSON, do not use markdown headings, do not cite sources — just speak "
    "to the patient as a clinician would."
)


STRONG_PROMPT_BASELINE_SYSTEM = (
    "You are an empathy-aware primary-care clinician writing a response to a "
    "patient who has just described their concerns. Structure your response "
    "to follow established communication frameworks:\n"
    "\n"
    "  - NURSE empathy: explicitly Name the patient's emotion, show "
    "    Understanding of why they feel it, Respect their effort, offer "
    "    Support, and Explore by inviting them to say more.\n"
    "  - Four Habits Model: open by acknowledging them and setting a shared "
    "    agenda, refer back to the goals or fears they themselves stated, "
    "    explain in plain language, and close with concrete next steps + a "
    "    teach-back invitation + a specific follow-up timeframe.\n"
    "\n"
    "When stating clinical claims (e.g. about evaluation, differential, "
    "or management), cite PubMed sources inline as [PMID 12345678]. If you "
    "do not know a specific PMID, write [PMID ?] rather than fabricating "
    "one. Do not produce JSON, headings, or bullet-point lists — write 2-4 "
    "short paragraphs as a clinician would. Do not make absolute diagnostic "
    "claims; describe possibilities your clinician will want to evaluate."
)


# One-shot example given to the strong-prompt baseline. Keeps the model
# anchored on the format rather than free-wheeling. The example is also a
# legitimate response, not a strawman.
STRONG_PROMPT_BASELINE_EXAMPLE = """\
Example patient: "I've been having heartburn most nights for two months. \
I'm worried it's something serious. I take ibuprofen for back pain."

Example response:
Thanks for telling me everything — it makes sense you're worried, two months \
of nightly heartburn is wearing and it's reasonable to want to know what's \
going on. I can hear that this has been affecting your sleep, and I want to \
work through this with you.

A couple of things stand out. The ibuprofen could be making the heartburn \
worse — NSAIDs are a common contributor to reflux symptoms [PMID ?]. The \
first thing your clinician will likely want to do is review whether the \
ibuprofen is still the right choice for your back pain, and consider a \
short trial of a proton-pump inhibitor to see if symptoms settle [PMID ?]. \
If you ever have trouble swallowing, vomiting blood, unintentional weight \
loss, or chest pain with exertion, please go to urgent care the same day — \
those would change the picture.

We'll plan to check in within 2-4 weeks to see how you're feeling on the \
new plan. Before you leave, could you tell me in your own words what we \
just agreed on? That way I can make sure I explained everything clearly."""


@dataclass
class BaselineResult:
    """Output of a baseline run. Deliberately unstructured to mirror what
    an unsteered LLM would produce — downstream metrics treat it as free
    text."""
    transcript_id: str
    scenario: str
    patient_utterances: list[str]
    system_prompt: str
    response_text: str
    condition: str = "naive_baseline"  # "naive_baseline" or "strong_prompt_baseline"
    mode: str = "real"  # "real" or "mock"


class NaiveLLMBaseline:
    """Single LLM call, single text output. No pipeline. No prompt structure."""

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
            "naive_baseline.respond transcript=%s turns=%d",
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
            response_text=_strip_reasoning(text),
            condition="naive_baseline",
            mode=mode,
        )


class StrongPromptLLMBaseline:
    """Same LLM, smarter prompt. The Phase 13 reviewer-defense baseline.

    Difference vs. NaiveLLMBaseline:
      - System prompt names NURSE + Four Habits and instructs structure.
      - One-shot example pinned in the user payload.
      - Asks for PMID-style citations (the model will hallucinate them
        — that's the point; provenance audit then shows the pipeline's
        cited PMIDs are real, the strong-prompt baseline's are not).
    """

    def __init__(
        self,
        llm_client: LLMClient,
        system_prompt: str = STRONG_PROMPT_BASELINE_SYSTEM,
        example: str = STRONG_PROMPT_BASELINE_EXAMPLE,
    ) -> None:
        self.llm = llm_client
        self.system_prompt = system_prompt
        self.example = example

    def respond(
        self,
        patient_utterances: list[str],
        *,
        transcript_id: str = "(unknown)",
        scenario: str = "",
        mode: str = "real",
    ) -> BaselineResult:
        transcript = "\n\n".join(f"Patient: {u}" for u in patient_utterances)
        user = (
            f"{self.example}\n\n"
            f"---\n\n"
            f"Now respond to this patient using the same format:\n\n"
            f"{transcript}"
        )
        log.info(
            "strong_prompt_baseline.respond transcript=%s turns=%d",
            transcript_id,
            len(patient_utterances),
        )
        text = self.llm.complete(
            system=self.system_prompt,
            user=user,
            response_format_json=False,
        )
        return BaselineResult(
            transcript_id=transcript_id,
            scenario=scenario,
            patient_utterances=patient_utterances,
            system_prompt=self.system_prompt,
            response_text=_strip_reasoning(text),
            condition="strong_prompt_baseline",
            mode=mode,
        )
