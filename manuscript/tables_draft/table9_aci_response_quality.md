# Table 9 — Response quality on ACI-Bench

Mean per-condition metrics across encounters. Bolded numbers in the manuscript are the Full pipeline row. ↓ = lower better.

| Condition | n | ROUGE-L F1 | Topic cov. | Halluc.strict ↓ | Halluc.semantic ↓ | Safety pass | NURSE n | 4H n | PMIDs n | FK |
|---|---|---|---|---|---|---|---|---|---|---|
| Naive baseline | 205 | 0.121 | 0.146 | 0.000 | — | 0.03 | 0.0 | 0.0 | 0.0 | 8.5 |
| Strong-prompt baseline | 205 | 0.132 | 0.200 | 0.000 | — | 0.12 | 0.0 | 0.0 | 0.0 | 9.0 |
| Framework only | 204 | 0.095 | 0.095 | 0.000 | — | 0.41 | 1.1 | 2.0 | 0.0 | 6.9 |
| Retrieval only | 198 | 0.118 | 0.134 | 0.182 | 0.023 | 0.30 | 1.9 | 2.9 | 0.4 | 8.3 |
| Full pipeline | 199 | 0.119 | 0.140 | 0.181 | 0.031 | 0.35 | 2.2 | 3.0 | 1.5 | 8.5 |