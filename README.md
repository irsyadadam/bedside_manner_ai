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

================================================================================
REPRODUCE FROM SCRATCH (empty machine → working pipeline in ~10 min)
================================================================================

This repo contains source only — no PubMed XML, no Chroma index, no
model weights. Everything heavy is regenerated by the bootstrap script
below. A fresh clone is < 5 MB on disk; the working tree after
bootstrap is ≈ 200 MB (corpus + index) plus ~5 GB of HuggingFace cache.

Prerequisites
-------------
- Python 3.11
- uv          (https://docs.astral.sh/uv/  — `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Optional: NVIDIA GPU + driver supporting CUDA 12.4+
- Optional: NCBI API key (free at https://www.ncbi.nlm.nih.gov/account/settings/)
- Optional: HuggingFace token (free at https://huggingface.co/settings/tokens)

One-shot recipe
---------------
    git clone https://github.com/irsyadadam/bedside_manner_ai.git
    cd bedside_manner_ai
    cp .env.example .env       # then edit if you have NCBI_API_KEY / HF_TOKEN
    bash scripts/bootstrap.sh  # uv sync + Phases 2..6, ~10 min on a fresh machine

That gives you:
  - 1,779 PubMed records (db/discovery.jsonl)
  - 1,751 normalized abstracts (db/parsed/*.json)
  - 6,880 embedded chunks indexed in Chroma (index/chroma/)
  - db/manifest.jsonl with full per-doc provenance
  - README updated in-place with the corpus summary

Trying the four-module pipeline
-------------------------------
Mock (no GPU, instant, deterministic):
    uv run python scripts/run_demo.py --demo --all
    uv run python scripts/gen_manuscript_artifacts.py --demo

Real LLM (DeepSeek-R1-Distill-Qwen-14B via local vLLM):
    bash scripts/start_vllm_server.sh &                  # ~28 GB download first run
    uv run python scripts/run_demo.py --all \
        --max-reasoning-docs 5                           # ~5 min/transcript
                                                          # (Module III runs the
                                                          #  5 doc calls concurrently
                                                          #  via asyncio.gather)

Phase-12 evaluation artifacts (Tables 4–6, Figs 7–12)
-----------------------------------------------------
    uv run python scripts/eval_ablations.py --demo       # Tables 4 + 5
        # or --reuse-traces-from manuscript/traces_real (after real-LLM run)
    uv run python scripts/sensitivity_sweep.py           # Fig 9 + 12 data
    uv run python scripts/provenance_audit.py            # Table 6
    uv run python scripts/render_figures.py              # all SVG figures

Or, in one go (driver wraps all of the above):
    uv run python scripts/gen_manuscript_artifacts.py --demo

Resuming a partial bootstrap
----------------------------
Every phase is idempotent — re-running `bash scripts/bootstrap.sh`
skips whatever's already done. You can also run individual phases:

    uv run python -m clinicomm.ingest.discovery     # Phase 2
    uv run python -m clinicomm.ingest.efetch        # Phase 3
    uv run python -m clinicomm.embed.chunk          # Phase 4
    uv run python -m clinicomm.embed.build_index    # Phase 5
    uv run python -m clinicomm.ingest.manifest      # Phase 6
    uv run python scripts/sanity_query.py           # Phase 5b sanity check

What gets regenerated vs. what's in git
---------------------------------------
In git:    source, prompts, transcripts (drafted), figures, tables,
           example traces (.md + .json), pyproject + uv.lock
NOT in git: db/raw/ db/parsed/ db/chunks/ db/discovery.jsonl
           db/manifest.jsonl index/chroma/ .hf_cache/ .venv/ logs/
           (see .gitignore for the full list)

manuscript/ tree (what's where, for forkers)
--------------------------------------------
  manuscript/
    figures_ascii/     ASCII figure drafts (fig1..fig6) + .notes.md
                       sidecars — starting points for Figma/TikZ polish.
                       Deterministic; checked into git.
    figures/           Publication-style SVG figures (fig7..fig12)
                       rendered by scripts/render_figures.py via seaborn.
                       Vector; safe to drop into a LaTeX paper.
    tables_draft/      Auto-generated tables (.md + .tex, booktabs).
                       table1_corpus           - corpus stats from manifest
                       table2_directives       - NURSE+Four Habits parsed
                                                 from response_generation.txt
                       table3_retrieval_sanity - top-5 per sanity query
                       table4_pipeline_vs_baseline
                       table5_module_ablation  - 4-condition mean metrics
                       table6_provenance_audit - mechanical citation check
    traces/            Mock-mode pipeline traces (md + json + baseline +
                       side-by-side comparison) per synthetic patient.
    traces_real/       Real-LLM pipeline traces (DeepSeek-R1-Distill-Qwen-14B).
                       Generated by `scripts/run_demo.py --all`.
    data/              Raw JSON sidecars feeding the figures (ablation
                       metrics, sensitivity sweeps, provenance audit).

If something is broken
----------------------
The full audit trail is in logs/<phase>_<UTC>.log — every phase
writes one. Each module also supports --dry-run.

================================================================================
OPERATOR NOTES (added by Phase 1)
================================================================================

LOCATION
  This repo lives at the current working directory (./), not /workspace/.
  All paths in the spec above are interpreted relative to the repo root.

PHASE LIST (current state — all phases complete)

  [x] Phase  1 — Environment + config
  [x] Phase  2 — PubMed discovery (ESearch + ESummary)
  [x] Phase  3 — Full record fetch (EFetch) + normalize
  [x] Phase  4 — Chunking
  [x] Phase  5 — Embedding + Chroma index + sanity queries
  [x] Phase  6 — Manifest + corpus summary
  [x] Phase  7 — Module I: Intake
  [x] Phase  8 — Module II: Retrieval
  [x] Phase  9 — Module III: Graph-RAG Reasoning
  [x] Phase 10 — Module IV: Response generation
  [x] Phase 11 — Orchestrator + demo
  [x] Phase 12 — Manuscript artifact preview (ASCII figs + tables
                 + baseline-LLM side-by-side comparison)

RUN INSTRUCTIONS

  Prerequisites
    - Python 3.11 (managed by uv).
    - uv installed (https://docs.astral.sh/uv/).
    - NVIDIA GPU with driver supporting CUDA 12.4+ (verified on
      RTX 6000 Ada, 48 GB, driver 550.x).
    - Environment variables (optional):
        NCBI_API_KEY        # raises PubMed rate limit 3/s -> 10/s

  Install
    uv sync
    # First run downloads ~5 GB of CUDA wheels (torch+cu124, xformers, vllm).

  LLM backend (free, local)
    Modules I, III, IV call a local vLLM server speaking the OpenAI
    chat-completions API. Default model: DeepSeek-R1-Distill-Qwen-14B.
    Speedups enabled by default: flash attention (FLASH_ATTN), prefix
    caching, chunked prefill, bf16.

    Start the server (foreground):
      bash scripts/start_vllm_server.sh

    Or in the background (logs to logs/vllm.log):
      nohup bash scripts/start_vllm_server.sh > logs/vllm.log 2>&1 &

    First start downloads the model into .hf_cache/ (~28 GB for the
    14B distill at bf16). Subsequent starts reuse the cache.

    Verify it's up:
      curl http://localhost:8000/v1/models

    Model can be overridden without editing config:
      VLLM_MODEL=deepseek-ai/DeepSeek-R1-Distill-Qwen-32B \
        bash scripts/start_vllm_server.sh
    (32B needs AWQ/FP8 quantization to fit in 48 GB — see
    pipeline.yaml notes.)

  Smoke test (Phase 1 only)
    uv run python -c "import clinicomm; print(clinicomm.__version__)"
    uv run python -c "import torch; assert torch.cuda.is_available(); \
                       print('GPU:', torch.cuda.get_device_name(0))"

  Per-phase entrypoints (filled in as phases are implemented)
    Phase 2:  uv run python -m clinicomm.ingest.discovery   --dry-run
    Phase 3:  uv run python -m clinicomm.ingest.efetch      --dry-run
    Phase 4:  uv run python -m clinicomm.embed.chunk        --dry-run
    Phase 5:  uv run python -m clinicomm.embed.build_index  --dry-run
              uv run python scripts/sanity_query.py
    Phase 6:  uv run python -m clinicomm.ingest.manifest
    Phase 11: uv run python scripts/run_demo.py demos/synthetic_patients/<id>.json
    Phase 12: uv run python scripts/gen_manuscript_artifacts.py

  Logs
    Each phase writes to stdout AND logs/<phase>_<UTC-timestamp>.log.

REPO STATE AFTER PHASE 1

  config/
    pipeline.yaml                       # canonical config (query, models, paths,
                                        # LLM = local vLLM + DeepSeek distill)
    prompts/
      intake_system.txt                 # TODO placeholder
      intake_completion_check.txt       # TODO placeholder
      assertion_extraction.txt          # TODO placeholder
      conflict_resolution.txt           # TODO placeholder
      response_generation.txt           # TODO body + populated
                                        # DIRECTIVES_START/END block
                                        # (NURSE + Four Habits)
  scripts/
    start_vllm_server.sh                # local LLM server w/ flash-attn
                                        # + prefix caching + chunked prefill
  clinicomm/                            # python package (empty submodules)
    ingest/ parse/ embed/ index/ modules/ manuscript/
  db/ raw/ parsed/ chunks/              # empty; populated phases 2-4
  index/chroma/                         # empty; populated phase 5
  demos/synthetic_patients/             # empty; user-authored phase 7+
  manuscript/figures_ascii/ tables_draft/ traces/   # empty; phase 12
  logs/                                 # phase logs accumulate here
  scripts/                              # CLI entrypoints (phases 5, 11, 12)
  pyproject.toml                        # deps pinned via uv
  uv.lock

CONVENTIONS RECAP (mirrors spec § CONVENTIONS)
  - All scripts runnable as `python -m clinicomm.<module>` (or via
    `uv run python -m ...`) and support --dry-run.
  - File writes are idempotent — re-running resumes, never duplicates.
  - All schemas live in clinicomm/schemas.py (pydantic v2).
  - LLM calls go through the local vLLM OpenAI-compatible endpoint
    (default: deepseek-ai/DeepSeek-R1-Distill-Qwen-14B). All inference
    runs locally on the GPU — no API costs. Modules use explicit
    max_tokens and request structured JSON via vLLM's guided-decoding
    (xgrammar) where appropriate.
  - This deviates from the original spec (§ ENVIRONMENT and § Phase 1
    say `anthropic` / `claude-opus-4-7`). The deviation is intentional
    and approved (see "make everything free" decision); the rest of
    the spec is honored.

================================================================================
CORPUS SUMMARY (Phase 6, auto-generated — refreshed by
`uv run python -m clinicomm.ingest.manifest`)
================================================================================

<!-- BEGIN AUTO-CORPUS-SUMMARY -->

_Last refreshed: 2026-05-19T20:52:13+00:00_

### Pipeline state
```
  Discovery PMIDs (Phase 2):   1779
  Raw XML records (Phase 3):   1779
  Parsed documents (Phase 3):  1751
  Total chunks (Phase 4):      6880
  Indexed vectors (Phase 5):   6880
  Structured abstracts:        1277 (72.9%)
  Records with DOI:            1738
  Records with issuing_body:   49 (guideline collective authors)
  Total chunk tokens:          672,953
```

### Date range
```
  Earliest year: 2018
  Latest year:   2026
  Median year:   2022

  2018:  229  ##################################
  2019:  205  ###############################
  2020:  263  ########################################
  2021:  232  ###################################
  2022:  200  ##############################
  2023:  202  ##############################
  2024:  151  ######################
  2025:  195  #############################
  2026:   74  ###########
```

### Pub-type breakdown
```
  Journal Article                                   1749
  Systematic Review                                 1513
  Meta-Analysis                                      536
  Research Support, Non-U.S. Gov't                   486
  Practice Guideline                                  88
  Review                                              81
  Case Reports                                        80
  Research Support, N.I.H., Extramural                72
  Comparative Study                                   17
  Research Support, U.S. Gov't, P.H.S.                14
  Research Support, U.S. Gov't, Non-P.H.S.            12
  Network Meta-Analysis                                7
  Consensus Statement                                  6
  Video-Audio Media                                    4
  Validation Study                                     4
  Guideline                                            2
  Randomized Controlled Trial                          2
  Multicenter Study                                    2
  Research Support, N.I.H., Intramural                 2
  Letter                                               2
  Scoping Review                                       2
  Retracted Publication                                2
  Evaluation Study                                     1
  Twin Study                                           1
  Historical Article                                   1
  Research Support, American Recovery and Reinvestment Act     1
```

### Top 20 journals
```
  The Cochrane database of systematic reviews                        40
  PloS one                                                           39
  BMJ open                                                           32
  Journal of advanced nursing                                        28
  BMC geriatrics                                                     27
  Journal of medical Internet research                               21
  International journal of environmental research and public healt   21
  JAMA                                                               19
  Patient education and counseling                                   18
  Medicine                                                           17
  BMC public health                                                  16
  BMC health services research                                       16
  Age and ageing                                                     15
  Journal of clinical nursing                                        14
  Frontiers in public health                                         14
  The Gerontologist                                                  13
  Scandinavian journal of caring sciences                            13
  International journal of nursing studies                           13
  Family practice                                                    11
  JAMA network open                                                  11
```

### Top 30 MeSH descriptors
```
  Humans                                            1751
  Adult                                             1098
  Female                                             722
  Aged                                               681
  Male                                               623
  Middle Aged                                        452
  Adolescent                                         318
  Young Adult                                        282
  Child                                              278
  Primary Health Care                                240
  Patient Discharge                                  221
  Aged, 80 and over                                  220
  Diagnosis, Differential                            220
  Communication                                      210
  Quality of Life                                    165
  Randomized Controlled Trials as Topic              132
  Language                                           110
  Qualitative Research                               104
  Health Literacy                                    101
  Patient-Centered Care                               91
  Treatment Outcome                                   91
  Risk Factors                                        90
  Transition to Adult Care                            73
  Hospitalization                                     72
  Empathy                                             68
  Aftercare                                           67
  Caregivers                                          67
  United States                                       66
  Child, Preschool                                    63
  Chronic Disease                                     61
```

### Embedding + index
```
  Embedding model:  BAAI/bge-large-en-v1.5
  Dimension:        1024
  Max seq length:   512
  Chunk size / overlap (tokens): 400 / 50
  Index backend:    chroma (cosine)
  Persist dir:      index/chroma
  Collection name:  pubmed_abstracts
```

### PubMed query used (verbatim from config/pipeline.yaml)
```
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
```

### Data lineage
```
  db/discovery.jsonl          Phase 2 — ESummary metadata per PMID
  db/raw/<PMID>.xml           Phase 3 — raw EFetch XML
  db/parsed/<PMID>.json       Phase 3 — normalized JSON (ParsedDocument)
  db/chunks/<PMID>.jsonl      Phase 4 — one Chunk per line
  index/chroma/               Phase 5 — Chroma persistent collection
  db/manifest.jsonl           Phase 6 — per-doc provenance index
  logs/sanity_query_*.json    Phase 5 — sanity-query persisted results
  logs/<phase>_<UTC>.log      every phase — per-run audit log
```

<!-- END AUTO-CORPUS-SUMMARY -->
