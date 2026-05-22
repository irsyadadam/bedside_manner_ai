# Table 7 — Per-dataset 5-condition headline

Mean per-condition metrics on each external dataset. **n** is the number of (transcript, condition) cells that produced a valid response (small variation across conditions reflects partial-failure cases where one condition errored on a transcript that otherwise completed).

Higher is better unless marked ↓. Strict-anchor hallucination includes legitimate clinical normalizations (e.g. patient says "burning when I pee" → Module I extracts "dysuria"); semantic-anchored hallucination filters those out and captures only genuine fabrications.

## PriMock57 (n=57 transcripts)

| Condition | n | Safety pass | autoDx pass | PMIDs / resp | NURSE n | 4H n | Halluc strict ↓ | Halluc sem ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Naive baseline | 57 | 5% | 39% | 0.00 | 0.00 | 0.00 | 0.000 | — |
| Strong-prompt baseline | 57 | 28% | 54% | 0.00 | 0.00 | 0.00 | 0.000 | — |
| Framework only | 56 | 34% | 75% | 0.00 | 1.04 | 1.88 | 0.000 | — |
| Retrieval only | 57 | 61% | 96% | 0.58 | 2.05 | 3.02 | 0.291 | 0.000 |
| **Full pipeline** | 55 | 58% | 91% | 1.25 | 2.22 | 3.25 | 0.325 | 0.000 |

## MTS-Dialog (n=235 transcripts)

| Condition | n | Safety pass | autoDx pass | PMIDs / resp | NURSE n | 4H n | Halluc strict ↓ | Halluc sem ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Naive baseline | 235 | 1% | 64% | 0.00 | 0.00 | 0.00 | 0.000 | — |
| Strong-prompt baseline | 235 | 22% | 72% | 0.00 | 0.00 | 0.00 | 0.000 | — |
| Framework only | 235 | 21% | 54% | 0.00 | 0.97 | 1.85 | 0.000 | — |
| Retrieval only | 235 | 18% | 46% | 0.26 | 1.52 | 2.44 | 0.289 | 0.016 |
| **Full pipeline** | 229 | 26% | 54% | 0.86 | 1.69 | 2.57 | 0.283 | 0.020 |

## ACI-Bench (n=205 transcripts)

| Condition | n | Safety pass | autoDx pass | PMIDs / resp | NURSE n | 4H n | Halluc strict ↓ | Halluc sem ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Naive baseline | 205 | 3% | 40% | 0.00 | 0.00 | 0.00 | 0.000 | — |
| Strong-prompt baseline | 205 | 12% | 58% | 0.00 | 0.00 | 0.00 | 0.000 | — |
| Framework only | 204 | 41% | 82% | 0.00 | 1.14 | 2.02 | 0.000 | — |
| Retrieval only | 198 | 30% | 82% | 0.44 | 1.86 | 2.85 | 0.182 | 0.023 |
| **Full pipeline** | 199 | 35% | 77% | 1.48 | 2.20 | 2.95 | 0.181 | 0.031 |

## Column definitions

- **Safety pass** — composite pass on the 4-item safety audit (escalation when red flag, no autonomous diagnosis, follow-up timeframe present, clinician-in-the-loop). All 4 must pass. ↑.
- **autoDx pass** — pass rate on the no-autonomous-diagnosis item alone, broken out as the cleanest single safety signal. ↑.
- **PMIDs / resp** — mean count of verifiable PubMed citations per response (real PMIDs from validated clusters). ↑.
- **NURSE n** — mean count of NURSE empathy elements applied per response (max 5: Name, Understand, Respect, Support, Explore). ↑.
- **4H n** — mean count of Four-Habits Model elements applied per response (max 4: Invest in beginning, Elicit patient perspective, Demonstrate empathy, Invest in end). ↑.
- **Halluc strict ↓** — fraction of Module I-extracted atoms not anchored in the transcript by verbatim/token-overlap. Includes both fabrications AND legitimate clinical normalizations. — = no atoms extracted.
- **Halluc sem ↓** — strict failures that also fail a BGE embedding-similarity check vs. transcript sentences. Approximates genuine fabrications by filtering out normalizations. Manuscript headline.

Reproducible from the per-condition summary JSON files in `manuscript/data/`; re-run `scripts/eval_against_gold.py --dataset all` to regenerate.
