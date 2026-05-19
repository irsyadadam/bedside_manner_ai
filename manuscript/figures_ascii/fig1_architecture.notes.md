# fig1_architecture — caption + design notes

## Caption draft (≈ one paragraph for the manuscript)

> **Figure 1. clinicomm system overview.** Patient utterances enter a
> four-module pipeline. Module I (Intake) extracts a structured
> `PatientConcernProfile` via repeated LLM calls, using templated (non-LLM)
> follow-up questions and an explicit red-flag safety screen. The
> finalized profile is the sole input to Module II (Retrieval), which
> decomposes it into sub-queries, retrieves top-k chunks from a Chroma
> vector index over abstracts (BAAI/bge-large-en-v1.5), and reranks
> documents by a weighted sum of semantic similarity, recency, journal
> authority, and concern coverage. Module III (Reasoning) extracts
> ClinicalAssertions per document, clusters them by `(type, addresses_concern)`
> with a 0.75 cosine-similarity threshold, and resolves divergent
> clusters with a separate LLM call governed by recency / authority /
> evidence strength rules. Module IV (Response) makes a single LLM call,
> applies NURSE and Four-Habits directives, attaches per-claim
> provenance, and runs a plain-language glossary pass. Every
> intermediate artifact is persisted for audit.

## Design decisions Claude made (review me)

- Vertical orientation, not horizontal — chosen for 80-column page width
  and so the four modules form a clear top-to-bottom narrative the reader
  can follow without horizontal scrolling.
- The Literature DB is rendered to the right of Module II only, with a
  single bidirectional-feeling arrow, to avoid cluttering Modules I/III/IV
  with a feeder that they don't actually use.
- "Graph expansion STUBBED" is called out explicitly. Without that label
  the figure overpromises Module II's v0 capability.
- Sub-bullets inside each module box are 3–4 lines max. Anything more
  would belong in fig2 (state machine) or fig3 (schema).

## Suggestions when polishing in Figma / TikZ

- Color modules by phase (cool→warm) to imply the data-flow direction.
- Replace the labeled arrows with annotated edges showing the actual
  pydantic class name (`PatientConcernProfile`, `RankedDocumentSet`,
  `StructuredContextArtifact`, `PatientResponse`).
- Add a small "audit log" lane down the right side: each module writes
  to `logs/<phase>_<UTC>.log` — easy to depict, anchors the
  reproducibility claim.
- The "STUBBED" callout should become a small badge ("v0") rather than
  inline text, since the polished figure will outlive that limitation.
