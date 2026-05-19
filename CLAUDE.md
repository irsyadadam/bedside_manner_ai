# CLAUDE.md — handoff to the next session

This file is read automatically by Claude Code at session start. It exists
so a fresh chat can pick up the project at the point a previous session
left it. **Read it top to bottom before touching anything.**

---

## What this repo is

`clinicomm` is an end-to-end research prototype for a manuscript on
patient-centered clinical communication via LLMs (NURSE + Four Habits
frameworks). Four pipeline modules:

  I.  Initial Screening Conversation — `clinicomm/modules/m1_intake.py`
  II. Clinical Guideline Lookup     — `clinicomm/modules/m2_retrieval.py`
  III. Graph-RAG Reasoning           — `clinicomm/modules/m3_reasoning.py`
  IV. Patient-Centric Response       — `clinicomm/modules/m4_response.py`

Orchestrator: `clinicomm/pipeline.py`.  
Single source of truth for any pipeline knob: `config/pipeline.yaml`.

LLM backend is **local vLLM serving DeepSeek-R1-Distill-Qwen-14B** (free,
no API). Embeddings: `BAAI/bge-large-en-v1.5` on CUDA. Corpus: 1,779
PubMed abstracts (SR/MA/Guideline/Consensus, 2018–2026, English).

---

## What's done (do NOT redo)

**Phases 1–12 complete.** Real-LLM trace artifacts and publication-ready
tables/figures are committed at `manuscript/{tables_draft, figures,
figures_ascii, traces, data}/`.

Headline numbers from the latest real-LLM run (n=3 synthetic patients):

| | naive | framework | retrieval | full |
|---|---:|---:|---:|---:|
| PMID citations / response | 0 | 0 | 1.3 | **2.0** |
| NURSE elements applied | 0 | 1.3 | 3.3 | **4.0** |
| Provenance ratio | 0.00 | 0.00 | 0.33 | **1.00** |
| Follow-up timeframe present | 0/3 | 1/3 | 2/3 | **3/3** |

Provenance audit: **17/17 clinical claims (100%) verbatim-supported** in
the cited source abstract (`manuscript/tables_draft/table6_provenance_audit.md`).

Per-module latency (async-batched Module III): ~3 min/transcript end-to-end
on RTX 6000 Ada.

---

## What's next — Phase 13: external dataset evaluation

The user explicitly asked to extend evaluation to:

- **PriMock57** (primary, START HERE) — 57 mock primary-care
  consultations with reference clinician notes. https://github.com/babylonhealth/primock57
- **ACI-Bench** — 207 doctor-patient encounters paired with full SOAP
  notes (MEDIQA-Chat 2023).
- **MTS-Dialog** — 1,700 short clinical conversations with
  section-labeled summaries (MEDIQA-Chat 2023).
- **NoteChat** (supplementary) — note-grounded synthetic dialogues at
  scale; stratified subsample for robustness.
- **MedSynth** (supplementary) — synthetic medical dialogues.

### Recommended phasing (~3 days of work)

1. **Day 1 — PriMock57 adapter + first pass.**
     - Add `clinicomm/datasets/__init__.py` + `clinicomm/datasets/base.py`
       with an `ExternalTranscript` dataclass: `id, scenario, turns,
       gold_note, raw_format`.
     - Add `clinicomm/datasets/primock57.py` to clone/load the dataset
       and convert each consultation to `ExternalTranscript`.
     - Add `scripts/eval_on_dataset.py --dataset primock57 --limit N
       --max-reasoning-docs 5` writing `manuscript/traces_external/primock57/
       trace_<id>.{md,json}`.
     - **Speaker handling default = "middle" option** (see decision below).
     - Run on n=57; eyeball outputs in 10 transcripts to catch failure modes.

2. **Day 2 — eval against gold notes.**
     - Add `clinicomm/external_metrics.py` with field-level F1 (problems
       in extracted `PatientConcernProfile` vs. HPI/PMH/Meds extracted
       from the gold note via simple regex or a separate cheap LLM call),
       and ROUGE-L + BERTScore on the full PatientResponse vs. the gold
       note's narrative.
     - Add `scripts/eval_against_gold.py` that reads
       `manuscript/traces_external/<dataset>/trace_*.json` and writes
       `manuscript/tables_draft/table7_external_eval_{primock57,aci,mts}.{md,tex}`.

3. **Day 3 — ACI-Bench + MTS-Dialog adapters; write manuscript prose.**
     - Same adapter pattern. For MTS at n=1,700, default to a
       stratified subsample of n=300 unless we want the full 24-hour
       run.
     - Regenerate Figs 7 + 11 with PriMock57 + ACI numbers as additional
       conditions in the radar/bars.
     - Append a "Phase 13 — External evaluation" section to README.

### Speaker-handling decision (already discussed; default = middle)

All four primary datasets have **both clinician and patient turns**, while
our Module I prompt currently expects only patient utterances. Three options:

- (simplest) Strip clinician turns; feed only patient utterances.
- **(middle, default)** Keep the clinician turns visible as conversational
  context in the user payload but still extract from the patient turns.
  5-line tweak to `config/prompts/intake_system.txt`.
- (highest) Bypass `next_prompt`; replay the clinician's actual question
  before each patient turn. Most realistic but loses the templated-
  questioner contribution.

Go with **(middle)** unless the user says otherwise. It's the smallest
prompt diff that materially improves disambiguation (e.g., "yes" to a
yes/no question).

### Estimated compute

- PriMock57 (57 transcripts × ~3 min): **~3 h** real-LLM wall-clock
- ACI-Bench (207 × ~3 min): **~10 h**
- MTS-Dialog stratified n=300 × ~1 min: **~5 h**
- NoteChat / MedSynth: defer to robustness section

---

## How to run things (cheat sheet)

### Fresh-machine reproduction
```bash
git clone https://github.com/irsyadadam/bedside_manner_ai.git
cd bedside_manner_ai
cp .env.example .env       # optional: NCBI_API_KEY / HF_TOKEN / NCBI_EMAIL
bash scripts/bootstrap.sh  # Phases 2–6 ingest, ~10 min
```

### Real LLM (DeepSeek-R1-Distill-Qwen-14B via local vLLM)
```bash
# First run downloads ~28 GB of weights; subsequent runs reuse .hf_cache/.
bash scripts/start_vllm_server.sh &
# Verify ready:
curl -s http://localhost:8000/v1/models | head -1
# Pipeline on all 3 transcripts, async-batched Module III:
uv run python scripts/run_demo.py --all --max-reasoning-docs 5
# Refresh Tables 4-6 + Figs 7/8/11 against the real traces:
bash scripts/run_postprocess_real.sh
```

### Mock LLM (offline, no GPU, deterministic)
```bash
uv run python scripts/run_demo.py --demo --all
uv run python scripts/gen_manuscript_artifacts.py --demo
```
**WARNING:** mock traces have known bugs the user found — phantom problems
from negation (mock has no negation parsing) and identical boilerplate
across concerns (mock emits the same communication directive for any
doc with "communic"/"empathy"/etc. in the title). The committed traces in
`manuscript/traces/` are REAL-LLM, not mock; running `--demo --all`
overwrites them with the broken mock versions. Don't commit those.

---

## Architecture decisions to honor (don't relitigate)

1. **All LLM calls go to local vLLM, not API.** The user explicitly chose
   free local inference. Do not introduce Anthropic / OpenAI cloud calls.

2. **Async-batched Module III.** `Reasoner.reason()` is sync at the call
   site but internally uses `asyncio.run(self._gather_extract(...))` so
   per-doc extraction is concurrent. Don't revert to serial.

3. **Module I extraction prompt is load-bearing for NURSE.** The
   `emotional_cues[].evidence_quote` field MUST stay verbatim — Module
   IV's NURSE "Name" element quotes it back to the patient. If you
   touch `config/prompts/intake_system.txt`, the verbatim-quote rule
   stays.

4. **Module IV citation validator** strips hallucinated `cluster_id`s
   and re-derives `all_pmids_used` / `all_cluster_ids_used` from valid
   citations. R1-distill in particular copies cluster IDs and PMIDs
   from the worked example in `response_generation.txt`. The validator
   in `m4_response.py:generate()` handles this; don't remove it.

5. **vLLM config: `gpu_memory_utilization=0.88`.** Higher (0.93) OOMs
   the BGE sentence-transformer when we try to load it in the same
   process. Don't bump back up.

6. **DIRECTIVES_START / DIRECTIVES_END markers in
   `config/prompts/response_generation.txt`** are parsed by Phase 12
   to auto-generate Table 2. If you edit the directives block, keep the
   markers + the `- framework:` / `element:` / `trigger:` / `rule:`
   YAML-ish format.

7. **Authority table is hand-curated** (`clinicomm/modules/_authority.py`).
   30 canonical journals + ~16 aliases. Not derived from JIF. Reviewer
   may push back — defensible as a starter list for v0, but be prepared
   to swap for a JIF- or SJR-derived score if asked.

8. **Graph expansion in Module II is stubbed.** `expand_neighborhood(seeds)
   -> seeds`. Don't remove the function — the call site stays stable so
   Phase 14+ can drop in a real document graph (citation / supersedes /
   shares-descriptor edges) without touching the retriever.

---

## Known issues / gotchas

- **Mock pipeline ≠ real pipeline output.** The committed traces are
  real-LLM. Do not commit traces produced by `--demo` mode.

- **vLLM transformers ABI pin.** `pyproject.toml` pins
  `transformers>=4.45,<5` because vLLM 0.8.5's tokenizer code uses
  attributes removed in transformers 5.x. Don't bump.

- **R1 reasoning chains.** DeepSeek-R1-Distill emits `<think>...</think>`
  blocks before its JSON output. `_safe_json_loads` in
  `m1_intake.py` / `m3_reasoning.py` / `m4_response.py` strips them.
  Don't remove the stripping.

- **HF_HOME default = `./.hf_cache`.** Lives in the repo root. Add to
  `.gitignore` (it already is) but be aware it can grow to ~30 GB.

- **NCBI rate limit.** Without `NCBI_API_KEY` set, ingest runs at 3
  req/s (vs. 10 with key). Functional either way.

- **No clinician raters yet.** Tables in your "must-have" list that need
  human raters (clinician rubric, gold-standard intake annotation,
  nDCG@k with relevance judgments) are deliberately deferred. Phase 13
  unblocks two of these via the dataset reference notes (PriMock's
  clinician notes serve as gold for Module I; ACI-Bench SOAP notes
  serve as gold for Module IV).

---

## Token / auth

The user's prior PAT (`ghp_P3mjqI...`) is exposed in this chat's
transcript. **Tell them to revoke it** and either set up SSH for the
remote or hand you a fresh PAT. Push using:

```bash
git push 'https://oauth2:<TOKEN>@github.com/irsyadadam/bedside_manner_ai.git' main
```

Never store the token in `.git/config` (no `git remote set-url`).

---

## File map

```
clinicomm/
  config.py                pipeline.yaml loader
  baseline.py              Naive LLM baseline (Phase 12)
  metrics.py               11-metric response scoring (Phase 12)
  ablations.py             framework_only + retrieval_only conditions
  schemas.py               all pydantic models (Phases 3, 4, 7-10)
  pipeline.py              Pipeline orchestrator
  logging_setup.py         per-phase logfile + stdout

  ingest/                  Phases 2, 3, 6
    eutils.py              rate-limited NCBI client
    discovery.py           Phase 2: ESearch + ESummary
    efetch.py              Phase 3: EFetch + parse-to-JSON
    manifest.py            Phase 6: manifest + README corpus summary

  parse/
    pubmed_xml.py          lxml-based parser, structured-abstract aware

  embed/                   Phases 4, 5
    chunk.py               BGE-tokenizer-based chunking
    build_index.py         Chroma persistent collection build

  index/
    chroma_store.py        thin wrapper

  modules/                 Phases 7-10
    m1_intake.py           Module I
    m2_retrieval.py        Module II
    m3_reasoning.py        Module III (async)
    m4_response.py         Module IV
    llm_client.py          VLLMClient (sync+async) + 4 mocks
    _authority.py          30-journal lookup
    _glossary.py           35-term plain-English substitution

  datasets/                ← Phase 13 (TO BUILD)
    base.py                ExternalTranscript dataclass
    primock57.py
    aci_bench.py
    mts_dialog.py
    notechat.py            (supplementary)
    medsynth.py            (supplementary)

  external_metrics.py      ← Phase 13 (TO BUILD)

scripts/
  bootstrap.sh             Fresh-machine Phases 2-6 in one shot
  start_vllm_server.sh     Local vLLM + DeepSeek-R1-Distill-14B
  sanity_query.py          Phase 5b retrieval sanity (5 queries)
  run_demo.py              Phase 11 driver: transcript -> trace MD+JSON
  gen_manuscript_artifacts.py    Phase 12 orchestrator
  eval_ablations.py        4-condition × N-transcript metrics
  sensitivity_sweep.py     threshold + top_k sweeps
  provenance_audit.py      mechanical claim/source faithfulness
  render_figures.py        seaborn -> SVG
  run_postprocess_real.sh  one-shot Tables 4-6 + Figs 7/8/11/12 refresh
  eval_on_dataset.py       ← Phase 13 (TO BUILD)
  eval_against_gold.py     ← Phase 13 (TO BUILD)

config/
  pipeline.yaml            canonical config
  prompts/
    intake_system.txt              Module I LLM system prompt
    intake_completion_check.txt    (TODO; Python is_complete works without it)
    assertion_extraction.txt       Module III per-doc extraction
    conflict_resolution.txt        Module III divergent-cluster resolver
    response_generation.txt        Module IV (contains DIRECTIVES block)

demos/synthetic_patients/  3 hand-authored transcripts (filled in)
  p001_fatigue_weightloss.json
  p002_hypertension_followup.json
  p003_depression_screening.json

manuscript/
  figures_ascii/    fig1..fig6 .txt + .notes.md (hand-authored, Phase 12)
  figures/          fig7..fig12 .svg (seaborn, Phase 12; real data)
  tables_draft/     table1..table6 .md + .tex (booktabs; real data)
  traces/           trace_<id>.{md,json} + baseline + comparison per patient
  data/             ablation_metrics.json + sensitivity_*.json + provenance_audit.json

db/                 NOT IN GIT — regenerated by bootstrap.sh
index/chroma/       NOT IN GIT — regenerated by bootstrap.sh
.hf_cache/          NOT IN GIT — HF redownloads (~30 GB once)
logs/               per-phase audit logs
```

---

## First commands for the next session

```bash
# 1. Make sure the pipeline still runs end-to-end on the existing
#    synthetic patients (smoke test, mock, < 30 s):
uv run python scripts/run_demo.py --demo \
    demos/synthetic_patients/p001_fatigue_weightloss.json \
    --out-dir /tmp/smoke && echo "smoke ok"

# 2. Bring up vLLM if not running:
pgrep -af vllm.entrypoints || (
    nohup bash scripts/start_vllm_server.sh > logs/vllm.log 2>&1 &
    until grep -q "Application startup complete" logs/vllm.log; do sleep 5; done
)

# 3. Start Phase 13 — PriMock57 adapter:
#    See section "What's next" above.
```

Good luck. The pipeline is real, the data is real, the next paper is
Phase 13 worth of work.
