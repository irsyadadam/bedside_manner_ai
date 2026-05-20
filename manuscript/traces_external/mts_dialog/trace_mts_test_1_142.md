# External-dataset trace — `mts_test_1_142`

- Dataset: **mts_dialog**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 2
- Gold sections: ['CC']

## Patient utterances (first 3)
1. [Clinician asked: "How are you feeling?"] I am feeling very weak and shaky.
2. [Clinician asked: "Oh I am so sorry."] It's okay.

## Gold sections
### CC

Weak and shaky.

## Condition: `naive`

_latency_: 14177 ms

**Response**

I understand that you're feeling weak and shaky, and I'm here to support you. It's important to take these symptoms seriously, so I want to ask a few questions to better understand what you're experiencing. How long have you been feeling this way? Are you experiencing any other symptoms, like dizziness, fatigue, or nausea? Have you had any changes in your eating habits, hydration, or stress levels recently?

Please know that I'm here to help you get to the bottom of this and provide the support you need. If you're feeling overwhelmed, don't hesitate to reach out. We'll work together to figure out what's going on and how to help you feel better.


## Condition: `strong_prompt`

_latency_: 14862 ms

**Response**

Thank you for sharing how you're feeling. It makes sense that you're feeling weak and shaky—it sounds like this has been taking a toll on you, and I want to understand more about what's been going on.

A few things could be contributing to these symptoms. Weakness and shakiness can be linked to low blood sugar, dehydration, or even vitamin deficiencies like low iron or vitamin B12 [PMID ?]. I want to make sure we address this together. 

We'll start by checking some basic labs to see if there's an underlying cause we can treat. In the meantime, I'll give you some tips to help manage these symptoms in the short term. Let's plan to follow up in 1-2 weeks to see how you're feeling and review the results. Before you go, could you summarize what we discussed today so I can make sure everything is clear?


## Condition: `framework_only`

_latency_: 6034 ms

**Response**

I can hear how you're feeling weak and shaky, and I'm here to help you through this.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again soon. In the meantime, if your symptoms get worse or you have any new concerns, please call us.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `retrieval_only`

_latency_: 22748 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- weakness and shakiness
medications: []
allergies: []
```

**Response**

It sounds like you're experiencing some concerning symptoms, like weakness and shakiness, which you mentioned are very severe.

While I don't have specific guidelines for this exact situation, I understand how serious these symptoms are. We'll work together to figure out what's going on and the best way to address them.

We'll schedule some tests to help us understand what's causing your weakness and shakiness.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to follow up in a week to review the test results and discuss any questions you have.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `full`

_latency_: 80146 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- weakness and shakiness
medications: []
allergies: []
```

**Response**

I understand you're experiencing weakness and shakiness, which you describe as being 'very' severe. Let's work together to figure out what's going on and how we can help.

To assess your situation, we'll start by understanding how often this happens and any specific patterns, which will help guide the next steps.

We'll begin by gathering more details about your symptoms to better understand what might be causing them.

This includes asking about how often you experience weakness and shakiness, any triggers, and whether there have been any changes in your usual routine or health recently.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to follow up within a week to review the information we gather and discuss the next steps together.

_cited PMIDs_: ['34588228']

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']
