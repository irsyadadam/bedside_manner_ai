# External-dataset trace — `mts_test_1_113`

- Dataset: **mts_dialog**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 2
- Gold sections: ['ALLERGY']

## Patient utterances (first 3)
1. [Clinician asked: "And you're allergic to Sulfa drugs, correct?"] Yes, ma'am.
2. [Clinician asked: "What happens when you take Sulfa drugs?"] I get incredibly dizzy and I can't stop vomiting.

## Gold sections
### ALLERGY

SULFA drugs.

## Condition: `naive`

_latency_: 11829 ms

**Response**

I understand how concerning and uncomfortable those symptoms must be for you. It sounds like you have a significant allergic reaction to sulfa drugs, which is something we should take very seriously. Your body is clearly reacting strongly to them, and it’s important to avoid sulfa medications in the future to prevent the same reaction.

To help stay safe, it’s a good idea to always check the ingredients of any medication and let your healthcare providers know about this allergy. Wearing a medical alert bracelet could also be a helpful precaution. If you ever experience these symptoms again, seek medical attention immediately. We’ll work together to manage your health in a way that avoids triggering this reaction.


## Condition: `strong_prompt`

_latency_: 18035 ms

**Response**

Thank you for sharing that with me. It makes sense that you're concerned about your reaction to sulfa drugs, especially since experiencing dizziness and vomiting can be quite unsettling. I can understand how this would make you cautious about your medications, and I want to ensure we find a solution that works well for you.

Given your history, it's important to review your current medications to see if sulfa drugs are still the right choice for you. If they're no longer necessary, we can explore alternative options that won't trigger these reactions. I want to make sure we're avoiding sulfa drugs moving forward to prevent any further issues.

Before you leave, could you summarize our plan in your own words? That way, I can ensure I've explained everything clearly. We'll follow up in about two weeks to check on your progress and adjust as needed.


## Condition: `framework_only`

_latency_: 6504 ms

**Response**

Thank you for sharing your concerns with me today.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again in 4 weeks. In the meantime, if you get new symptoms like blood in your stool, severe pain, fevers, or the fatigue getting much worse, please call us right away — don't wait for the appointment.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `retrieval_only`

_latency_: 20948 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 1
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- dizziness and vomiting
medications: []
allergies:
- Sulfa drugs
```

**Response**

It sounds like you're experiencing dizziness and vomiting, especially when taking Sulfa drugs. I want to understand how this is affecting you.

Dizziness and vomiting can be caused by various factors, including medication side effects. Since this happens when you take Sulfa drugs, it's important to consider whether this reaction is a known side effect or if there might be another underlying cause.

We should review your medications and consider alternatives if necessary.

We'll monitor your symptoms and see if they improve with any changes to your medication.

Can you tell me in your own words what we're going to do next?

Let's plan to follow up in a week to see how you're doing. If your symptoms get worse or if you have any new concerns, please reach out sooner.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `full`

_latency_: 129096 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 1
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- dizziness and vomiting
medications: []
allergies:
- Sulfa drugs
```

**Response**

It sounds like your main concern is the dizziness and vomiting you experience when taking sulfa drugs. I want to make sure I understand how this is affecting you.

Dizziness and vomiting can be concerning, especially when linked to medication use. In some cases, these symptoms might be related to how your body reacts to sulfa drugs. We'll need to look into this further to understand the cause.

We'll schedule a follow-up visit to discuss your symptoms in more detail and explore possible causes.

Please keep track of when the dizziness and vomiting occur and any other symptoms you notice, so we can better understand the pattern.

I want to make sure I explained this clearly — can you tell me, in your own words, what we'll do next to address your symptoms?

Let's plan to see each other again in a couple of weeks. In the meantime, if your symptoms get worse or you experience any new symptoms, please call us right away.

_cited PMIDs_: ['40720582']

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']
