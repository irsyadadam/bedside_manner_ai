# External-dataset trace — `aci_virtscribe_D2N145`

- Dataset: **aci_bench**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 63
- Gold sections: ['ASSESSMENT', 'CC', 'CURRENT_MEDICATIONS', 'HPI', 'INSTRUCTIONS', 'PAST_HISTORY', 'PHYSICAL_EXAM', 'PLAN']
- Gold note length: 2765 chars

## Patient utterances (first 3)
1. [Clinician asked: "hi , how are you doing , jacqueline ?"] i'm pretty . good . how are you ?
2. [Clinician asked: "good as well . so it sounds like we're , um , under good control right now ."] yes . it's doing much better .
3. [Clinician asked: "good , good . do you have any rash leftover ?"] yeah , i have a- a small bit leftover . i started using , uh , doxycycline only one a day because i think the pharmacist said if it's getting better , to just limit it to once a day .
... (60 more)

## Gold sections
### CC

Follow-up for perioral dermatitis.

### HPI

Jacqueline Miller is a 40-year-old female who is being seen today for a follow-up skin exam for perioral dermatitis. She also has a history of rosacea, including ocular rosacea. Today, she states that her perioral dermatitis is well-controlled, although it has not fully resolved. The patient was applying doxycycline twice a day with improvement, but her pharmacist advised her to reduce to once daily since it had started to improve; therefore, for approximately the past week, she has been using the doxycycline only once per day. She has not seen continued improvement but it has not worsened. She is using the sulfacetamide wash twice daily, denies drying of the skin, and reports that her skin is much improved moisturization. She also applies MetroCream immediately after using the sulfacetamide wash. She denies using other lotions and products, Cetaphil lotion or soap, or Neutrogena wipes. The patient did not begin Elidel because it is not covered by her insurance, and she was concerned about possible side effects from the medication.

### PAST_HISTORY

Medical
Perioral dermatitis.

### CURRENT_MEDICATIONS

Doxycycline cream. Apply twice daily.
MetroCream. 
Sulfacetamide wash. Apply topically twice daily.

### PHYSICAL_EXAM

Integumentary
Skin inspection of the face was performed today. On bilateral medial cheeks, there are a few, very faint, erythematous papules with mild redness around and underneath the nostrils. Fitzpatrick skin type is 4 to 5.

### ASSESSMENT

• Perioral dermatitis
• Rosacea, including ocular rosacea

Jacqueline Miller is a 40-year-old female who presented today for follow-up for her perioral dermatitis, which has improved but not resolved. She decreased her doxycycline per her pharmacist’s recommendation, which possibly stagnated the resolution of symptoms.

### PLAN

Perioral dermatitis.
I counseled the patient about the risks and benefits of doxycycline and recommended she resume twice daily application until she reaches full resolution, and at that point she should reduce application to once a day for an additional week. The patient will not be using Elidel as I reviewed the cost of the medication and without insurance, it was too expensive. I provided a prescription for Tacrolimus and counseled her on possible side effects of using the medication. She will continue with Sulfacetamide face wash once a day. Also, use Bruder mask as needed.

Rosacea, including ocular rosacea.
Continue using MetroCream twice daily. I recommended to gently wash her eyelids once daily with a gentle cleanser and try a gentle cream such as Vanicream.

### INSTRUCTIONS

Call the clinic if symptoms worsen. The patient will have a follow-up appointment in 4 weeks.

## Condition: `naive`

_latency_: 21911 ms

**Response**

It sounds like we've got a good plan to help clear up your rash. To recap, we'll have you continue using the sulfacetamide wash as you've been doing, and keep applying the metro cream after washing. We'll also increase the doxycycline back to twice a day to help tackle the rash more effectively. 

In addition, we'll add the tacrolimus ointment to your routine. Apply this twice daily, focusing only on the areas with the rash. It's important to remember that any initial tingling or redness you might feel is temporary and nothing to worry about. 

Once the rash is gone, we'll continue the doxycycline for one more week to ensure it doesn't come back. After that, you can stop using the tacrolimus. 

If your skin starts feeling dry, you can use a simple moisturizer like Vanicream or even a little petroleum jelly. Avoid any new products for now, especially anti-aging or plant-based ones, until your skin is fully cleared.

Please keep in touch if you notice any changes or if the rash gets worse. We'll schedule a follow-up in about four weeks to check on your progress. You've got all the refills you need, so you should be good to go. Let me know if you need anything else in the meantime.


## Condition: `strong_prompt`

_latency_: 28836 ms

**Response**

Thank you for sharing your concerns and treatment experiences, Jacqueline. I understand how frustrating it must be to see your rash plateau after initial improvement. It’s commendable that you’ve been adjusting your treatment and monitoring your skin’s response. I want to work together to get this under control as quickly as possible.

Given the situation, we’ll adjust your treatment plan. Increasing the doxycycline to twice daily can help maintain the improvements you’ve seen. Additionally, introducing the tacrolimus ointment twice daily to the affected areas should provide further relief. This medication is effective for calming inflammation without the risks of steroids, and any temporary tingling sensation is normal and short-lived.

To summarize, you’ll continue using your current face wash and metro cream, increase doxycycline to twice daily, and apply the tacrolimus ointment twice daily to the rash. Once the rash clears, we’ll taper off the tacrolimus and doxycycline gradually. If you notice any dryness, reduce the face wash to once daily. 

We’ll schedule a follow-up in four weeks to reassess your progress. In the meantime, if you experience any worsening symptoms or have questions, please reach out via MyChart or call. I’ll provide samples of a basic moisturizer like Vanicream to keep your skin hydrated without irritation.

Let me know if you have any questions or concerns about this plan. We’re in this together, and I’m here to support you every step of the way.


## Condition: `framework_only`

_latency_: 8669 ms

**Response**

I understand you're doing well overall, but you mentioned a small bit of rash leftover. Let's focus on getting that cleared up.

We'll continue with the doxycycline twice a day and the metro cream as we discussed.

If the rash doesn't improve or gets worse, please reach out.

Can you tell me in your own words what we're doing to treat the rash and when we'll follow up?

Let's plan to see each other again in four weeks. In the meantime, if the rash gets worse or you notice any new symptoms, please call us right away.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `retrieval_only`

_latency_: 304308 ms

**Extracted profile (summary)**
```yaml
n_problems: 3
n_medications: 1
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 2
problems:
- persistent fatigue
- unintentional weight loss
- rash
medications:
- doxycycline (once a day)
allergies: []
```

**Response**

Thank you for sharing your concerns about your persistent fatigue and unintentional weight loss. I understand how these symptoms must be affecting your daily life.

Persistent fatigue can be caused by a variety of issues, and it's important to explore possible causes thoroughly. We'll look into factors like underlying health conditions or lifestyle influences to help identify the right approach for you.

Unintentional weight loss can be a sign of various health issues, and it's crucial to determine the root cause. We'll assess potential causes such as nutritional deficiencies or metabolic disorders to guide the appropriate next steps.

Rashes can have many causes, and it's important to monitor how this rash responds to treatment. Since you've already started doxycycline, we'll check if it's effective and consider other possible causes if needed.

Our goal is to work together to uncover the underlying causes of your symptoms. By gathering more information and possibly running some tests, we can create a clearer picture of what's happening and how to address it.

It's important to support your ability to continue working. We'll ensure that any treatment plan we develop takes into account your work schedule and helps you maintain your productivity.

We'll schedule some tests to better understand the causes of your fatigue and weight loss.

We'll monitor your rash to see if it improves with the doxycycline you're already taking.

We'll review your medical history and current medications to identify any potential factors contributing to your symptoms.

I want to make sure I've explained everything clearly. Can you summarize what we're going to do next in your own words?

Let's plan to follow up in a week to review the test results and adjust our approach as needed. In the meantime, if your symptoms worsen or if you experience any new issues, please don't hesitate to reach out.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']

## Condition: `full`

_latency_: 340177 ms

**Extracted profile (summary)**
```yaml
n_problems: 3
n_medications: 1
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 2
problems:
- persistent fatigue
- unintentional weight loss
- rash
medications:
- doxycycline (once a day)
allergies: []
```

**Response**

Thank you for sharing your concerns with me. It sounds like you're dealing with several issues that are impacting your daily life.

Fatigue can be caused by various factors, including underlying health conditions. Given that your fatigue is persistent and accompanied by unintentional weight loss, it's important to explore potential causes thoroughly.

Unintentional weight loss can be a sign of various health issues. It's especially important to monitor this alongside your fatigue to understand the underlying causes.

Rashes can have many causes, and it's good that you've already started treatment with doxycycline. However, since the rash is ongoing, we should monitor its response to treatment and consider other possible causes if it doesn't improve.

Understanding the root cause of your symptoms is a key goal. We'll work together to gather the necessary information and run appropriate tests to help clarify what's happening.

Maintaining your ability to work is an important goal. We'll ensure that our approach to your care supports your ability to continue working as much as possible.

We'll schedule some blood tests to look into the causes of your fatigue and weight loss.

We'll monitor your rash and see how it responds to the doxycycline. If it doesn't improve, we may need to explore other treatments.

We'll set up a follow-up appointment in a few weeks to review the test results and adjust our plan based on what we find.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to see each other again in 4 weeks. In the meantime, if you notice any new symptoms or if your current symptoms worsen, please call us so we can address them promptly.

_cited PMIDs_: ['40759522', '40577011', '33658141']

_NURSE_: ['Support', 'Respect']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']
