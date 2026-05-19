"""Starter authority table used by Module II rerank (Phase 8).

30 journals — chosen to cover: top general medicine (NEJM/Lancet/JAMA/BMJ/
Annals), top systematic-review venues (Cochrane), top primary-care and
family-medicine journals (Annals of Family Medicine, BJGP, JGIM, CFP,
CMAJ), high-impact specialty journals likely to surface in our corpus
(Circulation, JACC, Chest, Eur Resp J), and the patient-communication
canon (Patient Education and Counseling, Health Communication).

Scores are in [0, 1]. Match is case-insensitive against the parsed-doc
`journal` field; aliases (e.g. "BMJ" vs "British Medical Journal") map
to the same score.

This is a starter list. To revise: edit the canonical scores in
CANONICAL below, and add any new aliases — _normalize() will lowercase
and strip on lookup.
"""
from __future__ import annotations

# Canonical journal name -> authority score in [0, 1].
CANONICAL: dict[str, float] = {
    # ---- Top-tier general medicine (1.00) ----
    "New England Journal of Medicine":                    1.00,
    "The Lancet":                                         1.00,
    "JAMA":                                               1.00,
    "BMJ":                                                1.00,
    "Annals of Internal Medicine":                        0.95,
    # ---- Top systematic-review venue ----
    "Cochrane Database of Systematic Reviews":            0.98,
    # ---- Top sub-titles of top-tier ----
    "JAMA Internal Medicine":                             0.92,
    "JAMA Network Open":                                  0.82,
    "PLOS Medicine":                                      0.90,
    "BMJ Open":                                           0.80,
    # ---- Primary care / family medicine ----
    "Annals of Family Medicine":                          0.88,
    "British Journal of General Practice":                0.82,
    "Journal of General Internal Medicine":               0.82,
    "American Family Physician":                          0.78,
    "Canadian Medical Association Journal":               0.85,
    "Canadian Family Physician":                          0.75,
    "Family Practice":                                    0.75,
    "BMC Primary Care":                                   0.68,
    "BMC Family Practice":                                0.68,
    # ---- High-impact specialty ----
    "Circulation":                                        0.92,
    "Journal of the American College of Cardiology":      0.92,
    "Chest":                                              0.85,
    "European Respiratory Journal":                       0.85,
    "Gastroenterology":                                   0.88,
    # ---- Patient communication / public health ----
    "Patient Education and Counseling":                   0.80,
    "Health Communication":                               0.72,
    "American Journal of Preventive Medicine":            0.80,
    "American Journal of Public Health":                  0.78,
    "Health Affairs":                                     0.78,
    # ---- Methodology / generalist OA ----
    "Mayo Clinic Proceedings":                            0.78,
}

# Aliases (case-insensitive after _normalize). Map alias -> canonical key.
ALIASES: dict[str, str] = {
    "the new england journal of medicine":     "New England Journal of Medicine",
    "n engl j med":                            "New England Journal of Medicine",
    "lancet":                                  "The Lancet",
    "british medical journal":                 "BMJ",
    "the cochrane database of systematic reviews": "Cochrane Database of Systematic Reviews",
    "the bmj":                                 "BMJ",
    "ploS one":                                "BMJ Open",  # intentionally NOT in top 30
    "cmaj : canadian medical association journal": "Canadian Medical Association Journal",
    "cmaj":                                    "Canadian Medical Association Journal",
    "the european respiratory journal":        "European Respiratory Journal",
    "the journal of the american college of cardiology": "Journal of the American College of Cardiology",
    "jacc":                                    "Journal of the American College of Cardiology",
    "ann fam med":                             "Annals of Family Medicine",
    "br j gen pract":                          "British Journal of General Practice",
    "j gen intern med":                        "Journal of General Internal Medicine",
    "am fam physician":                        "American Family Physician",
}


def _normalize(name: str | None) -> str:
    if not name:
        return ""
    return name.strip().lower()


# Lowercased canonical map, built once.
_LOOKUP: dict[str, float] = {**{_normalize(k): v for k, v in CANONICAL.items()}}
# Merge aliases.
for alias, canonical in ALIASES.items():
    score = CANONICAL.get(canonical)
    if score is not None:
        _LOOKUP[_normalize(alias)] = score


def authority_score(journal: str | None) -> float:
    """Return [0, 1]. 0.0 for unknown / missing journal."""
    return _LOOKUP.get(_normalize(journal), 0.0)


def listed_canonical_journals() -> list[tuple[str, float]]:
    return sorted(CANONICAL.items(), key=lambda kv: (-kv[1], kv[0]))
