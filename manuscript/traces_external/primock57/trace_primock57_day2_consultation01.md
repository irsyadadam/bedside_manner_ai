# External-dataset trace — `primock57_day2_consultation01`

- Dataset: **primock57**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 29
- Gold sections: ['HIGHLIGHTS', 'PRESENTING_COMPLAINT']
- Gold note length: 559 chars

## Patient utterances (first 3)
1. [Clinician asked: "Hi, there. Good morning!"] <INAUDIBLE_SPEECH/>
2. [Clinician asked: "Uh, I'm Dr. Dean Mesa from Babylon."] <INAUDIBLE_SPEECH/>
3. [Clinician asked: "Can you hear me OK?"] Yep. Can you find
... (26 more)

## Gold sections
### PRESENTING_COMPLAINT

I don't hear as well as I used to

### HIGHLIGHTS

difficulty hearing
tinnitus
need to exclude impacted wax
examine ear

## Condition: `naive`

_latency_: 19114 ms

**Response**

Thank you for sharing your concerns with me, Jack. I understand how frustrating and concerning it must be to experience a decline in your hearing, along with the ringing in your ear and occasional dizziness. These symptoms are valid, and I’m here to help you navigate them.

The first step we’ll take is to examine your ears to check for any wax buildup, which is a common cause of hearing issues. This simple check can help us rule out easy fixes and then explore other possibilities if needed. I also mentioned that the ringing you’re experiencing is called tinnitus, which is quite common but not always fully understood. While there’s no cure, there are strategies to manage it. In the meantime, I’ve included some resources for you to read more about tinnitus and hearing loss. Please feel free to reach out if you have any questions or concerns before your appointment. I’m here to support you through this.


## Condition: `strong_prompt`

_latency_: 25050 ms

**Response**

Thank you for sharing your concerns with me, Jack. It's understandable that you're feeling worried about your hearing. Experiencing a gradual decline in hearing, along with ringing in your ear and occasional dizziness, can be quite unsettling. I want to make sure we address this together and explore the possible reasons behind these symptoms.

Given that your hearing difficulty has been ongoing for six weeks and accompanied by tinnitus and mild dizziness, it's important to start with a thorough evaluation. One common cause of hearing issues is earwax buildup, which can lead to muffled hearing. We should begin with an ear examination to check for any blockages or wax impaction, as this is a straightforward and treatable issue [PMID ?].

If earwax isn't the culprit, we'll need to consider other possibilities, such as changes in the ear drum or issues with the balance system. Tinnitus itself is a complex condition, and while we may not always find a specific cause, understanding it better can help manage the symptoms [PMID ?].

To move forward, I recommend scheduling an appointment with an audiologist for an ear exam. This will give us a clearer picture and guide the next steps in your care. In the meantime, avoid using cotton buds, as they can push wax deeper into the ear.

Before we wrap up, could you summarize what we've discussed today? This will help ensure you feel confident about the plan and any next steps. We'll follow up in about two weeks to see how you're doing and adjust our approach as needed. Please don't hesitate to reach out if you have any questions or concerns in the meantime.


## Condition: `framework_only`

_latency_: 9373 ms

**Response**

Thank you for sharing your concerns about your hearing. It sounds like this has been going on for about six weeks, and you've noticed some ringing in your left ear along with occasional dizziness. I want to make sure we address this together.

We'll schedule an appointment for you to have your ear examined to check for wax buildup or other issues that might be causing your symptoms. This will help us understand what's going on and guide the next steps in your care.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again after the examination. In the meantime, if your symptoms worsen or you experience severe dizziness, please call us right away.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `retrieval_only`

_latency_: 126973 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- hearing loss
medications: []
allergies: []
```

**Response**

It sounds like you're concerned about your hearing loss, which has been getting worse over the past six weeks with some ringing in your left ear and occasional dizziness.

Hearing loss can be caused by various factors, and since your symptoms have been worsening, it's important to get a clearer picture of what might be causing it. We'll need to explore this further to understand the best approach for you.

We'll schedule a follow-up appointment to discuss your hearing loss in more detail and explore possible next steps together.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again soon to talk about your hearing loss further. If you notice any new symptoms or changes in your condition, please reach out so we can address them promptly.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `full`

_latency_: 177630 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- hearing loss
medications: []
allergies: []
```

**Response**

It sounds like you're concerned about your hearing loss, which has been happening on and off for about six weeks. You mentioned ringing in your left ear and occasional dizziness, and I want to make sure we address these symptoms together.

Hearing loss can be caused by various factors, and since it's been happening on and off with ringing in your ear and dizziness, we should explore common causes. This might include issues like ear infections, exposure to loud noises, or even underlying health conditions.

We'll schedule a hearing test to better understand the extent of your hearing loss.

We'll also check for any infections or other potential causes during your next visit.

If needed, we can explore options like hearing aids or other treatments to help manage your symptoms.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again in a few weeks. In the meantime, if your symptoms get worse or you notice any new issues like severe dizziness, please call us so we can address them promptly.

_cited PMIDs_: ['39366124', '40155879']

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']
