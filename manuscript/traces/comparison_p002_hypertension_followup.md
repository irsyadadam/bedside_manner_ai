# Comparison: pipeline vs. naive LLM baseline — `p002_hypertension_followup`

_Mode: **mock**  ·  generated: 2026-05-19T21:59:20+00:00_

## Scenario

41-year-old female teacher returning for a hypertension follow-up. Openly admits inconsistent adherence to lisinopril 20 mg (~4/7 days), bothered by ACE-inhibitor cough, mildly worried about lightheadedness on standing. Has two young kids, father had MI at 62 (lifelong smoker), wants to avoid more medications if possible.

## Patient transcript (input to both systems)

**Turn 1**

> I'm here for my blood pressure check, but I want to be straight with you — I haven't been good about taking the pills. Some weeks I just forget, and honestly when I feel fine I don't see the point. Plus the lisinopril gives me this dry cough that drives me crazy at night.

**Turn 2**

> I take it maybe four days out of seven if I'm being generous. Mornings are the worst — I'm getting ready, the kids are losing it, and it just slips. The cough started maybe two months in and hasn't gone away. I've also had a little dizziness when I stand up fast — not bad, just a moment.

**Turn 3**

> No chest pain. No vision changes — that I'd be more worried about. I get those dizzy moments standing up but nothing where I almost fell or anything. No leg swelling. No real headaches. And no — definitely no thoughts of hurting myself or anything like that. I'm frustrated, not depressed.

**Turn 4**

> Just the lisinopril 20 mg in the morning when I take it. No other prescriptions. No allergies. My mom was on blood pressure pills for years and did okay, my dad had a heart attack at 62 but he smoked his whole life. I don't smoke. I'm trying to walk more — got an Apple Watch and it nags me, which is kind of working.

**Turn 5**

> Honestly? I want fewer pills, not more. If there's a way to get my numbers down without the cough, I'd take that. But I also don't want to do something stupid that ends with me in a hospital bed — I have two kids in elementary school. I need to be around.

## (A) Naive LLM baseline — single call, no pipeline

_System prompt to the model:_

> You are a primary-care clinician. A patient has just described their concerns to you across several turns of dialogue. Write an empathetic, clinically appropriate written response addressed to the patient. Use plain language. Keep it to one or two short paragraphs. Do not use JSON, do not use markdown headings, do not cite sources — just speak to the patient as a clinician would.

_Model's reply:_

> Thank you for sharing what's been going on — I can tell this has been a lot to carry. From what you described ("I'm here for my blood pressure check, but I want to be straight with you — I hav..."), the right next step is to start with some basic workup so we can figure out what's contributing. I'd suggest we do some bloodwork and a focused exam, and then follow up in a couple of weeks to go over the results together. In the meantime, please reach out if anything gets worse or if new symptoms come up, and we'll handle it from there.

## (B) Pipeline output (Modules I–IV)

**Acknowledgment**

> I can hear how much this has been weighing on you — you said, "No vision changes — that I'd be more worried about". That's a real thing to be carrying, and I want to take it seriously while we figure out what's going on.

**Clinical information, per concern (with provenance):**

- **cough** (`problems[0]`) [PMID 33658141] [PMID 34848112] [PMID 38367963] [PMID 41092546]
    > For your cough: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **headache** (`problems[1]`) [PMID 33658141] [PMID 34848112] [PMID 38367963] [PMID 41092546]
    > For your headache: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **chest pain** (`problems[2]`) [PMID 33658141] [PMID 34848112] [PMID 38367963] [PMID 41092546]
    > For your chest pain: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **depressed mood** (`problems[3]`) [PMID 33658141] [PMID 34848112] [PMID 38367963] [PMID 41092546]
    > For your depressed mood: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **goal: "I want to be straight with you — I haven't been good about taking the pills"** (`patient_goals[0]`) [PMID 33658141] [PMID 34848112] [PMID 38367963] [PMID 41092546]
    > For your goal: "I want to be straight with you — I haven't been good about taking the pills": based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **goal: "I need to be around"** (`patient_goals[1]`) [PMID 33658141] [PMID 34848112] [PMID 38367963] [PMID 41092546]
    > For your goal: "I need to be around": based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

**Next steps:**

1. Because of the suicidal ideation, we'll start the workup today rather than wait — that includes bloodwork and a few tests to rule out the things you're most worried about.
2. We'll go through what each step is for, so you can decide what feels right.
3. I'll have someone follow up with you in the next few days to check in and answer any questions that come up.

**Teach-back:**

> I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

**Follow-up invitation:**

> Let's plan to see each other again in 2–4 weeks. In the meantime, if anything gets worse — especially any of the warning signs we talked about — please call us right away.

## What the pipeline adds

| Dimension | Naive LLM (A) | Pipeline (B) |
|---|---|---|
| Citations to literature | none | 4 PMIDs across 1 cluster(s) |
| Per-claim provenance | unverifiable | every clinical claim links to cluster\_id → PMID |
| NURSE elements (tracked) | implicit | Name, Understand, Respect, Support |
| Four Habits elements (tracked) | implicit | Invest in the beginning, Demonstrate empathy, Elicit the patient's perspective, Invest in the end |
| Verbatim emotional cue used | not applicable | "No vision changes — that I'd be more worried about" |
| Red-flag screen | implicit / may miss | explicit; flagged: suicidal ideation |
| Structured patient profile | none | 4 problems · 2 goals · 3 emotional cues · 1 red flags |
| Plain-language guarantee | model discretion | post-gen glossary pass (0 substitutions) |
| Audit trail | none | full intermediate artifacts at `logs/`, `manuscript/traces/` |
| Reproducibility | model-state-dependent | deterministic given same inputs |

---

_Generated by `scripts/gen_manuscript_artifacts.py`. The naive baseline is a single LLM call against the patient transcript with no intake extraction, no retrieval, no reasoning, and no framework directives — by design, to represent the control condition for the manuscript._
