# External-dataset trace — `primock57_day2_consultation03`

- Dataset: **primock57**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 46
- Gold sections: ['HIGHLIGHTS', 'PRESENTING_COMPLAINT']
- Gold note length: 790 chars

## Patient utterances (first 3)
1. Hello?
2. [Clinician asked: "Hi there. Good morning!"] Hi. <INAUDIBLE_SPEECH/>. Nice to meet you. Hello.
3. [Clinician asked: "Hello. I, I'm Doctor <INAUDIBLE_SPEECH/>. Nice to see you. Hi. Um, so, before we start your appointment, could I confirm your full name and date of birth, if that's OK?"] Uh, yeah. Uh, Mary Richards. Uh, and my, I'm forty years old. So.
... (43 more)

## Gold sections
### PRESENTING_COMPLAINT

I can't hear very well and my face is a bit numb

### HIGHLIGHTS

difficulty hearing
facial numbness
tinnitus
latex allergy
no facial assymetry

## Condition: `naive`

_latency_: 22223 ms

**Response**

Dear Mary,

Thank you for sharing your concerns with me. I understand how unsettling it must be to experience hearing loss and facial numbness, especially when it's affecting your work as a jockey. It's important to address these symptoms to ensure everything is checked properly.

Based on what you've described, there are a few possibilities we should consider, such as Bell's Palsy, which can cause facial weakness and numbness. However, to confirm this and rule out other potential issues, it's crucial for you to come in for a physical examination. This will allow us to assess your neurological health and examine your ear more closely.

Please remember, while I understand your concerns, the symptoms you're experiencing don't appear to be life-threatening. However, it's essential to get a thorough evaluation to provide you with the right care and reassurance. I've arranged for you to be booked into one of our Central London clinics for a face-to-face appointment. Once you receive the details, please call to confirm your slot at your convenience.

In the meantime, try to stay calm and avoid unnecessary stress. We're here to help, and I'm confident that once we see you, we can address your concerns more thoroughly.

Take care and I look forward to seeing you soon.

Best regards,  
[Your Name]  
Primary-Care Clinician


## Condition: `strong_prompt`

_latency_: 26844 ms

**Response**

Mary, thank you for sharing your concerns with me. It’s clear that you’re feeling worried about your symptoms, and I can understand why. Experiencing hearing loss and facial numbness on the same side, especially alongside ringing in the ear and occasional dizziness, must be unsettling. It’s important to address these symptoms to ensure everything is evaluated properly.

From what you’ve described, there are a few possibilities we should consider. One common condition that can cause facial numbness and hearing issues is Bell’s Palsy, which affects the facial nerve and can lead to temporary weakness or numbness. [PMID ?] Another consideration is Ramsay Hunt Syndrome, which involves the facial nerve and can cause similar symptoms, including hearing loss and rash. [PMID ?] Given the impact on your hearing and facial sensation, it’s crucial to get a thorough neurological and ear examination to rule out other potential issues, such as infections or neurological conditions.

To move forward, I’ve arranged for you to have a face-to-face appointment with one of our clinicians today. They will perform a detailed physical exam, including checking your hearing and facial nerve function, and may recommend imaging or other tests if needed. Please make sure to keep this appointment as it’s essential for getting accurate answers and reassurance.

After your visit, I’ll follow up with you to discuss the findings and next steps. In the meantime, if you experience severe symptoms like sudden hearing loss, worsening facial weakness, or severe dizziness, please seek immediate medical attention. My team will be in touch with you soon to schedule your appointment, and I’ll leave my contact information with them in case you have any questions before then.


## Condition: `framework_only`

_latency_: 10050 ms

**Response**

Thank you for sharing your concerns about your hearing and the numbness on your left side. It sounds like this has been worrying you, and I want to make sure we address it together.

We'll schedule a face-to-face appointment for you to be assessed by a clinician who can perform a neurological examination and check your hearing in detail. This will help us understand what's going on and provide the right guidance.

Please call our admin team after receiving the appointment confirmation to book a time that's convenient for you.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other in the clinic soon. If you experience any severe symptoms like sudden hearing loss or worsening numbness, please call us immediately.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `retrieval_only`

_latency_: 178119 ms

**Extracted profile (summary)**
```yaml
n_problems: 3
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- hearing problems
- facial numbness
- ringing in the ear
medications: []
allergies: []
```

**Response**

Thank you for sharing your concerns about your hearing problems, facial numbness, and occasional ringing in the ear. I understand how these symptoms might be worrying you, and I want to make sure we address them together.

Hearing problems can be caused by various factors, and it's important to get them checked to understand the underlying cause.

Facial numbness can be concerning, and it's crucial to determine the cause so we can provide appropriate care.

Occasional ringing in the ear can be related to different health issues, and we'll work together to figure out what's causing it.

We'll schedule some tests to better understand your hearing problems and facial numbness.

We'll also monitor the ringing in your ear to see if it becomes more frequent or severe.

Please keep track of any new symptoms and let us know if anything changes.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to follow up in a week to review the test results. In the meantime, if you experience any severe symptoms or if your hearing problems worsen, please call us right away.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `full`

_latency_: 236942 ms

**Extracted profile (summary)**
```yaml
n_problems: 3
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- hearing problems
- facial numbness
- ringing in my ear
medications: []
allergies: []
```

**Response**

It sounds like you're experiencing some concerning symptoms recently, like hearing problems and facial numbness. I want to make sure I understand how these are affecting your daily life.

Hearing problems can be caused by a variety of issues, and it's important to get them checked out, especially since they've been happening recently. We'll look into possible causes together.

Facial numbness can be due to several reasons, and it's good that you're bringing it up. We'll make sure to explore what might be causing it during your visit.

Ringing in the ear, or tinnitus, can be frustrating. We'll keep it in mind as we go through your symptoms and figure out the best way to address it.

We'll schedule some tests to get a better understanding of what's going on with your hearing and facial numbness.

We'll also keep an eye on the ringing in your ear and see how it progresses.

Please let us know if any of these symptoms get worse or if you notice anything new before your next appointment.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again in a few weeks. In the meantime, if you experience any severe symptoms or if things get worse, please call us right away.

_cited PMIDs_: ['35709018']

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']
