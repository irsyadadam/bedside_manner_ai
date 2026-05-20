# Table 8 — Module I extraction accuracy (MTS-Dialog)

Per-section precision / recall / F1 of fields extracted by Module I against MTS-Dialog gold sections. Strategy is `set` for discrete fields (MEDICATIONS / ALLERGIES) and `token_overlap` for free-text fields (HPI, PMH, etc.).

| Section | Strategy | Retrieval only P / R / F1 (n) | Full pipeline P / R / F1 (n) |
|---|---|---|---|
| HPI | token_overlap | 0.64 / 0.06 / **0.11** (n=70) | 0.65 / 0.06 / **0.11** (n=68) |
| PMH | token_overlap | 0.00 / 0.00 / **0.00** (n=12) | 0.00 / 0.00 / **0.00** (n=11) |
| MEDICATIONS | set | 0.35 / 0.34 / **0.34** (n=10) | 0.29 / 0.28 / **0.29** (n=10) |
| CC | token_overlap | 0.23 / 0.11 / **0.14** (n=14) | 0.23 / 0.13 / **0.15** (n=14) |
| ASSESSMENT | primary_cluster | 0.00 / 0.00 / **0.00** (n=12) | 0.00 / 0.00 / **0.00** (n=12) |
| PLAN | primary_cluster | 0.00 / 0.00 / **0.00** (n=3) | 0.00 / 0.00 / **0.00** (n=3) |
| **Macro F1 (over sections)** | — | **0.10** | **0.09** |