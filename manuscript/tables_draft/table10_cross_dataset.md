# Table 10 — Cross-dataset summary

Headline metrics for the Full pipeline vs. the Strong-prompt baseline across PriMock57 / MTS-Dialog / ACI-Bench. Demonstrates that the framework + retrieval contributions generalize across dialogue styles and gold-note formats.

| Dataset | Condition | n | ROUGE-L | Topic cov. | Halluc.strict ↓ | Halluc.semantic ↓ | Safety pass | NURSE n | 4H n |
|---|---|---|---|---|---|---|---|---|---|
| primock57 | Strong-prompt baseline | 57 | 0.106 | 0.207 | 0.000 | — | 0.28 | 0.0 | 0.0 |
| primock57 | Full pipeline | 55 | 0.096 | 0.137 | 0.325 | 0.000 | 0.58 | 2.2 | 3.3 |
| mts_dialog | Strong-prompt baseline | 235 | 0.082 | 0.687 | 0.000 | — | 0.22 | 0.0 | 0.0 |
| mts_dialog | Full pipeline | 229 | 0.079 | 0.656 | 0.283 | 0.020 | 0.26 | 1.7 | 2.6 |
| aci_bench | Strong-prompt baseline | 8 | 0.125 | 0.191 | 0.000 | — | 0.00 | 0.0 | 0.0 |
| aci_bench | Full pipeline | 8 | 0.109 | 0.139 | 0.177 | 0.000 | 0.38 | 2.0 | 2.6 |