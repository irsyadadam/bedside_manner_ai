# Comparison: pipeline vs. naive LLM baseline — `p002_hypertension_followup`

_Mode: **real**  ·  generated: 2026-05-19T23:34:39+00:00_

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

> Okay, so I'm trying to figure out how to respond to this patient. They came in for a blood pressure check but are honest about not taking their lisinopril consistently. They mentioned forgetting, especially in the mornings when they're busy, and a persistent dry cough that's bothering them at night. They also experience some dizziness when standing up quickly.
> 
> First, I need to acknowledge their honesty and frustrations. It's important they feel heard. I should express understanding that managing medications can be tough, especially with a busy schedule. The dry cough is a known side effect of lisinopril, so I should mention that and consider alternatives.
> 
> They mentioned wanting fewer pills, so I should think about other treatment options, like lifestyle changes or different medications that don't cause the cough. Maybe diuretics or other blood pressure meds could be an option. I should also encourage them to continue with their exercise, as they have an Apple Watch, which seems to be helping.
> 
> I need to address their concerns about being around for their kids, so emphasizing the importance of managing blood pressure to prevent future health issues is key. I should suggest strategies to help them remember their meds, like setting reminders or taking them at a more convenient time.
> 
> I should also check if they're experiencing any other symptoms, but they've already listed most, so maybe just confirm that there's no chest pain or other severe issues. Finally, I should propose next steps, like adjusting their medication or discussing lifestyle changes, and reassure them that we'll work together to find a solution.
> 
> I need to keep the tone empathetic, supportive, and clear, avoiding any medical jargon. The response should be concise, maybe two paragraphs, to cover all these points without overwhelming them.
> </think>
> 
> I understand how challenging it can be to stick to a medication routine, especially when you're juggling a busy schedule and feeling fine most of the time. The dry cough from lisinopril can be really frustrating, and I'm sorry you're dealing with that. It's completely valid to want a solution that works better for you. Let's explore other options together, like different medications or lifestyle changes, to manage your blood pressure without the side effects. We can also discuss strategies to help you remember your meds, like setting reminders. Your health and being there for your kids are important, and we'll work together to find a plan that suits you best.

## (B) Pipeline output (Modules I–IV)

**Acknowledgment**

> It sounds like managing your blood pressure is really challenging for you, especially with the dry cough from the lisinopril. You mentioned, "the lisinopril gives me this dry cough that drives me crazy at night," and I can understand how frustrating that must be.

**Clinical information, per concern (with provenance):**

- **high blood pressure** (`problems[0]`) [PMID 38533994]
    > High blood pressure can be tricky to manage, especially when medications cause side effects. The good news is that there are other ways to help control it, like lifestyle changes and sometimes adjusting medications.
- **manage blood pressure** (`patient_goals[0]`) [PMID 33658141]
    > Setting clear goals for managing your blood pressure is a great first step. We'll work together to find strategies that fit your life and help you reach those goals.
- **increase physical activity** (`patient_goals[1]`) [PMID 33658141]
    > Increasing physical activity is a key part of managing blood pressure. Even small steps, like using your Apple Watch to track daily activity, can make a big difference over time.
- **fewer medications** (`patient_goals[2]`) [PMID 40577011]
    > We'll explore ways to manage your blood pressure with fewer medications, focusing on lifestyle changes and monitoring to see if adjustments can be made.
- **avoid hospitalization** (`patient_goals[3]`) [PMID 40577011]
    > Our goal is to help you manage your blood pressure in a way that keeps you out of the hospital. This includes regular monitoring and adjusting your care plan as needed.

**Next steps:**

1. We'll review your current medications and see if adjusting them could help reduce side effects.
2. Discuss lifestyle changes that can support your blood pressure management.
3. Set up a follow-up appointment in 2 weeks to check progress and make any necessary adjustments.

**Teach-back:**

> I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

**Follow-up invitation:**

> Let's plan to meet again in 2 weeks. In the meantime, if you experience severe dizziness or your blood pressure doesn't improve, please call us right away.

## What the pipeline adds

| Dimension | Naive LLM (A) | Pipeline (B) |
|---|---|---|
| Citations to literature | none | 3 PMIDs across 3 cluster(s) |
| Per-claim provenance | unverifiable | every clinical claim links to cluster\_id → PMID |
| NURSE elements (tracked) | implicit | Name, Understand, Respect, Support |
| Four Habits elements (tracked) | implicit | Invest in the beginning, Elicit the patient's perspective, Invest in the end |
| Verbatim emotional cue used | not applicable | "the lisinopril gives me this dry cough that drives me crazy at night" |
| Red-flag screen | implicit / may miss | explicit; flagged: — |
| Structured patient profile | none | 1 problems · 4 goals · 4 emotional cues · 0 red flags |
| Plain-language guarantee | model discretion | post-gen glossary pass (0 substitutions) |
| Audit trail | none | full intermediate artifacts at `logs/`, `manuscript/traces/` |
| Reproducibility | model-state-dependent | deterministic given same inputs |

---

_Generated by `scripts/gen_manuscript_artifacts.py`. The naive baseline is a single LLM call against the patient transcript with no intake extraction, no retrieval, no reasoning, and no framework directives — by design, to represent the control condition for the manuscript._
