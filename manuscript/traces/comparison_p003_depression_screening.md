# Comparison: pipeline vs. naive LLM baseline — `p003_depression_screening`

_Mode: **real**  ·  generated: 2026-05-19T23:35:05+00:00_

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

> Okay, so I'm trying to figure out how to respond to this patient. They've been feeling really tired, their sleep is all over the place, and they're not eating much. They lost some weight without trying, which is concerning. They also mention not feeling joy anymore and even having thoughts about self-harm, though they don't act on them. Their last bloodwork was fine, but they're still worried something's wrong.
> 
> First, I need to acknowledge their feelings. They seem to be going through a tough time, so empathy is key. I should validate their symptoms and let them know it's okay to feel this way. They mentioned not wanting to be on pills long-term, so I should consider non-medical options first, like lifestyle changes or therapy.
> 
> They have a history of depression in the family, which might be relevant. Their past use of Lexapro suggests they've dealt with mental health before, but they're looking for alternatives now. I should explore other treatment options, maybe starting with therapy or lifestyle adjustments before considering medication again.
> 
> Their partner brought them in, so support systems are in place. That's a positive point. I should encourage them to lean on their partner and family. Also, their loss of interest in activities they used to enjoy points towards depression, so that's something to consider.
> 
> I need to address their sleep issues specifically. Maybe suggest some sleep hygiene practices. They mentioned using melatonin, so perhaps we can talk about other strategies to improve sleep without medication.
> 
> They expressed a desire to feel like themselves again, so setting realistic goals for improvement is important. I should reassure them that with the right support, they can feel better. It's also crucial to take their concerns seriously, even though their bloodwork is normal, because mental health can have physical symptoms.
> 
> I should structure the response to first empathize, then discuss possible steps, and end with encouragement and next steps. Keep it supportive and understanding, avoiding any medical jargon. Make sure they feel heard and that we're working together on this.
> </think>
> 
> I'm really sorry to hear you're going through this tough time. It sounds like you're feeling overwhelmed, exhausted, and disconnected from the things you used to enjoy. I want to acknowledge how strong you are for reaching out and being honest about your feelings, even though it's been hard. It's completely valid to feel this way, and you're not alone in this.
> 
> Given your symptoms—constant fatigue, disrupted sleep, loss of appetite, and a lack of joy—it’s important to explore what might be contributing to how you're feeling. While your bloodwork came back normal, we can still look into other areas, like your mental health, to see if there's a way to help you feel better. Since you’ve mentioned a history of depression in your family and your own experience with Lexapro in the past, we might consider whether depression is playing a role here. 
> 
> I understand you’re hesitant about long-term medication, and that’s okay. Let’s start by exploring other options, like lifestyle changes, therapy, or other non-medical approaches, to see if they can help you get back to feeling like yourself. We can also work on improving your sleep and energy levels, as these are key to your overall well-being. 
> 
> You’re doing the right thing by leaning on your partner and mom, and I encourage you to continue to rely on them for support. Together, we’ll take small steps toward helping you feel more like yourself again. Let’s schedule a time to talk more about your goals and what feels like the right path forward for you. You’ve already taken a brave step by being here, and I’m here to support you through this.

## (B) Pipeline output (Modules I–IV)

**Acknowledgment**

> I can hear how much this has been affecting you. You mentioned, "And nothing really brings me joy anymore" and "I think about it more than I'd like to admit," which shows how much this is weighing on you. I want to make sure we address these feelings while we figure out what's going on.

**Clinical information, per concern (with provenance):**

- **persistent fatigue** (`problems[0]`) [PMID 41031717]
    > Persistent fatigue, especially when combined with loss of appetite and thoughts of self-harm, can be a sign of underlying issues like depression. We'll start by looking into common causes of fatigue and your mental health.
- **find out what's causing the fatigue** (`patient_goals[0]`) [PMID 41031717]
    > To find out what's causing your fatigue, we'll start with some basic tests to check for common causes like vitamin deficiencies or thyroid issues. We'll also review your current medications to see if they might be contributing.
- **restore joy in life** (`patient_goals[1]`) [PMID 41092546]
    > Given your feelings of sadness and hopelessness, we should also explore ways to address your mental health. This might include therapy or other non-medical approaches you prefer.
- **sleep through the night** (`patient_goals[2]`) [PMID 41031717]
    > We'll also look into why you're having trouble sleeping. This could be related to your fatigue or stress, and we can suggest some strategies to help improve your sleep hygiene.
- **want to do things again** (`patient_goals[3]`) [PMID 41031717]
    > To help you get back to doing things you enjoy, we'll focus on improving your energy levels and mental well-being. This might involve a combination of medical treatment and lifestyle changes.
- **prefer non-pharmacological treatments first** (`patient_goals[4]`) [PMID 41031717]
    > We'll prioritize non-medical approaches first, such as therapy and lifestyle changes, to help you manage your symptoms.

**Next steps:**

1. Given your thoughts of self-harm, we need to address this urgently. We'll connect you with a mental health professional right away.
2. We'll schedule a blood test to check for common causes of fatigue, such as vitamin deficiencies or thyroid issues.
3. We'll review your current medications to see if they might be contributing to your fatigue.
4. We'll explore non-pharmacological treatment options, like therapy, to help improve your mental health and energy levels.
5. We'll discuss strategies to improve your sleep hygiene to help you sleep through the night.

**Teach-back:**

> I want to make sure I explained this clearly. Can you tell me, in your own words, what we're going to do next and why?

**Follow-up invitation:**

> Let's plan to see each other again in 2 weeks. In the meantime, if you feel overwhelmed or have any new symptoms, please call us right away.

## What the pipeline adds

| Dimension | Naive LLM (A) | Pipeline (B) |
|---|---|---|
| Citations to literature | none | 2 PMIDs across 2 cluster(s) |
| Per-claim provenance | unverifiable | every clinical claim links to cluster\_id → PMID |
| NURSE elements (tracked) | implicit | Name, Understand, Respect, Support |
| Four Habits elements (tracked) | implicit | Invest in the beginning, Elicit the patient's perspective, Demonstrate empathy, Invest in the end |
| Verbatim emotional cue used | not applicable | "And nothing really brings me joy anymore" |
| Red-flag screen | implicit / may miss | explicit; flagged: suicidal ideation |
| Structured patient profile | none | 1 problems · 5 goals · 3 emotional cues · 1 red flags |
| Plain-language guarantee | model discretion | post-gen glossary pass (0 substitutions) |
| Audit trail | none | full intermediate artifacts at `logs/`, `manuscript/traces/` |
| Reproducibility | model-state-dependent | deterministic given same inputs |

---

_Generated by `scripts/gen_manuscript_artifacts.py`. The naive baseline is a single LLM call against the patient transcript with no intake extraction, no retrieval, no reasoning, and no framework directives — by design, to represent the control condition for the manuscript._
