# Table 11 — LLM-as-judge rubric scoring

Per-item mean rubric score from the LLM judge. Cohen's κ between LLM ratings and clinician ratings is reported once the n=20–30 spot-check sample comes back (see `scripts/gen_clinician_forms.py`).

| Rubric item | Framework | Element | Framework only (mean) | Full pipeline (mean) | Naive baseline (mean) | Retrieval only (mean) | Strong-prompt baseline (mean) | Cohen κ (LLM vs. human) |
|---|---|---|---|---|---|---|---|---|
| `nurse_name` | NURSE | Name (the emotion) | 0.54 (n=294) | 0.73 (n=281) | 0.66 (n=300) | 0.68 (n=293) | 0.82 (n=300) | _pending human ratings_ |
| `nurse_understand` | NURSE | Understand | 0.41 (n=294) | 0.67 (n=281) | 0.64 (n=300) | 0.65 (n=293) | 0.82 (n=300) | _pending human ratings_ |
| `nurse_respect` | NURSE | Respect | 0.24 (n=294) | 0.34 (n=281) | 0.55 (n=300) | 0.28 (n=293) | 0.77 (n=300) | _pending human ratings_ |
| `nurse_support` | NURSE | Support | 0.64 (n=294) | 0.84 (n=281) | 0.88 (n=300) | 0.81 (n=293) | 0.95 (n=300) | _pending human ratings_ |
| `nurse_explore` | NURSE | Explore | 0.24 (n=294) | 0.60 (n=281) | 0.41 (n=300) | 0.62 (n=293) | 0.70 (n=300) | _pending human ratings_ |
| `habits_open` | Four Habits | Invest in the beginning | 0.89 (n=294) | 0.91 (n=281) | 0.80 (n=300) | 0.95 (n=293) | 0.99 (n=300) | _pending human ratings_ |
| `habits_perspective` | Four Habits | Elicit the patient's perspective | 0.43 (n=294) | 0.68 (n=281) | 0.61 (n=300) | 0.67 (n=293) | 0.86 (n=300) | _pending human ratings_ |
| `habits_empathy` | Four Habits | Demonstrate empathy | 0.53 (n=294) | 0.70 (n=281) | 0.67 (n=300) | 0.66 (n=293) | 0.85 (n=300) | _pending human ratings_ |
| `habits_close` | Four Habits | Invest in the end | 0.91 (n=294) | 0.96 (n=281) | 0.21 (n=300) | 0.99 (n=293) | 0.95 (n=300) | _pending human ratings_ |
| `safety_no_dx` | Safety | No autonomous diagnosis | 1.00 (n=294) | 1.00 (n=281) | 0.96 (n=300) | 1.00 (n=293) | 0.97 (n=300) | _pending human ratings_ |
| `safety_escalation` | Safety | Appropriate escalation | 0.17 (n=294) | 0.09 (n=281) | 0.09 (n=300) | 0.05 (n=293) | 0.10 (n=300) | _pending human ratings_ |
| `safety_clinician_loop` | Safety | Clinician in the loop | 0.74 (n=294) | 0.74 (n=281) | 0.40 (n=300) | 0.72 (n=293) | 0.88 (n=300) | _pending human ratings_ |
| `plain_language` | Communication | Plain language | 1.00 (n=294) | 1.00 (n=281) | 1.00 (n=300) | 1.00 (n=293) | 1.00 (n=300) | _pending human ratings_ |
| `teach_back` | Communication | Teach-back present | 0.91 (n=294) | 0.98 (n=281) | 0.01 (n=300) | 1.00 (n=293) | 0.92 (n=300) | _pending human ratings_ |