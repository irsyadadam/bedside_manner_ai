# fig4_retrieval — caption + design notes

## Caption draft

> **Figure 4. Module II — retrieval pipeline.** The patient concern
> profile is decomposed deterministically into N sub-queries (one per
> problem, one per goal, and one global context query), each encoded
> with BAAI/bge-large-en-v1.5 (1024-d, L2-normalized) and used for a
> top-k = 20 cosine search against a persistent Chroma index of 6,880
> abstract chunks. The graph-expansion stage is **stubbed in v0**
> (flat retrieval; planned edge types: `cites`, `supersedes`,
> `shares-descriptor`). Aggregated to the document level, candidates
> are reranked by a greedy maximal-marginal-relevance pass with weights
> 0.5·semantic + 0.2·recency + 0.2·authority + 0.1·coverage, returning
> the top-20 documents as the sole input to Module III.

## Design decisions Claude made (review me)

- The graph-expansion box stays in the diagram even though it is a
  no-op, because the surrounding architecture *expects* it: future
  versions slot the real expansion in without redrawing anything.
  The "STUBBED" callout is non-negotiable for honesty in v0.
- Listed the four rerank weights inline because they're the only place
  in the system where numerical hyperparameters are exposed to the
  reader. Burying them in a separate equation would dilute the figure.
- Showed seed-chunk boxes (c-1..c-5) twice (before and after expansion)
  rather than abstracting them away — the identity-mapping is the point.

## Suggestions when polishing in Figma / TikZ

- Gray out the expansion box and the edge-legend with a "v0 stub"
  label; that's the honest visual signal.
- Render the rerank weights as a horizontal stacked bar (50/20/20/10)
  somewhere next to that block — that helps the reader retain the
  weighting story from a single glance.
- The "candidate documents (~80 for p001)" number is real (count it
  from the saved RankedDocumentSet JSON); keep the figure
  parameterized so the manuscript can reflect the exact number for
  the chosen demo patient.
