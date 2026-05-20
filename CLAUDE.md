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

## Phase 13 — scaffolding complete, real-LLM runs pending (2026-05-20)

**Status:** All Phase 13 code is in place + smoke-tested (23/23 tests
pass via `uv run python tests/test_phase13_smoke.py`). The next session
runs the real-LLM evaluation on the three external datasets and fills
in Tables 8–11 + Figs 13–16.

**Files added this session:**

```
clinicomm/datasets/__init__.py        ExternalTranscript, Turn
clinicomm/datasets/base.py            dataclass + speaker strategies
clinicomm/datasets/mts_dialog.py      MTS-Dialog adapter + downloader
clinicomm/datasets/primock57.py       PriMock57 adapter (git clone)
clinicomm/datasets/aci_bench.py       ACI-Bench adapter (git clone)
clinicomm/external_metrics.py         field-F1, hallucination, ROUGE-L,
                                      BERTScore, topic coverage, NURSE/
                                      Four-Habits/safety rubric (LLM-judge),
                                      Cohen κ, trust-calibration bins
clinicomm/baseline.py                 + StrongPromptLLMBaseline
scripts/eval_on_dataset.py            5-condition runner per dataset
scripts/eval_against_gold.py          metrics → Tables 8/9/10/11 + Fig data
scripts/gen_clinician_forms.py        emit-forms / score-forms subcommands
tests/test_phase13_smoke.py           23 tests, no GPU / no network needed
README.md                             "CLAIMS AND SCOPE" section added at top
pyproject.toml                        + rouge_score, bert_score, pandas
```

`uv sync` once before the first real-LLM run to install the three new
deps. They're light — rouge_score is pure Python, bert_score reuses our
torch+transformers stack, pandas is the only new heavy dep.

### Run plan (exact commands + expected wall-clock)

The driver scripts are idempotent: trace_<id>.json that already exists
is skipped on the next run, so each step can be killed + resumed.

```bash
# 0. Sync new deps once.
uv sync

# 1. Bring up vLLM if not running.
pgrep -af vllm.entrypoints || (
    nohup bash scripts/start_vllm_server.sh > logs/vllm.log 2>&1 &
    until grep -q "Application startup complete" logs/vllm.log; do sleep 5; done
)

# 2. Smoke (mock LLM, ~30 s — verifies the drivers work end-to-end).
uv run python scripts/eval_on_dataset.py --dataset mts --demo --limit 2 \
    --conditions naive strong_prompt
ls manuscript/traces_external/mts_dialog/

# 3. Real-LLM evaluation, dataset-by-dataset.
#    Each step writes trace_<id>.{md,json} into
#    manuscript/traces_external/<dataset>/.

#    3a. PriMock57 — end-to-end story dataset (~3 h on RTX 6000 Ada).
uv run python scripts/eval_on_dataset.py --dataset primock57 \
    --download --max-reasoning-docs 5

#    3b. MTS-Dialog — Module I extraction accuracy (~5 h for n=300 stratified).
uv run python scripts/eval_on_dataset.py --dataset mts \
    --download --limit 300 --max-reasoning-docs 5

#    3c. ACI-Bench — Module IV response quality (~10 h for all n=207).
uv run python scripts/eval_on_dataset.py --dataset aci \
    --download --max-reasoning-docs 5

# 4. Compute external metrics + emit Tables 8/9/10/11 + Fig 15 data.
#    --llm-judge adds one judge call per response (heavy; ~3 h extra
#    for n=564). --bertscore loads a ~2GB model on first call.
uv run python scripts/eval_against_gold.py --dataset all \
    --llm-judge --bertscore

# 5. Generate clinician-rater forms (offline, instant). Ship to a
#    collaborator. Once they return them, the score-forms subcommand
#    computes κ for Table 11.
uv run python scripts/gen_clinician_forms.py emit-forms \
    --rater-code R1 --n-per-stratum 4
# (Optionally repeat for a second rater R2 to also report inter-clinician κ.)

# 6. After ratings come back, parse + κ.
uv run python scripts/gen_clinician_forms.py score-forms --rater-code R1
```

**Total real-LLM wall-clock budget:** ~18 h end-to-end (PriMock 3 + MTS
5 + ACI 10) for the trace runs, +3 h for the LLM-judge pass = ~21 h.
Run steps 3a–3c in parallel screens/tmux if you want — they don't
contend on GPU because vLLM multiplexes requests.

### What the Phase 13 outputs unlock for the paper

```
Table 8   — MTS Module-I extraction P/R/F1 per field + macro
            (no human annotation needed — gold sections are labeled)
Table 9   — ACI Module-IV response quality, 5-way ablation
            (naive | strong_prompt | framework_only | retrieval_only | full)
Table 10  — Cross-dataset rollup (Full + Strong-prompt baseline rows)
Table 11  — LLM-judge per-item means + Cohen κ vs. clinician spot-check
Fig 13    — 4-way ablation × 3 datasets (faceted)
Fig 14    — MTS per-field F1 heatmap
Fig 15    — Trust calibration: confidence vs. safety-pass curve
Fig 16    — Safety-pass × response-quality scatter, dataset-colored
```

### Defensibility checklist (run before submission)

- [ ] README "CLAIMS AND SCOPE" section is the first thing reviewers see ✓ (done this session)
- [ ] Strong-prompt baseline beats naive but loses to Full on provenance
      and hallucination — confirm post-eval ✓ (pending Phase 13 runs)
- [ ] Hallucination rate < 5% for Full pipeline on all 3 datasets — confirm
- [ ] Safety-pass rate > 80% for Full pipeline — confirm
- [ ] Cohen κ ≥ 0.4 (moderate) for at least one rater — confirm
- [ ] Outcomes language scrubbed from manuscript prose (the README is done; the
      paper draft may still have residual outcomes claims to remove)

## Phase 13 — locked framing decisions (do not relitigate)

1. **Companion-not-replacement, hard.** The manuscript measures
   empathy/provenance/safety surrogate markers, not patient outcomes /
   satisfaction / adherence. The original proposal language ("enhances
   satisfaction, adherence, outcomes") is overclaim and has been moved
   to README §"CLAIMS AND SCOPE" as out-of-scope future work.
2. **Realistic venue target: JAMIA.** Floor: AMIA / ClinicalNLP.
3. **Strong-prompt local baseline** added next to NaiveLLMBaseline. No
   cloud-API baseline (honors §"all local" decision).
4. **Dual-track human eval.** LLM-judge runs at full coverage;
   stratified n=20–30 clinician sample scored against the same rubric
   for inter-rater κ in Table 11. Rubric form scaffolding lives in
   `scripts/gen_clinician_forms.py`.
5. **Safety audit is non-negotiable.** 4-item check (escalation when
   red-flag triggered / no autonomous diagnostic claim / no
   contraindicated advice / follow-up timeframe present) is what
   operationalizes the "companion" claim; without it the framing is
   rhetoric.

## What's next — Phase 13: external dataset evaluation

The user explicitly asked to extend evaluation to three primary datasets.
Each plays a **different evaluation role** — don't treat them as
interchangeable:

- **PriMock57** (primary, START HERE) — 57 mock primary-care
  consultations with reference clinician notes.
  https://github.com/babylonhealth/primock57
  **Best for end-to-end pipeline validation.** Real-clinician dialogue
  patterns + reference notes serve as a holistic "did the pipeline
  produce something clinically reasonable?" check. Smallest n, so
  cheapest to iterate on.

- **MTS-Dialog** — 1,700 short clinical conversations with
  **section-labeled summaries** (MEDIQA-Chat 2023).
  **THIS IS THE KEY DATASET FOR MODULE I ACCURACY.** Each conversation
  has a labeled summary with section headers like HPI, PMH, MEDICATIONS,
  ALLERGIES, FAMILY_HISTORY, SOCIAL_HISTORY, REVIEW_OF_SYSTEMS,
  PHYSICAL_EXAM, ASSESSMENT, PLAN, GENHX, DIAGNOSIS, EDCOURSE, etc.
  These map almost 1:1 to fields in `PatientConcernProfile`:
      HPI                 -> problems[].label + onset + timing
      PMH                 -> relevant_history
      MEDICATIONS         -> medications
      ALLERGIES           -> allergies
      FAMILY_HISTORY      -> relevant_history (annotated)
      ASSESSMENT          -> can score against Module III primaries
  So MTS-Dialog gives Table 8 (Module I extraction accuracy with
  precision/recall/F1 per field) **for free, with no hand-annotation
  required**. This is the dataset that unlocks the strongest "the
  pipeline actually extracts what a clinician would" quantitative
  claim for the manuscript. Subsample to n=300 for the paper unless
  you want the full 24-h run.

- **ACI-Bench** — 207 doctor-patient encounters paired with full SOAP
  notes (MEDIQA-Chat 2023).
  **Best for Module IV response-quality comparison.** Full SOAP notes
  (Subjective/Objective/Assessment/Plan) let you score the generated
  `PatientResponse` against a clinician-written response on the same
  encounter via ROUGE-L, BERTScore, and the same NURSE/Four-Habits
  rubric we already have. Medium n; 10 h real-LLM wall-clock.

- **NoteChat** (supplementary) — note-grounded synthetic dialogues at
  scale; stratified subsample for robustness.
- **MedSynth** (supplementary) — synthetic medical dialogues.

**Recommended ordering of which dataset to attack first** has changed
slightly given the MTS insight: PriMock57 still goes first for the
end-to-end story, but **MTS-Dialog is the highest-value second dataset**
(not third) because it lets you fill in Table 8 with no human labeling
effort.

### Recommended phasing (~4 days of work; revised after the MTS insight)

1. **Day 1 — PriMock57 adapter + first pass (end-to-end story).**
     - Add `clinicomm/datasets/__init__.py` + `clinicomm/datasets/base.py`
       with an `ExternalTranscript` dataclass: `id, scenario, turns,
       gold_note, gold_sections, raw_format`. (`gold_sections` is a
       dict[section_label, text] — populated by MTS adapter, may be
       empty for PriMock/ACI.)
     - Add `clinicomm/datasets/primock57.py` to clone/load the dataset
       and convert each consultation to `ExternalTranscript`.
     - Add `scripts/eval_on_dataset.py --dataset {primock57|mts|aci}
       --limit N --max-reasoning-docs 5` writing
       `manuscript/traces_external/<dataset>/trace_<id>.{md,json}`.
     - **Speaker handling default = "middle" option** (see decision below).
     - Run PriMock57 (n=57); eyeball outputs in 10 transcripts to catch
       failure modes.

2. **Day 2 — MTS-Dialog adapter + Module I extraction accuracy
   (Table 8 unlocked).**
     - Add `clinicomm/datasets/mts_dialog.py`. The dataset's gold
       summaries are themselves section-labeled (HPI / PMH / MEDICATIONS
       / ALLERGIES / FAMILY_HISTORY / SOCIAL_HISTORY / ASSESSMENT /
       PLAN / GENHX / etc.). Parse them into `gold_sections`.
     - Add `clinicomm/external_metrics.py::field_level_extraction_f1()`
       which maps section labels to `PatientConcernProfile` fields:

           HPI            -> problems[].label / onset / timing
           PMH            -> relevant_history
           MEDICATIONS    -> medications
           ALLERGIES      -> allergies
           FAMILY_HISTORY -> relevant_history (substring-matched)
           ASSESSMENT     -> Module III cluster primaries (for Table 7)

       For each field, tokenize / set-ify the gold vs. extracted values
       and compute precision/recall/F1. Where the gold is free text
       (HPI is a paragraph), use a lightweight semantic match (token
       overlap with stemming or a cheap LLM-as-judge call).
     - Run the pipeline on a stratified subsample of n=300 MTS
       conversations (~5 h real-LLM).
     - Emit `manuscript/tables_draft/table8_mts_extraction_accuracy.{md,tex}`
       with per-field precision/recall/F1 + aggregate macro-F1. This is
       the table the manuscript hangs the "Module I extracts what a
       clinician would" claim on, no hand-annotation required.

3. **Day 3 — ACI-Bench adapter + Module IV response-quality eval
   (Table 9).**
     - Add `clinicomm/datasets/aci_bench.py`. ACI-Bench's reference
       notes are full SOAP notes — use them as gold for the
       `PatientResponse` text.
     - Extend `external_metrics.py` with:
           ROUGE-L (response vs. gold note Subjective+Assessment+Plan
                   sections, since Module IV does not produce an
                   Objective/exam section)
           BERTScore on the same comparison
           Per-section presence: does the generated response cover the
                   topics the gold note covers? (Topic-keyword overlap
                   per section.)
     - Run pipeline on all 207 ACI-Bench encounters (~10 h).
     - Emit `manuscript/tables_draft/table9_aci_response_quality.{md,tex}`.

4. **Day 4 — Manuscript prose + figure refresh + cross-dataset table.**
     - Regenerate Figs 7 + 11 + Table 5 to include three new conditions
       (or just three new sub-rows in the existing Table 5 for the same
       4-way ablation, one block per dataset).
     - Add `Table 10 — Cross-dataset summary` aggregating
       {PriMock57, MTS-Dialog, ACI-Bench} headline metrics in one place.
     - Append a "Phase 13 — External evaluation" section to README.
     - Update CLAUDE.md (this file!) to mark Phase 13 done and propose
       Phase 14 (full-text retrieval? clinician rubric scoring?
       supervised fine-tuning on NoteChat-derived data?).

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
