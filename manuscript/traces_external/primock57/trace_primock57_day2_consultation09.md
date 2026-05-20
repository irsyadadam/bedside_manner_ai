# External-dataset trace — `primock57_day2_consultation09`

- Dataset: **primock57**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 39
- Gold sections: ['HIGHLIGHTS', 'PRESENTING_COMPLAINT']
- Gold note length: 754 chars

## Patient utterances (first 3)
1. [Clinician asked: "Hi there, good morning. Or good afternoon, sorry.  Hi."] Hello there. Uh, good afternoon. This is Jack.
2. [Clinician asked: "Good afternoon. Hi. This, this is Doctor Deen Mirza from GP at Hand."] I do.
3. [Clinician asked: "All right. So before we start your appointment, could I please confirm your full name and date of birth?"] Yes, uh, my name is Jack Armani.
... (36 more)

## Gold sections
### PRESENTING_COMPLAINT

I can't move my left arm

### HIGHLIGHTS

Difficulty moving left arm
Tingling present on left side of face
Difficulty swallowing water
Speech seems ‘harder' or ‘slow'
? CVA
LAS called

## Condition: `naive`

_latency_: 20049 ms

**Response**

Thank you for sharing your concerns with me, Jack. I understand how alarming this must feel, especially when you're experiencing symptoms like difficulty moving your arm, tingling on your face, and challenges with swallowing and speech. These symptoms can be signs of a serious condition, such as a stroke, which requires immediate medical attention.

I've already arranged for an ambulance to be on its way, and they will take you to the hospital where you'll receive the care you need. Please make sure the front door is unlocked and stay near it so the paramedics can access you easily. The medical team there is prepared to assess you and provide the necessary treatment.

You're doing the right thing by seeking help quickly, and I'm here to support you. The ambulance should arrive shortly, and they will ensure you get the care you need. Take a deep breath, stay calm, and know that help is on the way. You're not alone in this.


## Condition: `strong_prompt`

_latency_: 26257 ms

**Response**

Thank you for sharing your concerns with me. It’s completely understandable that you’re worried, especially with symptoms like sudden arm weakness, facial tingling, and speech difficulty. These could be signs of a stroke or transient ischemic attack (TIA), which are serious conditions that require immediate attention.

Given your symptoms and medical history, including type 2 diabetes and high blood pressure, it’s crucial to seek emergency care. Conditions like diabetes and hypertension can increase stroke risk, so it’s important to address this promptly. I recommend calling an ambulance right away to get to the nearest emergency room. The medical team there can perform the necessary evaluations, such as imaging, to determine the cause and appropriate treatment.

While waiting for the ambulance, try to stay calm and remain in a safe place. Once at the hospital, they’ll assess you thoroughly. After your evaluation, we can discuss further steps. Please let me know if you have any questions or need assistance before the ambulance arrives. Your health and safety are our top priorities.


## Condition: `framework_only`

_latency_: 7978 ms

**Response**

Thank you for reaching out. It sounds like you're experiencing some concerning symptoms, and I'm here to help.

We'll arrange for an ambulance to come to your home as we speak. Please prepare to go to the hospital for further assessment by the stroke team.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Once you're at the hospital, the doctors will assess your condition and determine the next steps. We'll follow up with you as soon as we have more information.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `retrieval_only`

_latency_: 145447 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 1
n_goals: 0
problems:
- dysphagia
medications: []
allergies: []
```

**Response**

I can hear how much this has been on your mind. You mentioned, "Is this something I should be worried about?" That shows you're taking it seriously, and I want to make sure we address it together.

Dysphagia, or difficulty swallowing, can sometimes be a sign of an underlying condition. Since we don't have more details about when this started or how severe it is, we'll need to look into it carefully.

We'll schedule some tests to get a better understanding of what's going on with your swallowing difficulties.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to check in again in a week. If you notice any new symptoms or if the difficulty swallowing gets worse, please call us right away.

_NURSE_: ['Name', 'Understand', 'Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']

## Condition: `full`

_latency_: 184002 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 1
n_goals: 0
problems:
- dysphagia
medications: []
allergies: []
```

**Response**

I can hear how much this has been on your mind — you asked, "Is this something I should be worried about." That's a valid concern, and I want to make sure we address it together.

Dysphagia, or difficulty swallowing, can sometimes be a sign of an underlying issue. To understand it better, we'll look into your medical history and any symptoms you're experiencing. This will help us figure out the best way to move forward.

We'll start by gathering more information about your symptoms and medical history to better understand what might be causing the dysphagia.

This will help us identify the right next steps and ensure we address your concerns effectively.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to review your symptoms and medical history in our next session. In the meantime, if you experience any difficulty breathing or severe pain, please reach out immediately.

_cited PMIDs_: ['39366124']

_NURSE_: ['Name', 'Understand', 'Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']
