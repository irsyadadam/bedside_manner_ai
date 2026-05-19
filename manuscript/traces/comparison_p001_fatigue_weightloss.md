# Comparison: pipeline vs. naive LLM baseline — `p001_fatigue_weightloss`

_Mode: **real**  ·  generated: 2026-05-19T23:34:22+00:00_

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

> Okay, so I need to respond to this patient who's been feeling really tired and losing weight without trying. He's worried about cancer, especially since his dad had colon cancer. He's a contractor and can't afford to take weeks off, so he wants to know what's going on quickly.
> 
> First, I should acknowledge his concerns. He's been feeling this way for a month, which is significant. The weight loss is a red flag, especially with family history. I should empathize with his worry but also explain that there are other possible causes for his symptoms.
> 
> He mentioned fatigue, headaches, and trouble sleeping. No chest pain or other severe symptoms, which is good. He's on lisinopril, so I should consider other possibilities like thyroid issues, anemia, or maybe something else metabolic. His BP is under control, so that's not the main issue.
> 
> I need to suggest some tests. Maybe a CBC to check for anemia, a thyroid panel, liver function tests, and a basic metabolic panel. If those come back normal, we can rule out some common issues. If not, further steps like imaging or a colonoscopy might be needed.
> 
> I should reassure him that we'll get to the bottom of it without making him take too much time off. Emphasize that early detection is key and that we're taking it step by step. Let him know that his concerns are valid and that we're working together on this.
> 
> I should keep the tone empathetic and supportive, letting him know that his health is a priority but also understanding his need to work. Make sure he feels heard and that we're moving forward with a plan.
> </think>
> 
> I understand how concerning this must be for you, especially given your family history and how your symptoms are impacting your work and daily life. It’s important to address these concerns thoroughly, and I want to reassure you that we’ll work together to get to the bottom of what’s going on.
> 
> Given your symptoms—fatigue, weight loss, and headaches—it’s important to rule out potential causes systematically. We’ll start with some basic tests, like blood work to check for anemia, thyroid function, and other metabolic issues, as well as a urinalysis. Depending on the results, we may consider imaging or other specialized tests. The good news is that many conditions are easier to manage when diagnosed early, and we’re taking steps to ensure we identify whatever is causing your symptoms.
> 
> In the meantime, let’s focus on managing your energy levels and symptoms. We’ll create a plan that allows you to continue working while we gather more information. Your health is our priority, and I’m here to support you through this process. Together, we’ll make sure you feel safe and get the answers you need.

## (B) Pipeline output (Modules I–IV)

**Acknowledgment**

> I can hear how much this has been worrying you — you mentioned, "My wife is convinced it's cancer and honestly I am too." That's a real concern, and I want to make sure we address it carefully.

**Clinical information, per concern (with provenance):**

- **persistent fatigue** (`problems[0]`) [PMID 38604640]
    > Persistent fatigue, especially when it's getting worse and linked to unexplained weight loss, can be a sign of several health issues. We'll need to look into this more thoroughly to understand what's going on.
- **unintentional weight loss** (`problems[1]`) [PMID 38604640]
    > Unexplained weight loss, especially over a short period, can be a red flag for various health conditions. It's important to investigate this to rule out serious issues.
- **dull headaches** (`problems[2]`) [PMID 38604640]
    > Dull headaches that happen almost every day could be related to stress or other underlying issues. We'll keep an eye on this as we work through your other concerns.
- **find out what's going on** (`patient_goals[0]`) [PMID 38604640]
    > Our main goal is to figure out what's causing these symptoms. We'll start with some tests to get a clearer picture.
- **keep working** (`patient_goals[1]`) [PMID 38604640]
    > We'll work together to manage your health so you can stay active and continue working. Your ability to work is important, and we'll keep that in mind as we move forward.
- **feel safe** (`patient_goals[2]`) [PMID 38604640]
    > We'll make sure you understand the steps we're taking so you feel reassured about your health and treatment.

**Next steps:**

1. Given the red flag of unexplained weight loss, we'll prioritize some immediate tests to get a clearer picture of what's going on.
2. We'll schedule a follow-up visit in 4 weeks to review the results and discuss the next steps.
3. If any test results come back early, I'll reach out to you right away to keep you informed.

**Teach-back:**

> I want to make sure I explained everything clearly. Can you tell me, in your own words, what we're going to do next and why?

**Follow-up invitation:**

> Let's plan to meet again in 4 weeks. In the meantime, if you experience any new symptoms like severe pain or if your fatigue gets much worse, please call us immediately.

## What the pipeline adds

| Dimension | Naive LLM (A) | Pipeline (B) |
|---|---|---|
| Citations to literature | none | 1 PMIDs across 1 cluster(s) |
| Per-claim provenance | unverifiable | every clinical claim links to cluster\_id → PMID |
| NURSE elements (tracked) | implicit | Name, Understand, Respect, Support |
| Four Habits elements (tracked) | implicit | Invest in the beginning, Elicit the patient's perspective, Demonstrate empathy, Invest in the end |
| Verbatim emotional cue used | not applicable | "My wife is convinced it's cancer and honestly I am too" |
| Red-flag screen | implicit / may miss | explicit; flagged: unexplained weight loss |
| Structured patient profile | none | 3 problems · 3 goals · 4 emotional cues · 1 red flags |
| Plain-language guarantee | model discretion | post-gen glossary pass (0 substitutions) |
| Audit trail | none | full intermediate artifacts at `logs/`, `manuscript/traces/` |
| Reproducibility | model-state-dependent | deterministic given same inputs |

---

_Generated by `scripts/gen_manuscript_artifacts.py`. The naive baseline is a single LLM call against the patient transcript with no intake extraction, no retrieval, no reasoning, and no framework directives — by design, to represent the control condition for the manuscript._
