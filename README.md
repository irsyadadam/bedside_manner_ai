You are building an end-to-end research prototype for a manuscript on
patient-centered clinical communication via LLMs. Four modules:
  I.   Initial Screening Conversation (structured multi-turn intake)
  II.  Clinical Guideline Lookup (retrieval over PubMed corpus)
  III. Graph-RAG Reasoning Engine (assertion extraction + clustering)
  IV.  Patient-centric Empathy-aware Response

This is a research prototype, not production. Prioritize reproducibility,
provenance, clean intermediate artifacts, and runnable demos over polish.
Abstracts-only corpus (no full text).

REPO LAYOUT
Create everything under /workspace/clinicomm/:
  /workspace/clinicomm/
    config/                  # pipeline.yaml, prompts/*.txt
    clinicomm/               # python package
      ingest/                # PubMed ingest
      parse/                 # XML → normalized JSON
      embed/                 # chunking + embedding
      index/                 # Chroma wrapper
      modules/
        m1_intake.py         # Module I
        m2_retrieval.py      # Module II
        m3_reasoning.py      # Module III
        m4_response.py       # Module IV
      manuscript/            # styling/utilities for artifact generation
      schemas.py             # pydantic models for all artifacts
      pipeline.py            # orchestrator: m1 → m2 → m3 → m4
    db/
      raw/                   # raw EFetch XML per PMID
      parsed/                # normalized JSON per document
      chunks/                # chunked text + metadata
      manifest.jsonl
    index/chroma/            # persistent vector index
    demos/synthetic_patients/  # transcript JSONs (I will fill in)
    manuscript/
      figures_ascii/         # ASCII figure drafts + .notes.md sidecars
      tables_draft/          # auto-generated .md + .tex tables
      traces/                # full pipeline runs on synthetic patients
    logs/
    scripts/                 # CLI entrypoints
    README.md

DOMAIN
Primary care general intake for adult patients. Corpus targets clinical
guidelines, systematic reviews, and meta-analyses covering common
presenting complaints in adult primary care and patient communication
best practices.

PUBMED QUERY (use exactly this string with E-utilities ESearch)
(
  (
    "Primary Health Care"[MeSH] OR
    "General Practice"[MeSH] OR
    "Physicians, Primary Care"[MeSH] OR
    "Family Practice"[MeSH]
  )
  OR
  (
    "Physician-Patient Relations"[MeSH] OR
    "Communication"[MeSH] OR
    "Patient-Centered Care"[MeSH] OR
    "Empathy"[MeSH]
  )
  OR
  (
    "Symptom Assessment"[MeSH] OR
    "Medical History Taking"[MeSH] OR
    "Diagnosis, Differential"[MeSH:NoExp]
  )
)
AND (
  "Practice Guideline"[pt] OR
  "Guideline"[pt] OR
  "Systematic Review"[pt] OR
  "Meta-Analysis"[pt]
)
AND ("2018/01/01"[PDAT] : "2026/12/31"[PDAT])
AND English[lang]
AND humans[mesh]
AND ("adult"[MeSH] OR "middle aged"[MeSH] OR "aged"[MeSH])

PHASES (stop and report after each — do not proceed without my confirmation)

PHASE 1 — Environment + config
- Set up uv environment with: requests, biopython, lxml, beautifulsoup4,
  sentence-transformers, chromadb, pydantic>=2, tqdm, tenacity, pyyaml,
  anthropic, networkx, rich.
- Write config/pipeline.yaml: PubMed query (above), NCBI_API_KEY env
  var, rate limit (10/s if key else 3), embedding model
  (BAAI/bge-large-en-v1.5), chunk size (400 tokens — abstracts are
  short, smaller chunks help), overlap (50), Anthropic model
  (claude-opus-4-7), top_k retrieval (20), graph expansion hops (1).
- Write config/prompts/*.txt placeholders for: intake_system,
  intake_completion_check, assertion_extraction, conflict_resolution,
  response_generation. Leave clear TODO markers — I'll write the
  actual prompts. response_generation.txt must include explicit
  DIRECTIVES_START / DIRECTIVES_END markers around the NURSE +
  Four Habits directives section (Phase 12 reads between these).
- Write README.md with phase list and run instructions.
- STOP. Show config + README + prompt file list.

PHASE 2 — PubMed discovery (ESearch + ESummary)
- ESearch with the configured query, paginated retmax=10000, using
  WebEnv/QueryKey history.
- Print total count. If >10000, STOP and ask before proceeding.
- ESummary in batches of 200 for metadata. Write to db/discovery.jsonl.
- STOP. Show total count, date distribution, top 10 journals, 10-row
  sample of titles.

PHASE 3 — Full record fetch (EFetch)
- EFetch XML for each PMID, save to db/raw/<PMID>.xml.
- Respect rate limits. tenacity retry on 429/500/timeout with
  exponential backoff.
- Parse into normalized JSON with schema:
    pmid, doi, title, abstract (structured if available — preserve
    section labels like BACKGROUND/METHODS/RESULTS/CONCLUSIONS),
    journal, pub_date, pub_types, mesh_headings (descriptor +
    qualifiers + major_topic flag), authors, issuing_body (parse
    from collective author or affiliation where guideline).
- Drop records with no abstract. Log dropped count.
- Write db/parsed/<PMID>.json.
- STOP. Show 3 examples + retention rate.

PHASE 4 — Chunking
- Abstracts only. If structured abstract, one chunk per labeled
  section. If unstructured, sliding window 400 tokens / 50 overlap.
- Chunk schema: chunk_id, pmid, section_label, position, text,
  token_count.
- Write db/chunks/<PMID>.jsonl.
- STOP. Show chunk count distribution + examples from both structured
  and unstructured.

PHASE 5 — Embedding + index
- Load BAAI/bge-large-en-v1.5. Use GPU if available, batch 64.
- Build Chroma persistent collection at index/chroma/ with chunk
  text, embedding, and full metadata.
- Write scripts/sanity_query.py running 5 hard-coded queries:
    "patient with fatigue and weight loss"
    "managing hypertension in primary care"
    "communicating bad news to patients"
    "screening for depression adult"
    "evaluating chronic cough"
  Print top-5 results per query with metadata. Persist the raw
  results to logs/sanity_query_<timestamp>.json (Phase 12 may
  use this for an appendix table).
- STOP. Show sanity-query output. I will judge retrieval quality.

PHASE 6 — Manifest + corpus summary
- Write db/manifest.jsonl with full per-doc provenance.
- Append to README: corpus size, date range, pub type breakdown,
  top 20 journals, MeSH frequency, embedding model, query used.
- STOP. Show summary.

PHASE 7 — Module I: Intake
- Implement clinicomm/modules/m1_intake.py:
  - PatientConcernProfile pydantic model with: problems (list of
    {label, onset, severity, timing, associated_symptoms,
    interventions_tried, status}), medications, allergies,
    relevant_history, patient_goals, emotional_cues (list of
    {cue, evidence_quote}), red_flags (list of {flag, evidence}),
    unknowns (list of fields needing follow-up), turn_count,
    completion_status.
  - IntakeAgent class wrapping Anthropic client with:
    - update_profile(profile, user_turn) → updated profile
      (one LLM call with intake_system prompt + current profile +
      latest turn; returns structured JSON).
    - next_prompt(profile) → next templated question or None if
      complete. Question selection logic: prioritize problems with
      most unknowns; check red-flag screen done; check minimum
      descriptors per problem (onset + severity + timing minimum).
    - is_complete(profile) → bool based on completion criteria.
  - run_intake(transcript) function taking a list of user turns
    and returning the final profile (for offline testing on
    synthetic transcripts).
- Write demos/synthetic_patients/ with 3 hand-written patient
  transcript JSON stubs (multi-turn, varied complaints). I will
  fill these in — leave TODO markers, do not auto-fill.
- STOP. Show the schema, the agent skeleton, and a dry-run
  trace on one stub transcript using a placeholder LLM mock.

PHASE 8 — Module II: Retrieval
- Implement clinicomm/modules/m2_retrieval.py:
  - decompose_profile(profile) → list of sub-queries (one per
    problem, one per goal, one global context query).
  - embed_queries(sub_queries) using same model as index.
  - retrieve_seeds(query_embeddings, top_k=20) via Chroma.
  - For v0: skip graph expansion (no document graph built yet).
    Add a stub function expand_neighborhood(seeds) → seeds that
    we will replace later. Document this clearly in the code.
  - rerank(candidates, profile) by:
      semantic_similarity * 0.5
      + recency_score (linear decay over years) * 0.2
      + authority_score (lookup table of high-authority journals
        — provide a starter list of 30 journals) * 0.2
      + coverage_bonus (rewards docs that match concerns not yet
        covered by higher-ranked docs) * 0.1
  - Return RankedDocumentSet (pydantic model).
- STOP. Show a retrieval trace on the stub profile.

PHASE 9 — Module III: Graph-RAG Reasoning (abstracts adaptation)
- Implement clinicomm/modules/m3_reasoning.py:
  - For each retrieved document, one LLM call with
    assertion_extraction prompt → list of ClinicalAssertion
    (pydantic: assertion_text, assertion_type [recommendation /
    contraindication / monitoring / communication_directive /
    finding], confidence, source_pmid, source_chunk_id,
    addresses_concern [reference to profile element]).
  - Cluster assertions across documents: group by
    (assertion_type, addresses_concern, semantic similarity of
    assertion_text using same embedding model, threshold 0.75).
  - For each cluster: if all assertions agree → mark convergent,
    high confidence. If disagreement → mark divergent, run
    conflict_resolution LLM call to pick primary (recency +
    authority) and retain alternatives.
  - Output: StructuredContextArtifact (pydantic) with ordered
    clusters, each with primary_assertion, supporting_pmids,
    alternative_assertions, confidence, addresses_concern.
- Note in code comments: abstracts-only means assertion granularity
  is coarser; flag this as a limitation for the manuscript.
- STOP. Show a reasoning trace on the stub profile + retrieval set.

PHASE 10 — Module IV: Response generation
- Implement clinicomm/modules/m4_response.py:
  - Single LLM call with response_generation prompt taking:
    PatientConcernProfile, StructuredContextArtifact,
    communication directives (NURSE + Four Habits as bulleted
    rules in the prompt, between DIRECTIVES_START / DIRECTIVES_END
    markers — Phase 12 reads these).
  - Structured output: PatientResponse pydantic with sections
    (acknowledgment, clinical_information_per_concern, next_steps,
    teach_back_prompt, follow_up_invitation), and provenance
    (per claim: list of supporting cluster_ids → pmids).
  - Implement a plain-language substitution pass: regex-based
    glossary lookup (provide a starter glossary of 30 common
    medical terms → plain English) applied post-generation.
  - Emotional cue handling: if profile.emotional_cues non-empty,
    the prompt includes the NURSE empathy template.
- STOP. Show a response trace end-to-end on the stub patient.

PHASE 11 — Orchestrator + demo
- Implement clinicomm/pipeline.py running the full pipeline
  on a synthetic transcript file → final response with full
  provenance trace.
- Write scripts/run_demo.py that takes a transcript JSON path
  and writes a Markdown report containing: the transcript, the
  final profile, the ranked document set, the structured context
  artifact, the final response, and a provenance appendix.
- Run on all 3 synthetic transcripts (once I've filled them in).
  If transcripts are still stubs, run on a single hard-coded
  example transcript embedded in scripts/run_demo.py so we have
  at least one real pipeline trace available for Phase 12.
- STOP. Show the Markdown reports.

PHASE 12 — Manuscript artifact preview (ASCII figures + auto-gen tables)
- Goal: produce ASCII sketches of conceptual figures (for me to
  polish in Figma/TikZ) and auto-generated tables/qualitative traces
  from real pipeline output. No matplotlib figures in this pass.

- ASCII figure drafts — write each as a .txt file with a header
  comment explaining what the figure communicates and where it
  appears in the manuscript. Use box-drawing characters
  (├ │ └ ─ ┐ etc.) or plain ASCII (+--+ | |), whichever renders
  structure most clearly. ~80-column width. Label every arrow
  and box.

  Files to produce in manuscript/figures_ascii/:

    fig1_architecture.txt
      Horizontal pipeline: Module I → II → III → IV. On each arrow
      label the artifact passed:
        raw dialogue → PatientConcernProfile → RankedDocumentSet
        → StructuredContextArtifact → PatientResponse
      Each module box: 2–3 lines describing its role.
      Include a "Literature DB" cylinder feeding into Module II.

    fig2_intake_state_machine.txt
      States: AWAITING_TURN, UPDATING_PROFILE, CHECKING_COMPLETION,
      SELECTING_NEXT_PROMPT, EMITTING_PROFILE. Labeled transitions
      (e.g., "completion criteria met"). Show templated prompt
      branching as a sub-decision.

    fig3_schema_illustration.txt
      Tree/indented view of PatientConcernProfile populated with
      a concrete synthetic example (fatigue + weight loss patient).
      Nested fields: problems[] with attributes, emotional_cues,
      red_flags, unknowns. Realistic enough to appear verbatim
      in the manuscript.

    fig4_retrieval.txt
      Two-stage retrieval diagram:
        [query embeddings] → [ANN search] → [seed docs (5 boxes)]
          → [graph expansion 1-hop] → [expanded set (8 boxes)]
          → [reranker] → [ranked output]
      Mark graph-expansion stage with
      "(v0: stubbed — flat retrieval)" so the figure is honest
      about current state. Show edge type legend:
      cites / supersedes / shares-descriptor.

    fig5_reasoning.txt
      Assertion extraction → clustering.
      Left: 3 retrieved docs, each with 2–3 extracted assertions
      (labeled assertion_type).
      Middle: clustering arrows grouping by concern + type.
      Right: 2 clusters — one convergent (3 docs agree), one
      divergent (2 docs disagree; primary chosen by
      recency+authority, alternative retained). Annotate the
      resolution rule visibly.

    fig6_end_to_end_trace.txt
      Two-column ASCII:
        Left: patient utterance from a synthetic transcript.
        Right: corresponding final response section, with inline
        markers showing which profile element it addresses,
        which assertion cluster it cites, and which NURSE element
        shaped the phrasing.
      Use 3–4 utterance/response pairs from one synthetic patient.

  For each ASCII file also write a sibling .notes.md with:
    - One-paragraph caption draft for the manuscript.
    - Design decisions Claude made that I may want to change.
    - Suggestions for what to emphasize when polishing in Figma/TikZ.

- Auto-generated tables (real artifacts from pipeline data):

    manuscript/tables_draft/table1_corpus.md and .tex
      Read db/manifest.jsonl + db/parsed/*.json.
      Rows: total docs, date range, structured-abstract %, mean
      abstract length, pub type counts, top-10 journals, top-10
      MeSH descriptors. Booktabs format for .tex.

    manuscript/tables_draft/table2_directives.md and .tex
      Read config/prompts/response_generation.txt — extract the
      section between DIRECTIVES_START / DIRECTIVES_END markers.
      Columns: framework (NURSE | Four Habits), element, trigger
      condition, generation rule.

    manuscript/tables_draft/table3_retrieval_sanity.md and .tex
      Read logs/sanity_query_<latest>.json (from Phase 5).
      5 queries × top-5 PMIDs with title + similarity score.
      Marked as appendix table.

- Qualitative traces (real pipeline output, not ASCII):

    manuscript/traces/trace_<patient_id>.md
      For each synthetic patient with a filled-in transcript, run
      full pipeline and emit:
        - Transcript (dialogue format)
        - Final PatientConcernProfile (pretty-printed YAML)
        - Top-5 retrieved documents (PMID, title, journal, score)
        - StructuredContextArtifact (clusters with provenance)
        - Final PatientResponse with inline [PMID] citation markers
        - Annotation appendix: which NURSE/Four Habits element
          triggered which phrasing in the response
      If a transcript is still a stub, skip it and note in the
      console output which patient IDs were skipped.

- Write scripts/gen_manuscript_artifacts.py that runs everything
  in this phase. ASCII files are written directly by the script
  (they are deterministic templates, not LLM output — write them
  as Python string literals so they're reproducible). Tables and
  traces are generated by reading pipeline state.

- Append to README a "Manuscript artifacts" section:
    - ASCII figures in figures_ascii/ are starting points — to be
      polished in Figma/TikZ.
    - Tables in tables_draft/ are auto-generated from pipeline
      state; re-run gen_manuscript_artifacts.py to refresh.
    - Traces in traces/ are full pipeline runs on synthetic
      patients.

- STOP. Show the file listing, plus the contents of
  fig1_architecture.txt and table1_corpus.md as a sample.

DO NOT
- Do not build a web UI or interactive chat loop. Offline pipeline
  only — read transcript JSON, write Markdown report.
- Do not infer the PubMed query, domain, or inclusion criteria from
  context. Use exactly what's in config/pipeline.yaml.
- Do not write the LLM prompts in config/prompts/ — leave TODO
  stubs. I will write them after seeing the module structure.
- Do not auto-fill the synthetic patient transcripts. Leave stubs.
- Do not implement the document graph for Module II in this pass —
  v0 uses flat vector retrieval. Leave the expand_neighborhood stub.
- Do not parallelize NCBI requests beyond the configured rate limit.
- Do not add evaluation harnesses, unit test suites beyond smoke
  tests, or fancy logging frameworks.
- Do not use matplotlib in Phase 12. ASCII figures only; tables as
  Markdown + LaTeX.
- Do not auto-generate the system architecture, state machine, or
  schema as rendered images — ASCII drafts only, I will polish.
- Do not fabricate corpus stats — read from real pipeline output.
  If pipeline output is missing for a table, skip it and note it
  in the console output rather than inventing numbers.
- Do not skip STOP checkpoints.

CONVENTIONS
- All scripts runnable as `python -m clinicomm.<module>` with a
  --dry-run flag.
- Log to stdout + logs/<phase>_<timestamp>.log.
- All file writes idempotent — re-running resumes, doesn't duplicate.
- pydantic v2 models for all schemas, exported from
  clinicomm/schemas.py.
- Anthropic SDK calls use claude-opus-4-7 with explicit max_tokens
  and structured output via tool use where appropriate.

Start with Phase 1. Stop after each phase and wait for my approval
before continuing.
