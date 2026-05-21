# Table 9 — Response quality on ACI-Bench

Mean per-condition metrics across encounters. Bolded numbers in the manuscript are the Full pipeline row. ↓ = lower better.

| Condition | n | ROUGE-L F1 | Topic cov. | Halluc.strict ↓ | Halluc.semantic ↓ | Safety pass | NURSE n | 4H n | PMIDs n | FK |
|---|---|---|---|---|---|---|---|---|---|---|
| Naive baseline | 8 | 0.098 | 0.135 | 0.000 | — | 0.00 | 0.0 | 0.0 | 0.0 | 8.8 |
| Strong-prompt baseline | 8 | 0.125 | 0.191 | 0.000 | — | 0.00 | 0.0 | 0.0 | 0.0 | 8.9 |
| Framework only | 8 | 0.083 | 0.103 | 0.000 | — | 0.62 | 1.4 | 2.1 | 0.0 | 6.7 |
| Retrieval only | 8 | 0.103 | 0.129 | 0.141 | 0.000 | 0.25 | 1.1 | 2.8 | 1.0 | 8.3 |
| Full pipeline | 8 | 0.109 | 0.139 | 0.177 | 0.000 | 0.38 | 2.0 | 2.6 | 1.1 | 7.7 |