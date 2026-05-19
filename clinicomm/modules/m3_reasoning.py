"""Module III — Graph-RAG Reasoning (abstracts adaptation).

Pipeline:
    for each RankedDocument in the RankedDocumentSet:
        one LLM call (assertion_extraction.txt) -> list[ClinicalAssertion]
    cluster_assertions(all_assertions, threshold=0.75)
        -> list[AssertionCluster] grouped by (type, addresses_concern)
           then merged by embedding-similarity >= threshold
    for each cluster:
        if all assertions agree (length 1 or all-same-text):
            -> convergent; primary = highest-confidence assertion
        else:
            -> one LLM call (conflict_resolution.txt) chooses primary;
               others retained as alternatives with retain_reason
    emit StructuredContextArtifact

ABSTRACTS-ONLY LIMITATION (record in manuscript Methods/Limitations):
Module III runs on chunked abstracts, not full text. Assertion
granularity is therefore coarser than a full-text system would
produce — some details (dose, duration, sub-population caveats) live
only in the methods or discussion of the full paper and are
unrecoverable here. The pipeline records this in
StructuredContextArtifact.notes so the limitation is visible in every
generated trace.

CLI:
  uv run python -m clinicomm.modules.m3_reasoning --demo
      # mocked end-to-end on Phase 8's demo retrieval set

  uv run python -m clinicomm.modules.m3_reasoning --retrieval <path>
      # uses the configured vLLM server; <path> is a saved
      # RankedDocumentSet JSON from m2_retrieval
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table
from sentence_transformers import SentenceTransformer

from clinicomm.config import load_config
from clinicomm.logging_setup import setup_logging
from clinicomm.modules._authority import CANONICAL as AUTHORITY_TABLE
from clinicomm.modules._authority import authority_score
from clinicomm.modules.llm_client import LLMClient, MockReasoningLLM, VLLMClient
from clinicomm.schemas import (
    AssertionCluster,
    ClinicalAssertion,
    PatientConcernProfile,
    RankedDocument,
    RankedDocumentSet,
    StructuredContextArtifact,
)

log = logging.getLogger("clinicomm.modules.m3_reasoning")
console = Console()


# Order used for the "evidence_strength" tiebreaker if the conflict
# resolver falls through to that rule (we don't currently call it from
# Python, but keep the order documented here for parity with the
# prompt). Higher = preferred.
PUBTYPE_RANK = {
    "Practice Guideline":   5,
    "Guideline":            5,
    "Systematic Review":    4,
    "Meta-Analysis":        4,
    "Consensus Statement":  3,
    "Randomized Controlled Trial": 3,
    "Review":               2,
    "Journal Article":      1,
}


# --------------------------------------------------------------------------
# Reasoner
# --------------------------------------------------------------------------


class Reasoner:
    def __init__(
        self,
        llm_client: LLMClient,
        embedding_model: SentenceTransformer,
        assertion_prompt: str,
        conflict_prompt: str,
        cluster_threshold: float = 0.75,
    ) -> None:
        self.llm = llm_client
        self.embed = embedding_model
        self.assertion_prompt = assertion_prompt
        self.conflict_prompt = conflict_prompt
        self.cluster_threshold = cluster_threshold

    # ---- extraction (one LLM call per doc) ------------------------------

    def extract_assertions(
        self,
        doc: RankedDocument,
        profile: PatientConcernProfile,
    ) -> list[ClinicalAssertion]:
        meta = {
            "pmid": doc.pmid,
            "title": doc.title,
            "journal": doc.journal,
            "pub_date": doc.pub_date,
            "pub_year": doc.pub_year,
            "pub_types": doc.pub_types,
            "issuing_body": doc.issuing_body,
        }
        candidates = doc.addresses_concerns
        # Trim full_text to keep prompt bounded (most abstracts <2k chars).
        text = doc.full_text[:8000]
        user_payload = (
            f"DOCUMENT_METADATA:\n{json.dumps(meta, ensure_ascii=False)}\n\n"
            f"DOCUMENT_TEXT:\n{text}\n\n"
            f"PATIENT_PROFILE:\n{profile.model_dump_json(indent=2)}\n\n"
            f"ADDRESSES_CONCERN_CANDIDATES:\n{json.dumps(candidates)}\n"
        )
        raw = self.llm.complete(
            system=self.assertion_prompt,
            user=user_payload,
            response_format_json=True,
        )
        data = _safe_json_loads(raw, context=f"extract({doc.pmid})")
        if not data:
            return []
        out: list[ClinicalAssertion] = []
        for entry in data.get("assertions", []) or []:
            try:
                a = ClinicalAssertion.model_validate(entry)
            except ValidationError as e:
                log.warning(
                    "skipping malformed assertion from pmid=%s: %s",
                    doc.pmid,
                    e.errors()[0]["msg"] if e.errors() else str(e),
                )
                continue
            out.append(a)
        return out

    # ---- clustering (purely local, embedding-based) ---------------------

    def cluster_assertions(
        self, assertions: list[ClinicalAssertion]
    ) -> list[list[ClinicalAssertion]]:
        """Returns groups of assertions. Each group:
          - shares (assertion_type, addresses_concern)
          - and is internally cosine-similar (>= self.cluster_threshold)
            via single-link agglomerative merging.
        """
        if not assertions:
            return []

        groups: dict[tuple[str, str | None], list[ClinicalAssertion]] = {}
        for a in assertions:
            key = (a.assertion_type, a.addresses_concern)
            groups.setdefault(key, []).append(a)

        clusters: list[list[ClinicalAssertion]] = []
        for key, group in groups.items():
            if len(group) == 1:
                clusters.append(group)
                continue
            texts = [a.assertion_text for a in group]
            embs = self.embed.encode(
                texts,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            # Cosine similarity matrix (embs already normalized).
            sims = embs @ embs.T
            n = len(group)
            # Single-link clustering: union-find on edges >= threshold.
            parent = list(range(n))

            def find(x: int) -> int:
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            def union(a: int, b: int) -> None:
                pa, pb = find(a), find(b)
                if pa != pb:
                    parent[pa] = pb

            for i in range(n):
                for j in range(i + 1, n):
                    if sims[i, j] >= self.cluster_threshold:
                        union(i, j)
            root_to_members: dict[int, list[int]] = {}
            for i in range(n):
                root_to_members.setdefault(find(i), []).append(i)
            for members in root_to_members.values():
                clusters.append([group[i] for i in members])
        return clusters

    # ---- per-cluster resolution -----------------------------------------

    def resolve_cluster(
        self,
        cluster: list[ClinicalAssertion],
        doc_lookup: dict[str, RankedDocument],
    ) -> AssertionCluster:
        atype = cluster[0].assertion_type
        addresses = cluster[0].addresses_concern
        cluster_id = f"{atype}::{addresses or 'global'}::{cluster[0].assertion_id}"

        if len(cluster) == 1:
            return AssertionCluster(
                cluster_id=cluster_id,
                assertion_type=atype,
                addresses_concern=addresses,
                primary_assertion=cluster[0],
                supporting_pmids=[cluster[0].source_pmid],
                alternative_assertions=[],
                convergent=True,
                confidence=cluster[0].confidence,
                resolution_rule=None,
                resolution_rationale=None,
            )

        # Convergent if all texts are identical post-normalization.
        norm_texts = {re.sub(r"\s+", " ", a.assertion_text.strip().lower()) for a in cluster}
        if len(norm_texts) == 1:
            primary = max(cluster, key=lambda a: a.confidence)
            return AssertionCluster(
                cluster_id=cluster_id,
                assertion_type=atype,
                addresses_concern=addresses,
                primary_assertion=primary,
                supporting_pmids=sorted({a.source_pmid for a in cluster}),
                alternative_assertions=[],
                convergent=True,
                confidence=min(1.0, sum(a.confidence for a in cluster) / len(cluster) + 0.05),
                resolution_rule=None,
                resolution_rationale=None,
            )

        # Divergent -> LLM call.
        cluster_payload = self._cluster_payload(cluster, doc_lookup)
        user_payload = (
            f"CLUSTER:\n{json.dumps(cluster_payload, ensure_ascii=False)}\n\n"
            f"AUTHORITY_TABLE:\n{json.dumps(AUTHORITY_TABLE, ensure_ascii=False)}\n"
        )
        raw = self.llm.complete(
            system=self.conflict_prompt,
            user=user_payload,
            response_format_json=True,
        )
        data = _safe_json_loads(raw, context=f"resolve({cluster_id})")
        primary_id = (data or {}).get("primary_assertion_id") or ""
        primary = next((a for a in cluster if a.assertion_id == primary_id), None)
        if primary is None:
            # LLM returned an id not in the cluster: fall back to recency+confidence.
            log.warning(
                "conflict resolver returned unknown primary_id=%r for cluster %s; "
                "falling back to recency + confidence tiebreak.",
                primary_id,
                cluster_id,
            )
            primary = max(
                cluster,
                key=lambda a: (
                    doc_lookup.get(a.source_pmid).pub_year or 0
                    if a.source_pmid in doc_lookup
                    else 0,
                    a.confidence,
                ),
            )
            data = {
                "primary_rationale": "Fallback: most-recent + highest-confidence",
                "resolution_rule": "recency",
                "alternatives": [
                    {"assertion_id": a.assertion_id, "retain_reason": "(auto) non-primary"}
                    for a in cluster
                    if a.assertion_id != primary.assertion_id
                ],
            }
        alt_ids = {alt["assertion_id"] for alt in data.get("alternatives", []) or []}
        alternatives = [a for a in cluster if a.assertion_id in alt_ids]
        # Anything in the cluster not the primary and not in alt_ids gets
        # appended (the prompt forbids dropping; defend against drift).
        missing = [
            a for a in cluster if a.assertion_id != primary.assertion_id and a.assertion_id not in alt_ids
        ]
        if missing:
            log.warning(
                "conflict resolver dropped %d non-primary assertions; re-attaching",
                len(missing),
            )
            alternatives.extend(missing)

        return AssertionCluster(
            cluster_id=cluster_id,
            assertion_type=atype,
            addresses_concern=addresses,
            primary_assertion=primary,
            supporting_pmids=sorted({a.source_pmid for a in cluster}),
            alternative_assertions=alternatives,
            convergent=False,
            confidence=primary.confidence,
            resolution_rule=data.get("resolution_rule"),
            resolution_rationale=data.get("primary_rationale"),
        )

    def _cluster_payload(
        self,
        cluster: list[ClinicalAssertion],
        doc_lookup: dict[str, RankedDocument],
    ) -> dict:
        entries = []
        for a in cluster:
            doc = doc_lookup.get(a.source_pmid)
            entries.append(
                {
                    "assertion_id": a.assertion_id,
                    "assertion_text": a.assertion_text,
                    "assertion_type": a.assertion_type,
                    "confidence": a.confidence,
                    "evidence_quote": a.evidence_quote,
                    "source_pmid": a.source_pmid,
                    "addresses_concern": a.addresses_concern,
                    "journal": doc.journal if doc else None,
                    "pub_year": doc.pub_year if doc else None,
                    "pub_date": doc.pub_date if doc else None,
                    "pub_types": doc.pub_types if doc else [],
                    "authority_score": authority_score(doc.journal) if doc else 0.0,
                }
            )
        return {"assertions": entries}

    # ---- top-level driver -----------------------------------------------

    def reason(
        self,
        retrieval: RankedDocumentSet,
        profile: PatientConcernProfile,
    ) -> StructuredContextArtifact:
        doc_lookup: dict[str, RankedDocument] = {d.pmid: d for d in retrieval.documents}
        log.info("extracting assertions from %d documents", len(retrieval.documents))
        all_assertions: list[ClinicalAssertion] = []
        for i, doc in enumerate(retrieval.documents, 1):
            assertions = self.extract_assertions(doc, profile)
            log.info("  [%d/%d] pmid=%s -> %d assertions",
                     i, len(retrieval.documents), doc.pmid, len(assertions))
            all_assertions.extend(assertions)

        log.info("total assertions extracted: %d", len(all_assertions))
        groups = self.cluster_assertions(all_assertions)
        log.info("clusters formed: %d", len(groups))

        resolved: list[AssertionCluster] = []
        for group in groups:
            resolved.append(self.resolve_cluster(group, doc_lookup))

        # Order: convergent first within each addresses_concern bucket,
        # then divergent. Stable within each.
        def order_key(c: AssertionCluster) -> tuple:
            return (
                c.addresses_concern or "~",  # ~ sorts last; nulls go to the end
                0 if c.convergent else 1,
                -c.confidence,
            )

        resolved.sort(key=order_key)

        n_div = sum(1 for c in resolved if not c.convergent)
        return StructuredContextArtifact(
            clusters=resolved,
            n_documents_processed=len(retrieval.documents),
            n_assertions_extracted=len(all_assertions),
            n_clusters=len(resolved),
            n_convergent_clusters=len(resolved) - n_div,
            n_divergent_clusters=n_div,
            cluster_similarity_threshold=self.cluster_threshold,
            notes=[
                "Abstracts-only prototype: assertion granularity is coarser "
                "than a full-text system would produce.",
                "Module II graph expansion is stubbed in v0 (flat vector "
                "retrieval). See clinicomm.modules.m2_retrieval.expand_neighborhood.",
            ],
        )


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _safe_json_loads(raw: str, *, context: str) -> dict | None:
    s = (raw or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
        s = s.strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        log.error("JSON parse failed (%s): %s", context, e)
        log.error("raw[:400]: %s", s[:400])
        return None


def _load_prompts(cfg: dict) -> tuple[str, str]:
    a = Path(cfg["prompts"]["assertion_extraction"]).read_text(encoding="utf-8")
    c = Path(cfg["prompts"]["conflict_resolution"]).read_text(encoding="utf-8")
    return a, c


def _load_retrieval(path: Path) -> RankedDocumentSet:
    return RankedDocumentSet.model_validate_json(path.read_text(encoding="utf-8"))


def _load_profile(path: Path) -> PatientConcernProfile:
    return PatientConcernProfile.model_validate_json(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Trace rendering
# --------------------------------------------------------------------------


def _print_trace(art: StructuredContextArtifact) -> None:
    tbl = Table(title="StructuredContextArtifact — top-level counts")
    tbl.add_column("metric")
    tbl.add_column("value", justify="right")
    tbl.add_row("documents processed",     str(art.n_documents_processed))
    tbl.add_row("assertions extracted",    str(art.n_assertions_extracted))
    tbl.add_row("clusters",                str(art.n_clusters))
    tbl.add_row("  convergent",            str(art.n_convergent_clusters))
    tbl.add_row("  divergent (LLM-resolved)", str(art.n_divergent_clusters))
    tbl.add_row("cluster threshold",       f"{art.cluster_similarity_threshold:.2f}")
    console.print(tbl)

    if not art.clusters:
        return

    console.rule("[bold]Clusters[/bold]")
    for i, c in enumerate(art.clusters):
        kind = "CONVERGENT" if c.convergent else "DIVERGENT"
        console.print(
            f"\n[bold]Cluster {i + 1}[/bold]  [{kind}]  "
            f"type=[cyan]{c.assertion_type}[/cyan]  "
            f"addresses=[magenta]{c.addresses_concern or '(global)'}[/magenta]  "
            f"conf={c.confidence:.2f}  supporting_pmids={c.supporting_pmids}"
        )
        p = c.primary_assertion
        console.print(
            f"  [bold]primary:[/bold] [{p.source_pmid}] {p.assertion_text}"
        )
        if c.alternative_assertions:
            console.print(f"  [bold]alternatives ({len(c.alternative_assertions)}):[/bold]")
            for a in c.alternative_assertions[:4]:
                console.print(
                    f"    - [{a.source_pmid}] ({a.confidence:.2f}) {a.assertion_text[:140]}"
                )
        if c.resolution_rule:
            console.print(
                f"  [bold]resolution:[/bold] rule=[yellow]{c.resolution_rule}[/yellow]  "
                f"rationale={c.resolution_rationale}"
            )

    if art.notes:
        console.rule("[dim]notes (manuscript Limitations)[/dim]")
        for n in art.notes:
            console.print(f"  • {n}")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(prog="clinicomm.modules.m3_reasoning")
    p.add_argument("--config", default="config/pipeline.yaml")
    src = p.add_mutually_exclusive_group(required=False)
    src.add_argument(
        "--demo",
        action="store_true",
        help="Use MockReasoningLLM + Phase 8 demo retrieval set.",
    )
    src.add_argument(
        "--retrieval",
        type=Path,
        help="Path to a saved RankedDocumentSet JSON (from m2_retrieval --save).",
    )
    p.add_argument(
        "--profile",
        type=Path,
        help="Optional PatientConcernProfile JSON. With --demo we use the "
        "built-in demo profile; with --retrieval, provide a real profile.",
    )
    p.add_argument(
        "--save",
        type=Path,
        help="Write the StructuredContextArtifact JSON here.",
    )
    p.add_argument(
        "--limit-docs",
        type=int,
        default=None,
        help="Cap how many ranked documents are processed (testing).",
    )
    args = p.parse_args()

    cfg = load_config(args.config)
    log_path = setup_logging(
        phase="phase09_reasoning",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    assertion_prompt, conflict_prompt = _load_prompts(cfg)

    # Embedding model — used purely for clustering text similarity.
    device = (
        "cuda"
        if cfg["embedding"]["use_gpu_if_available"] and torch.cuda.is_available()
        else "cpu"
    )
    log.info("loading SentenceTransformer %s on %s", cfg["embedding"]["model"], device)
    embed_model = SentenceTransformer(cfg["embedding"]["model"], device=device)

    if args.demo or not args.retrieval:
        # Build retrieval + profile via the same demo helpers used in Phase 8.
        from clinicomm.modules.m2_retrieval import Retriever, _demo_profile

        profile = _demo_profile()
        log.info("Mode: --demo (MockReasoningLLM); running Phase 8 retrieval first.")
        retriever = Retriever(cfg, sentence_model=embed_model)
        retrieval = retriever.retrieve(profile)
        llm = MockReasoningLLM()
    else:
        retrieval = _load_retrieval(args.retrieval)
        if args.profile:
            profile = _load_profile(args.profile)
        else:
            console.print(
                "[yellow]--retrieval was provided without --profile; "
                "Module III still works (the profile is only echoed into "
                "extraction prompts), but Module IV will want a real "
                "profile downstream.[/yellow]"
            )
            profile = PatientConcernProfile()
        log.info("Mode: live VLLMClient.")
        llm = VLLMClient(cfg["llm"])

    if args.limit_docs:
        retrieval.documents = retrieval.documents[: args.limit_docs]
        log.info("--limit-docs=%d", args.limit_docs)

    reasoner = Reasoner(
        llm_client=llm,
        embedding_model=embed_model,
        assertion_prompt=assertion_prompt,
        conflict_prompt=conflict_prompt,
        cluster_threshold=0.75,
    )
    artifact = reasoner.reason(retrieval, profile)
    _print_trace(artifact)

    out_path = args.save
    if out_path is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = Path(cfg["paths"]["logs"]) / f"m3_reasoning_{ts}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"\nSaved StructuredContextArtifact to [cyan]{out_path}[/cyan]")


if __name__ == "__main__":
    main()
