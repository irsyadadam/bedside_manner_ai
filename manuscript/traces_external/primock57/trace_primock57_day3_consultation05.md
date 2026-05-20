# External-dataset trace — `primock57_day3_consultation05`

- Dataset: **primock57**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 34
- Gold sections: ['HIGHLIGHTS', 'PRESENTING_COMPLAINT']
- Gold note length: 712 chars

## Patient utterances (first 3)
1. Hello.
2. [Clinician asked: "Hello. Hi, I'm Doctor Jacob and welcome to Babylon. How are you doing?"] I'm OK, thank you. Um, not feeling that great actually.
3. [Clinician asked: "<INAUDIBLE_SPEECH/> Good. <INAUDIBLE_SPEECH/> Alright. I can't see your face properly , just, yeah that's it. That's good. Thank you. So, I'm sorry to hear that. But just before we start, is it alright if you could confirm your name for me please?"] <INAUDIBLE_SPEECH/> I'm Mary Jane Grey, um.
... (31 more)

## Gold sections
### PRESENTING_COMPLAINT

I've been feeling dizzy

### HIGHLIGHTS

dizziness
premature ovarian failure
HRT
labrynthitis

## Condition: `naive`

_latency_: 15222 ms

**Response**

Mary, I understand how unsettling these symptoms must be for you. The dizziness and ear buzzing sound concerning, and I’m glad you reached out for help. Based on what you’ve described, it does sound like labyrinthitis, which is an inflammation in the inner ear that can cause vertigo and hearing issues. The medication prescribed should help alleviate your symptoms, but it’s important to take it as directed.

Please make sure to rest and avoid activities that could be unsafe if you’re feeling unsteady. If your symptoms worsen, especially if you experience severe nausea or vomiting, let us know right away. You’ve taken the right step by booking an appointment, and I’m here if you have any more questions or concerns. Take care and feel better soon.


## Condition: `strong_prompt`

_latency_: 24701 ms

**Response**

Mary, thank you for sharing your symptoms with me. It sounds like you're feeling quite unwell with this dizziness and ear buzzing, and I can understand how concerning this must be for you, especially since it's lasting longer than the previous episode.

Given your symptoms—dizziness, ear buzzing, and feeling unstable—it's important to consider possible causes. One possibility is labyrinthitis, which involves inflammation in the inner ear and can lead to vertigo, hearing issues, and imbalance [PMID ?]. Another consideration is vestibular neuritis, which is similar but typically doesn't cause hearing loss. Meniere's disease is another option, characterized by vertigo, hearing loss, and tinnitus, though it usually presents with episodic symptoms [PMID ?]. Lastly, benign paroxysmal positional vertigo (BPPV) could be a consideration, though it's typically shorter in duration and triggered by head movements.

In the meantime, I've prescribed an anti-nausea medication to help manage your symptoms. Please take it as directed, and if you experience severe nausea, vomiting, or sudden hearing loss, seek immediate care at the emergency room.

We'll schedule an appointment for you to see a specialist for further evaluation. Before you leave, could you summarize the plan in your own words to ensure clarity? I'll follow up with you in a week to see how you're doing and adjust the plan as needed. Please don't hesitate to reach out if you have any questions or concerns in the meantime.


## Condition: `framework_only`

_latency_: 7755 ms

**Response**

I understand you're feeling unwell with dizziness and ear buzzing, and it's been ongoing for about two hours now. You mentioned it started while making breakfast, and it's been persistent since then.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again soon. If your symptoms get worse or you develop severe nausea or vomiting, please call us right away.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `retrieval_only`

_latency_: 130938 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- dizziness with spinning sensation
medications: []
allergies: []
```

**Response**

It sounds like you're experiencing a very uncomfortable episode with dizziness and spinning. I want to understand how this is affecting you right now.

Dizziness can be caused by a variety of issues, and since it started just two hours ago and is continuous, we'll need to look into possible causes. This could include inner ear problems, low blood sugar, or other factors. We'll do some tests to figure out what's going on.

We'll schedule some tests to check for common causes of dizziness, like inner ear issues or low blood sugar.

Please come back for a follow-up visit so we can review the results together.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again for the follow-up visit. In the meantime, if the dizziness gets worse or you experience any new symptoms, please call us so we can address them promptly.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `full`

_latency_: 206479 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- dizziness with spinning sensation
medications: []
allergies: []
```

**Response**

It sounds like you're experiencing dizziness with a spinning sensation that's been going on continuously for about two hours. You mentioned hearing a buzzing in your ears and feeling off, which must be unsettling.

Dizziness with a spinning sensation, especially when it's sudden and persistent, can be concerning. Given that it's been ongoing for two hours, it's important to consider possible causes like inner ear issues or neurological factors. The primary consideration here is to rule out more serious conditions, such as spinning dizziness or other balance disorders.

We'll schedule a follow-up visit to assess your condition further and determine the next appropriate steps. If symptoms worsen or new symptoms develop, such as severe headaches or vision changes, please contact us immediately.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again in a week. In the meantime, if you experience any severe symptoms like difficulty speaking, weakness, or loss of consciousness, please call us right away.

_cited PMIDs_: ['31237649']

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']
