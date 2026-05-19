# Comparison: pipeline vs. naive LLM baseline — `p003_depression_screening`

_Mode: **mock**  ·  generated: 2026-05-19T21:59:20+00:00_

## Scenario

34-year-old graphic designer, female, presenting with several months of fatigue, hypersomnia, anorexia, anhedonia, and passive suicidal ideation on screening. Prior episode after father's death ten years ago, treated with escitalopram for ~18 months. Currently no antidepressant. Maternal hx of depression. Partner urged the visit.

## Patient transcript (input to both systems)

**Turn 1**

> I don't know if I should be here for this. I'm just tired all the time, my sleep is a mess, and I don't really want to eat. My partner said I should come in. I keep thinking something must be wrong but my last bloodwork was fine.

**Turn 2**

> It's been a few months I guess. The tiredness is constant. I sleep for ten hours and feel like I haven't slept at all. I've lost some weight too, maybe six or seven pounds, but I'm not trying. And nothing really brings me joy anymore. I used to love hiking — I haven't been once this year.

**Turn 3**

> No chest pain or anything physical like that. No bleeding. About thoughts of hurting myself — there's been a few times when I wondered if it would be easier if I weren't here, but I wouldn't actually do anything. I have my partner, my mom. I'm not going to do that to them. But I think about it more than I'd like to admit.

**Turn 4**

> I'm not on anything regular. I take melatonin some nights for sleep. No allergies. I was on Lexapro for about a year and a half, ten years ago after my dad died — it helped at the time. No other medical issues. My mom had depression too.

**Turn 5**

> I just want to feel like myself again. I don't want to be on pills long-term — I really didn't like being on Lexapro for that long. If we could try something else first, I'd prefer that. Mostly I want to sleep through the night and actually want to do things again.

## (A) Naive LLM baseline — single call, no pipeline

_System prompt to the model:_

> You are a primary-care clinician. A patient has just described their concerns to you across several turns of dialogue. Write an empathetic, clinically appropriate written response addressed to the patient. Use plain language. Keep it to one or two short paragraphs. Do not use JSON, do not use markdown headings, do not cite sources — just speak to the patient as a clinician would.

_Model's reply:_

> Thank you for sharing what's been going on — I can tell this has been a lot to carry. From what you described ("I don't know if I should be here for this. I'm just tired all the time, my sleep..."), the right next step is to start with some basic workup so we can figure out what's contributing. I'd suggest we do some bloodwork and a focused exam, and then follow up in a couple of weeks to go over the results together. In the meantime, please reach out if anything gets worse or if new symptoms come up, and we'll handle it from there.

## (B) Pipeline output (Modules I–IV)

**Acknowledgment**

> I can hear how much this has been weighing on you — you said, "I was on Lexapro for about a year and a half, ten years ago after my dad died — it helped at the time". That's a real thing to be carrying, and I want to take it seriously while we figure out what's going on.

**Clinical information, per concern (with provenance):**

- **fatigue** (`problems[0]`) [PMID 32284167] [PMID 33658141] [PMID 34448868] [PMID 41092546]
    > For your fatigue: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **weight loss** (`problems[1]`) [PMID 32284167] [PMID 33658141] [PMID 34448868] [PMID 41092546]
    > For your weight loss: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **chest pain** (`problems[2]`) [PMID 32284167] [PMID 33658141] [PMID 34448868] [PMID 41092546]
    > For your chest pain: based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **goal: "I'd like to admit"** (`patient_goals[0]`) [PMID 32284167] [PMID 33658141] [PMID 34448868] [PMID 41092546]
    > For your goal: "I'd like to admit": based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **goal: "I just want to feel like myself again"** (`patient_goals[1]`) [PMID 32284167] [PMID 33658141] [PMID 34448868] [PMID 41092546]
    > For your goal: "I just want to feel like myself again": based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.
- **goal: "I want to sleep through the night and actually want to do things again"** (`patient_goals[2]`) [PMID 32284167] [PMID 33658141] [PMID 34448868] [PMID 41092546]
    > For your goal: "I want to sleep through the night and actually want to do things again": based on current guidance, Use patient-centered communication strategies (plain language, teach-back, shared decision-making) when discussing this concern.

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
| Verbatim emotional cue used | not applicable | "I was on Lexapro for about a year and a half, ten years ago after my dad died — it helped at the time" |
| Red-flag screen | implicit / may miss | explicit; flagged: suicidal ideation |
| Structured patient profile | none | 3 problems · 3 goals · 1 emotional cues · 1 red flags |
| Plain-language guarantee | model discretion | post-gen glossary pass (0 substitutions) |
| Audit trail | none | full intermediate artifacts at `logs/`, `manuscript/traces/` |
| Reproducibility | model-state-dependent | deterministic given same inputs |

---

_Generated by `scripts/gen_manuscript_artifacts.py`. The naive baseline is a single LLM call against the patient transcript with no intake extraction, no retrieval, no reasoning, and no framework directives — by design, to represent the control condition for the manuscript._
