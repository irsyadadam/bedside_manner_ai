# Table 6 — Provenance audit (mechanical)

_Auto-generated 2026-05-19T23:14:11+00:00; paraphrase-threshold = 0.55_

Each clinical claim in a generated `PatientResponse` cites a `cluster_id`; that cluster's `primary_assertion.evidence_quote` is checked against the source abstract.

## Overall

| Classification | Count | Share |
|---|---:|---:|
| supported | 17 | 100.0% |
| paraphrased | 0 | 0.0% |
| unsupported | 0 | 0.0% |
| orphan_cluster | 0 | 0.0% |
| **total** | **17** | 100% |

## By trace

| Trace | Supported | Paraphrased | Unsupported | Orphan |
|---|---:|---:|---:|---:|
| p001_fatigue_weightloss | 6 | 0 | 0 | 0 |
| p002_hypertension_followup | 5 | 0 | 0 | 0 |
| p003_depression_screening | 6 | 0 | 0 | 0 |

**Definitions.**  *supported* = evidence quote appears verbatim (whitespace-normalized) in the source abstract.  *paraphrased* = ≥ paraphrase-threshold of evidence-quote tokens occur in the abstract.  *unsupported* = neither.  *orphan_cluster* = the response cited a `cluster_id` that does not exist in the structured-context artifact (a regression to investigate).

**Limitations.** Token overlap is a lower bound on faithfulness — a semantically faithful paraphrase using different vocabulary may score *unsupported* mechanically. Human review on a subsample is recommended.
