# Comparison: pipeline vs. naive LLM baseline — `p001_fatigue_weightloss`

_Mode: **mock**  ·  generated: 2026-05-19T21:59:20+00:00_

## Scenario

52-year-old male contractor presenting with 1-month fatigue and unintentional ~12-pound weight loss. Father had colon cancer diagnosed late at 55. Patient and his wife both fear cancer. Wants to keep working.

## Patient transcript (input to both systems)

**Turn 1**

> I've been so tired the past month, and I've lost about 12 pounds without trying. My wife is convinced it's cancer and honestly I am too. I just want to know what's going on so I can keep working — I'm a contractor, if I can't be on my feet I can't earn.

**Turn 2**

> It started about a month ago. Some days I feel a 7 out of 10 tired — I can barely get through my shifts. I'm taking ibuprofen sometimes for headaches but nothing for the fatigue itself. Sleep is okay but I'm not waking up rested.

**Turn 3**

> No chest pain, no shortness of breath, nothing like that. No fainting, no sudden weakness on one side. But I have been getting these dull headaches in the morning, almost every day. No fevers, no blood in stool that I've seen — I'd have noticed.

**Turn 4**

> I'm on lisinopril 10 mg once a day for blood pressure, been on it for years. No allergies that I know of. My dad had colon cancer at 55 — they caught it late and he didn't make it. I don't smoke. Maybe a beer or two on the weekends.

**Turn 5**

> I'd really like to rule out the cancer thing — I want to feel safe again, you know? And I need to keep working. If we can do whatever's needed without me taking weeks off, that'd be a huge help.

## (A) Naive LLM baseline — single call, no pipeline

_System prompt to the model:_

> You are a primary-care clinician. A patient has just described their concerns to you across several turns of dialogue. Write an empathetic, clinically appropriate written response addressed to the patient. Use plain language. Keep it to one or two short paragraphs. Do not use JSON, do not use markdown headings, do not cite sources — just speak to the patient as a clinician would.

_Model's reply:_

> Thank you for sharing what's been going on — I can tell this has been a lot to carry. From what you described ("I've been so tired the past month, and I've lost about 12 pounds without trying...."), the right next step is to start with some basic workup so we can figure out what's contributing. I'd suggest we do some bloodwork and a focused exam, and then follow up in a couple of weeks to go over the results together. In the meantime, please reach out if anything gets worse or if new symptoms come up, and we'll handle it from there.

## (B) Pipeline output (Modules I–IV)

**Acknowledgment**

> I can hear how much this has been weighing on you — you said, "My wife is convinced it's cancer and honestly I am too". That's a real thing to be carrying, and I want to take it seriously while we figure out what's going on.

**Clinical information, per concern (with provenance):**

- **fatigue** (`problems[0]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]
    > For your fatigue: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **weight loss** (`problems[1]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]
    > For your weight loss: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **headache** (`problems[2]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]
    > For your headache: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **shortness of breath** (`problems[3]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]
    > For your shortness of breath: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **chest pain** (`problems[4]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]
    > For your chest pain: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **goal: "I just want to know what's going on so I can keep working — I'm a contractor, if I can't be on my feet I can't earn"** (`patient_goals[0]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]
    > For your goal: "I just want to know what's going on so I can keep working — I'm a contractor, if I can't be on my feet I can't earn": based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **goal: "I want to feel safe again, you know? And I need to keep working"** (`patient_goals[1]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]
    > For your goal: "I want to feel safe again, you know? And I need to keep working": based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **goal: "I need to keep working"** (`patient_goals[2]`) [PMID 33658141] [PMID 34448868] [PMID 41092546]
    > For your goal: "I need to keep working": based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

**Next steps:**

1. Because of the unexplained weight loss, we'll start the workup today rather than wait — that includes bloodwork and a few tests to rule out the things you're most worried about.
2. We'll go through what each step is for, so you can decide what feels right.
3. I'll have someone follow up with you in the next few days to check in and answer any questions that come up.

**Teach-back:**

> I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

**Follow-up invitation:**

> Let's plan to see each other again in 2–4 weeks. In the meantime, if anything gets worse — especially any of the warning signs we talked about — please call us right away.

## What the pipeline adds

| Dimension | Naive LLM (A) | Pipeline (B) |
|---|---|---|
| Citations to literature | none | 3 PMIDs across 1 cluster(s) |
| Per-claim provenance | unverifiable | every clinical claim links to cluster\_id → PMID |
| NURSE elements (tracked) | implicit | Name, Understand, Respect, Support |
| Four Habits elements (tracked) | implicit | Invest in the beginning, Demonstrate empathy, Elicit the patient's perspective, Invest in the end |
| Verbatim emotional cue used | not applicable | "My wife is convinced it's cancer and honestly I am too" |
| Red-flag screen | implicit / may miss | explicit; flagged: unexplained weight loss; neurologic deficit |
| Structured patient profile | none | 5 problems · 3 goals · 3 emotional cues · 2 red flags |
| Plain-language guarantee | model discretion | post-gen glossary pass (0 substitutions) |
| Audit trail | none | full intermediate artifacts at `logs/`, `manuscript/traces/` |
| Reproducibility | model-state-dependent | deterministic given same inputs |

---

_Generated by `scripts/gen_manuscript_artifacts.py`. The naive baseline is a single LLM call against the patient transcript with no intake extraction, no retrieval, no reasoning, and no framework directives — by design, to represent the control condition for the manuscript._
