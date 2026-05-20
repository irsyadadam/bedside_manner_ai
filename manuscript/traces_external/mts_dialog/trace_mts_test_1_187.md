# External-dataset trace — `mts_test_1_187`

- Dataset: **mts_dialog**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 3
- Gold sections: ['CC']

## Patient utterances (first 3)
1. [Clinician asked: "Ma'am, are you feeling okay?"] No not really, I feel dizzy.
2. [Clinician asked: "Who brought you to emergency?"] My husband, he is trying to find parking outside.
3. [Clinician asked: "Well, your blood pressure looks quite high and so does your heartbeat. Do you have a history of hypertension or tachycardia, how old are you?"] I am sixty six.

## Gold sections
### CC

This is a 66-year-old patient who came to the emergency room because she was feeling dizzy and was found to be tachycardic and hypertensive.

## Condition: `naive`

_latency_: 13740 ms

**Response**

I'm really sorry to hear that you're feeling dizzy, Mrs. [Last Name]. Your husband did the right thing by bringing you in. I can see that your blood pressure is high, and your heart rate is up. At 66, it's important we get to the bottom of this. Let's run some tests to see what's going on and make sure you feel better. If you have any other symptoms or questions, please let me know. We're here to figure this out together and get you back to feeling like yourself.


## Condition: `strong_prompt`

_latency_: 15766 ms

**Response**

Thank you for sharing how you're feeling. It's completely understandable that you're concerned about feeling dizzy, especially with your blood pressure and heart rate being elevated. I can see how this might be unsettling, and I'm here to help figure out what's going on.

Given your age and the readings we have, it's important to explore possible causes for your dizziness, such as dehydration or potential heart issues. I'll arrange for some tests to get a clearer picture of your health. It's also wise to review your current medications to ensure they're not contributing to your symptoms.

We'll monitor your condition closely and schedule a follow-up in the next few days to assess your progress. Before you leave, could you summarize what we've discussed so far? This will help ensure you're clear on the plan and any next steps.


## Condition: `framework_only`

_latency_: 6825 ms

**Response**

It sounds like you're not feeling well, and your husband brought you in because of that.

We'll check your blood pressure and heart rate again to see if they're still high and discuss what might be causing your dizziness.

Can you tell me, in your own words, what we're going to do next and why?

Let's plan to monitor your condition closely. If your symptoms get worse or if you have chest pain, trouble breathing, or fainting spells, please call us right away.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `retrieval_only`

_latency_: 37068 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- dizziness
medications: []
allergies: []
```

**Response**

Thank you for coming in to discuss your concerns. I understand that you're currently experiencing dizziness, and I want to make sure we address this together.

Dizziness can be caused by a variety of factors, and it's important to explore these systematically. Given your age, we'll consider common causes in older adults, such as inner ear issues or blood pressure changes.

We'll schedule some tests to better understand what's causing the dizziness, such as blood work and a hearing assessment.

Let's plan to follow up in two weeks to review the results and discuss next steps.

I want to make sure I explained this clearly. Can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again in two weeks. In the meantime, if you experience any severe dizziness or fall, please call us right away.

_cited PMIDs_: ['39366124', '40155879']

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `full`

_latency_: 89462 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- dizziness
medications: []
allergies: []
```

**Response**

It sounds like you're experiencing dizziness recently, and I want to understand how this is affecting your daily life.

Dizziness can be caused by a variety of issues, and it's important to figure out what's going on. Based on clinical guidelines, we'll start with some basic tests to check for common causes of dizziness.

We'll schedule some tests to look into the possible causes of your dizziness.

Please keep track of when the dizziness happens and any other symptoms you notice, and let us know if anything changes.

Can you tell me, in your own words, what we're going to do next to figure out what's causing your dizziness?

Let's plan to check in again in a week to review the test results. If you experience severe dizziness or any new symptoms like chest pain or vision changes, please call us right away.

_cited PMIDs_: ['35709018']

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']
