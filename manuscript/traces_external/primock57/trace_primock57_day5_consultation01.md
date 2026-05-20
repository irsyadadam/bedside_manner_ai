# External-dataset trace — `primock57_day5_consultation01`

- Dataset: **primock57**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 50
- Gold sections: ['HIGHLIGHTS', 'PRESENTING_COMPLAINT']
- Gold note length: 971 chars

## Patient utterances (first 3)
1. [Clinician asked: "Ohh, hello."] <INAUDIBLE_SPEECH/>
2. [Clinician asked: "Hello. I'm Doctor Geraghty. Ohh,  sorry. <INAUDIBLE_SPEECH/>. Can I take your, full name, date of birth, and, your home address please?"] Uh, yeah it's uh, . Um, and, five, um, Kings Place.
3. [Clinician asked: "<INAUDIBLE_SPEECH/> And are you in a, uh, and your date of birth?"] Uh, it's the twentieth, of the fourth, nineteen ninety.
... (47 more)

## Gold sections
### PRESENTING_COMPLAINT

I have a headache

### HIGHLIGHTS

Left sided headache
Intermittent
Non positional
Doesn't feel feverish
No tingling/numbness/weakness/rash
Worse with light but vision not altered

## Condition: `naive`

_latency_: 26023 ms

**Response**

Hello [Patient's Name],

Thank you for sharing your symptoms with me. I can tell how uncomfortable and frustrated you must be feeling with this persistent headache. It's important to acknowledge how challenging this must be for you.

Based on your description, it sounds like you might be experiencing a migraine, which can be quite intense and debilitating. However, since you don't have a prior history of headaches, I'll also consider other possibilities. To help alleviate your symptoms, I recommend taking Ibuprofen if you're not allergic, along with staying well-hydrated and resting in a dark, quiet environment. Keep an eye on your symptoms—if the pain worsens, or if you develop a fever or new symptoms, please seek immediate care.

It might also be a good idea to monitor your blood pressure, as high blood pressure can sometimes cause headaches. If the headache doesn't improve with these steps, or if you're concerned, please don't hesitate to reach out for further evaluation.

I hope you start feeling better soon. Take care of yourself and let me know if you need anything else.

Warm regards,  
[Your Name]


## Condition: `strong_prompt`

_latency_: 33812 ms

**Response**

Thank you for sharing your concerns with me. It sounds like you're feeling quite unwell with this sudden, severe headache, and I can understand how worrying that must be, especially since it's something you haven't experienced before. It's important to take this seriously and explore what might be causing it.

Given your symptoms—throbbing pain on the left side, sensitivity to light, and the fact that it's new—it could be a migraine, even though you haven't had them before. Migraines can sometimes appear suddenly, triggered by stress or other factors. Alternatively, it might be a tension headache or even a sinus headache. I'll suggest taking some ibuprofen if you're able, as it can help reduce inflammation and pain. Staying hydrated and resting in a quiet, dark room might also ease your symptoms.

We'll keep an eye on how you're feeling. If the pain worsens, you develop a fever, or experience any new symptoms like a rash, it's important to seek immediate care. I recommend checking your blood pressure at home if possible, as high blood pressure can sometimes cause headaches. We can schedule a follow-up in a few days to see how you're doing. Please let me know if you have any questions or concerns in the meantime.


## Condition: `framework_only`

_latency_: 7986 ms

**Response**

Thank you for sharing your concerns about your headache. It sounds like you're experiencing significant discomfort, and I want to make sure we address it together.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again in a few days. In the meantime, if your headache gets worse or you develop any new symptoms like a high fever, severe pain, or vision changes, please call us right away.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `retrieval_only`

_latency_: 166890 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 2
n_goals: 0
problems:
- really bad headache
medications: []
allergies: []
```

**Response**

I can hear how frustrating this must be for you — you mentioned, "really bad." That kind of pain can make it hard to focus on anything else.

A bad headache that started suddenly could be due to a number of things. Since it's been with you since yesterday morning and is mainly on the left side, we'll want to check for common causes like tension headaches or sinus issues. We'll also look into other possibilities to make sure there's nothing more serious going on.

We'll schedule some tests to figure out what's causing the headache, like blood work or imaging if needed.

We'll check in with you again soon to review the results and plan the next steps together.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again in a week. In the meantime, if the headache gets worse or you develop new symptoms like vision changes or trouble speaking, please call us right away.

_NURSE_: ['Name', 'Understand']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']

## Condition: `full`

_latency_: 172497 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- really bad headache
medications: []
allergies: []
```

**Response**

I understand you're experiencing a really bad headache since yesterday morning, and it's been quite severe.

A really bad headache can be concerning, especially when it comes on suddenly. The structured context suggests that clinical judgement is important in evaluating such symptoms, though it's more specific than sensitive for certain conditions.

We'll need to evaluate this further. Since there are no immediate red flags, we can start with some basic tests to rule out common causes.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to follow up in a week. If the headache gets worse or you develop new symptoms like vision changes or trouble speaking, please call us right away.

_cited PMIDs_: ['35709018']

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']
