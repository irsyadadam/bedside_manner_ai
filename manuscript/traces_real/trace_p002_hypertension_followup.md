# Pipeline trace — `p002_hypertension_followup`

_Mode: **real**  ·  Generated: 2026-05-19T22:53:27+00:00_

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

> When did the high blood pressure first start?

**Patient:**

> Just the lisinopril 20 mg in the morning when I take it. No other prescriptions. No allergies. My mom was on blood pressure pills for years and did okay, my dad had a heart attack at 62 but he smoked his whole life. I don't smoke. I'm trying to walk more — got an Apple Watch and it nags me, which is kind of working.

**Turn 5** — *agent (templated):*

> When did the high blood pressure first start?

**Patient:**

> Honestly? I want fewer pills, not more. If there's a way to get my numbers down without the cough, I'd take that. But I also don't want to do something stupid that ends with me in a hospital bed — I have two kids in elementary school. I need to be around.

_Intake completion at last turn: **False** (status: `in_progress`)_

## Final `PatientConcernProfile`

```yaml
problems:
- label: high blood pressure
  onset: null
  severity: null
  timing: about four days a week
  associated_symptoms:
  - dry cough
  - dizziness upon standing
  interventions_tried:
  - lisinopril
  status: unknown
medications:
- lisinopril (20 mg, daily)
allergies:
- No known allergies
relevant_history:
- 'Family history: mother on blood pressure pills, father had heart attack at 62 (smoker)'
- 'Lifestyle: non-smoker, trying to increase physical activity with Apple Watch'
patient_goals:
- manage blood pressure
- increase physical activity
- fewer medications
- avoid hospitalization
emotional_cues:
- cue: frustration
  evidence_quote: I take it maybe four days out of seven if I'm being generous. Mornings
    are the worst — I'm getting ready, the kids are losing it, and it just slips.
- cue: frustration
  evidence_quote: the lisinopril gives me this dry cough that drives me crazy at night
- cue: frustration
  evidence_quote: I'm frustrated, not depressed
- cue: worry
  evidence_quote: I don't want to do something stupid that ends with me in a hospital
    bed — I have two kids in elementary school. I need to be around.
red_flags: []
unknowns:
- problems[0].onset
- problems[0].severity
- red_flag_screen_complete
turn_count: 5
completion_status: in_progress
```

## Top 5 retrieved documents (Module II)

Sub-queries decomposed: **6**.  top_k chunks/sub-query: **20**.  Graph expansion: `stub`.  Rerank weights: `{'semantic_similarity': 0.5, 'recency': 0.2, 'authority': 0.2, 'coverage_bonus': 0.1}`.

| Rank | PMID | Year | Journal | sem | rec | aut | cov | total | Title |
|---:|---|---:|---|---:|---:|---:|---:|---:|---|
| 1 | 40577011 | 2025 | JAMA network open | 0.704 | 0.88 | 0.82 | 0.17 | 0.707 | Interventions to Address Potentially Inappropriate Prescribing for Older Primary Care Patients: A Sy |
| 2 | 38533994 | 2024 | The Cochrane database of systematic reviews | 0.665 | 0.75 | 0.98 | 0.17 | 0.695 | Mobile phone text messaging for medication adherence in secondary prevention of cardiovascular disea |
| 3 | 38604640 | 2024 | BMJ open | 0.651 | 0.75 | 0.80 | 0.17 | 0.652 | Do patients with type 2 diabetes mellitus included in randomised clinical trials differ from general |
| 4 | 33658141 | 2021 | Patient education and counseling | 0.713 | 0.38 | 0.80 | 0.50 | 0.642 | Communicating with older adults with long-term conditions about self-management goals: A systematic  |
| 5 | 33464342 | 2021 | JAMA | 0.639 | 0.38 | 1.00 | 0.00 | 0.595 | Interventions for Tobacco Cessation in Adults, Including Pregnant Persons: Updated Evidence Report a |

## `StructuredContextArtifact` (Module III)

- Documents processed: **5**  · Assertions extracted: **19**  · Clusters: **9** (convergent=5, divergent=4)  · Similarity threshold: **0.75**

### Cluster 1 · DIVERGENT · `recommendation` · addresses=`patient_goals` · confidence=0.90

**Primary** (`33658141_0`, conf=0.90): Healthcare professionals should encourage older adults to engage actively with shared decision-making (SDM) and goal setting.

> _evidence_: We encourage HCPs to prepare older adults to engage actively with SDM and the goal setting process

**Alternatives (1):**
- `33658141_1` (conf=0.85) — Patient-centred communication resources can help identify realistic and relevant goals for older adults in daily life.

_Resolution rule: **confidence** — Recency: Both assertions are from the same 2021 publication, so recency does not resolve the tie. Next, authority score: both are from 'Patient education and counseling' with a score of 0.8. Moving to evidence strength, both are Journal Articles and Systematic Reviews, so no difference there. Coverage is the same as both address patient_goals. Finally, confidence is higher in the second assertion (0.85 vs 0.9), but since confidence is the last tiebreaker, the first assertion is chosen as primary based on the order of application of the rules._

Supporting PMIDs (1): 33658141

### Cluster 2 · DIVERGENT · `finding` · addresses=`problems[0]` · confidence=0.60

**Primary** (`38533994_0`, conf=0.60): Mobile phone text messaging may have little to no effect on systolic blood pressure compared to usual care.

> _evidence_: text messaging may have little to no effect on systolic blood pressure

**Alternatives (3):**
- `38533994_1` (conf=0.60) — Mobile phone text messaging may have little to no effect on diastolic blood pressure compared to usual care.
- `38533994_2` (conf=0.60) — Mobile phone text messaging may have little to no effect on low-density lipoprotein cholesterol compared to usual care.
- `38533994_3` (conf=0.60) — Mobile phone text messaging may have little to no effect on heart rate compared to usual care.

_Resolution rule: **coverage** — Recency: All assertions are from the same 2024 publication, so recency does not resolve the tie. Next, authority: all are from the Cochrane Database of Systematic Reviews with a high authority score of 0.98. Since all have the same authority, we look at evidence strength. All are Journal Articles, Systematic Reviews, and Meta-Analyses, which are the highest ranked. Finally, coverage: each assertion addresses a different aspect of problems[0], so all are retained as alternatives._

Supporting PMIDs (1): 38533994

### Cluster 3 · CONVERGENT · `finding` · addresses=`sub_query[3]` · confidence=0.90

**Primary** (`40577011_0`, conf=0.90): Interventions to address potentially inappropriate prescribing were associated with a reduction in the number of medications prescribed.

> _evidence_: Interventions to address potentially inappropriate prescribing were associated with a reduction in the number of medications prescribed

Supporting PMIDs (1): 40577011

### Cluster 4 · CONVERGENT · `finding` · addresses=`sub_query[3]` · confidence=0.85

**Primary** (`40577011_1`, conf=0.85): There were no substantial differences in nonserious adverse drug reactions, injurious falls, quality of life, medical visits, emergency department admissions, hospitalizations, or all-cause mortality.

> _evidence_: there were no substantial differences in the other outcomes

Supporting PMIDs (1): 40577011

### Cluster 5 · CONVERGENT · `finding` · addresses=`(global)` · confidence=0.90

**Primary** (`33464342_2`, conf=0.90): Among pregnant persons, behavioral interventions were associated with greater smoking cessation during late pregnancy compared with no intervention.

> _evidence_: Among pregnant persons, behavioral interventions were associated with greater smoking cessation during late pregnancy (RR, 1.35 [95% CI, 1.23-1.48]), compared with no intervention.

Supporting PMIDs (1): 33464342

### Cluster 6 · CONVERGENT · `finding` · addresses=`(global)` · confidence=0.90

**Primary** (`33464342_3`, conf=0.90): Rates of validated cessation among pregnant women allocated to NRT compared with placebo were not significantly different.

> _evidence_: Rates of validated cessation among pregnant women allocated to NRT compared with placebo were not significantly different (pooled RR, 1.11 [95% CI, 0.79-1.56], n = 2033).

Supporting PMIDs (1): 33464342

### Cluster 7 · CONVERGENT · `finding` · addresses=`(global)` · confidence=0.75

**Primary** (`33464342_4`, conf=0.75): Data on the effectiveness and safety of electronic cigarettes for smoking cessation among adults are limited and results are inconsistent.

> _evidence_: Data on the effectiveness and safety of electronic cigarettes for smoking cessation among adults are also limited and results are inconsistent.

Supporting PMIDs (1): 33464342

### Cluster 8 · DIVERGENT · `finding` · addresses=`(global)` · confidence=0.90

**Primary** (`38604640_0`, conf=0.90): Patients with type 2 diabetes mellitus in general practice are older than those in randomised controlled trials.

> _evidence_: General-practice patients were older than randomised controlled trial patients (mean (SD) 68.8 (1.1) vs 59.9 years (standardised difference 0.8))

**Alternatives (5):**
- `38604640_1` (conf=0.90) — General-practice patients with type 2 diabetes mellitus have a higher body mass index compared to those in randomised controlled trials.
- `38604640_2` (conf=0.90) — General-practice patients smoke less than those included in randomised controlled trials.
- `38604640_3` (conf=0.90) — General-practice patients more frequently use antihypertensive drugs compared to randomised controlled trial patients.
- `38604640_4` (conf=0.90) — General-practice patients have a lower incidence of myocardial infarction compared to randomised controlled trial patients.
- ... and 1 more

_Resolution rule: **recency** — Recency: All assertions are from the same 2024 publication; rule 1 does not resolve the tie. Next, authority score is the same for all (0.8); rule 2 does not resolve. Pub_types are identical, so rule 3 does not help. Coverage is the same as all address the same concern; rule 4 does not help. Finally, confidence is the same, so rule 5 does not apply. Since all rules are tied, any assertion can be primary, but we select the first one._

Supporting PMIDs (1): 38604640

### Cluster 9 · DIVERGENT · `finding` · addresses=`(global)` · confidence=0.90

**Primary** (`33464342_0`, conf=0.90): Combined pharmacotherapy and behavioral interventions are associated with increased quit rates compared with minimal support or placebo at 6 months or longer.

> _evidence_: Combined pharmacotherapy and behavioral interventions (pooled risk ratio [RR], 1.83 [95% CI, 1.68-1.98]), NRT (RR, 1.55 [95% CI, 1.49-1.61]), bupropion (RR, 1.64 [95% CI, 1.52-1.77]), varenicline (RR, 2.24 [95% CI, 2.06-2.43]), and behavioral interventions such as advice from clinicians (RR, 1.76 [9

**Alternatives (1):**
- `33464342_1` (conf=0.90) — Behavioral interventions such as advice from clinicians are associated with increased quit rates compared with minimal support or placebo at 6 months or longer.

_Resolution rule: **evidence_strength** — Recency: Both assertions are from the same 2021 publication, so recency does not resolve the tie. Next, authority is considered, but both are from JAMA with the same authority score. Moving to evidence strength, the first assertion is a Systematic Review, which is higher than the second's Journal Article. Therefore, the first assertion is selected as primary._

Supporting PMIDs (1): 33464342

**Limitations recorded by Module III:**
- Abstracts-only prototype: assertion granularity is coarser than a full-text system would produce.
- Module II graph expansion is stubbed in v0 (flat vector retrieval). See clinicomm.modules.m2_retrieval.expand_neighborhood.

## Final `PatientResponse` (Module IV)

### Acknowledgment

> It sounds like managing your blood pressure is really challenging for you, especially with the dry cough from the lisinopril. You mentioned, "the lisinopril gives me this dry cough that drives me crazy at night," and I can understand how frustrating that must be.

### Clinical information, per concern

**high blood pressure** (`problems[0]`) [PMID 38533994]

> High blood pressure can be tricky to manage, especially when medications cause side effects. The good news is that there are other ways to help control it, like lifestyle changes and sometimes adjusting medications.

Citations:
- `finding::problems[0]::38533994_0` → primary `38533994_0` (supports: 38533994)

**manage blood pressure** (`patient_goals[0]`) [PMID 33658141]

> Setting clear goals for managing your blood pressure is a great first step. We'll work together to find strategies that fit your life and help you reach those goals.

Citations:
- `recommendation::patient_goals::33658141_0` → primary `33658141_0` (supports: 33658141)

**increase physical activity** (`patient_goals[1]`) [PMID 33658141]

> Increasing physical activity is a key part of managing blood pressure. Even small steps, like using your Apple Watch to track daily activity, can make a big difference over time.

Citations:
- `recommendation::patient_goals::33658141_0` → primary `33658141_0` (supports: 33658141)

**fewer medications** (`patient_goals[2]`) [PMID 40577011]

> We'll explore ways to manage your blood pressure with fewer medications, focusing on lifestyle changes and monitoring to see if adjustments can be made.

Citations:
- `finding::sub_query[3]::40577011_0` → primary `40577011_0` (supports: 40577011)

**avoid hospitalization** (`patient_goals[3]`) [PMID 40577011]

> Our goal is to help you manage your blood pressure in a way that keeps you out of the hospital. This includes regular monitoring and adjusting your care plan as needed.

Citations:
- `finding::sub_query[3]::40577011_0` → primary `40577011_0` (supports: 40577011)

### Next steps

1. We'll review your current medications and see if adjusting them could help reduce side effects.
2. Discuss lifestyle changes that can support your blood pressure management.
3. Set up a follow-up appointment in 2 weeks to check progress and make any necessary adjustments.

### Teach-back prompt

> I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

### Follow-up invitation

> Let's plan to meet again in 2 weeks. In the meantime, if you experience severe dizziness or your blood pressure doesn't improve, please call us right away.

## Provenance appendix

### Framework elements applied

- **NURSE** elements applied: ['Name', 'Understand', 'Respect', 'Support']
- **Four Habits** elements applied: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']

### Cluster → PMIDs used in the response

- `recommendation::patient_goals::33658141_0` · `recommendation` · addresses=`patient_goals` · primary `33658141_0` · PMIDs: 33658141
- `finding::problems[0]::38533994_0` · `finding` · addresses=`problems[0]` · primary `38533994_0` · PMIDs: 38533994
- `finding::sub_query[3]::40577011_0` · `finding` · addresses=`sub_query[3]` · primary `40577011_0` · PMIDs: 40577011

### All PMIDs cited (deduped)

- 38533994
- 33658141
- 40577011

_No glossary substitutions were needed (LLM produced plain language directly)._

---

_Generated by `scripts/run_demo.py` · mode `real` · transcript `p002_hypertension_followup`_