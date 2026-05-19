"""Module-level ablation conditions for Table 5.

Four conditions on the same transcript:

  (a) naive            — single LLM call, no framework prompt, no retrieval,
                          no reasoning, no structured output.
                          Implemented in clinicomm/baseline.py.

  (b) framework_only   — single Module-IV-style LLM call with the
                          response_generation.txt system prompt (NURSE +
                          Four Habits DIRECTIVES) applied directly to the
                          raw transcript. NO Module I profile, NO retrieval,
                          NO structured context. Tests: how much of the gain
                          is framework-prompting alone?

  (c) retrieval_only   — Module I (intake extraction) → Module II
                          (retrieval) → Module IV, with the StructuredContext
                          replaced by a stub artifact: one cluster per
                          top-N retrieved doc, each cluster's primary_assertion
                          is the doc's title (no LLM extraction, no clustering,
                          no conflict resolution). Tests: how much of the gain
                          comes from Module III specifically?

  (d) full             — Modules I+II+III+IV. Default Pipeline.run().

Each condition returns a PatientResponse so downstream metrics code can
treat them uniformly. For (a) we wrap the free-text in a degenerate
PatientResponse skeleton; for (b) and (c) the LLM is asked to produce
the proper structured JSON.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from clinicomm.baseline import NaiveLLMBaseline
from clinicomm.modules.llm_client import LLMClient
from clinicomm.modules.m1_intake import IntakeAgent
from clinicomm.modules.m2_retrieval import Retriever
from clinicomm.modules.m4_response import Responder
from clinicomm.schemas import (
    AssertionCluster,
    ClinicalAssertion,
    ConcernExplanation,
    PatientConcernProfile,
    PatientResponse,
    RankedDocumentSet,
    StructuredContextArtifact,
)

log = logging.getLogger("clinicomm.ablations")


# --------------------------------------------------------------------------
# (a) Naive baseline → PatientResponse adapter
# --------------------------------------------------------------------------


def naive_to_patient_response(
    baseline_text: str,
    *,
    transcript_id: str,
) -> PatientResponse:
    """Wrap the free-text baseline in a minimal PatientResponse so the
    metrics code can consume it uniformly. Every structured / framework
    field is empty by construction — that's the whole point of the
    condition.
    """
    # Use the entire text as acknowledgment so word_count + FK grade see it.
    return PatientResponse(
        acknowledgment=baseline_text,
        clinical_information_per_concern=[],
        next_steps=[],
        teach_back_prompt="",
        follow_up_invitation="",
        nurse_elements_applied=[],
        four_habits_elements_applied=[],
        all_cluster_ids_used=[],
        all_pmids_used=[],
        glossary_substitutions=[],
    )


# --------------------------------------------------------------------------
# (b) Framework-only condition
# --------------------------------------------------------------------------


def framework_only_response(
    *,
    llm: LLMClient,
    response_prompt: str,
    patient_utterances: list[str],
    transcript_id: str,
) -> PatientResponse:
    """Single LLM call with the response_generation.txt system prompt
    against a HOLLOW profile + EMPTY structured context, so the NURSE +
    Four Habits directives are present but no extracted-profile fields
    and no cluster_ids exist to cite.

    The prompt's rule "every clinical claim must cite a cluster" forces
    the LLM to either omit citations or invent them. We strip invented
    cluster_ids in Responder.generate(); see m4_response.py.
    """
    profile = PatientConcernProfile()
    context = StructuredContextArtifact(
        clusters=[],
        n_documents_processed=0,
        n_assertions_extracted=0,
        n_clusters=0,
        n_convergent_clusters=0,
        n_divergent_clusters=0,
        cluster_similarity_threshold=0.0,
        notes=[
            "FRAMEWORK-ONLY ABLATION: no retrieval, no reasoning. "
            "Module IV is operating on the raw transcript with the "
            "DIRECTIVES block as its only source of structure."
        ],
    )
    # Inject the raw transcript into the profile so the response prompt
    # has *something* to anchor on. We put it in relevant_history as a
    # last-resort field — clearly labeled as the ablation hint.
    transcript_text = " | ".join(patient_utterances)
    profile.relevant_history = [
        f"(framework-only ablation) raw patient utterances: {transcript_text}"
    ]
    responder = Responder(llm, response_prompt)
    return responder.generate(profile, context)


# --------------------------------------------------------------------------
# (c) Retrieval-only condition
# --------------------------------------------------------------------------


def retrieval_only_response(
    *,
    cfg: dict,
    intake_llm: LLMClient,
    response_llm: LLMClient,
    intake_prompt: str,
    response_prompt: str,
    patient_utterances: list[str],
    transcript_id: str,
    top_n_docs: int = 5,
) -> tuple[PatientResponse, PatientConcernProfile, RankedDocumentSet]:
    """Module I → Module II → stub-context → Module IV.

    We skip Module III entirely. Instead, for each of the top-N retrieved
    documents we synthesize a one-assertion cluster:

        cluster_id = "retrieval_only::{pmid}"
        primary_assertion.assertion_text = "(from retrieval; not clustered) " + title
        supporting_pmids = [pmid]
        convergent = True

    This preserves Module IV's citation pipeline so we can compare
    apples-to-apples with the full pipeline.
    """
    # ---- Module I ----
    agent = IntakeAgent(intake_llm, intake_prompt)
    profile, _ = agent.run_intake(patient_utterances)

    # ---- Module II ----
    retriever = Retriever(cfg)
    ranked = retriever.retrieve(profile)

    # ---- stub context ----
    clusters: list[AssertionCluster] = []
    for d in ranked.documents[:top_n_docs]:
        cid = f"retrieval_only::{d.pmid}"
        primary = ClinicalAssertion(
            assertion_id=f"{d.pmid}_retr",
            assertion_text=(
                "(retrieval-only ablation; not clustered) "
                + (d.title or "")[:240]
            ),
            assertion_type="finding",
            confidence=0.6,
            source_pmid=d.pmid,
            source_chunk_id=None,
            addresses_concern=None,
            evidence_quote=(d.full_text or "")[:280],
        )
        clusters.append(
            AssertionCluster(
                cluster_id=cid,
                assertion_type="finding",
                addresses_concern=None,
                primary_assertion=primary,
                supporting_pmids=[d.pmid],
                alternative_assertions=[],
                convergent=True,
                confidence=0.6,
            )
        )
    context = StructuredContextArtifact(
        clusters=clusters,
        n_documents_processed=top_n_docs,
        n_assertions_extracted=top_n_docs,
        n_clusters=len(clusters),
        n_convergent_clusters=len(clusters),
        n_divergent_clusters=0,
        cluster_similarity_threshold=0.0,
        notes=[
            "RETRIEVAL-ONLY ABLATION: Module III is bypassed. Each "
            "top-retrieved document is wrapped as a singleton cluster; "
            "no assertion extraction, no clustering, no conflict resolution."
        ],
    )

    # ---- Module IV ----
    responder = Responder(response_llm, response_prompt)
    response = responder.generate(profile, context)
    return response, profile, ranked


__all__ = [
    "naive_to_patient_response",
    "framework_only_response",
    "retrieval_only_response",
]
