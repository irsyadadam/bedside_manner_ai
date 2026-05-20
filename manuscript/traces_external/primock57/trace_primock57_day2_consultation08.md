# External-dataset trace — `primock57_day2_consultation08`

- Dataset: **primock57**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 54
- Gold sections: ['HIGHLIGHTS', 'PRESENTING_COMPLAINT']
- Gold note length: 1129 chars

## Patient utterances (first 3)
1. [Clinician asked: "Hi, good morning!"] Hello there!
2. [Clinician asked: "Hi there, this is uh this is Doctor Dean  from <INAUDIBLE_SPEECH/> ."] Hello there? Um, I'm wondering if you can help me today.
3. [Clinician asked: "<INAUDIBLE_SPEECH/> OK,  sure,  I'll try. Before we start, could I please confirm your full name and date of birth?"] Yes, it's Sarah Smith, and it's the second of November, um, nineteen ninety two.
... (51 more)

## Gold sections
### PRESENTING_COMPLAINT

I've been feeling very hot and sweaty for the past week

### HIGHLIGHTS

fever
sweatiness
muscle aches
nausea
fatigue
night sweats
Recent foreign travel
cerazette
Nil allergies
hayfever
nurse
non smoker
PUO
need to exclude malaria

## Condition: `naive`

_latency_: 17074 ms

**Response**

Dear Sarah,

I understand how challenging it must be to deal with these symptoms for an extended period. It’s important that we get to the bottom of what’s causing your fever and other不适感. Based on your recent travel to a rural area in Vietnam and the symptoms you’re experiencing, we need to consider potential infections, including malaria, even though you took preventive medication.

The next steps involve scheduling some blood tests to check for any underlying infections. Please make sure to follow up on the instructions provided. If you have any concerns or questions before your appointment, don’t hesitate to reach out. Your health is our priority, and I’m here to support you through this.

Take care and feel better soon.

Best regards,  
[Your Name]  
Clinician


## Condition: `strong_prompt`

_latency_: 24571 ms

**Response**

Thank you for sharing all that with me, Sarah. It sounds like you're feeling really unwell, and I can understand how concerning this must be for you. Having a fever for a week, along with all these other symptoms, is exhausting, and I want to make sure we get to the bottom of it.

Given your recent trip to Vietnam and the rural areas you visited, we need to consider a few possibilities. Malaria is a strong contender, especially since you were taking preventative medication. Other infections, like dengue or typhoid, could also be in the mix. It's also possible that this is a bacterial infection that needs specific treatment. To figure this out, we'll need to do some blood tests, which can help us identify what's going on [PMID ?].

We'll start with a physical exam and then arrange for those blood tests. Depending on the results, we might need to do more tests or consider other treatments. In the meantime, make sure to stay hydrated and rest as much as possible.

Before you leave, could you tell me in your own words what we've agreed on today? That way, I can ensure everything is clear. We'll follow up in the next few days once we have the test results.


## Condition: `framework_only`

_latency_: 8033 ms

**Response**

Thank you for sharing all this with me. It sounds like you're going through a tough time with this fever and feeling unwell.

We'll arrange for some blood tests to help figure out what's going on. We'll also schedule a follow-up visit to review the results together.

Can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again in a week. If you experience any severe symptoms like difficulty breathing or chest pain, please call us right away.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `retrieval_only`

_latency_: 172587 ms

**Extracted profile (summary)**
```yaml
n_problems: 2
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- fever
- migraines
medications: []
allergies: []
```

**Response**

It sounds like you're dealing with a lot of symptoms, like fever and muscle aches, that have been going on for about a week. I want to make sure I understand what's been happening.

Fever with symptoms like sweating, muscle aches, nausea, fatigue, and night sweats can be caused by a variety of issues. It's important to check for common causes like infections, especially since you've been feeling this way for about a week.

Migraines can be triggered by things like high-pressure days or changes in the weather. Since you've been dealing with this for years, we'll look into ways to manage your symptoms and identify any patterns that might help us understand what's going on.

We'll start by checking for common causes of your fever and symptoms through some basic tests.

For your migraines, we'll work together to identify possible triggers and explore treatment options that could help reduce your symptoms.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again in a couple of weeks. In the meantime, keep track of your symptoms and let me know if anything changes or gets worse.

_cited PMIDs_: ['35593186', '39366124']

_NURSE_: ['Invest in the beginning']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective"]

## Condition: `full`

_latency_: 227082 ms

**Extracted profile (summary)**
```yaml
n_problems: 2
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 0
problems:
- fever
- migraines
medications: []
allergies: []
```

**Response**

It sounds like you're dealing with a lot of symptoms, like fever and muscle aches, that have been going on for about a week. I want to make sure I understand how this is affecting your daily life.

Fever can be a sign of many things, like infections. Given that your fever has lasted a week and you've tried over-the-counter medications without much relief, it's important to figure out what's causing it. We should consider doing some tests to check for common causes.

Migraines can be triggered by things like stress or changes in weather. Since you've been dealing with this for years, it might help to identify your specific triggers and find ways to manage them.

We'll schedule a test to check for common causes of your fever, like COVID-19.

We'll also talk about ways to manage your migraines better, focusing on identifying your triggers and possible treatments.

Please keep track of your symptoms and let us know if anything changes or gets worse before your next visit.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again in a few weeks. In the meantime, if your fever doesn't improve or if you develop any new symptoms like a severe headache or difficulty breathing, please call us right away.

_cited PMIDs_: ['35593186', '40155879']

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']
