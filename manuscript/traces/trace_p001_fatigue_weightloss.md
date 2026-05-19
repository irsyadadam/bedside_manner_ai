# Pipeline trace — `p001_fatigue_weightloss`

_Mode: **mock**  ·  Generated: 2026-05-19T21:59:20+00:00_

## Scenario

52-year-old male contractor presenting with 1-month fatigue and unintentional ~12-pound weight loss. Father had colon cancer diagnosed late at 55. Patient and his wife both fear cancer. Wants to keep working.

## Transcript

**Turn 1** — *agent (templated):*

> What brings you in today? Take your time and tell me what's been going on.

**Patient:**

> I've been so tired the past month, and I've lost about 12 pounds without trying. My wife is convinced it's cancer and honestly I am too. I just want to know what's going on so I can keep working — I'm a contractor, if I can't be on my feet I can't earn.

**Turn 2** — *agent (templated):*

> When did the weight loss first start?

**Patient:**

> It started about a month ago. Some days I feel a 7 out of 10 tired — I can barely get through my shifts. I'm taking ibuprofen sometimes for headaches but nothing for the fatigue itself. Sleep is okay but I'm not waking up rested.

**Turn 3** — *agent (templated):*

> When did the weight loss first start?

**Patient:**

> No chest pain, no shortness of breath, nothing like that. No fainting, no sudden weakness on one side. But I have been getting these dull headaches in the morning, almost every day. No fevers, no blood in stool that I've seen — I'd have noticed.

**Turn 4** — *agent (templated):*

> On a scale of 1 to 10, or in your own words, how bad has the weight loss been?

**Patient:**

> I'm on lisinopril 10 mg once a day for blood pressure, been on it for years. No allergies that I know of. My dad had colon cancer at 55 — they caught it late and he didn't make it. I don't smoke. Maybe a beer or two on the weekends.

**Turn 5** — *agent (templated):*

> On a scale of 1 to 10, or in your own words, how bad has the weight loss been?

**Patient:**

> I'd really like to rule out the cancer thing — I want to feel safe again, you know? And I need to keep working. If we can do whatever's needed without me taking weeks off, that'd be a huge help.

_Intake completion at last turn: **False** (status: `in_progress`)_

## Final `PatientConcernProfile`

```yaml
problems:
- label: fatigue
  onset: started about a month ago
  severity: 7 out of 10
  timing: null
  associated_symptoms: []
  interventions_tried: []
  status: unknown
- label: weight loss
  onset: null
  severity: null
  timing: null
  associated_symptoms: []
  interventions_tried: []
  status: unknown
- label: headache
  onset: started about a month ago
  severity: 7 out of 10
  timing: in the morning
  associated_symptoms: []
  interventions_tried: []
  status: unknown
- label: shortness of breath
  onset: null
  severity: null
  timing: in the morning
  associated_symptoms: []
  interventions_tried: []
  status: unknown
- label: chest pain
  onset: null
  severity: null
  timing: in the morning
  associated_symptoms: []
  interventions_tried: []
  status: unknown
medications:
- ibuprofen sometimes for headaches but nothing for the fatigue itself
- lisinopril 10 mg once a day for blood pressure, been on it for years
- weeks off, that'd be a huge help
allergies: []
relevant_history: []
patient_goals:
- I just want to know what's going on so I can keep working — I'm a contractor, if
  I can't be on my feet I can't earn
- I want to feel safe again, you know? And I need to keep working
- I need to keep working
emotional_cues:
- cue: fear
  evidence_quote: My wife is convinced it's cancer and honestly I am too
- cue: fear
  evidence_quote: My dad had colon cancer at 55 — they caught it late and he didn't
    make it
- cue: fear
  evidence_quote: I'd really like to rule out the cancer thing — I want to feel safe
    again, you know? And I need to keep working
red_flags:
- flag: unexplained weight loss
  evidence: I've been so tired the past month, and I've lost about 12 pounds without
    trying
- flag: neurologic deficit
  evidence: No fainting, no sudden weakness on one side
unknowns:
- problems[0].timing
- problems[1].onset
- problems[1].severity
- problems[1].timing
- problems[3].onset
- problems[3].severity
- problems[4].onset
- problems[4].severity
turn_count: 5
completion_status: in_progress
```

## Top 5 retrieved documents (Module II)

Sub-queries decomposed: **9**.  top_k chunks/sub-query: **20**.  Graph expansion: `stub`.  Rerank weights: `{'semantic_similarity': 0.5, 'recency': 0.2, 'authority': 0.2, 'coverage_bonus': 0.1}`.

| Rank | PMID | Year | Journal | sem | rec | aut | cov | total | Title |
|---:|---|---:|---|---:|---:|---:|---:|---:|---|
| 1 | 40983262 | 2026 | American journal of preventive medicine | 0.689 | 1.00 | 0.80 | 0.22 | 0.727 | Systematic Review of Dementia Risk Screening Tools in Primary Care Settings. |
| 2 | 41092546 | 2026 | Patient education and counseling | 0.675 | 1.00 | 0.80 | 0.11 | 0.708 | Patient-clinician communication in longitudinal care settings about adverse childhood experiences (A |
| 3 | 38719772 | 2024 | The European respiratory journal | 0.705 | 0.75 | 0.85 | 0.11 | 0.684 | European Respiratory Society clinical practice guideline on symptom management for adults with serio |
| 4 | 38533994 | 2024 | The Cochrane database of systematic reviews | 0.629 | 0.75 | 0.98 | 0.11 | 0.672 | Mobile phone text messaging for medication adherence in secondary prevention of cardiovascular disea |
| 5 | 38521534 | 2024 | BMJ open | 0.706 | 0.75 | 0.80 | 0.00 | 0.663 | Prognostic factors and prediction models for hospitalisation and all-cause mortality in adults prese |

## `StructuredContextArtifact` (Module III)

- Documents processed: **20**  · Assertions extracted: **40**  · Clusters: **4** (convergent=2, divergent=2)  · Similarity threshold: **0.75**

### Cluster 1 · CONVERGENT · `communication_directive` · addresses=`(global)` · confidence=0.85

**Primary** (`41092546_1`, conf=0.80): Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

> _evidence_: Patient-clinician communication in longitudinal care settings about adverse childhood experiences (ACEs) and adult traumas: A systematic review of reviews.

Supporting PMIDs (3): 33658141, 34448868, 41092546

### Cluster 2 · CONVERGENT · `monitoring` · addresses=`(global)` · confidence=0.70

**Primary** (`40983262_1`, conf=0.70): Periodic screening / monitoring is supported by this journal article.

> _evidence_: Systematic Review of Dementia Risk Screening Tools in Primary Care Settings.

Supporting PMIDs (1): 40983262

### Cluster 3 · DIVERGENT · `finding` · addresses=`(global)` · confidence=0.78

**Primary** (`40983262_2`, conf=0.78): This journal article synthesizes evidence relevant to the patient's concerns.

> _evidence_: Systematic Review of Dementia Risk Screening Tools in Primary Care Settings.

**Alternatives (15):**
- `41092546_2` (conf=0.78) — This journal article synthesizes evidence relevant to the patient's concerns.
- `38719772_1` (conf=0.78) — This journal article synthesizes evidence relevant to the patient's concerns.
- `38521534_1` (conf=0.78) — This systematic review synthesizes evidence relevant to the patient's concerns.
- `35833228_1` (conf=0.78) — This systematic review synthesizes evidence relevant to the patient's concerns.
- ... and 11 more

_Resolution rule: **recency** — Recency: pub_year=2026 wins among [2026, 2026, 2024, 2024, 2023, 2021, 2021, 2021, 2021, 2021, 2026, 2021, 2020, 2020, 2019, 2026]; authority and confidence used as tiebreakers if needed._

Supporting PMIDs (16): 31237649, 31558663, 32032375, 33658141, 33882128, 33952533, 33992082, 34448868, 34588228, 35833228...

### Cluster 4 · DIVERGENT · `recommendation` · addresses=`(global)` · confidence=0.72

**Primary** (`40983262_0`, conf=0.72): Per this 2026 journal article, consider the approach described in: "Systematic Review of Dementia Risk Screening Tools in Primary Care Settings."

> _evidence_: Systematic Review of Dementia Risk Screening Tools in Primary Care Settings.

**Alternatives (19):**
- `41092546_0` (conf=0.72) — Per this 2026 journal article, consider the approach described in: "Patient-clinician communication in longitudinal care settings about adverse childhood expe"
- `38719772_0` (conf=0.72) — Per this 2024 journal article, consider the approach described in: "European Respiratory Society clinical practice guideline on symptom management for adults "
- `38533994_0` (conf=0.72) — Per this 2024 journal article, consider the approach described in: "Mobile phone text messaging for medication adherence in secondary prevention of cardiovasc"
- `38521534_0` (conf=0.72) — Per this 2024 systematic review, consider the approach described in: "Prognostic factors and prediction models for hospitalisation and all-cause mortality in ad
- ... and 15 more

_Resolution rule: **recency** — Recency: pub_year=2026 wins among [2026, 2026, 2024, 2024, 2024, 2022, 2023, 2021, 2021, 2021, 2021, 2020, 2021, 2026, 2021, 2020, 2020, 2019, 2026, 2026]; authority and confidence used as tiebreakers if needed._

Supporting PMIDs (20): 31237649, 31558663, 32032375, 33285618, 33658141, 33882128, 33952533, 33992082, 34448868, 34588228...

**Limitations recorded by Module III:**
- Abstracts-only prototype: assertion granularity is coarser than a full-text system would produce.
- Module II graph expansion is stubbed in v0 (flat vector retrieval). See clinicomm.modules.m2_retrieval.expand_neighborhood.

## Final `PatientResponse` (Module IV)

### Acknowledgment

> I can hear how much this has been weighing on you — you said, "My wife is convinced it's cancer and honestly I am too". That's a real thing to be carrying, and I want to take it seriously while we figure out what's going on.

### Clinical information, per concern

**fatigue** (`problems[0]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]

> For your fatigue: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

Citations:
- `communication_directive::global::41092546_1` → primary `41092546_1` (supports: 33658141, 34448868, 41092546)

**weight loss** (`problems[1]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]

> For your weight loss: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

Citations:
- `communication_directive::global::41092546_1` → primary `41092546_1` (supports: 33658141, 34448868, 41092546)

**headache** (`problems[2]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]

> For your headache: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

Citations:
- `communication_directive::global::41092546_1` → primary `41092546_1` (supports: 33658141, 34448868, 41092546)

**shortness of breath** (`problems[3]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]

> For your shortness of breath: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

Citations:
- `communication_directive::global::41092546_1` → primary `41092546_1` (supports: 33658141, 34448868, 41092546)

**chest pain** (`problems[4]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]

> For your chest pain: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

Citations:
- `communication_directive::global::41092546_1` → primary `41092546_1` (supports: 33658141, 34448868, 41092546)

**goal: "I just want to know what's going on so I can keep working — I'm a contractor, if I can't be on my feet I can't earn"** (`patient_goals[0]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]

> For your goal: "I just want to know what's going on so I can keep working — I'm a contractor, if I can't be on my feet I can't earn": based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

Citations:
- `communication_directive::global::41092546_1` → primary `41092546_1` (supports: 33658141, 34448868, 41092546)

**goal: "I want to feel safe again, you know? And I need to keep working"** (`patient_goals[1]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]

> For your goal: "I want to feel safe again, you know? And I need to keep working": based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

Citations:
- `communication_directive::global::41092546_1` → primary `41092546_1` (supports: 33658141, 34448868, 41092546)

**goal: "I need to keep working"** (`patient_goals[2]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]

> For your goal: "I need to keep working": based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

Citations:
- `communication_directive::global::41092546_1` → primary `41092546_1` (supports: 33658141, 34448868, 41092546)

### Next steps

1. Because of the unexplained weight loss, we'll start the workup today rather than wait — that includes bloodwork and a few tests to rule out the things you're most worried about.
2. We'll go through what each step is for, so you can decide what feels right.
3. I'll have someone follow up with you in the next few days to check in and answer any questions that come up.

### Teach-back prompt

> I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

### Follow-up invitation

> Let's plan to see each other again in 2–4 weeks. In the meantime, if anything gets worse — especially any of the warning signs we talked about — please call us right away.

## Provenance appendix

### Framework elements applied

- **NURSE** elements applied: ['Name', 'Understand', 'Respect', 'Support']
- **Four Habits** elements applied: ['Invest in the beginning', 'Demonstrate empathy', "Elicit the patient's perspective", 'Invest in the end']

### Cluster → PMIDs used in the response

- `communication_directive::global::41092546_1` · `communication_directive` · addresses=`(global)` · primary `41092546_1` · PMIDs: 33658141, 34448868, 41092546

### All PMIDs cited (deduped)

- 33658141
- 34448868
- 41092546

_No glossary substitutions were needed (LLM produced plain language directly)._

---

_Generated by `scripts/run_demo.py` · mode `mock` · transcript `p001_fatigue_weightloss`_