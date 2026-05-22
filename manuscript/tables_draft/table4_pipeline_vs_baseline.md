# Table 4. Pipeline vs. LLM-only baselines, by dataset

*Headline metrics on each external dataset comparing the full pipeline (Modules I–IV) against two LLM-only controls: a naive baseline (same local DeepSeek-R1-Distill-Qwen-14B with a generic “write an empathetic response” prompt) and a strong-prompt baseline (same model, prompt explicitly instructing NURSE + Four-Habits structure and PMID-style citations). Bold cells indicate the best per-row condition; ↑ higher is better, ↓ lower is better.*

| Dataset | Metric | Naive | Strong-prompt | Full pipeline |
|:---|:---|---:|---:|---:|
| **PriMock57 (n=57)** | Safety pass ↑ | 5% | 28% | **58%** |
|   | autoDx pass ↑ | 39% | 54% | **91%** |
|   | PMIDs / resp ↑ | 0.00 | 0.00 | **1.25** |
|   | NURSE n ↑ | 0.00 | 0.00 | **2.22** |
|   | 4H n ↑ | 0.00 | 0.00 | **3.25** |
|   | Halluc strict ↓ | —† | —† | 0.325 |
|   | Halluc sem ↓ | — | — | 0.000 |
| **MTS-Dialog (n=235)** | Safety pass ↑ | 1% | 22% | **26%** |
|   | autoDx pass ↑ | 64% | **72%** | 54% |
|   | PMIDs / resp ↑ | 0.00 | 0.00 | **0.86** |
|   | NURSE n ↑ | 0.00 | 0.00 | **1.69** |
|   | 4H n ↑ | 0.00 | 0.00 | **2.57** |
|   | Halluc strict ↓ | —† | —† | 0.283 |
|   | Halluc sem ↓ | — | — | 0.020 |
| **ACI-Bench (n=205)** | Safety pass ↑ | 3% | 12% | **35%** |
|   | autoDx pass ↑ | 40% | 58% | **77%** |
|   | PMIDs / resp ↑ | 0.00 | 0.00 | **1.48** |
|   | NURSE n ↑ | 0.00 | 0.00 | **2.20** |
|   | 4H n ↑ | 0.00 | 0.00 | **2.95** |
|   | Halluc strict ↓ | —† | —† | 0.181 |
|   | Halluc sem ↓ | — | — | 0.031 |

**Reading.** Bolded cells indicate the row's best-performing condition. Across both datasets, the full pipeline dominates on every provenance and empathy-marker metric. The autonomous-diagnosis (autoDx) pass rate flips direction on MTS-Dialog (favoring the strong-prompt baseline) because MTS's short section-focused snippets cause LLM-only conditions to produce vague, accidentally safe responses while the pipeline retrieves and references specific clinical content — a deployment-context sensitivity discussed in §5.

† **Halluc strict** cells for LLM-only baselines are reported as “—” because those conditions do not run Module I — they extract no patient-profile atoms, so their hallucination rate is trivially 0/0 = 0. The pipeline's 0.32–0.33 strict rate is reported alongside its 0.000 *semantic*-anchored rate; the gap is entirely accounted for by legitimate clinical normalizations (see Table 7 footnote and §4.3).

<small>Auto-generated from `manuscript/data/external_metrics_*.json` on 2026-05-22T16:28:04+00:00.</small>
