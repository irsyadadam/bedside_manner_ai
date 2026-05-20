# External-dataset trace — `mts_val_74`

- Dataset: **mts_dialog**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 3
- Gold sections: ['GYNHX']

## Patient utterances (first 3)
1. [Clinician asked: "Hello, miss. What brings you into the practice today?"] I have been missing a lot of periods and I am not sexually active. I do not bleed. Is something wrong with me?
2. [Clinician asked: "What is your history with your reproductive parts? Have you had any surgeries?"] I have everything still. I have both ovaries, I have a uterus, and I have a cervix still.
3. [Clinician asked: "Are you on any type of hormonal therapies?"] I am not taking anything. This is the first time I have brought this up to the doctor.

## Gold sections
### GYNHX

She does not bleed.  She has both ovaries, as well as her uterus and cervix.  She is on no hormonal therapy.

## Condition: `naive`

_latency_: 12934 ms

**Response**

Thank you for sharing your concerns with me. It's completely valid to feel worried when something like this happens, and I'm here to help you figure it out. Missing periods can be caused by a variety of things, even when you're not sexually active. Stress, changes in weight, or hormonal imbalances are common reasons, but there could be others. Let's work together to find out what's going on. I might suggest some tests, like blood work or an ultrasound, to check for common causes. You're not alone in this, and we'll get to the bottom of it together. Please feel free to ask any questions you have or let me know if you're experiencing any other symptoms.


## Condition: `strong_prompt`

_latency_: 20076 ms

**Response**

Thank you for sharing your concerns with me. It’s completely understandable that you’re worried about missing periods when you’re not sexually active and haven’t experienced any bleeding. Missing periods can be unsettling, and I appreciate your courage in bringing this up with me today.

Given your history of having all your reproductive organs intact and not being on any hormonal therapies, there are a few possibilities we should consider. One common cause could be polycystic ovary syndrome (PCOS), which can disrupt menstrual cycles [PMID ?]. Other possibilities might include hormonal imbalances, such as issues with your thyroid gland, which can also affect your menstrual cycle [PMID ?]. It’s also worth noting that stress, nutritional factors, or changes in your lifestyle can sometimes impact your periods.

To get a clearer picture, I recommend we start with some basic tests. A blood test can check your hormone levels, including thyroid function and reproductive hormones, which will help us understand what might be going on [PMID ?]. Depending on the results, we might also consider an ultrasound to look at your uterus and ovaries [PMID ?].

We’ll plan to review the results together in about 2-4 weeks. Before you leave today, could you summarize what we’ve discussed so far? This will help ensure you feel confident about the next steps and that I’ve explained everything clearly.


## Condition: `framework_only`

_latency_: 7925 ms

**Response**

It sounds like you're concerned about missing periods and wondering if something is wrong, especially since you're not sexually active and not experiencing bleeding.

We'll need to schedule some tests to understand what's going on with your menstrual cycle. This might include blood tests or a pelvic exam to check everything is working as it should.

Can you tell me in your own words what we're going to do next and why it's important?

Let's plan to follow up in a week to review the test results. In the meantime, keep track of any changes or symptoms and let us know if anything new comes up.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `retrieval_only`

_latency_: 43271 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 1
n_goals: 1
problems:
- missing periods
medications: []
allergies: []
```

**Response**

I can hear how much this has been worrying you — you said, "Is something wrong with me?" That's a real concern, and I want to make sure we get to the bottom of it.

Missing periods can be caused by a variety of factors, and it's important to figure out what's going on. Given your recent onset and lack of other symptoms like bleeding, we'll focus on common causes that don't involve serious conditions.

Our goal is to work together to understand what's causing your missing periods. We'll start with some basic tests to check for common reasons behind this issue.

We'll begin with some basic tests to help us understand what's causing your missing periods.

We'll schedule a follow-up visit to review the results and discuss the next steps together.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again in a few weeks. In the meantime, if you notice any new symptoms or changes, please call us so we can address them promptly.

_NURSE_: ['Name', 'Understand', 'Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']

## Condition: `full`

_latency_: 76969 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 0
n_allergies: 0
n_red_flags: 0
n_emotional: 1
n_goals: 1
problems:
- missing periods
medications: []
allergies: []
```

**Response**

I can hear how much this has been worrying you — you said, "Is something wrong with me?" That's a real concern, and I want to make sure we get to the bottom of it together.

It's important to figure out why you're missing periods. Given your recent onset and lack of other symptoms like bleeding, we'll start with some basic tests to check for common causes.

We'll work together to understand what's going on. Your goal to find out what's wrong is really important, and we'll make sure to keep you informed every step of the way.

We'll start with some basic blood tests to check for common causes of missed periods.

We'll schedule a follow-up visit in a few weeks to review the results and plan the next steps together.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again in a few weeks. In the meantime, if you notice any new symptoms or changes, please call us so we can address them promptly.

_cited PMIDs_: ['33658141']

_NURSE_: ['Name', 'Understand', 'Respect', 'Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']
