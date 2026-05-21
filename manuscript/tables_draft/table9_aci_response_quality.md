# Table 9 — Response quality on ACI-Bench

Mean per-condition metrics across encounters. Bolded numbers in the manuscript are the Full pipeline row. ↓ = lower better.

| Condition | n | ROUGE-L F1 | Topic cov. | Halluc.strict ↓ | Halluc.semantic ↓ | Safety pass | NURSE n | 4H n | PMIDs n | FK |
|---|---|---|---|---|---|---|---|---|---|---|
| Naive baseline | 153 | 0.119 | 0.147 | 0.000 | — | 0.02 | 0.0 | 0.0 | 0.0 | 8.5 |
| Strong-prompt baseline | 153 | 0.130 | 0.198 | 0.000 | — | 0.09 | 0.0 | 0.0 | 0.0 | 9.0 |
| Framework only | 152 | 0.093 | 0.096 | 0.000 | — | 0.39 | 1.1 | 2.0 | 0.0 | 6.9 |
| Retrieval only | 148 | 0.116 | 0.133 | 0.196 | 0.016 | 0.29 | 1.8 | 2.8 | 0.4 | 8.2 |
| Full pipeline | 148 | 0.117 | 0.140 | 0.191 | 0.028 | 0.30 | 2.1 | 2.9 | 1.5 | 8.5 |