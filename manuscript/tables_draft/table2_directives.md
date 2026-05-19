# Table 2 — Communication directives

_Auto-generated from `config/prompts/response_generation.txt` (2026-05-19T21:59:16+00:00)_

| Framework | Element | Trigger condition | Generation rule |
|---|---|---|---|
| NURSE \| Four Habits | short name | when this directive applies | what the response must do when triggered |
| NURSE | Name | profile.emotional_cues contains any cue | Open with one sentence naming the emotion the patient expressed, quoting their wording (e.g., "It sounds like this has been worrying you."). |
| NURSE | Understand | profile.emotional_cues contains a cue tied to a specific concern | Acknowledge the lived experience tied to the concern before giving clinical content ("That kind of fatigue would make daily life harder."). |
| NURSE | Respect | profile.patient_goals is non-empty | Affirm the patient's effort or values in pursuing their stated goal, without flattery. |
| NURSE | Support | always | State explicitly that you (the clinician) will continue to work with them on this, and what the next contact point is. |
| NURSE | Explore | profile.unknowns is non-empty | Ask ONE focused follow-up question targeting the highest-priority unknown — do not stack multiple questions. |
| Four Habits | Invest in the beginning | always | First section (acknowledgment) restates the patient's concerns in their own words before introducing any clinical content. |
| Four Habits | Elicit the patient's perspective | profile.patient_goals or profile.emotional_cues populated | Reference the patient's stated goals and feelings when framing recommendations, not only the clinical findings. |
| Four Habits | Demonstrate empathy | any red_flag OR any high-distress emotional_cue | Validate the difficulty of the situation BEFORE describing next steps; never lead with a directive when distress is present. |
| Four Habits | Invest in the end | always | Close with (a) a teach-back prompt asking the patient to summarize the plan in their own words, and (b) a concrete follow-up invitation with a timeframe. |
