"""Module IV — Patient response generation.

Pipeline:
    1. Build the user payload (profile + structured context +
       concern_paths + flags).
    2. ONE LLM call with response_generation.txt as the system prompt.
    3. Parse + validate as PatientResponse.
    4. Post-generation glossary substitution pass over patient-facing
       string fields. Log every substitution to
       PatientResponse.glossary_substitutions.

CLI:
  uv run python -m clinicomm.modules.m4_response --demo
      # mocked end-to-end on Phase 9's demo artifact

  uv run python -m clinicomm.modules.m4_response \
       --profile <path> --context <path>
      # uses the configured vLLM server
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel

from clinicomm.config import load_config
from clinicomm.logging_setup import setup_logging
from clinicomm.modules._glossary import apply_to_text
from clinicomm.modules.llm_client import LLMClient, MockResponseLLM, VLLMClient
from clinicomm.schemas import (
    GlossarySubstitution,
    PatientConcernProfile,
    PatientResponse,
    StructuredContextArtifact,
)

log = logging.getLogger("clinicomm.modules.m4_response")
console = Console()


# --------------------------------------------------------------------------
# Responder
# --------------------------------------------------------------------------


class Responder:
    def __init__(
        self,
        llm_client: LLMClient,
        response_prompt: str,
    ) -> None:
        self.llm = llm_client
        self.response_prompt = response_prompt

    # ---- public ----------------------------------------------------------

    def generate(
        self,
        profile: PatientConcernProfile,
        context: StructuredContextArtifact,
    ) -> PatientResponse:
        concern_paths = self._concern_paths(profile)
        nurse_triggered = bool(profile.emotional_cues)
        red_flag_triggered = bool(profile.red_flags)

        user_payload = (
            f"PATIENT_PROFILE:\n{profile.model_dump_json(indent=2)}\n\n"
            f"STRUCTURED_CONTEXT:\n{context.model_dump_json(indent=2)}\n\n"
            f"CONCERN_PATHS:\n{json.dumps(concern_paths)}\n\n"
            f"FLAGS:\n"
            f"  nurse_triggered: {str(nurse_triggered).lower()}\n"
            f"  red_flag_triggered: {str(red_flag_triggered).lower()}\n"
        )
        raw = self.llm.complete(
            system=self.response_prompt,
            user=user_payload,
            response_format_json=True,
        )
        data = _safe_json_loads(raw, context="response_generation")
        if not data:
            raise RuntimeError("response generation returned no parseable JSON")
        try:
            response = PatientResponse.model_validate(data)
        except ValidationError as e:
            log.error("PatientResponse schema validation failed: %s", e)
            log.error("payload (first 800 chars): %s", json.dumps(data)[:800])
            raise

        # Validate cluster_ids referenced in citations actually exist in
        # the structured context. The prompt forbids invented ids; defend
        # against drift anyway. R1-distill in particular tends to copy
        # cluster_ids and PMIDs from the worked example in the prompt.
        valid_cluster_ids = {c.cluster_id for c in context.clusters}
        valid_pmids_by_cluster = {c.cluster_id: set(c.supporting_pmids) for c in context.clusters}
        n_dropped_clusters = 0
        n_dropped_pmids = 0
        for section in response.clinical_information_per_concern:
            kept_citations = []
            for cite in section.citations:
                if cite.cluster_id not in valid_cluster_ids:
                    n_dropped_clusters += 1
                    continue
                # Even within a valid cluster, the LLM might list PMIDs
                # that aren't actually in that cluster's supporting_pmids.
                allowed_pmids = valid_pmids_by_cluster[cite.cluster_id]
                kept_pmids = [p for p in cite.pmids if p in allowed_pmids]
                n_dropped_pmids += len(cite.pmids) - len(kept_pmids)
                cite.pmids = kept_pmids
                kept_citations.append(cite)
            section.citations = kept_citations
        if n_dropped_clusters or n_dropped_pmids:
            log.warning(
                "response validator: dropped %d invalid cluster citations and "
                "%d invalid PMID references",
                n_dropped_clusters,
                n_dropped_pmids,
            )

        # Re-derive aggregate fields from the (filtered) section citations
        # so all_cluster_ids_used / all_pmids_used can't carry hallucinated ids.
        unique_clusters: list[str] = []
        unique_pmids: list[str] = []
        for section in response.clinical_information_per_concern:
            for cite in section.citations:
                if cite.cluster_id and cite.cluster_id not in unique_clusters:
                    unique_clusters.append(cite.cluster_id)
                for p in cite.pmids:
                    if p not in unique_pmids:
                        unique_pmids.append(p)
        response.all_cluster_ids_used = unique_clusters
        response.all_pmids_used = unique_pmids

        # Post-generation glossary pass.
        response = self._apply_glossary(response)
        return response

    # ---- helpers ---------------------------------------------------------

    @staticmethod
    def _concern_paths(profile: PatientConcernProfile) -> list[str]:
        paths: list[str] = []
        for i in range(len(profile.problems)):
            paths.append(f"problems[{i}]")
        for i in range(len(profile.patient_goals)):
            paths.append(f"patient_goals[{i}]")
        return paths

    @staticmethod
    def _apply_glossary(response: PatientResponse) -> PatientResponse:
        subs: list[GlossarySubstitution] = []

        # Patient-facing scalar fields:
        for field in ("acknowledgment", "teach_back_prompt", "follow_up_invitation"):
            new, log_entries = apply_to_text(getattr(response, field), field)
            setattr(response, field, new)
            for e in log_entries:
                subs.append(
                    GlossarySubstitution(
                        field=e.field, original=e.original, plain=e.plain, count=e.count
                    )
                )

        # next_steps (list of strings):
        new_steps: list[str] = []
        for i, step in enumerate(response.next_steps):
            new, log_entries = apply_to_text(step, f"next_steps[{i}]")
            new_steps.append(new)
            for e in log_entries:
                subs.append(
                    GlossarySubstitution(
                        field=e.field, original=e.original, plain=e.plain, count=e.count
                    )
                )
        response.next_steps = new_steps

        # clinical_information_per_concern[].explanation:
        for j, section in enumerate(response.clinical_information_per_concern):
            new, log_entries = apply_to_text(
                section.explanation,
                f"clinical_information_per_concern[{j}].explanation",
            )
            section.explanation = new
            for e in log_entries:
                subs.append(
                    GlossarySubstitution(
                        field=e.field, original=e.original, plain=e.plain, count=e.count
                    )
                )

        response.glossary_substitutions = subs
        return response


# --------------------------------------------------------------------------
# Helpers (parsing, CLI)
# --------------------------------------------------------------------------


def _safe_json_loads(raw: str, *, context: str) -> dict | None:
    s = (raw or "").strip()
    s = re.sub(r"<think>.*?</think>", "", s, flags=re.DOTALL).strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
        s = s.strip()
    if not s.startswith("{") and not s.startswith("["):
        m = re.search(r"\{.*\}", s, flags=re.DOTALL)
        if m:
            s = m.group(0)
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        log.error("JSON parse failed (%s): %s", context, e)
        log.error("raw[:400]: %s", s[:400])
        return None


def _load_prompt(cfg: dict) -> str:
    return Path(cfg["prompts"]["response_generation"]).read_text(encoding="utf-8")


def _print_trace(response: PatientResponse) -> None:
    console.rule("[bold]PatientResponse[/bold]")

    console.print(
        Panel.fit(
            response.acknowledgment,
            title="acknowledgment",
            border_style="green",
        )
    )

    for sec in response.clinical_information_per_concern:
        cite_lines = []
        for c in sec.citations:
            pmids = ",".join(c.pmids[:5]) + ("..." if len(c.pmids) > 5 else "")
            cite_lines.append(f"    cluster={c.cluster_id}  (pmids: {pmids})")
        cite_block = "\n".join(cite_lines) if cite_lines else "    (no citations)"
        console.print(
            Panel.fit(
                f"{sec.explanation}\n\n[dim]citations:[/dim]\n{cite_block}",
                title=f"concern: {sec.concern_label}  [{sec.profile_path}]",
                border_style="cyan",
            )
        )

    steps = "\n".join(f"  {i + 1}. {s}" for i, s in enumerate(response.next_steps))
    console.print(Panel.fit(steps, title="next_steps", border_style="yellow"))
    console.print(
        Panel.fit(response.teach_back_prompt, title="teach_back_prompt", border_style="magenta")
    )
    console.print(
        Panel.fit(response.follow_up_invitation, title="follow_up_invitation", border_style="blue")
    )

    console.rule("[dim]annotations[/dim]")
    console.print(f"  NURSE elements applied:        {response.nurse_elements_applied}")
    console.print(f"  Four Habits elements applied:  {response.four_habits_elements_applied}")
    console.print(f"  Unique cluster_ids cited:      {response.all_cluster_ids_used}")
    console.print(f"  Unique PMIDs cited:            {response.all_pmids_used}")
    if response.glossary_substitutions:
        console.print(
            f"  Glossary substitutions ({len(response.glossary_substitutions)}):"
        )
        for s in response.glossary_substitutions[:10]:
            console.print(
                f"    [{s.field}]  '{s.original}' -> '{s.plain}'  (x{s.count})"
            )
        if len(response.glossary_substitutions) > 10:
            console.print(
                f"    ... and {len(response.glossary_substitutions) - 10} more"
            )
    else:
        console.print("  Glossary substitutions:        none triggered")


def _load_profile(path: Path) -> PatientConcernProfile:
    return PatientConcernProfile.model_validate_json(path.read_text(encoding="utf-8"))


def _load_context(path: Path) -> StructuredContextArtifact:
    return StructuredContextArtifact.model_validate_json(path.read_text(encoding="utf-8"))


def main() -> None:
    p = argparse.ArgumentParser(prog="clinicomm.modules.m4_response")
    p.add_argument("--config", default="config/pipeline.yaml")
    p.add_argument(
        "--demo",
        action="store_true",
        help="Use MockResponseLLM. Runs Phases 8 + 9 on the demo profile first.",
    )
    p.add_argument(
        "--profile",
        type=Path,
        help="PatientConcernProfile JSON (skipped if --demo).",
    )
    p.add_argument(
        "--context",
        type=Path,
        help="StructuredContextArtifact JSON (skipped if --demo).",
    )
    p.add_argument("--save", type=Path, help="Write PatientResponse JSON here.")
    args = p.parse_args()

    cfg = load_config(args.config)
    log_path = setup_logging(
        phase="phase10_response",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    response_prompt = _load_prompt(cfg)

    if args.demo or not (args.profile and args.context):
        # Run Phases 8 + 9 inline against the canned demo profile.
        from clinicomm.modules.m2_retrieval import Retriever, _demo_profile
        from clinicomm.modules.m3_reasoning import Reasoner
        from clinicomm.modules.llm_client import MockReasoningLLM
        from sentence_transformers import SentenceTransformer
        import torch

        device = (
            "cuda"
            if cfg["embedding"]["use_gpu_if_available"] and torch.cuda.is_available()
            else "cpu"
        )
        embed = SentenceTransformer(cfg["embedding"]["model"], device=device)

        profile = _demo_profile()
        log.info("Running inline Phase 8 (Retriever)...")
        retrieval = Retriever(cfg, sentence_model=embed).retrieve(profile)
        log.info("Running inline Phase 9 (Reasoner, mocked)...")
        assertion_prompt = Path(cfg["prompts"]["assertion_extraction"]).read_text(
            encoding="utf-8"
        )
        conflict_prompt = Path(cfg["prompts"]["conflict_resolution"]).read_text(
            encoding="utf-8"
        )
        reasoner = Reasoner(
            llm_client=MockReasoningLLM(),
            embedding_model=embed,
            assertion_prompt=assertion_prompt,
            conflict_prompt=conflict_prompt,
            cluster_threshold=0.75,
        )
        context = reasoner.reason(retrieval, profile)
        llm = MockResponseLLM()
    else:
        profile = _load_profile(args.profile)
        context = _load_context(args.context)
        llm = VLLMClient(cfg["llm"])

    responder = Responder(llm, response_prompt)
    log.info("Generating response (1 LLM call)...")
    response = responder.generate(profile, context)
    _print_trace(response)

    out_path = args.save
    if out_path is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = Path(cfg["paths"]["logs"]) / f"m4_response_{ts}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(response.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"\nSaved PatientResponse to [cyan]{out_path}[/cyan]")


if __name__ == "__main__":
    main()
