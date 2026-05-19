"""Module I — Initial Screening Conversation (Intake).

Two-track design (mirrors the proposal):
  - update_profile(profile, turn) : LLM call. Reads intake_system.txt,
                                    substitutes the running profile +
                                    latest utterance, parses JSON,
                                    validates into PatientConcernProfile.
                                    The LLM never speaks to the patient.
  - next_prompt(profile)          : TEMPLATED. Picks the next clinician
                                    question from a constrained bank
                                    based on profile.unknowns. The
                                    only thing the patient ever sees.
  - is_complete(profile)          : bool. Three gates (problem
                                    descriptors complete, red-flag
                                    screen done, >=1 goal).

CLI:
  uv run python -m clinicomm.modules.m1_intake --demo
      # offline trace using MockLLMClient on canned utterances

  uv run python -m clinicomm.modules.m1_intake --transcript <path>
      # uses the configured vLLM server; transcript must have
      # patient_utterances filled in (default stubs in
      # demos/synthetic_patients/ have TODO markers)
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Iterable

from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from clinicomm.config import load_config
from clinicomm.logging_setup import setup_logging
from clinicomm.modules.llm_client import LLMClient, MockLLMClient, VLLMClient
from clinicomm.schemas import PatientConcernProfile

log = logging.getLogger("clinicomm.modules.m1_intake")
console = Console()


# Hard-coded utterance set for --demo. Designed to exercise the loop:
# adds two problems, multiple emotional cues, a red flag, and goals.
# These are NOT in demos/synthetic_patients/ — those stubs stay empty
# per the spec, so the user fills them in.
DEMO_UTTERANCES: list[str] = [
    "I've been so tired the past month, and I've lost about 12 pounds without trying. "
    "My wife is convinced it's cancer and honestly I am too. I just want to know "
    "what's going on so I can keep working.",
    "It started about a month ago. Some days I feel a 7 out of 10 tired — I can barely "
    "get through my shifts. I'm taking ibuprofen sometimes for headaches but nothing "
    "for the fatigue itself.",
    "No chest pain, no shortness of breath, nothing like that. But I have been getting "
    "these dull headaches in the morning, almost every day.",
    "I'm on lisinopril 10 mg once a day. No allergies that I know of. My dad had colon "
    "cancer at 55 and I'd really like to rule that out — I want to feel safe again.",
]


# Templated question bank. Keys are matched against unknowns paths.
_TEMPLATES = {
    "opener": (
        "What brings you in today? Take your time and tell me what's been going on."
    ),
    "red_flag_screen": (
        "Before we go further, I want to check on a few quick safety questions. "
        "Have you had any chest pain, trouble breathing, sudden weakness or "
        "numbness, severe headaches, unexplained bleeding, or any thoughts of "
        "harming yourself recently?"
    ),
    "onset": "When did the {label} first start?",
    "severity": (
        "On a scale of 1 to 10, or in your own words, how bad has the {label} been?"
    ),
    "timing": (
        "How often does the {label} happen, and how long does it usually last?"
    ),
    "associated_symptoms": (
        "Is the {label} happening alongside anything else — other symptoms or "
        "changes you've noticed?"
    ),
    "interventions_tried": (
        "Have you tried anything for the {label} so far — medications, home "
        "remedies, anything else?"
    ),
    "medications": (
        "What medications are you currently taking, including anything "
        "over-the-counter or as-needed?"
    ),
    "allergies": (
        "Do you have any allergies to medications, foods, or anything else?"
    ),
    "relevant_history": (
        "Are there any past medical issues, surgeries, or family history that "
        "might be relevant to share?"
    ),
    "patient_goals": (
        "What are you hoping we'll be able to help with today? What would feel "
        "like a good outcome for you?"
    ),
}


# --------------------------------------------------------------------------
# IntakeAgent
# --------------------------------------------------------------------------


class IntakeAgent:
    """Owns the intake loop. One LLM call per patient turn; question
    selection is purely templated.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        intake_system_prompt: str,
        max_turns: int = 20,
        max_attempts_per_template: int = 2,
    ) -> None:
        self.llm = llm_client
        self.system_prompt = intake_system_prompt
        self.max_turns = max_turns
        self.max_attempts = max_attempts_per_template
        # Counter: (template_key, problem_idx_or_None) -> times asked.
        # Prevents next_prompt() from looping on a single gap when the
        # patient (or mock LLM) hasn't been able to fill it in.
        self._asked_count: dict[tuple[str, int | None], int] = {}

    # -- LLM extraction ----------------------------------------------------

    def update_profile(
        self,
        profile: PatientConcernProfile,
        user_turn: str,
    ) -> PatientConcernProfile:
        """One LLM call. Returns the merged, validated profile."""
        user_payload = (
            f"CURRENT_PROFILE_JSON:\n{profile.model_dump_json(indent=2)}\n\n"
            f"LATEST_PATIENT_TURN: {user_turn}"
        )
        raw = self.llm.complete(
            system=self.system_prompt,
            user=user_payload,
            response_format_json=True,
        )
        cleaned = _strip_code_fences(raw)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            log.error("intake LLM returned non-JSON: %s", e)
            log.error("raw response (first 400 chars): %s", cleaned[:400])
            raise
        try:
            return PatientConcernProfile.model_validate(data)
        except ValidationError as e:
            log.error("intake LLM JSON failed schema validation: %s", e)
            log.error("payload (first 800 chars): %s", json.dumps(data)[:800])
            raise

    # -- templated question selection -------------------------------------

    def next_prompt(self, profile: PatientConcernProfile) -> str | None:
        """Pick the highest-priority unresolved question. None when done OR
        when every relevant template has been asked `max_attempts` times.

        Each candidate template is keyed by (template_name, problem_idx);
        once a key's counter hits `self.max_attempts`, we move past it
        rather than re-asking. This prevents next_prompt from looping
        on a single gap when the patient (or LLM) doesn't fill it.
        """
        if self.is_complete(profile):
            return None

        # Build candidates in priority order:
        #   (template_key, problem_idx_or_None, rendered_text)
        candidates: list[tuple[str, int | None, str]] = []

        if not profile.problems:
            candidates.append(("opener", None, _TEMPLATES["opener"]))

        if "red_flag_screen_complete" in profile.unknowns:
            candidates.append(
                ("red_flag_screen", None, _TEMPLATES["red_flag_screen"])
            )

        # All problems, sorted by # unresolved descriptors (descending).
        scored: list[tuple[int, int, "Problem"]] = []  # noqa: F821
        for i, p in enumerate(profile.problems):
            n_unknown = sum(
                1 for k in ("onset", "severity", "timing") if getattr(p, k) is None
            )
            scored.append((n_unknown, i, p))
        scored.sort(reverse=True)

        for _, idx, problem in scored:
            for field in ("onset", "severity", "timing"):
                if getattr(problem, field) is None:
                    candidates.append(
                        (field, idx, _TEMPLATES[field].format(label=problem.label))
                    )
            for field in ("associated_symptoms", "interventions_tried"):
                if f"problems[{idx}].{field}" in profile.unknowns:
                    candidates.append(
                        (field, idx, _TEMPLATES[field].format(label=problem.label))
                    )

        if "patient_goals" in profile.unknowns or not profile.patient_goals:
            candidates.append(("patient_goals", None, _TEMPLATES["patient_goals"]))
        if "medications" in profile.unknowns:
            candidates.append(("medications", None, _TEMPLATES["medications"]))
        if "allergies" in profile.unknowns:
            candidates.append(("allergies", None, _TEMPLATES["allergies"]))
        if "relevant_history" in profile.unknowns:
            candidates.append(
                ("relevant_history", None, _TEMPLATES["relevant_history"])
            )

        # First candidate whose counter is under the cap wins.
        for template_key, problem_idx, text in candidates:
            key = (template_key, problem_idx)
            if self._asked_count.get(key, 0) < self.max_attempts:
                self._asked_count[key] = self._asked_count.get(key, 0) + 1
                return text
        return None

    # -- completion check -------------------------------------------------

    def is_complete(self, profile: PatientConcernProfile) -> bool:
        """All three gates must pass:
          A. every problem has onset+severity+timing
          B. red-flag screen has been performed at least once
          C. patient_goals has >=1 entry
        We also honor the LLM's explicit "ready_for_handoff" signal.
        """
        if profile.completion_status == "ready_for_handoff":
            return True
        if not profile.problems:
            return False
        # A
        for p in profile.problems:
            if p.onset is None or p.severity is None or p.timing is None:
                return False
        # B — proxy: red_flag_screen_complete not in unknowns
        if "red_flag_screen_complete" in profile.unknowns:
            return False
        # C
        if not profile.patient_goals:
            return False
        return True

    def _most_unknown_problem(
        self, profile: PatientConcernProfile
    ) -> tuple[int, "Problem"] | None:  # noqa: F821
        if not profile.problems:
            return None
        scored = []
        for i, p in enumerate(profile.problems):
            n_unknown = sum(
                1 for k in ("onset", "severity", "timing") if getattr(p, k) is None
            )
            scored.append((n_unknown, i, p))
        scored.sort(reverse=True)  # prefer the most-unknown problem
        n, idx, p = scored[0]
        if n == 0:
            return (idx, p)  # surfaced for associated_symptoms / interventions paths
        return (idx, p)

    # -- offline driver ---------------------------------------------------

    def run_intake(
        self, patient_utterances: Iterable[str]
    ) -> tuple[PatientConcernProfile, list[dict]]:
        """Process a sequence of utterances. Returns (final_profile, trace).

        trace[i] = {
          turn, agent_prompt, patient_utterance, profile_after, complete,
        }
        """
        # Fresh ask counters per intake run (so re-using the same agent
        # instance across multiple patients is safe).
        self._asked_count.clear()
        profile = PatientConcernProfile()
        trace: list[dict] = []
        for i, utterance in enumerate(patient_utterances):
            agent_prompt = self.next_prompt(profile)
            profile = self.update_profile(profile, utterance)
            trace.append(
                {
                    "turn": i + 1,
                    "agent_prompt": agent_prompt
                    or "(intake already complete; processing additional utterance)",
                    "patient_utterance": utterance,
                    "profile_after": profile.model_dump(),
                    "complete": self.is_complete(profile),
                }
            )
            if self.is_complete(profile) and i + 1 >= len(list(patient_utterances)):
                break
            if i + 1 >= self.max_turns:
                log.warning("max_turns=%d hit; stopping", self.max_turns)
                break
        return profile, trace


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _strip_code_fences(s: str) -> str:
    """Defensive: remove ```json ... ``` if the LLM wraps despite instructions."""
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _load_intake_system(cfg: dict) -> str:
    path = Path(cfg["prompts"]["intake_system"])
    return path.read_text(encoding="utf-8")


def _load_transcript(path: Path) -> tuple[str, list[str]]:
    """Returns (scenario_id, patient_utterances). Skips TODO-only stubs."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    scenario = raw.get("patient_id") or path.stem
    utterances: list[str] = []
    for t in raw.get("turns") or []:
        u = (t.get("patient_utterance") or "").strip()
        if u and not u.upper().startswith("TODO"):
            utterances.append(u)
    return scenario, utterances


# --------------------------------------------------------------------------
# Trace rendering
# --------------------------------------------------------------------------


def _print_trace(scenario: str, trace: list[dict], final: PatientConcernProfile) -> None:
    console.rule(f"[bold]Intake trace — {scenario}[/bold]")
    for t in trace:
        console.print(
            Panel.fit(
                f"[bold cyan]Turn {t['turn']}[/bold cyan] "
                f"(complete={t['complete']})\n\n"
                f"[bold]Agent (templated):[/bold]\n  {t['agent_prompt']}\n\n"
                f"[bold]Patient:[/bold]\n  {t['patient_utterance']}",
                border_style="cyan",
                title=f"turn {t['turn']}",
            )
        )
        # Compact per-turn extraction summary
        prof = t["profile_after"]
        summary_lines = []
        summary_lines.append(
            f"  problems          ({len(prof['problems'])}): "
            + ", ".join(p["label"] for p in prof["problems"])
        )
        for i, p in enumerate(prof["problems"]):
            summary_lines.append(
                f"    [{i}] {p['label']}: onset={p['onset']!r} "
                f"severity={p['severity']!r} timing={p['timing']!r} status={p['status']}"
            )
        summary_lines.append(
            f"  patient_goals     ({len(prof['patient_goals'])}): "
            + " | ".join(prof["patient_goals"])
        )
        summary_lines.append(
            f"  emotional_cues    ({len(prof['emotional_cues'])}): "
            + " | ".join(f"{c['cue']}<-{c['evidence_quote'][:40]!r}" for c in prof["emotional_cues"])
        )
        summary_lines.append(
            f"  red_flags         ({len(prof['red_flags'])}): "
            + " | ".join(f"{r['flag']}<-{r['evidence'][:40]!r}" for r in prof["red_flags"])
        )
        summary_lines.append(
            f"  medications       ({len(prof['medications'])}): "
            + ", ".join(prof["medications"])
        )
        summary_lines.append(f"  unknowns          : {prof['unknowns']}")
        summary_lines.append(
            f"  completion_status : {prof['completion_status']}"
        )
        console.print("\n".join(summary_lines))
        console.print()

    console.rule("[bold]Final profile (validated)[/bold]")
    console.print(
        Syntax(
            json.dumps(final.model_dump(), indent=2),
            "json",
            line_numbers=False,
            word_wrap=True,
        )
    )


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(prog="clinicomm.modules.m1_intake")
    p.add_argument("--config", default="config/pipeline.yaml")
    src = p.add_mutually_exclusive_group(required=False)
    src.add_argument(
        "--demo",
        action="store_true",
        help="Use MockLLMClient + canned utterances (offline; no vLLM needed).",
    )
    src.add_argument(
        "--transcript",
        type=Path,
        help="Path to a synthetic-patient transcript JSON "
        "(uses the configured vLLM server).",
    )
    p.add_argument("--save", type=Path, help="Write the final profile JSON here.")
    args = p.parse_args()

    cfg = load_config(args.config)
    log_path = setup_logging(
        phase="phase07_intake",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    if not args.demo and not args.transcript:
        # Default behavior: run --demo so the module is self-checking.
        args.demo = True

    intake_system = _load_intake_system(cfg)

    if args.demo:
        log.info("Mode: --demo (MockLLMClient, canned utterances)")
        agent = IntakeAgent(MockLLMClient(), intake_system)
        scenario = "demo_canned_utterances"
        utterances = DEMO_UTTERANCES
    else:
        log.info("Mode: --transcript %s (live VLLMClient)", args.transcript)
        scenario, utterances = _load_transcript(args.transcript)
        if not utterances:
            console.print(
                f"[red]Transcript {args.transcript} has no non-TODO "
                "patient_utterance entries. Fill it in first.[/red]"
            )
            return
        agent = IntakeAgent(VLLMClient(cfg["llm"]), intake_system)

    final, trace = agent.run_intake(utterances)
    _print_trace(scenario, trace, final)

    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(final.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"\nSaved final profile to [cyan]{args.save}[/cyan]")


if __name__ == "__main__":
    main()
