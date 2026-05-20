# External-dataset trace — `primock57_day1_consultation13`

- Dataset: **primock57**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 55
- Gold sections: ['HIGHLIGHTS', 'PRESENTING_COMPLAINT']
- Gold note length: 847 chars

## Patient utterances (first 3)
1. [Clinician asked: "There's no <INAUDIBLE_SPEECH/>. , hello?"] . Hi there.
2. [Clinician asked: "Hello there. Um, thanks for, thanks for, being here. Um, before I go any further, can I uh, confirm your name and your age please?"] Yes, it's um Adriana Katherine . And I'm twenty six year old.
3. [Clinician asked: "<INAUDIBLE_SPEECH/> OK, Adriana, and how can I help you this afternoon?"] Well, I have this like really crazy headache that's been going on for a few days. And it really annoys me.
... (52 more)

## Gold sections
### PRESENTING_COMPLAINT

I've had a blinding headache for a few days

### HIGHLIGHTS

headache
Visual aura
photophobia
nauseous
mother and sister - migraines
migraines

## Condition: `naive`

_latency_: 21380 ms

**Response**

Adriana, I truly understand how frustrating and concerning this headache must be for you. It’s important to acknowledge how strong and brave you are for taking the time to share your symptoms with me. Based on what you’ve described, it does sound like this could be a migraine, especially considering your family history. Migraines can be quite challenging, but the good news is that we have some effective treatments to help manage the pain and prevent future episodes.

I recommend trying stronger pain relievers like Naproxen or a combination of Paracetamol and Codeine, which can be very helpful for migraines. It’s also a good idea to keep track of your symptoms and any potential triggers in a headache diary. This can provide valuable insights into what might be causing your headaches and how to avoid them in the future.

Please make sure to follow up with me in about a week to two weeks, or sooner if your symptoms worsen or if you experience any new issues like vision changes or severe weakness. In the meantime, if anything feels off or if the pain doesn’t improve, don’t hesitate to reach out. You’re not alone in this, and we’re here to support you through it. Take care, and I hope you feel better soon.


## Condition: `strong_prompt`

_latency_: 26698 ms

**Response**

Thank you for sharing your concerns with me, Adriana. It sounds like you're in a lot of discomfort, and I can understand how worrying this must be, especially given your family history of migraines. Having a severe headache for three days is exhausting, and I want to work with you to find some relief.

From what you've described, the pattern of your symptoms—aching around your right eye, sensitivity to light, and the fact that it's not improving with ibuprofen—does make me think of migraines. Since your mom and sister have them, it’s something we should consider. Migraines can run in families, and they often present with these kinds of symptoms [PMID ?]. 

For now, I’ll prescribe you a stronger anti-inflammatory, like naproxen, which can sometimes help with migraines better than ibuprofen [PMID ?]. We might also add some codeine if needed. In the meantime, I’d like you to keep track of what’s happening with your headaches—when they occur, what makes them worse or better, and any other symptoms you notice. This will help us figure out if there are triggers we can avoid.

Let’s plan to check in in about a week to see how you’re doing. If the headaches aren’t getting better or if they get worse, or if you have any new symptoms like vision changes or weakness, please give me a call right away. I want to make sure we’re on the right track.

Before you go, can you tell me in your own words what we’ve agreed on today? That way I can make sure everything makes sense to you.


## Condition: `framework_only`

_latency_: 6457 ms

**Response**

I understand you're experiencing a severe headache that's been going on for a few days, and it's been quite challenging for you.

Can you tell me, in your own words, what we discussed today and what you plan to do next?

Please let me know if your symptoms get worse or if there's anything else I can help with. We can always schedule another appointment if needed.


## Condition: `retrieval_only`

_latency_: 200010 ms

**Extracted profile (summary)**
```yaml
n_problems: 3
n_medications: 0
n_allergies: 0
n_red_flags: 1
n_emotional: 1
n_goals: 0
problems:
- crazy headache
- vision disturbances
- difficulty focusing
medications: []
allergies: []
```

**Response**

I can hear how frustrating this must be for you. You mentioned, "But it doesn't really help, no. In the past it did help me, which is why I decided to try it. But..." I understand how that can feel overwhelming.

Headaches that come and go but are always present can be concerning. The current guidance suggests evaluating for potential causes, especially when combined with other symptoms like vision changes.

Vision disturbances can be a sign of various conditions and should be evaluated carefully. The recommended approach is to conduct a thorough assessment to identify potential causes.

Difficulty focusing can be related to multiple factors and may require further investigation to determine the underlying cause.

Given the neurological red flag you mentioned, we'll prioritize evaluating the vision disturbances and headaches first. This may include some tests to rule out specific causes.

We'll schedule a follow-up appointment in the next week to review the results and discuss the next steps together.

If you experience any severe symptoms like sudden vision loss or intense headaches, please reach out immediately.

I want to make sure I explained this clearly. Can you tell me, in your own words, what we're going to do next and why?

Let's plan to meet again in a week. If you notice any new symptoms or if things get worse, please don't wait—contact us right away.

_cited PMIDs_: ['35608838']

_NURSE_: ['Name', 'Understand', 'Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Demonstrate empathy', 'Invest in the end']

## Condition: `full`

_latency_: 239319 ms

**Extracted profile (summary)**
```yaml
n_problems: 3
n_medications: 0
n_allergies: 0
n_red_flags: 1
n_emotional: 0
n_goals: 0
problems:
- crazy headache
- vision disturbances
- difficulty focusing
medications: []
allergies: []
```

**Response**

I understand you're experiencing a lot of challenges right now, especially with the headaches and vision issues. Your concerns are important, and I want to make sure we address them thoroughly.

Headaches that are persistent and worsening can be concerning. The primary consideration here is to rule out more serious causes, and the guidance suggests that we should approach this with thorough testing rather than waiting.

Vision disturbances can be a sign of various issues, and the current evidence suggests that we should evaluate this carefully. However, there isn't specific guidance on how to proceed with this particular concern.

Difficulty focusing can be related to multiple factors, and while we don't have specific guidelines for this exact situation, we'll work together to explore possible causes and next steps.

Given the red flag of neurological symptoms, we'll prioritize evaluating the vision disturbances and headaches. This includes ordering specific tests to rule out more serious conditions.

We'll schedule a follow-up appointment to review the test results and discuss any further actions needed.

If you experience any severe symptoms, such as vision loss or intense headaches, please contact us immediately.

I want to make sure I explained this clearly. Can you tell me, in your own words, what we're going to do next and why?

Let's plan to meet again in two weeks. If you notice any new symptoms or if your current symptoms worsen, please reach out to us as soon as possible.

_cited PMIDs_: ['35709018']

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Demonstrate empathy', 'Invest in the end']
