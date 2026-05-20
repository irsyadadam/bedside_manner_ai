# Table 10 — Cross-dataset summary

Headline metrics for the Full pipeline vs. the Strong-prompt baseline across PriMock57 / MTS-Dialog / ACI-Bench. Demonstrates that the framework + retrieval contributions generalize across dialogue styles and gold-note formats.

| Dataset | Condition | n | ROUGE-L | Topic cov. | Halluc.strict ↓ | Halluc.semantic ↓ | Safety pass | NURSE n | 4H n |
|---|---|---|---|---|---|---|---|---|---|
| mts_dialog | Strong-prompt baseline | 235 | 0.082 | 0.687 | 0.000 | — | 0.22 | 0.0 | 0.0 |
| mts_dialog | Full pipeline | 229 | 0.079 | 0.656 | 0.283 | 0.020 | 0.26 | 1.7 | 2.6 |