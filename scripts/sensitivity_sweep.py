"""Hyperparameter sensitivity sweeps for Figure 12 (3 panels):

  Panel A — cluster_similarity_threshold ∈ {0.65, 0.70, 0.75, 0.80, 0.85}
            -> n_clusters, n_convergent, n_divergent
  Panel B — retrieval top_k ∈ {5, 10, 20, 30, 50}
            -> unique candidate documents, sub-query coverage
  Panel C — chunk_size ∈ {200, 400, 600}     (gated by --include-chunk-size)
            -> retrieval-quality proxy on 5 sanity queries

Panels A and B are CHEAP — pure recomputation on existing pipeline state.
Panel C is EXPENSIVE — requires re-chunking + re-embedding + re-indexing
per value, so it's opt-in.

Outputs:
  manuscript/data/sensitivity_threshold.json
  manuscript/data/sensitivity_topk.json
  manuscript/data/sensitivity_chunksize.json   (when --include-chunk-size)
"""
from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import torch
from rich.console import Console
from sentence_transformers import SentenceTransformer

from clinicomm.config import load_config
from clinicomm.logging_setup import setup_logging
from clinicomm.modules.m2_retrieval import (
    Retriever,
    decompose_profile,
    embed_queries,
    retrieve_seeds,
)
from clinicomm.index.chroma_store import open_collection
from clinicomm.modules.m3_reasoning import Reasoner
from clinicomm.modules.llm_client import MockReasoningLLM
from clinicomm.pipeline import Pipeline, load_transcript
from clinicomm.schemas import (
    AssertionCluster,
    ClinicalAssertion,
    PatientConcernProfile,
    RankedDocument,
)

log = logging.getLogger("clinicomm.sensitivity_sweep")
console = Console()


# --------------------------------------------------------------------------
# Panel A — cluster threshold
# --------------------------------------------------------------------------


def sweep_cluster_threshold(
    assertions: list[ClinicalAssertion],
    embed_model: SentenceTransformer,
    values: list[float],
) -> list[dict]:
    """For each threshold value, re-cluster the same set of assertions and
    return {threshold, n_clusters, n_convergent, n_divergent}."""
    out: list[dict] = []
    for thr in values:
        reasoner = Reasoner(
            llm_client=MockReasoningLLM(),
            embedding_model=embed_model,
            assertion_prompt="",  # unused (we don't call extract here)
            conflict_prompt="",
            cluster_threshold=thr,
        )
        groups = reasoner.cluster_assertions(assertions)
        n_clusters = len(groups)
        # Resolve each group locally to count convergent vs divergent —
        # no LLM call required because resolve_cluster routes by length+text.
        # We need a doc_lookup; pass {} since we won't trigger divergence
        # resolution (mock would handle it anyway).
        n_convergent = 0
        n_divergent = 0
        for g in groups:
            if len(g) == 1:
                n_convergent += 1
                continue
            norm_texts = {a.assertion_text.strip().lower() for a in g}
            if len(norm_texts) == 1:
                n_convergent += 1
            else:
                n_divergent += 1
        out.append(
            {
                "threshold": thr,
                "n_clusters": n_clusters,
                "n_convergent": n_convergent,
                "n_divergent": n_divergent,
            }
        )
    return out


# --------------------------------------------------------------------------
# Panel B — top_k
# --------------------------------------------------------------------------


def sweep_top_k(
    cfg: dict,
    profile: PatientConcernProfile,
    embed_model: SentenceTransformer,
    values: list[int],
) -> list[dict]:
    """For each top_k value, re-run retrieval and record:
      n_candidate_chunks      (sum of seeds across sub-queries; before dedup)
      n_candidate_documents   (unique PMIDs in seeds; the pool the reranker
                                draws from)
      n_returned_documents    (after rerank cap, final_n_documents)
      sub_queries_covered     (# distinct sub_query indices represented
                                in the final ranked set)
    """
    sub_queries = decompose_profile(profile)
    embs = embed_queries(embed_model, sub_queries)
    coll = open_collection(
        cfg["index"]["persist_dir"],
        cfg["index"]["collection_name"],
        create_if_missing=False,
    )

    out: list[dict] = []
    orig_top_k = cfg["retrieval"]["top_k"]
    try:
        for k in values:
            per_query_seeds = retrieve_seeds(coll, embs, top_k=k)
            n_candidate_chunks = sum(len(seeds) for seeds in per_query_seeds)
            unique_pmids: set[str] = set()
            for seeds in per_query_seeds:
                for chunk in seeds:
                    unique_pmids.add(chunk.pmid)

            # Then run the full rerank via Retriever so coverage numbers
            # also include the greedy MMR step.
            cfg["retrieval"]["top_k"] = k
            retriever = Retriever(cfg, sentence_model=embed_model)
            ranked = retriever.retrieve(profile)
            covered_sq = set()
            for d in ranked.documents:
                for s in d.addresses_concerns:
                    covered_sq.add(s)
            out.append(
                {
                    "top_k": k,
                    "n_sub_queries": len(ranked.sub_queries),
                    "n_candidate_chunks": n_candidate_chunks,
                    "n_candidate_documents": len(unique_pmids),
                    "n_returned_documents": len(ranked.documents),
                    "sub_queries_covered": len(covered_sq),
                }
            )
    finally:
        cfg["retrieval"]["top_k"] = orig_top_k
    return out


# --------------------------------------------------------------------------
# Panel C — chunk size (opt-in)
# --------------------------------------------------------------------------


def sweep_chunk_size(values: list[int]) -> list[dict]:
    """Each value requires re-running Phases 4 + 5, which is expensive.
    We don't run that here automatically — instead, this is a placeholder
    that records intent. Pass --include-chunk-size to actually drive a
    Phase 4 + 5 rerun externally."""
    return [
        {
            "chunk_size": v,
            "status": "deferred — run scripts/bootstrap.sh --chunk-size=v",
        }
        for v in values
    ]


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(prog="scripts/sensitivity_sweep.py")
    p.add_argument("--config", default="config/pipeline.yaml")
    p.add_argument("--include-chunk-size", action="store_true",
                   help="Include Panel C placeholder rows (full sweep is "
                   "expensive; see docstring).")
    p.add_argument("--threshold-values", default="0.65,0.70,0.75,0.80,0.85")
    p.add_argument("--top-k-values", default="5,10,20,30,50")
    p.add_argument("--chunk-size-values", default="200,400,600")
    p.add_argument("--data-dir", type=Path, default=Path("manuscript/data"))
    args = p.parse_args()

    cfg = load_config(args.config)
    log_path = setup_logging(
        phase="phase12_sensitivity",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    args.data_dir.mkdir(parents=True, exist_ok=True)

    # Embedding model + Pipeline (mock) — we'll use the demo profile +
    # the saved demo trace as our anchor data.
    device = "cuda" if cfg["embedding"]["use_gpu_if_available"] and torch.cuda.is_available() else "cpu"
    embed_model = SentenceTransformer(cfg["embedding"]["model"], device=device)

    pipeline = Pipeline.with_mocks(cfg, embed_model=embed_model)
    # Use p001 as the anchor for both panels (it's our canonical demo).
    transcripts = sorted(Path(cfg["paths"]["synthetic_patients"]).glob("p001*.json"))
    if not transcripts:
        console.print("[red]p001 transcript missing — sensitivity sweep needs it.[/red]")
        return
    pid, scenario, utts = load_transcript(transcripts[0])
    console.print(f"Anchor transcript: {pid}  ({len(utts)} turns)")

    result = pipeline.run(utts, transcript_id=pid, scenario=scenario)
    profile = result.profile

    # Flatten all assertions across the existing Module III run.
    all_assertions: list[ClinicalAssertion] = []
    for c in result.structured_context.clusters:
        all_assertions.append(c.primary_assertion)
        all_assertions.extend(c.alternative_assertions)
    console.print(f"Total assertions to re-cluster: {len(all_assertions)}")

    # --- Panel A ---
    thr_values = [float(x) for x in args.threshold_values.split(",")]
    panel_a = sweep_cluster_threshold(all_assertions, embed_model, thr_values)
    (args.data_dir / "sensitivity_threshold.json").write_text(
        json.dumps(
            {
                "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "anchor_transcript": pid,
                "n_assertions": len(all_assertions),
                "panel_a": panel_a,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    console.print("[green]Panel A done[/green]")
    for row in panel_a:
        console.print(
            f"  thr={row['threshold']:.2f}  clusters={row['n_clusters']:>3}  "
            f"conv={row['n_convergent']:>3}  div={row['n_divergent']:>3}"
        )

    # --- Panel B ---
    top_k_values = [int(x) for x in args.top_k_values.split(",")]
    panel_b = sweep_top_k(cfg, profile, embed_model, top_k_values)
    (args.data_dir / "sensitivity_topk.json").write_text(
        json.dumps(
            {
                "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "anchor_transcript": pid,
                "n_sub_queries": panel_b[0]["n_sub_queries"] if panel_b else 0,
                "panel_b": panel_b,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    console.print("[green]Panel B done[/green]")
    for row in panel_b:
        console.print(
            f"  top_k={row['top_k']:>3}  returned_docs={row['n_returned_documents']:>3}  "
            f"sub_queries_covered={row['sub_queries_covered']:>2}/{row['n_sub_queries']}"
        )

    # --- Panel C (placeholder unless --include-chunk-size) ---
    if args.include_chunk_size:
        cs_values = [int(x) for x in args.chunk_size_values.split(",")]
        panel_c = sweep_chunk_size(cs_values)
        (args.data_dir / "sensitivity_chunksize.json").write_text(
            json.dumps(
                {
                    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "panel_c": panel_c,
                    "note": "Each value requires a full Phase 4 + 5 rerun "
                    "with config/pipeline.yaml chunk_size_tokens edited. "
                    "Run scripts/bootstrap.sh after editing the config.",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        console.print("[green]Panel C (placeholder) written[/green]")


if __name__ == "__main__":
    main()
