# fig5_reasoning — caption + design notes

## Caption draft

> **Figure 5. Module III — assertion extraction and clustering.**
> Each retrieved document yields a small number of `ClinicalAssertion`
> records via one LLM call (left column). Assertions are grouped by
> `(type, addresses_concern)` and merged into clusters when the cosine
> similarity of their text embeddings exceeds 0.75 (BAAI/bge-large-en-
> v1.5; single-link union-find). Convergent clusters skip the LLM —
> the highest-confidence assertion is the primary by default. Divergent
> clusters trigger a `conflict_resolution` LLM call that picks a primary
> by recency, then authority, evidence strength, coverage, and finally
> confidence, retaining every non-primary assertion as an alternative
> with a retain-reason.

## Design decisions Claude made (review me)

- Used a hypertension example for the divergent cluster (2019 SR vs
  2025 guideline → target BP threshold change) because it's a
  well-known case where recency really does matter clinically.
- Used PHQ-9 for the convergent cluster because both abstracts give
  the same recommendation; clearer signal of "no LLM call needed".
- Annotated cluster boxes with the actual fields the runtime stores
  (`supporting_pmids`, `alternative_assertions[].retain_reason`) so
  the figure doubles as documentation for the schema.

## Suggestions when polishing in Figma / TikZ

- Render the cluster boxes in two colors (green=convergent,
  amber=divergent) — instantly readable.
- For the divergent cluster, put the resolution rule chain
  (recency → authority → evidence → coverage → confidence) along the
  resolution arrow as labeled tick marks, indicating where the chain
  stopped.
- Add a small "0.75" pill annotation on the clustering arrow to keep
  the threshold visible.
