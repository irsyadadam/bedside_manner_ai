# External-dataset trace — `primock57_day5_consultation12`

- Dataset: **primock57**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 46
- Gold sections: ['HIGHLIGHTS', 'PRESENTING_COMPLAINT']
- Gold note length: 706 chars

## Patient utterances (first 3)
1. Hi.
2. [Clinician asked: "Hi there. It's Doctor Smith from Babylon."] Hey. How are you?
3. [Clinician asked: "How are you doing? <INAUDIBLE_SPEECH/>. Good thank you. Can you confirm your name, date of birth, and your, home address please?"] Um, yes I can. Uh, it's, Mary Smith.
... (43 more)

## Gold sections
### PRESENTING_COMPLAINT

Headache

### HIGHLIGHTS



## Condition: `naive`

_latency_: 19302 ms

**Response**

Mary, I understand how concerning and uncomfortable this headache must be for you, especially since it's something you haven't experienced before. It's natural to feel worried, but the steps we discussed should help alleviate the pain. Rest, hydration, and the recommended medications are a good start. If the headache persists or gets worse, or if you develop any new symptoms, please don't hesitate to reach out. We're here to support you through this. Take care and feel better soon.


## Condition: `strong_prompt`

_latency_: 23596 ms

**Response**

Mary, thank you for sharing your concerns with me. It sounds like you're in discomfort, and it's understandable to be concerned since this is new for you. Having a severe headache for the first time can be unsettling, especially when it's persistent and hasn't responded to pain relief.

Given your symptoms—an intense, throbbing headache on the left side without other signs like nausea or vision changes—I'm thinking this might be a migraine or possibly a tension headache. However, since you're 28 and this is your first experience with such a headache, it's important to consider other possibilities. I'll suggest trying a different pain reliever, like Paracetamol, and ensuring you take it with food to avoid stomach issues. Rest and hydration are key, so I recommend you take it easy today.

If the pain worsens or you develop new symptoms like vomiting or vision changes, please seek immediate care. We'll follow up in a week to reassess your symptoms and adjust our approach if needed. Let me know if you have any questions or concerns in the meantime.


## Condition: `framework_only`

_latency_: 12128 ms

**Response**

Thank you for reaching out about your headache. It sounds like it's been quite uncomfortable, especially since it's something you haven't experienced before.

We recommend taking a slightly stronger pain reliever, such as Paracetamol, with food. Rest and stay hydrated. If the pain worsens or new symptoms appear, like fever or vomiting, please contact us immediately. We'll follow up in a day or two to see how you're doing.

Try to avoid stress and maintain your usual diet and lifestyle. If the headache persists or gets worse, give us a call.

If you have any questions or need further assistance, don't hesitate to reach out.

Can you tell me in your own words what you plan to do next and how you'll manage your headache?

Let's check in again in a day or two. If your symptoms don't improve or get worse, please call us right away.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `retrieval_only`

_latency_: 118101 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- headache
medications: []
allergies: []
```

**Response**

It sounds like you're experiencing a significant headache that started yesterday. I want to understand how this is affecting you and what we can do together to address it.

Headaches can be caused by a variety of factors, and since yours started recently and is severe, we'll want to explore potential causes systematically. This approach ensures we cover all possibilities without jumping to conclusions too quickly.

We'll start by reviewing your medical history and any recent changes that might be related to your headache.

We'll schedule some tests to rule out common causes and monitor your symptoms closely.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again in a week. In the meantime, keep track of when your headaches occur, how severe they are, and any other symptoms you notice. If they get worse or you experience new symptoms like vision changes or trouble speaking, please call us right away.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `full`

_latency_: 171032 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- headache
medications: []
allergies: []
```

**Response**

It sounds like you're experiencing a bad headache that started yesterday morning. I want to understand how this is affecting your daily life.

Headaches can be caused by many things, and since yours started suddenly and is severe, we'll need to consider different possibilities. The primary step is to assess the pattern and characteristics of the headache to guide the next steps.

We'll start by reviewing your medical history and any medications you're taking.

We'll schedule a follow-up visit to monitor your symptoms and assess the need for further evaluation.

Can you tell me, in your own words, what we discussed today and what you plan to do next?

Let's plan to see each other again in a week. If your headache worsens or you develop new symptoms like vision changes, severe nausea, or confusion, please call us right away.

_cited PMIDs_: ['35709018']

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']
