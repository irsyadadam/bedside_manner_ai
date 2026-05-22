# Table 11 — LLM-as-judge rubric scoring

Per-item mean rubric score from the LLM judge. Cohen's κ between LLM ratings and clinician ratings is reported once the n=20–30 spot-check sample comes back (see `scripts/gen_clinician_forms.py`).

| Rubric item | Framework | Element | Framework only (mean) | Full pipeline (mean) | Naive baseline (mean) | Retrieval only (mean) | Strong-prompt baseline (mean) | Cohen κ (LLM vs. human) |
|---|---|---|---|---|---|---|---|---|
| `nurse_name` | NURSE | Name (the emotion) | 0.66 (n=488) | 0.79 (n=461) | 0.74 (n=497) | 0.76 (n=471) | 0.89 (n=496) | _pending human ratings_ |
| `nurse_understand` | NURSE | Understand | 0.54 (n=488) | 0.75 (n=461) | 0.72 (n=497) | 0.75 (n=471) | 0.89 (n=496) | _pending human ratings_ |
| `nurse_respect` | NURSE | Respect | 0.27 (n=488) | 0.38 (n=461) | 0.64 (n=497) | 0.36 (n=471) | 0.82 (n=496) | _pending human ratings_ |
| `nurse_support` | NURSE | Support | 0.73 (n=488) | 0.87 (n=461) | 0.92 (n=497) | 0.86 (n=471) | 0.97 (n=496) | _pending human ratings_ |
| `nurse_explore` | NURSE | Explore | 0.31 (n=488) | 0.64 (n=461) | 0.30 (n=497) | 0.68 (n=471) | 0.60 (n=496) | _pending human ratings_ |
| `habits_open` | Four Habits | Invest in the beginning | 0.91 (n=488) | 0.90 (n=461) | 0.78 (n=497) | 0.93 (n=471) | 0.99 (n=496) | _pending human ratings_ |
| `habits_perspective` | Four Habits | Elicit the patient's perspective | 0.55 (n=488) | 0.77 (n=461) | 0.70 (n=497) | 0.77 (n=471) | 0.91 (n=496) | _pending human ratings_ |
| `habits_empathy` | Four Habits | Demonstrate empathy | 0.65 (n=488) | 0.78 (n=461) | 0.74 (n=497) | 0.75 (n=471) | 0.91 (n=496) | _pending human ratings_ |
| `habits_close` | Four Habits | Invest in the end | 0.94 (n=488) | 0.97 (n=461) | 0.26 (n=497) | 0.99 (n=471) | 0.97 (n=496) | _pending human ratings_ |
| `safety_no_dx` | Safety | No autonomous diagnosis | 1.00 (n=488) | 1.00 (n=461) | 0.93 (n=497) | 1.00 (n=471) | 0.93 (n=496) | _pending human ratings_ |
| `safety_escalation` | Safety | Appropriate escalation | 0.19 (n=488) | 0.10 (n=461) | 0.06 (n=497) | 0.07 (n=471) | 0.07 (n=496) | _pending human ratings_ |
| `safety_clinician_loop` | Safety | Clinician in the loop | 0.81 (n=488) | 0.83 (n=461) | 0.55 (n=497) | 0.81 (n=471) | 0.92 (n=496) | _pending human ratings_ |
| `plain_language` | Communication | Plain language | 1.00 (n=488) | 1.00 (n=461) | 1.00 (n=497) | 1.00 (n=471) | 1.00 (n=496) | _pending human ratings_ |
| `teach_back` | Communication | Teach-back present | 0.94 (n=488) | 0.98 (n=461) | 0.00 (n=497) | 1.00 (n=471) | 0.91 (n=496) | _pending human ratings_ |