# Table 11 — LLM-as-judge rubric scoring

Per-item mean rubric score from the LLM judge. Cohen's κ between LLM ratings and clinician ratings is reported once the n=20–30 spot-check sample comes back (see `scripts/gen_clinician_forms.py`).

| Rubric item | Framework | Element | Framework only (mean) | Full pipeline (mean) | Naive baseline (mean) | Retrieval only (mean) | Strong-prompt baseline (mean) | Cohen κ (LLM vs. human) |
|---|---|---|---|---|---|---|---|---|
| `nurse_name` | NURSE | Name (the emotion) | 0.53 (n=286) | 0.72 (n=273) | 0.66 (n=292) | 0.67 (n=286) | 0.81 (n=292) | _pending human ratings_ |
| `nurse_understand` | NURSE | Understand | 0.40 (n=286) | 0.66 (n=273) | 0.64 (n=292) | 0.65 (n=286) | 0.82 (n=292) | _pending human ratings_ |
| `nurse_respect` | NURSE | Respect | 0.24 (n=286) | 0.34 (n=273) | 0.55 (n=292) | 0.28 (n=286) | 0.77 (n=292) | _pending human ratings_ |
| `nurse_support` | NURSE | Support | 0.63 (n=286) | 0.84 (n=273) | 0.87 (n=292) | 0.81 (n=286) | 0.95 (n=292) | _pending human ratings_ |
| `nurse_explore` | NURSE | Explore | 0.24 (n=286) | 0.59 (n=273) | 0.41 (n=292) | 0.62 (n=286) | 0.71 (n=292) | _pending human ratings_ |
| `habits_open` | Four Habits | Invest in the beginning | 0.89 (n=286) | 0.90 (n=273) | 0.80 (n=292) | 0.95 (n=286) | 0.99 (n=292) | _pending human ratings_ |
| `habits_perspective` | Four Habits | Elicit the patient's perspective | 0.42 (n=286) | 0.68 (n=273) | 0.61 (n=292) | 0.67 (n=286) | 0.86 (n=292) | _pending human ratings_ |
| `habits_empathy` | Four Habits | Demonstrate empathy | 0.53 (n=286) | 0.69 (n=273) | 0.67 (n=292) | 0.65 (n=286) | 0.85 (n=292) | _pending human ratings_ |
| `habits_close` | Four Habits | Invest in the end | 0.91 (n=286) | 0.96 (n=273) | 0.21 (n=292) | 0.99 (n=286) | 0.95 (n=292) | _pending human ratings_ |
| `safety_no_dx` | Safety | No autonomous diagnosis | 1.00 (n=286) | 1.00 (n=273) | 0.96 (n=292) | 1.00 (n=286) | 0.97 (n=292) | _pending human ratings_ |
| `safety_escalation` | Safety | Appropriate escalation | 0.17 (n=286) | 0.08 (n=273) | 0.09 (n=292) | 0.06 (n=286) | 0.10 (n=292) | _pending human ratings_ |
| `safety_clinician_loop` | Safety | Clinician in the loop | 0.74 (n=286) | 0.74 (n=273) | 0.38 (n=292) | 0.72 (n=286) | 0.87 (n=292) | _pending human ratings_ |
| `plain_language` | Communication | Plain language | 1.00 (n=286) | 1.00 (n=273) | 1.00 (n=292) | 1.00 (n=286) | 1.00 (n=292) | _pending human ratings_ |
| `teach_back` | Communication | Teach-back present | 0.91 (n=286) | 0.97 (n=273) | 0.01 (n=292) | 1.00 (n=286) | 0.91 (n=292) | _pending human ratings_ |