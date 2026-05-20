# External-dataset trace — `primock57_day2_consultation05`

- Dataset: **primock57**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 54
- Gold sections: ['HIGHLIGHTS', 'PRESENTING_COMPLAINT']
- Gold note length: 989 chars

## Patient utterances (first 3)
1. [Clinician asked: "Hi there. Good morning. I'm Doctor <INAUDIBLE_SPEECH/> from GP at Hand. Nice to see you."] Hi.
2. [Clinician asked: "OK. So, um, before we start your appointment. Could I confirm your full name and date of birth please?"] Yeah, it's John Smith, and I am thirty two years old.
3. [Clinician asked: "Sorry, I didn't catch your date of birth."] I'm thirty two years old.
... (51 more)

## Gold sections
### PRESENTING_COMPLAINT

My asthma is not responding to my inhalers

### HIGHLIGHTS



## Condition: `naive`

_latency_: 27655 ms

**Response**

Dear John,

I understand that you're experiencing some unsettling symptoms over the past month, including fatigue, weakness, nausea, and episodes of numbness and tingling in your right hand, along with a slight change in your gait. These symptoms are concerning, and I want to ensure you get the care you need.

Given your symptoms and family history of stroke, it's important to consider the possibility of transient ischemic attacks (TIAs), which are sometimes referred to as mini-strokes. While I understand you're a doctor, it's crucial to have these symptoms evaluated by specialists to rule out any serious conditions and to determine the best course of action.

I've referred you to a TIA clinic for further evaluation. They will likely conduct imaging and other tests to assess your situation. In the meantime, if you experience any prolonged episodes or if your symptoms worsen, please seek immediate medical attention at the emergency room.

Please don't hesitate to reach out if you have any questions or concerns. We're here to support you through this process.

Take care, and I look forward to hearing from you.

Best regards,  
[Your Name]  
GP at Hand


## Condition: `strong_prompt`

_latency_: 30329 ms

**Response**

Thank you for sharing your concerns with me, John. It's clear you've been experiencing some unsettling symptoms, and I appreciate your proactive approach in seeking help. Given your background as a medical professional, I understand your concerns are heightened, especially with a family history of stroke.

It's completely reasonable to feel worried about these symptoms, particularly the pins and needles sensation in your right hand, weakness, and changes in your gait. These could be signs of a transient ischemic attack (TIA), often referred to as a mini-stroke, which is something we need to evaluate promptly. Research indicates that early assessment is crucial for such symptoms [PMID ?].

To move forward, I'll refer you to a TIA clinic for specialized evaluation. They should contact you within the next couple of days. In the meantime, if your symptoms worsen or persist, it's important to seek immediate care at the emergency room.

Before we conclude, could you summarize our plan for me? This will help ensure you're clear on the next steps. Remember, you can reach out if you have any questions or need further assistance. Take care, and I look forward to hearing from you soon.


## Condition: `framework_only`

_latency_: 7565 ms

**Response**

Thank you for sharing your concerns with me. It sounds like you're experiencing some unusual symptoms that have been going on for about a month, and it's understandable that you're feeling worried and unsure about what's happening.

I want to make sure I explained this clearly. Can you tell me, in your own words, what we're going to do next and why?

Let's plan to follow up in the next few days. If your symptoms get worse or if you have any new concerns, please reach out to us as soon as possible.


## Condition: `retrieval_only`

_latency_: 176007 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 3
n_goals: 1
problems:
- weird symptoms
medications: []
allergies: []
```

**Response**

I can hear how much this is worrying you — you said, "I don't know what's causing them." That makes sense given how many symptoms you're experiencing, like numbness and fatigue.

When someone experiences multiple unusual symptoms like numbness, weakness, and fatigue, it's important to consider a range of possible causes. This includes looking at how symptoms develop and any patterns they might follow.

Understanding the underlying cause of your symptoms is a key goal. We'll work together to explore possible reasons and get clarity on what's going on.

We'll start by gathering more detailed information about your symptoms and how they've been progressing.

We'll schedule some tests to help identify potential causes.

We'll review the results together and discuss the next steps in understanding what's going on.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to follow up in a week to review the test results. In the meantime, if your symptoms get worse or you notice anything new, please reach out.

_NURSE_: ['Name', 'Understand', 'Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']

## Condition: `full`

_latency_: 198256 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 1
problems:
- weird symptoms
medications: []
allergies: []
```

**Response**

It sounds like you're dealing with a lot of strange symptoms that are worrying you. You mentioned things like numbness in your hands and arms, weird sensations, fatigue, and nausea. I want to make sure I understand how all these symptoms are affecting your daily life.

Experiencing multiple unusual symptoms like numbness, weakness, and fatigue can be concerning. While there are many possible causes, it's important to start with a thorough evaluation to identify the underlying issue.

Our goal is to work together to figure out what's causing these symptoms. This might involve some tests and questions to get a clearer picture of what's going on.

We'll start by scheduling some tests to get a better understanding of what might be causing these symptoms.

We'll also review your medical history and discuss any medications or treatments you've tried so far.

I want to make sure I explained this clearly. Can you tell me, in your own words, what we're going to do next to figure out what's causing these symptoms?

Let's plan to follow up in a week to review the test results. In the meantime, if you experience any severe symptoms like sudden weakness or loss of sensation, please call us right away.

_cited PMIDs_: ['40471580', '40155879']

_NURSE_: ['Support', 'Respect']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']
