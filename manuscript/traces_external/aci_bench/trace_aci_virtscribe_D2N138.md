# External-dataset trace — `aci_virtscribe_D2N138`

- Dataset: **aci_bench**
- Mode: real
- Speaker strategy: middle
- # patient utterances: 58
- Gold sections: ['ALLERGIES', 'ASSESSMENT', 'CC', 'CURRENT_MEDICATIONS', 'HPI', 'INSTRUCTIONS', 'PAST_HISTORY', 'PLAN', 'RESULTS', 'SOCIAL_HISTORY']
- Gold note length: 5317 chars

## Patient utterances (first 3)
1. [Clinician asked: "hi emily , how are you ?"] i'm pretty good , how are you ?
2. [Clinician asked: "i'm good , thank you . so gosh , we last talked a little bit over a year ago and it was just a telemedicine visit , but it seems like you've been doing pretty good . i know there was an insurance change . i think you had switched over to wixela , is that right ?"] yep , that's right , and it's what i'm currently using .
3. [Clinician asked: "okay , and that's the 250/50 dose , correct ?"] yes , correct .
... (55 more)

## Gold sections
### CC

Follow-up for asthma, allergic rhinitis, and food allergy.

### HPI

Emily Hernandez is a 20-year-old female presenting today for an annual follow-up for asthma, allergic rhinitis, and food allergy. Due to insurance changes during the interim of our last office appointment from 04/2020, she was switched from Symbicort to Wixela. She uses Zyrtec in the spring, summer, and fall for her seasonal allergy symptoms, which tends to work well. She has known peanut and tree nut allergies, which she tries to avoid. She does tolerate almonds and cashew.

Mrs. Hernandez is trying to join the military, who require a certain fitness level without use of a rescue or maintenance inhaler, so she has been weaning off her inhalers. She uses albuterol prior to a run, but otherwise functions without it. She has been reducing her Wixela dose, using 1 inhalation once daily 3 times per week, with remaining days using it twice per day as prescribed. She feels this is working well. She denies urgent care or emergency room visits for respiratory issues in the past year. She denies requiring prednisone for breathing issues in the past year.

She hopes to be enlisted in the military in early spring of 2022. She is currently undergoing exertional testing to this purpose. She exp…

### PAST_HISTORY

Medical
Asthma.
Allergy rhinitis.
Food allergies to peanut and tree nuts.

### SOCIAL_HISTORY

Currently smokes tobacco and vapes, trying to reduce and interested in cessation in preparation for joining the army.

### CURRENT_MEDICATIONS

Wixela Inhub 250 mcg-50 mcg/dose powder for inhalation. 1 puff 2 times daily in the morning and evening.
Proair HFA as needed.
EpiPen as needed.
Alvesco 80 mcg 2 puff 2 times daily.

### ALLERGIES

Peanuts cause a severe, anaphylactic reaction.
Montelukast sodium, “seizure-like” reaction.

### RESULTS

Asthma Control Test (ACT) Results: ACT score is 21.
Current food skin test sensitivities include peanuts.

### ASSESSMENT

• Moderate persistent asthma, uncomplicated.
• Allergic rhinitis.
• Anaphylactic reaction due to peanuts.

Emily Hernandez is a 20-year-old female who presented today for her yearly follow-up appointment for asthma, allergic rhinitis, and food allergy.

### PLAN

Moderate persistent asthma, uncomplicated
The patient has been using Wixela inhaler daily and admits to reducing her daily dose to one puff per day, 3-4 days per week as she feels she does not always need it the full dose. Additionally, she aspires to join the military and she must meet certain physical fitness requirements without the use of her inhaler. I counseled the patient on current asthma treatment guidelines which recommend using Wixela and Alvesco only when needed during periods of illness. The patient agreed to reducing her medicine to Alvesco which is a single medication, versus 2 in Welixa. The patient will continue to use her albuterol inhaler as needed. Her ACT score is 21 today and her spirometry test today was better than it was in 2019, though she recalls that it was smoky from wildfires during her last breathing test.

Allergic rhinitis
She will continue to use Zyrtec as needed, primarily during spring and fall and sometimes in summer. Her current dose cadence is 3 times per week when she works outside. Symptoms are currently under control.

Anaphylactic reaction due to peanuts
The patient has successfully avoided peanuts. Plan is to continue with current methods…

### INSTRUCTIONS

Moderate persistent asthma, uncomplicated
Start Alvesco, 2 puffs twice daily. Keep Wixela in case Alvesco does not work well. Continue albuterol as needed. Return in 4 months to repeat ACT and spirometry testing.

Allergic rhinitis
Continue Zyrtec 10 mg daily as needed.

Anaphylactic reaction due to peanuts
Continue strict avoidance of peanuts. I will refill her EpiPen today.

## Condition: `naive`

_latency_: 15268 ms

**Response**

Emily, it's great to hear how well you're managing your asthma with Wixela. It sounds like you're doing a fantastic job, especially with your upcoming military goals. I'm glad the breathing test showed improvement, which is a testament to your hard work and dedication.

Switching to Alvesco 80mcg is a good step to potentially reduce your asthma medication while still maintaining control. Remember, it's two puffs twice a day, and keep Wixela handy just in case. We'll check your progress in four months to see how things are going.

You're being very responsible with your peanut allergy, and it's smart to stay cautious. Keep up the good work with Zyrtec and your EpiPen. Let me know if you have any questions or concerns in the meantime. You've got this!


## Condition: `strong_prompt`

_latency_: 22905 ms

**Response**

Thanks for sharing all that with me, Emily. It sounds like you're doing a lot to manage your asthma and work toward your military goals, and I can tell you're really motivated about this. It makes sense you'd want to minimize your reliance on the inhaler, and I appreciate your proactive approach to avoiding triggers like smoke and allergens.

Given your current asthma control with Wixela, we have a couple of options to consider. We could continue using it as you are now, which is actually an off-label use but works well for some people. Alternatively, we could switch to Alvesco, which is covered by Kaiser and might offer a simpler regimen. I'll call in the Alvesco prescription for you, starting with the lower dose of 80 mcg, and you'll take two puffs twice a day. This way, we can monitor how you respond and adjust as needed.

We'll plan to repeat your breathing test in four months to track your progress. In the meantime, keep using your inhaler as directed, and don't hesitate to reach out if you have any questions or concerns. Before you leave, could you summarize our plan in your own words so I can make sure everything is clear?

You're doing great, Emily. Keep up the excellent work, and I'll see you in four months for that follow-up. Wishing you all the best with your military goals!


## Condition: `framework_only`

_latency_: 8137 ms

**Response**

It sounds like you're doing a lot to manage your asthma and prepare for the military. I'm glad to hear that your breathing tests are looking good.

We'll continue monitoring your asthma with the alvesco inhaler and repeat the breathing test in four months to track your progress.

Can you tell me, in your own words, what we're going to do next and why?

Let's plan to check in again in four months for the follow-up breathing test. If you experience any breathing difficulties in the meantime, please reach out sooner.

_NURSE_: ['Support']
_Four Habits_: ['Invest in the beginning', 'Invest in the end']

## Condition: `retrieval_only`

_latency_: 166465 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 1
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 4
problems:
- shortness of breath
medications:
- Wixela
allergies: []
```

**Response**

Thank you for sharing your goals and concerns with me. It sounds like your main focus is on reducing your reliance on the albuterol inhaler to meet your military standards and achieve your fitness goals.

Based on your report of using the albuterol inhaler and the current guidelines, it's important to understand the underlying cause of your shortness of breath. This will help us tailor a plan that fits your goals of reducing inhaler use and maintaining fitness.

To help you reduce your reliance on the inhaler, we'll need to identify the cause of your shortness of breath and develop a management plan that aligns with your fitness goals.

Understanding the root cause of your breathing difficulties will be key to creating a fitness plan that minimizes your need for the inhaler.

We'll work together to create a fitness strategy that addresses your breathing challenges and supports your goal of passing the fitness test without using the inhaler.

To support your enlistment goal, we'll focus on managing your breathing symptoms and developing a fitness plan that aligns with your timeline.

We'll schedule a follow-up visit to discuss your symptoms in more detail and explore options to help you reduce your reliance on the inhaler.

In the meantime, keep track of when you experience shortness of breath and any other symptoms, and let me know if there are any changes.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to meet again in a few weeks to review your progress and adjust our plan as needed. If you have any questions or concerns before then, feel free to reach out.

_cited PMIDs_: ['38719772']

_NURSE_: ['Support', 'Respect']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']

## Condition: `full`

_latency_: 200703 ms

**Extracted profile (summary)**
```yaml
n_problems: 1
n_medications: 1
n_allergies: 0
n_red_flags: 0
n_emotional: 0
n_goals: 3
problems:
- dyspnea
medications:
- Wixela
allergies: []
```

**Response**

I understand you're here because of your shortness of breath during strenuous activity. You mentioned you're trying to use your inhaler less and preparing for military service, and you want to be able to exert without needing the inhaler by early spring 2022.

Graded exercise therapy is suggested for managing symptoms like shortness of breath. This approach helps gradually increase activity levels and can reduce the need for your inhaler.

We can explore ways to reduce your reliance on the inhaler through exercises and techniques that help manage your symptoms more effectively.

To support your goal of preparing for military service, we'll focus on strategies to improve your breathing and reduce the need for your inhaler, ensuring you're ready for the physical demands required.

By implementing a structured exercise plan and using proven techniques, we aim to help you meet your goal of being inhaler-free by early spring 2022.

We'll start with graded exercise therapy to help manage your shortness of breath and reduce your reliance on the inhaler.

We'll also introduce some breathing techniques and possibly use handheld fans to make your activities more comfortable.

We'll monitor your progress and adjust the plan as needed to ensure you're on track to meet your goals.

I want to make sure I explained this clearly — can you tell me, in your own words, what we're going to do next and why?

Let's plan to check in every 4 weeks to review your progress. If you experience any worsening symptoms or need adjustments to your plan, please reach out sooner.

_cited PMIDs_: ['38719772']

_NURSE_: ['Support', 'Respect']
_Four Habits_: ['Invest in the beginning', "Elicit the patient's perspective", 'Invest in the end']
