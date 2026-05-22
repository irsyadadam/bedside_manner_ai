# Table 11b — LLM-judge rubric scoring, per dataset

Per-item mean rubric score broken out by external dataset. Reveals the deployment-context dependence of each condition's rubric-item performance that Table 11's pooled view averages away.

## PriMock57 (n=57 transcripts)

| Rubric item | Element | Naive | Strong-prompt | Framework only | Retrieval only | Full pipeline |
|---|---|---:|---:|---:|---:|---:|
| `nurse_name` | Name (the emotion) | 0.98 (n=57) | 1.00 (n=57) | 0.96 (n=56) | 1.00 (n=54) | 0.98 (n=53) |
| `nurse_understand` | Understand | 0.96 (n=57) | 1.00 (n=57) | 0.82 (n=56) | 1.00 (n=54) | 0.92 (n=53) |
| `nurse_respect` | Respect | 0.51 (n=57) | 0.68 (n=57) | 0.27 (n=56) | 0.31 (n=54) | 0.28 (n=53) |
| `nurse_support` | Support | 0.96 (n=57) | 1.00 (n=57) | 0.98 (n=56) | 1.00 (n=54) | 0.96 (n=53) |
| `nurse_explore` | Explore | 0.05 (n=57) | 0.58 (n=57) | 0.50 (n=56) | 0.87 (n=54) | 0.66 (n=53) |
| `habits_open` | Invest in the beginning | 0.82 (n=57) | 1.00 (n=57) | 1.00 (n=56) | 0.94 (n=54) | 0.89 (n=53) |
| `habits_perspective` | Elicit the patient's perspective | 0.95 (n=57) | 1.00 (n=57) | 0.79 (n=56) | 0.98 (n=54) | 0.94 (n=53) |
| `habits_empathy` | Demonstrate empathy | 0.98 (n=57) | 1.00 (n=57) | 0.96 (n=56) | 1.00 (n=54) | 0.98 (n=53) |
| `habits_close` | Invest in the end | 0.63 (n=57) | 0.98 (n=57) | 1.00 (n=56) | 1.00 (n=54) | 0.98 (n=53) |
| `safety_no_dx` | No autonomous diagnosis | 0.81 (n=57) | 0.91 (n=57) | 1.00 (n=56) | 0.98 (n=54) | 1.00 (n=53) |
| `safety_escalation` | Appropriate escalation | 0.37 (n=57) | 0.39 (n=57) | 0.48 (n=56) | 0.19 (n=54) | 0.23 (n=53) |
| `safety_clinician_loop` | Clinician in the loop | 0.67 (n=57) | 0.96 (n=57) | 0.91 (n=56) | 0.91 (n=54) | 0.96 (n=53) |
| `plain_language` | Plain language | 1.00 (n=57) | 1.00 (n=57) | 1.00 (n=56) | 1.00 (n=54) | 1.00 (n=53) |
| `teach_back` | Teach-back present | 0.00 (n=57) | 0.82 (n=57) | 1.00 (n=56) | 1.00 (n=54) | 1.00 (n=53) |

## MTS-Dialog (n=235 transcripts)

| Rubric item | Element | Naive | Strong-prompt | Framework only | Retrieval only | Full pipeline |
|---|---|---:|---:|---:|---:|---:|
| `nurse_name` | Name (the emotion) | 0.58 (n=235) | 0.77 (n=235) | 0.43 (n=230) | 0.60 (n=232) | 0.65 (n=220) |
| `nurse_understand` | Understand | 0.56 (n=235) | 0.77 (n=235) | 0.30 (n=230) | 0.56 (n=232) | 0.60 (n=220) |
| `nurse_respect` | Respect | 0.56 (n=235) | 0.79 (n=235) | 0.23 (n=230) | 0.27 (n=232) | 0.36 (n=220) |
| `nurse_support` | Support | 0.85 (n=235) | 0.94 (n=235) | 0.55 (n=230) | 0.77 (n=232) | 0.80 (n=220) |
| `nurse_explore` | Explore | 0.50 (n=235) | 0.74 (n=235) | 0.18 (n=230) | 0.56 (n=232) | 0.58 (n=220) |
| `habits_open` | Invest in the beginning | 0.80 (n=235) | 0.98 (n=235) | 0.87 (n=230) | 0.95 (n=232) | 0.91 (n=220) |
| `habits_perspective` | Elicit the patient's perspective | 0.53 (n=235) | 0.82 (n=235) | 0.33 (n=230) | 0.60 (n=232) | 0.61 (n=220) |
| `habits_empathy` | Demonstrate empathy | 0.59 (n=235) | 0.81 (n=235) | 0.42 (n=230) | 0.57 (n=232) | 0.62 (n=220) |
| `habits_close` | Invest in the end | 0.10 (n=235) | 0.94 (n=235) | 0.89 (n=230) | 0.99 (n=232) | 0.95 (n=220) |
| `safety_no_dx` | No autonomous diagnosis | 1.00 (n=235) | 0.99 (n=235) | 1.00 (n=230) | 1.00 (n=232) | 1.00 (n=220) |
| `safety_escalation` | Appropriate escalation | 0.02 (n=235) | 0.03 (n=235) | 0.09 (n=230) | 0.03 (n=232) | 0.05 (n=220) |
| `safety_clinician_loop` | Clinician in the loop | 0.31 (n=235) | 0.85 (n=235) | 0.70 (n=230) | 0.67 (n=232) | 0.68 (n=220) |
| `plain_language` | Plain language | 1.00 (n=235) | 1.00 (n=235) | 1.00 (n=230) | 1.00 (n=232) | 1.00 (n=220) |
| `teach_back` | Teach-back present | 0.01 (n=235) | 0.94 (n=235) | 0.89 (n=230) | 1.00 (n=232) | 0.97 (n=220) |

## ACI-Bench (n=205 transcripts)

| Rubric item | Element | Naive | Strong-prompt | Framework only | Retrieval only | Full pipeline |
|---|---|---:|---:|---:|---:|---:|
| `nurse_name` | Name (the emotion) | 0.84 (n=205) | 0.99 (n=204) | 0.84 (n=202) | 0.89 (n=185) | 0.90 (n=188) |
| `nurse_understand` | Understand | 0.82 (n=205) | 0.99 (n=204) | 0.75 (n=202) | 0.90 (n=185) | 0.88 (n=188) |
| `nurse_respect` | Respect | 0.77 (n=205) | 0.90 (n=204) | 0.32 (n=202) | 0.49 (n=185) | 0.42 (n=188) |
| `nurse_support` | Support | 0.98 (n=205) | 1.00 (n=204) | 0.88 (n=202) | 0.94 (n=185) | 0.92 (n=188) |
| `nurse_explore` | Explore | 0.14 (n=205) | 0.45 (n=204) | 0.42 (n=202) | 0.76 (n=185) | 0.70 (n=188) |
| `habits_open` | Invest in the beginning | 0.75 (n=205) | 1.00 (n=204) | 0.93 (n=202) | 0.91 (n=185) | 0.89 (n=188) |
| `habits_perspective` | Elicit the patient's perspective | 0.82 (n=205) | 1.00 (n=204) | 0.72 (n=202) | 0.91 (n=185) | 0.91 (n=188) |
| `habits_empathy` | Demonstrate empathy | 0.84 (n=205) | 0.99 (n=204) | 0.83 (n=202) | 0.91 (n=185) | 0.91 (n=188) |
| `habits_close` | Invest in the end | 0.35 (n=205) | 1.00 (n=204) | 0.99 (n=202) | 0.99 (n=185) | 0.98 (n=188) |
| `safety_no_dx` | No autonomous diagnosis | 0.89 (n=205) | 0.86 (n=204) | 1.00 (n=202) | 1.00 (n=185) | 0.99 (n=188) |
| `safety_escalation` | Appropriate escalation | 0.01 (n=205) | 0.03 (n=204) | 0.23 (n=202) | 0.10 (n=185) | 0.11 (n=188) |
| `safety_clinician_loop` | Clinician in the loop | 0.80 (n=205) | 1.00 (n=204) | 0.92 (n=202) | 0.96 (n=185) | 0.97 (n=188) |
| `plain_language` | Plain language | 1.00 (n=205) | 1.00 (n=204) | 1.00 (n=202) | 1.00 (n=185) | 0.99 (n=188) |
| `teach_back` | Teach-back present | 0.00 (n=205) | 0.91 (n=204) | 1.00 (n=202) | 1.00 (n=185) | 0.99 (n=188) |

## Reading

- The 0/1 scoring is anchored by positive + negative example for each item (see `clinicomm.external_metrics.RUBRIC_ITEMS`). Same rubric goes to human raters via `scripts/gen_clinician_forms.py`.
- Each row's column-to-column delta isolates how much that condition's design contributes to the rubric item's behavior, within that deployment context.
- Items where ALL conditions score near 1.00 (e.g., plain_language) reflect free LLM behavior, not framework contribution.
- Items where the naive baseline scores near 0 but pipeline conditions score >0.9 (e.g., teach_back, habits_close on PriMock+ACI) are the framework's clearest contributions.
