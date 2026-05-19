"""Module II — Clinical Guideline Lookup (Retrieval).

Inputs:  PatientConcernProfile (Phase 7 output)
Outputs: RankedDocumentSet     (Phase 8 output; sole input to Module III)

Pipeline (per the spec):
    decompose_profile(profile)
        -> list[SubQuery]                     # one per problem, one per
                                              # goal, one global context
    embed_queries(sub_queries)
        -> np.ndarray (N, dim)                # BGE-large-en-v1.5
    retrieve_seeds(qe, top_k=20)
        -> list[RetrievedChunk] per sub-query # Chroma top_k
    expand_neighborhood(seeds)
        -> seeds                              # STUB — see note in code
    rerank(candidates, profile)
        -> RankedDocumentSet                  # 0.5 sem + 0.2 rec
                                              # + 0.2 auth + 0.1 cov

Why coverage_bonus uses greedy selection: the bonus only makes sense
relative to already-selected documents. We do a base-score sort, then
walk the list selecting one document at a time, awarding the coverage
bonus based on which sub-queries are still uncovered.

CLI:
  uv run python -m clinicomm.modules.m2_retrieval --demo
  uv run python -m clinicomm.modules.m2_retrieval --profile <path>
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import torch
from rich.console import Console
from rich.table import Table
from sentence_transformers import SentenceTransformer

from clinicomm.config import load_config
from clinicomm.index.chroma_store import open_collection
from clinicomm.logging_setup import setup_logging
from clinicomm.modules._authority import authority_score, listed_canonical_journals
from clinicomm.schemas import (
    PatientConcernProfile,
    RankedDocument,
    RankedDocumentSet,
    RetrievedChunk,
    SubQuery,
)

log = logging.getLogger("clinicomm.modules.m2_retrieval")
console = Console()


# --------------------------------------------------------------------------
# 1. decompose_profile
# --------------------------------------------------------------------------


def decompose_profile(profile: PatientConcernProfile) -> list[SubQuery]:
    """Turn a PatientConcernProfile into a list of natural-language
    sub-queries. The query strings are deterministic templates — not LLM
    generated — so retrieval is reproducible. Sub-queries are ordered:

      1. one per problem  (carries red_flag context for that problem)
      2. one per goal
      3. one global-context query (medications, history, demographics,
         any unattributed red flags)
    """
    queries: list[SubQuery] = []

    # ---- per-problem sub-queries ----
    for i, p in enumerate(profile.problems):
        bits: list[str] = [p.label]
        if p.onset:
            bits.append(f"onset {p.onset}")
        if p.severity:
            bits.append(f"severity {p.severity}")
        if p.timing:
            bits.append(f"timing {p.timing}")
        if p.associated_symptoms:
            bits.append(
                "associated with " + ", ".join(p.associated_symptoms)
            )
        if p.interventions_tried:
            bits.append("tried " + ", ".join(p.interventions_tried))
        # Attach the *evidence* of any red flag that name-matches this problem.
        for rf in profile.red_flags:
            if p.label.lower().split()[0] in rf.flag.lower():
                bits.append(f"red flag: {rf.flag}")
        text = (
            "Adult primary care: "
            + " | ".join(bits)
            + ". What guideline-based assessment, workup, or "
            "management is recommended?"
        )
        queries.append(
            SubQuery(
                source="problem",
                source_index=i,
                addresses=f"problems[{i}]",
                text=text,
            )
        )

    # ---- per-goal sub-queries ----
    for i, g in enumerate(profile.patient_goals):
        queries.append(
            SubQuery(
                source="goal",
                source_index=i,
                addresses=f"patient_goals[{i}]",
                text=(
                    f"Patient goal: \"{g}\". What clinician communication, "
                    "shared decision-making, or counseling guidance addresses "
                    "this goal?"
                ),
            )
        )

    # ---- one global-context sub-query ----
    ctx_bits: list[str] = []
    if profile.medications:
        ctx_bits.append("medications: " + "; ".join(profile.medications))
    if profile.allergies:
        ctx_bits.append("allergies: " + "; ".join(profile.allergies))
    if profile.relevant_history:
        ctx_bits.append("history: " + "; ".join(profile.relevant_history))
    # Red flags not attributed to a specific problem.
    attributed = set()
    for p in profile.problems:
        first_tok = p.label.lower().split()[0] if p.label else ""
        for rf in profile.red_flags:
            if first_tok and first_tok in rf.flag.lower():
                attributed.add(rf.flag)
    other_red = [rf.flag for rf in profile.red_flags if rf.flag not in attributed]
    if other_red:
        ctx_bits.append("red flags: " + "; ".join(other_red))
    if not ctx_bits:
        ctx_bits.append("adult primary-care visit context")
    queries.append(
        SubQuery(
            source="global_context",
            source_index=0,
            addresses=None,
            text="Patient context — " + " | ".join(ctx_bits),
        )
    )
    return queries


# --------------------------------------------------------------------------
# 2. embed_queries
# --------------------------------------------------------------------------


def embed_queries(
    model: SentenceTransformer, sub_queries: list[SubQuery]
) -> list[list[float]]:
    """Encode sub-queries with the same model the index uses. BGE-v1.5
    does not need an instruction prefix on queries (per model card)."""
    if not sub_queries:
        return []
    texts = [sq.text for sq in sub_queries]
    embs = model.encode(
        texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False
    )
    return embs.tolist()


# --------------------------------------------------------------------------
# 3. retrieve_seeds
# --------------------------------------------------------------------------


def retrieve_seeds(
    coll,
    query_embeddings: list[list[float]],
    top_k: int = 20,
) -> list[list[RetrievedChunk]]:
    """Returns one list of chunks per sub-query, in Chroma's ranked
    order (cosine distance → similarity)."""
    out: list[list[RetrievedChunk]] = []
    if not query_embeddings:
        return out
    res = coll.query(
        query_embeddings=query_embeddings,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    for q_i in range(len(query_embeddings)):
        per_query: list[RetrievedChunk] = []
        ids = res["ids"][q_i]
        docs = res["documents"][q_i]
        metas = res["metadatas"][q_i]
        dists = res["distances"][q_i]
        for k in range(len(ids)):
            per_query.append(
                RetrievedChunk(
                    chunk_id=ids[k],
                    pmid=metas[k].get("pmid", ""),
                    section_label=(metas[k].get("section_label") or "") or None,
                    text=docs[k],
                    semantic_similarity=1.0 - float(dists[k]),
                    matched_sub_query_indices=[q_i],
                )
            )
        out.append(per_query)
    return out


# --------------------------------------------------------------------------
# 4. expand_neighborhood (STUB)
# --------------------------------------------------------------------------


def expand_neighborhood(
    per_query_seeds: list[list[RetrievedChunk]],
) -> list[list[RetrievedChunk]]:
    """v0 STUB. Returns input unchanged.

    The README spec calls for 1-hop graph expansion over a document graph
    (edges: cites / supersedes / shares-descriptor). We have not built
    that graph yet — Phase 8 explicitly uses flat vector retrieval. This
    function exists so the call site stays stable when the real graph
    expansion lands (Phase 9+). DO NOT remove the call to this function
    from the retriever just because it is a no-op today.
    """
    return per_query_seeds


# --------------------------------------------------------------------------
# 5. rerank
# --------------------------------------------------------------------------


# Year range used to normalize recency. Anchored to the corpus filter
# in config/pipeline.yaml (2018/01/01 .. 2026/12/31). Linear decay:
#   recency(y) = (y - year_min) / (year_max - year_min)
RECENCY_YEAR_MIN = 2018
RECENCY_YEAR_MAX = 2026


def _recency_score(pub_year: int | None) -> float:
    if pub_year is None:
        return 0.0
    if pub_year >= RECENCY_YEAR_MAX:
        return 1.0
    if pub_year <= RECENCY_YEAR_MIN:
        return 0.0
    return (pub_year - RECENCY_YEAR_MIN) / (RECENCY_YEAR_MAX - RECENCY_YEAR_MIN)


def _aggregate_to_documents(
    per_query_seeds: list[list[RetrievedChunk]],
    parsed_dir: Path,
) -> dict[str, RankedDocument]:
    """Group seed chunks by pmid; load parsed-doc metadata; build
    a per-pmid RankedDocument with all retrieved chunks attached.
    """
    by_pmid: dict[str, list[RetrievedChunk]] = {}
    for q_i, seeds in enumerate(per_query_seeds):
        for c in seeds:
            # Re-attach sub-query index in case multiple sub-queries
            # surfaced the same chunk.
            if c.chunk_id in {x.chunk_id for x in by_pmid.get(c.pmid, [])}:
                # Already collected; just extend the matched indices.
                for x in by_pmid[c.pmid]:
                    if x.chunk_id == c.chunk_id and q_i not in x.matched_sub_query_indices:
                        x.matched_sub_query_indices.append(q_i)
                continue
            by_pmid.setdefault(c.pmid, []).append(c)

    docs: dict[str, RankedDocument] = {}
    for pmid, chunks in by_pmid.items():
        parsed_path = parsed_dir / f"{pmid}.json"
        if not parsed_path.exists():
            log.warning("parsed doc missing for pmid=%s — skipping", pmid)
            continue
        meta = json.loads(parsed_path.read_text(encoding="utf-8"))
        pub_date = meta.get("pub_date")
        pub_year = (
            int(pub_date[:4]) if pub_date and pub_date[:4].isdigit() else None
        )
        full_text_pieces: list[str] = []
        for s in meta.get("abstract", []) or []:
            lbl = s.get("section_label")
            txt = s.get("text", "")
            if lbl:
                full_text_pieces.append(f"{lbl}: {txt}")
            else:
                full_text_pieces.append(txt)
        full_text = "\n\n".join(full_text_pieces)

        max_sim = max((c.semantic_similarity for c in chunks), default=0.0)
        # addresses_concerns: distinct sub-query indices that pulled in
        # any chunk for this doc.
        addr_idx: set[int] = set()
        for c in chunks:
            addr_idx.update(c.matched_sub_query_indices)
        addresses_concerns = [f"sub_query[{i}]" for i in sorted(addr_idx)]

        docs[pmid] = RankedDocument(
            pmid=pmid,
            title=meta.get("title") or "",
            journal=meta.get("journal"),
            pub_year=pub_year,
            pub_date=pub_date,
            pub_types=meta.get("pub_types") or [],
            issuing_body=meta.get("issuing_body"),
            chunks=chunks,
            full_text=full_text,
            addresses_concerns=addresses_concerns,
            semantic_similarity=max_sim,
            recency_score=_recency_score(pub_year),
            authority_score=authority_score(meta.get("journal")),
            coverage_bonus=0.0,
            total_score=0.0,
        )
    return docs


def rerank(
    candidates: dict[str, RankedDocument],
    sub_queries: list[SubQuery],
    profile: PatientConcernProfile,  # noqa: ARG001 — reserved for future use
    weights: dict[str, float],
    final_n: int,
) -> list[RankedDocument]:
    """Greedy rerank. Returns up to `final_n` documents.

    Per the spec, the formula is:
        total = 0.5 * semantic + 0.2 * recency + 0.2 * authority + 0.1 * cov

    `cov` is the fraction of as-yet-uncovered sub-queries that this
    document covers — recomputed each step as we greedily pick.
    """
    w_sem = weights["semantic_similarity"]
    w_rec = weights["recency"]
    w_aut = weights["authority"]
    w_cov = weights["coverage_bonus"]

    remaining = dict(candidates)
    selected: list[RankedDocument] = []
    n_sub_queries = max(1, len(sub_queries))
    covered: set[int] = set()  # sub_query indices already covered

    while remaining and len(selected) < final_n:
        best_pmid = None
        best_score = -1.0
        best_doc = None
        for pmid, doc in remaining.items():
            this_doc_covers = {
                int(s.replace("sub_query[", "").rstrip("]"))
                for s in doc.addresses_concerns
            }
            new_covered = this_doc_covers - covered
            cov_bonus = len(new_covered) / n_sub_queries  # in [0, 1]
            total = (
                w_sem * doc.semantic_similarity
                + w_rec * doc.recency_score
                + w_aut * doc.authority_score
                + w_cov * cov_bonus
            )
            if total > best_score:
                best_score = total
                best_pmid = pmid
                best_doc = doc
                best_cov_bonus = cov_bonus
                best_new = new_covered
        if best_doc is None:
            break
        # Stamp the scores at the moment of selection.
        best_doc.coverage_bonus = best_cov_bonus
        best_doc.total_score = best_score
        covered |= best_new
        selected.append(best_doc)
        del remaining[best_pmid]
    return selected


# --------------------------------------------------------------------------
# Retriever — wires everything together
# --------------------------------------------------------------------------


class Retriever:
    def __init__(
        self,
        cfg: dict,
        sentence_model: SentenceTransformer | None = None,
    ) -> None:
        self.cfg = cfg
        self.top_k = int(cfg["retrieval"]["top_k"])
        self.weights = cfg["retrieval"]["rerank_weights"]
        self.final_n = int(cfg["retrieval"].get("final_n_documents", 20))
        self.parsed_dir = Path(cfg["paths"]["db_parsed"])
        self.coll = open_collection(
            cfg["index"]["persist_dir"],
            cfg["index"]["collection_name"],
            create_if_missing=False,
        )
        if sentence_model is not None:
            self.model = sentence_model
        else:
            device = (
                "cuda"
                if cfg["embedding"]["use_gpu_if_available"]
                and torch.cuda.is_available()
                else "cpu"
            )
            log.info(
                "loading SentenceTransformer %s on %s",
                cfg["embedding"]["model"],
                device,
            )
            self.model = SentenceTransformer(cfg["embedding"]["model"], device=device)

    def retrieve(self, profile: PatientConcernProfile) -> RankedDocumentSet:
        sub_queries = decompose_profile(profile)
        log.info("decomposed profile into %d sub-queries", len(sub_queries))

        embs = embed_queries(self.model, sub_queries)
        per_query_seeds = retrieve_seeds(self.coll, embs, top_k=self.top_k)
        per_query_seeds = expand_neighborhood(per_query_seeds)

        candidates = _aggregate_to_documents(per_query_seeds, self.parsed_dir)
        log.info("unique candidate documents after aggregation: %d", len(candidates))

        ranked = rerank(candidates, sub_queries, profile, self.weights, self.final_n)
        log.info("returning %d ranked documents", len(ranked))

        return RankedDocumentSet(
            sub_queries=sub_queries,
            documents=ranked,
            rerank_weights=self.weights,
            top_k_chunks_per_query=self.top_k,
            final_n_documents=self.final_n,
            expansion_used="stub",
        )


# --------------------------------------------------------------------------
# Trace rendering / CLI
# --------------------------------------------------------------------------


def _print_trace(rds: RankedDocumentSet) -> None:
    console.rule("[bold]Sub-queries[/bold]")
    sq_tbl = Table()
    sq_tbl.add_column("#", justify="right")
    sq_tbl.add_column("source")
    sq_tbl.add_column("addresses")
    sq_tbl.add_column("query (truncated)")
    for i, sq in enumerate(rds.sub_queries):
        sq_tbl.add_row(
            str(i),
            sq.source,
            sq.addresses or "—",
            sq.text[:90] + ("..." if len(sq.text) > 90 else ""),
        )
    console.print(sq_tbl)

    console.rule("[bold]Final ranked documents[/bold]")
    tbl = Table(show_lines=False)
    tbl.add_column("rank", justify="right")
    tbl.add_column("PMID")
    tbl.add_column("year")
    tbl.add_column("journal", overflow="fold")
    tbl.add_column("sem", justify="right")
    tbl.add_column("rec", justify="right")
    tbl.add_column("aut", justify="right")
    tbl.add_column("cov", justify="right")
    tbl.add_column("total", justify="right")
    tbl.add_column("covers")
    tbl.add_column("title (truncated)", overflow="fold")
    for i, d in enumerate(rds.documents):
        tbl.add_row(
            str(i + 1),
            d.pmid,
            str(d.pub_year or "—"),
            (d.journal or "")[:30],
            f"{d.semantic_similarity:.3f}",
            f"{d.recency_score:.2f}",
            f"{d.authority_score:.2f}",
            f"{d.coverage_bonus:.2f}",
            f"{d.total_score:.3f}",
            ",".join(str(s.replace("sub_query[", "").rstrip("]")) for s in d.addresses_concerns),
            (d.title or "")[:60],
        )
    console.print(tbl)


def _load_profile(path: Path) -> PatientConcernProfile:
    return PatientConcernProfile.model_validate_json(path.read_text(encoding="utf-8"))


def _demo_profile() -> PatientConcernProfile:
    """A small profile that exercises Phase 8 without depending on the
    user's stub transcripts. Mirrors the Phase 7 demo scenario."""
    from clinicomm.schemas import EmotionalCue, Problem, RedFlag

    return PatientConcernProfile(
        problems=[
            Problem(
                label="fatigue",
                onset="about 1 month ago",
                severity="7/10",
                timing="daily, worse in the afternoons",
                associated_symptoms=["unintentional weight loss ~12 lb"],
                interventions_tried=[],
                status="worsening",
            ),
            Problem(
                label="unintentional weight loss",
                onset="about 1 month ago",
                severity="~12 lb",
                timing="past month",
                associated_symptoms=["fatigue"],
                interventions_tried=[],
                status="worsening",
            ),
            Problem(
                label="morning headache",
                onset="past few weeks",
                severity="dull, ~4/10",
                timing="most mornings",
                associated_symptoms=[],
                interventions_tried=["ibuprofen PRN"],
                status="stable",
            ),
        ],
        medications=["lisinopril 10 mg daily", "ibuprofen PRN for headaches"],
        allergies=["NKDA"],
        relevant_history=["father with colon cancer at age 55"],
        patient_goals=[
            "find out what's going on",
            "keep working",
            "feel safe again",
        ],
        emotional_cues=[
            EmotionalCue(
                cue="fear",
                evidence_quote="My wife is convinced it's cancer and honestly I am too",
            ),
            EmotionalCue(
                cue="worry",
                evidence_quote="I just want to know what's going on",
            ),
        ],
        red_flags=[
            RedFlag(
                flag="unexplained weight loss",
                evidence="I've lost about 12 pounds without trying",
            )
        ],
        unknowns=[],
        turn_count=4,
        completion_status="ready_for_handoff",
    )


def main() -> None:
    p = argparse.ArgumentParser(prog="clinicomm.modules.m2_retrieval")
    p.add_argument("--config", default="config/pipeline.yaml")
    src = p.add_mutually_exclusive_group(required=False)
    src.add_argument(
        "--demo",
        action="store_true",
        help="Use a built-in demo profile (mirrors Phase 7 demo).",
    )
    src.add_argument(
        "--profile",
        type=Path,
        help="Path to a PatientConcernProfile JSON (e.g. saved from Module I).",
    )
    p.add_argument(
        "--save",
        type=Path,
        help="Write the RankedDocumentSet JSON here.",
    )
    p.add_argument(
        "--show-authority",
        action="store_true",
        help="Print the 30-journal authority table and exit.",
    )
    args = p.parse_args()

    cfg = load_config(args.config)
    log_path = setup_logging(
        phase="phase08_retrieval",
        level=cfg.get("logging", {}).get("level", "INFO"),
        logs_dir=cfg["paths"]["logs"],
    )
    log.info("Logging to %s", log_path)

    if args.show_authority:
        tbl = Table(title="Authority table (starter; edit clinicomm/modules/_authority.py)")
        tbl.add_column("journal")
        tbl.add_column("score", justify="right")
        for j, s in listed_canonical_journals():
            tbl.add_row(j, f"{s:.2f}")
        console.print(tbl)
        console.print(f"[dim]({len(listed_canonical_journals())} canonical journals)[/dim]")
        return

    if args.profile:
        profile = _load_profile(args.profile)
        scenario = args.profile.stem
    else:
        # Default to --demo.
        profile = _demo_profile()
        scenario = "demo_canned_profile"
        log.info("No --profile given; using built-in demo profile.")

    retriever = Retriever(cfg)
    rds = retriever.retrieve(profile)
    _print_trace(rds)

    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(rds.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"\nSaved ranked document set to [cyan]{args.save}[/cyan]")
    else:
        # Always persist a timestamped trace for downstream phases.
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = Path(cfg["paths"]["logs"]) / f"m2_retrieval_{scenario}_{ts}.json"
        out.write_text(rds.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"\nSaved ranked document set to [cyan]{out}[/cyan]")


if __name__ == "__main__":
    main()
