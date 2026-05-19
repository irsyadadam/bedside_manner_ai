# Pipeline trace — `p002_hypertension_followup`

_Mode: **mock**  ·  Generated: 2026-05-19T21:59:20+00:00_

## Scenario

41-year-old female teacher returning for a hypertension follow-up. Openly admits inconsistent adherence to lisinopril 20 mg (~4/7 days), bothered by ACE-inhibitor cough, mildly worried about lightheadedness on standing. Has two young kids, father had MI at 62 (lifelong smoker), wants to avoid more medications if possible.

## Transcript

**Turn 1** — *agent (templated):*

> What brings you in today? Take your time and tell me what's been going on.

**Patient:**

> I'm here for my blood pressure check, but I want to be straight with you — I haven't been good about taking the pills. Some weeks I just forget, and honestly when I feel fine I don't see the point. Plus the lisinopril gives me this dry cough that drives me crazy at night.

**Turn 2** — *agent (templated):*

> Before we go further, I want to check on a few quick safety questions. Have you had any chest pain, trouble breathing, sudden weakness or numbness, severe headaches, unexplained bleeding, or any thoughts of harming yourself recently?

**Patient:**

> I take it maybe four days out of seven if I'm being generous. Mornings are the worst — I'm getting ready, the kids are losing it, and it just slips. The cough started maybe two months in and hasn't gone away. I've also had a little dizziness when I stand up fast — not bad, just a moment.

**Turn 3** — *agent (templated):*

> Before we go further, I want to check on a few quick safety questions. Have you had any chest pain, trouble breathing, sudden weakness or numbness, severe headaches, unexplained bleeding, or any thoughts of harming yourself recently?

**Patient:**

> No chest pain. No vision changes — that I'd be more worried about. I get those dizzy moments standing up but nothing where I almost fell or anything. No leg swelling. No real headaches. And no — definitely no thoughts of hurting myself or anything like that. I'm frustrated, not depressed.

**Turn 4** — *agent (templated):*

> When did the depressed mood first start?

**Patient:**

> Just the lisinopril 20 mg in the morning when I take it. No other prescriptions. No allergies. My mom was on blood pressure pills for years and did okay, my dad had a heart attack at 62 but he smoked his whole life. I don't smoke. I'm trying to walk more — got an Apple Watch and it nags me, which is kind of working.

**Turn 5** — *agent (templated):*

> When did the depressed mood first start?

**Patient:**

> Honestly? I want fewer pills, not more. If there's a way to get my numbers down without the cough, I'd take that. But I also don't want to do something stupid that ends with me in a hospital bed — I have two kids in elementary school. I need to be around.

_Intake completion at last turn: **False** (status: `in_progress`)_

## Final `PatientConcernProfile`

```yaml
problems:
- label: cough
  onset: started maybe two months in and hasn't gone awa
  severity: null
  timing: null
  associated_symptoms: []
  interventions_tried: []
  status: unknown
- label: headache
  onset: null
  severity: null
  timing: null
  associated_symptoms: []
  interventions_tried: []
  status: unknown
- label: chest pain
  onset: null
  severity: null
  timing: null
  associated_symptoms: []
  interventions_tried: []
  status: unknown
- label: depressed mood
  onset: null
  severity: null
  timing: null
  associated_symptoms: []
  interventions_tried: []
  status: unknown
medications:
- the pills
- it maybe four days out of seven if I'm being generous
- it
allergies: []
relevant_history: []
patient_goals:
- I want to be straight with you — I haven't been good about taking the pills
- I need to be around
emotional_cues:
- cue: worry
  evidence_quote: No vision changes — that I'd be more worried about
- cue: frustration
  evidence_quote: I'm frustrated, not depressed
- cue: sadness
  evidence_quote: If there's a way to get my numbers down without the cough, I'd take
    that
red_flags:
- flag: suicidal ideation
  evidence: And no — definitely no thoughts of hurting myself or anything like that
unknowns:
- problems[0].severity
- problems[0].timing
- problems[1].onset
- problems[1].severity
- problems[1].timing
- problems[2].onset
- problems[2].severity
- problems[2].timing
- problems[3].onset
- problems[3].severity
- problems[3].timing
turn_count: 5
completion_status: in_progress
```

## Top 5 retrieved documents (Module II)

Sub-queries decomposed: **7**.  top_k chunks/sub-query: **20**.  Graph expansion: `stub`.  Rerank weights: `{'semantic_similarity': 0.5, 'recency': 0.2, 'authority': 0.2, 'coverage_bonus': 0.1}`.

| Rank | PMID | Year | Journal | sem | rec | aut | cov | total | Title |
|---:|---|---:|---|---:|---:|---:|---:|---:|---|
| 1 | 41092546 | 2026 | Patient education and counseling | 0.655 | 1.00 | 0.80 | 0.29 | 0.716 | Patient-clinician communication in longitudinal care settings about adverse childhood experiences (A |
| 2 | 41466386 | 2025 | BMC primary care | 0.734 | 0.88 | 0.68 | 0.29 | 0.707 | Screening tools for ruling out mood and anxiety disorders in adults in primary care: a rapid systema |
| 3 | 38719772 | 2024 | The European respiratory journal | 0.687 | 0.75 | 0.85 | 0.14 | 0.678 | European Respiratory Society clinical practice guideline on symptom management for adults with serio |
| 4 | 39366124 | 2025 | Patient education and counseling | 0.670 | 0.88 | 0.80 | 0.00 | 0.670 | Roles and contributions of companions in healthcare professional-older patient interaction: A system |
| 5 | 38367963 | 2024 | BMJ open | 0.685 | 0.75 | 0.80 | 0.00 | 0.652 | Triadic communication with teenagers and young adults with cancer: a systematic literature review -  |

## `StructuredContextArtifact` (Module III)

- Documents processed: **20**  · Assertions extracted: **38**  · Clusters: **5** (convergent=3, divergent=2)  · Similarity threshold: **0.75**

### Cluster 1 · CONVERGENT · `communication_directive` · addresses=`(global)` · confidence=0.85

**Primary** (`41092546_1`, conf=0.80): Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

> _evidence_: Patient-clinician communication in longitudinal care settings about adverse childhood experiences (ACEs) and adult traumas: A systematic review of reviews.

Supporting PMIDs (4): 33658141, 34848112, 38367963, 41092546

### Cluster 2 · CONVERGENT · `recommendation` · addresses=`(global)` · confidence=0.72

**Primary** (`36250577_0`, conf=0.72): Per this 2022 journal article, consider the approach described in: "Biomarkers as point-of-care tests to guide prescription of antibiotics in people with acut"

> _evidence_: Biomarkers as point-of-care tests to guide prescription of antibiotics in people with acute respiratory infections in primary care.

Supporting PMIDs (1): 36250577

### Cluster 3 · CONVERGENT · `monitoring` · addresses=`(global)` · confidence=0.70

**Primary** (`41466386_1`, conf=0.70): Periodic screening / monitoring is supported by this journal article.

> _evidence_: Screening tools for ruling out mood and anxiety disorders in adults in primary care: a rapid systematic review.

Supporting PMIDs (1): 41466386

### Cluster 4 · DIVERGENT · `finding` · addresses=`(global)` · confidence=0.78

**Primary** (`41092546_2`, conf=0.78): This journal article synthesizes evidence relevant to the patient's concerns.

> _evidence_: Patient-clinician communication in longitudinal care settings about adverse childhood experiences (ACEs) and adult traumas: A systematic review of reviews.

**Alternatives (12):**
- `41466386_2` (conf=0.78) — This journal article synthesizes evidence relevant to the patient's concerns.
- `38719772_1` (conf=0.78) — This journal article synthesizes evidence relevant to the patient's concerns.
- `39366124_1` (conf=0.78) — This systematic review synthesizes evidence relevant to the patient's concerns.
- `38521534_1` (conf=0.78) — This systematic review synthesizes evidence relevant to the patient's concerns.
- ... and 8 more

_Resolution rule: **recency** — Recency: pub_year=2026 wins among [2026, 2025, 2024, 2025, 2024, 2022, 2023, 2021, 2021, 2022, 2021, 2025, 2025]; authority and confidence used as tiebreakers if needed._

Supporting PMIDs (13): 33658141, 33952533, 33992082, 34546354, 35833228, 35971077, 38521534, 38719772, 39366124, 40419299...

### Cluster 5 · DIVERGENT · `recommendation` · addresses=`(global)` · confidence=0.72

**Primary** (`41092546_0`, conf=0.72): Per this 2026 journal article, consider the approach described in: "Patient-clinician communication in longitudinal care settings about adverse childhood expe"

> _evidence_: Patient-clinician communication in longitudinal care settings about adverse childhood experiences (ACEs) and adult traumas: A systematic review of reviews.

**Alternatives (18):**
- `41466386_0` (conf=0.72) — Per this 2025 journal article, consider the approach described in: "Screening tools for ruling out mood and anxiety disorders in adults in primary care: a rap"
- `38719772_0` (conf=0.72) — Per this 2024 journal article, consider the approach described in: "European Respiratory Society clinical practice guideline on symptom management for adults "
- `39366124_0` (conf=0.72) — Per this 2025 systematic review, consider the approach described in: "Roles and contributions of companions in healthcare professional-older patient interaction
- `38367963_0` (conf=0.72) — Per this 2024 systematic review, consider the approach described in: "Triadic communication with teenagers and young adults with cancer: a systematic literature
- ... and 14 more

_Resolution rule: **recency** — Recency: pub_year=2026 wins among [2026, 2025, 2024, 2025, 2024, 2024, 2021, 2022, 2023, 2021, 2022, 2022, 2021, 2021, 2022, 2021, 2025, 2025, 2026]; authority and confidence used as tiebreakers if needed._

Supporting PMIDs (19): 33658141, 33952533, 33992082, 34131914, 34546354, 34693994, 34848112, 35237885, 35833228, 35971077...

**Limitations recorded by Module III:**
- Abstracts-only prototype: assertion granularity is coarser than a full-text system would produce.
- Module II graph expansion is stubbed in v0 (flat vector retrieval). See clinicomm.modules.m2_retrieval.expand_neighborhood.

## Final `PatientResponse` (Module IV)

### Acknowledgment

> I can hear how much this has been weighing on you — you said, "No vision changes — that I'd be more worried about". That's a real thing to be carrying, and I want to take it seriously while we figure out what's going on.

### Clinical information, per concern

**cough** (`problems[0]`) [PMID 33658141] [PMID 34848112] [PMID 38367963] [PMID 41092546]

> For your cough: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

Citations:
- `communication_directive::global::41092546_1` → primary `41092546_1` (supports: 33658141, 34848112, 38367963, 41092546)

**headache** (`problems[1]`) [PMID 33658141] [PMID 34848112] [PMID 38367963] [PMID 41092546]

> For your headache: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

Citations:
- `communication_directive::global::41092546_1` → primary `41092546_1` (supports: 33658141, 34848112, 38367963, 41092546)

**chest pain** (`problems[2]`) [PMID 33658141] [PMID 34848112] [PMID 38367963] [PMID 41092546]

> For your chest pain: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

Citations:
- `communication_directive::global::41092546_1` → primary `41092546_1` (supports: 33658141, 34848112, 38367963, 41092546)

**depressed mood** (`problems[3]`) [PMID 33658141] [PMID 34848112] [PMID 38367963] [PMID 41092546]

> For your depressed mood: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

Citations:
- `communication_directive::global::41092546_1` → primary `41092546_1` (supports: 33658141, 34848112, 38367963, 41092546)

**goal: "I want to be straight with you — I haven't been good about taking the pills"** (`patient_goals[0]`) [PMID 33658141] [PMID 34848112] [PMID 38367963] [PMID 41092546]

> For your goal: "I want to be straight with you — I haven't been good about taking the pills": based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

Citations:
- `communication_directive::global::41092546_1` → primary `41092546_1` (supports: 33658141, 34848112, 38367963, 41092546)

**goal: "I need to be around"** (`patient_goals[1]`) [PMID 33658141] [PMID 34848112] [PMID 38367963] [PMID 41092546]

> For your goal: "I need to be around": based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

Citations:
- `communication_directive::global::41092546_1` → primary `41092546_1` (supports: 33658141, 34848112, 38367963, 41092546)

### Next steps

1. Because of the suicidal ideation, we'll start the workup today rather than wait — that includes bloodwork and a few tests to rule out the things you're most worried about.
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

- `communication_directive::global::41092546_1` · `communication_directive` · addresses=`(global)` · primary `41092546_1` · PMIDs: 33658141, 34848112, 38367963, 41092546

### All PMIDs cited (deduped)

- 33658141
- 34848112
- 38367963
- 41092546

_No glossary substitutions were needed (LLM produced plain language directly)._

---

_Generated by `scripts/run_demo.py` · mode `mock` · transcript `p002_hypertension_followup`_