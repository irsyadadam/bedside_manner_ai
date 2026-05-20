"""End-to-end orchestrator. Module I -> II -> III -> IV.

Two construction modes:

  Pipeline.with_mocks(cfg)
      Uses MockLLMClient / MockReasoningLLM / MockResponseLLM.
      Loads the embedding model once and shares it across modules.
      Goal: deterministic, no-network, reproducible traces. Used by
      scripts/run_demo.py --demo and by Phase 12 artifact generation.

  Pipeline.with_real_llm(cfg)
      Single VLLMClient instance shared across all three reasoning
      modules (intake + reasoning + response). Embedding model
      loaded the same way. Requires scripts/start_vllm_server.sh
      to be running.

run() takes a list of patient_utterances + scenario metadata and
returns a PipelineResult containing every intermediate artifact for
the Markdown report.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import torch
from sentence_transformers import SentenceTransformer

from clinicomm.config import load_config
from clinicomm.modules.llm_client import (
    LLMClient,
    MockLLMClient,
    MockReasoningLLM,
    MockResponseLLM,
    VLLMClient,
)
from clinicomm.modules.m1_intake import IntakeAgent
from clinicomm.modules.m2_retrieval import Retriever
from clinicomm.modules.m3_reasoning import Reasoner
from clinicomm.modules.m4_response import Responder
from clinicomm.schemas import (
    PatientConcernProfile,
    PatientResponse,
    RankedDocumentSet,
    StructuredContextArtifact,
)

log = logging.getLogger("clinicomm.pipeline")


# --------------------------------------------------------------------------
# Result container
# --------------------------------------------------------------------------


@dataclass
class PipelineResult:
    """Everything Phase 11's report writer / Phase 12's trace generator need."""
    transcript_id: str
    scenario: str
    patient_utterances: list[str]
    intake_trace: list[dict]
    profile: PatientConcernProfile
    ranked_docs: RankedDocumentSet
    structured_context: StructuredContextArtifact
    response: PatientResponse
    # Mode tag so the Markdown report can note whether mocks were used.
    mode: str = "real"  # "real" or "mock"
    # Per-module wall-clock latency in milliseconds — populated by
    # Pipeline.run(). Empty dict before instrumentation runs. Phase 12
    # Fig 11 plots this.
    module_timings_ms: dict[str, float] | None = None


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------


class Pipeline:
    def __init__(
        self,
        cfg: dict,
        *,
        intake_llm: LLMClient,
        reasoning_llm: LLMClient,
        response_llm: LLMClient,
        embed_model: SentenceTransformer,
        mode: str = "real",
    ) -> None:
        self.cfg = cfg
        self.mode = mode
        self._embed = embed_model

        # Load every prompt once at construction.
        self._intake_prompt = Path(cfg["prompts"]["intake_system"]).read_text(encoding="utf-8")
        self._assertion_prompt = Path(cfg["prompts"]["assertion_extraction"]).read_text(encoding="utf-8")
        self._conflict_prompt = Path(cfg["prompts"]["conflict_resolution"]).read_text(encoding="utf-8")
        self._response_prompt = Path(cfg["prompts"]["response_generation"]).read_text(encoding="utf-8")

        # Hold the LLM clients as "templates" — in mock mode we
        # re-instantiate them per run() so their accumulated state
        # (the mock profile builder, etc.) doesn't bleed across
        # transcripts. In real mode VLLMClient is stateless so the
        # same instance is reused.
        self._intake_llm_tmpl = intake_llm
        self._reasoning_llm_tmpl = reasoning_llm
        self._response_llm_tmpl = response_llm

        # Retriever is stateless — build once, reuse.
        self.retriever = Retriever(cfg, sentence_model=embed_model)

    # ---- private --------------------------------------------------------

    def _fresh_llms(self) -> tuple[LLMClient, LLMClient, LLMClient]:
        if self.mode == "mock":
            return (
                type(self._intake_llm_tmpl)(),
                type(self._reasoning_llm_tmpl)(),
                type(self._response_llm_tmpl)(),
            )
        return (self._intake_llm_tmpl, self._reasoning_llm_tmpl, self._response_llm_tmpl)

    # ---- factories ------------------------------------------------------

    @classmethod
    def with_mocks(
        cls,
        cfg: dict,
        embed_model: SentenceTransformer | None = None,
    ) -> "Pipeline":
        if embed_model is None:
            embed_model = _load_embed_model(cfg)
        return cls(
            cfg,
            intake_llm=MockLLMClient(),
            reasoning_llm=MockReasoningLLM(),
            response_llm=MockResponseLLM(),
            embed_model=embed_model,
            mode="mock",
        )

    @classmethod
    def with_real_llm(
        cls,
        cfg: dict,
        embed_model: SentenceTransformer | None = None,
    ) -> "Pipeline":
        if embed_model is None:
            embed_model = _load_embed_model(cfg)
        # Single VLLMClient is fine — the OpenAI-compatible server
        # multiplexes requests internally.
        shared = VLLMClient(cfg["llm"])
        return cls(
            cfg,
            intake_llm=shared,
            reasoning_llm=shared,
            response_llm=shared,
            embed_model=embed_model,
            mode="real",
        )

    # ---- main entrypoint ------------------------------------------------

    def run(
        self,
        patient_utterances: Iterable[str],
        *,
        transcript_id: str,
        scenario: str,
        max_reasoning_docs: int | None = None,
    ) -> PipelineResult:
        import time

        utterances = list(patient_utterances)
        log.info(
            "pipeline.run transcript=%s mode=%s utterances=%d",
            transcript_id,
            self.mode,
            len(utterances),
        )

        # Build per-run LLM clients (fresh in mock mode, shared real
        # client in real mode) so accumulated mock state doesn't bleed
        # across transcripts.
        intake_llm, reasoning_llm, response_llm = self._fresh_llms()
        intake_agent = IntakeAgent(intake_llm, self._intake_prompt)
        reasoner = Reasoner(
            llm_client=reasoning_llm,
            embedding_model=self._embed,
            assertion_prompt=self._assertion_prompt,
            conflict_prompt=self._conflict_prompt,
            cluster_threshold=0.75,
        )
        responder = Responder(response_llm, self._response_prompt)

        timings: dict[str, float] = {}

        # ---- Module I: Intake ------------------------------------------
        log.info("[M1] running intake (%d turns) ...", len(utterances))
        _t = time.perf_counter()
        profile, intake_trace = intake_agent.run_intake(utterances)
        timings["module_1_intake"] = (time.perf_counter() - _t) * 1000.0
        log.info(
            "[M1] done. problems=%d emotional_cues=%d red_flags=%d goals=%d complete=%s",
            len(profile.problems),
            len(profile.emotional_cues),
            len(profile.red_flags),
            len(profile.patient_goals),
            intake_agent.is_complete(profile),
        )

        # ---- Module II: Retrieval --------------------------------------
        log.info("[M2] running retrieval ...")
        _t = time.perf_counter()
        ranked = self.retriever.retrieve(profile)
        timings["module_2_retrieval"] = (time.perf_counter() - _t) * 1000.0
        log.info(
            "[M2] done. sub_queries=%d ranked_docs=%d",
            len(ranked.sub_queries),
            len(ranked.documents),
        )

        # ---- Module III: Reasoning -------------------------------------
        if max_reasoning_docs is not None and max_reasoning_docs < len(ranked.documents):
            log.info("[M3] capping docs at %d (was %d)",
                     max_reasoning_docs, len(ranked.documents))
            ranked.documents = ranked.documents[:max_reasoning_docs]
        log.info("[M3] running reasoning over %d docs ...", len(ranked.documents))
        _t = time.perf_counter()
        context = reasoner.reason(ranked, profile)
        timings["module_3_reasoning"] = (time.perf_counter() - _t) * 1000.0
        log.info(
            "[M3] done. assertions=%d clusters=%d (conv=%d div=%d)",
            context.n_assertions_extracted,
            context.n_clusters,
            context.n_convergent_clusters,
            context.n_divergent_clusters,
        )

        # ---- Module IV: Response ---------------------------------------
        log.info("[M4] running response generation ...")
        _t = time.perf_counter()
        response = responder.generate(profile, context)
        timings["module_4_response"] = (time.perf_counter() - _t) * 1000.0
        log.info(
            "[M4] done. nurse=%s habits=%s glossary_subs=%d",
            response.nurse_elements_applied,
            response.four_habits_elements_applied,
            len(response.glossary_substitutions),
        )
        timings["total_ms"] = sum(timings.values())
        log.info(
            "[timings ms] m1=%.0f  m2=%.0f  m3=%.0f  m4=%.0f  total=%.0f",
            timings["module_1_intake"],
            timings["module_2_retrieval"],
            timings["module_3_reasoning"],
            timings["module_4_response"],
            timings["total_ms"],
        )

        return PipelineResult(
            transcript_id=transcript_id,
            scenario=scenario,
            patient_utterances=utterances,
            intake_trace=intake_trace,
            profile=profile,
            ranked_docs=ranked,
            structured_context=context,
            response=response,
            mode=self.mode,
            module_timings_ms=timings,
        )


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _load_embed_model(cfg: dict) -> SentenceTransformer:
    # CLINICOMM_FORCE_CPU_EMBED forces CPU even when CUDA is available.
    # Used when multiple concurrent eval processes would otherwise OOM
    # the GPU (vLLM + N×BGE > 48GB). Retrieval is the only heavy
    # consumer of this embedding model at inference time, and it
    # encodes ≤3 short sub-queries per transcript, so CPU encoding
    # adds ~1-2s per pipeline run — negligible.
    import os
    force_cpu = os.environ.get("CLINICOMM_FORCE_CPU_EMBED", "").lower() in (
        "1", "true", "yes",
    )
    device = (
        "cuda"
        if (not force_cpu)
        and cfg["embedding"]["use_gpu_if_available"]
        and torch.cuda.is_available()
        else "cpu"
    )
    log.info("loading SentenceTransformer %s on %s%s",
             cfg["embedding"]["model"], device,
             " (CLINICOMM_FORCE_CPU_EMBED=1)" if force_cpu else "")
    return SentenceTransformer(cfg["embedding"]["model"], device=device)


def load_transcript(path: str | Path) -> tuple[str, str, list[str]]:
    """Returns (patient_id, scenario, patient_utterances). Skips TODO
    placeholder utterances so partially-filled transcripts also run."""
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    pid = raw.get("patient_id") or p.stem
    scenario = raw.get("scenario") or ""
    utterances: list[str] = []
    for t in raw.get("turns") or []:
        u = (t.get("patient_utterance") or "").strip()
        if u and not u.upper().startswith("TODO"):
            utterances.append(u)
    return pid, scenario, utterances


def is_stub_transcript(path: str | Path) -> bool:
    """True if every patient_utterance is a TODO placeholder."""
    _, _, utterances = load_transcript(path)
    return len(utterances) == 0
