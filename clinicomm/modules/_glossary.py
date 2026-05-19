"""Plain-language glossary used by Module IV's post-generation pass.

The LLM is *instructed* to use plain language in the prompt. This pass
is a belt-and-suspenders safety net: if a medical term slips through,
substitute it with the patient-friendly phrasing. Substitutions are
logged into PatientResponse.glossary_substitutions so the trace shows
exactly what was changed.

Matching rules:
  - whole-word, case-insensitive
  - preserves the case style of the first character when reasonable
  - only applied to patient-facing string fields, never to metadata
    (cluster_ids, pmids, framework labels, etc.)

To extend: add to GLOSSARY below. Keys are terms-as-they-appear in the
LLM output (singular). Values are the plain-English replacement.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# 35 starter entries — covers the most common slipups in primary-care
# language. Keys are lowercased.
GLOSSARY: dict[str, str] = {
    "hypertension":              "high blood pressure",
    "hyperlipidemia":            "high cholesterol",
    "myocardial infarction":     "heart attack",
    "cerebrovascular accident":  "stroke",
    "transient ischemic attack": "mini-stroke",
    "dyspnea":                   "trouble breathing",
    "syncope":                   "fainting",
    "hematuria":                 "blood in the urine",
    "hemoptysis":                "coughing up blood",
    "melena":                    "black tarry stool",
    "hematemesis":               "vomiting blood",
    "diaphoresis":               "sweating",
    "pyrexia":                   "fever",
    "tachycardia":               "fast heartbeat",
    "bradycardia":               "slow heartbeat",
    "edema":                     "swelling",
    "ecchymosis":                "bruise",
    "pruritus":                  "itching",
    "vertigo":                   "spinning dizziness",
    "dysuria":                   "painful urination",
    "nocturia":                  "needing to urinate at night",
    "polyuria":                  "urinating a lot",
    "polydipsia":                "being very thirsty",
    "polyphagia":                "being very hungry",
    "anorexia":                  "loss of appetite",
    "arthralgia":                "joint pain",
    "myalgia":                   "muscle aches",
    "paresthesia":               "tingling or pins-and-needles",
    "claudication":              "leg pain when walking",
    "lymphadenopathy":           "swollen glands",
    "cachexia":                  "severe unintentional weight loss",
    "hypoxia":                   "low oxygen",
    "hyperglycemia":             "high blood sugar",
    "hypoglycemia":              "low blood sugar",
    "contraindicated":           "not safe to use",
}


@dataclass
class _Substitution:
    field: str
    original: str
    plain: str
    count: int


def _compile_patterns() -> list[tuple[re.Pattern, str, str]]:
    """Order longer terms first so 'transient ischemic attack' wins
    over 'attack' if we ever add the latter."""
    items = sorted(GLOSSARY.items(), key=lambda kv: -len(kv[0]))
    out = []
    for term, plain in items:
        pat = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        out.append((pat, term, plain))
    return out


_PATTERNS = _compile_patterns()


def apply_to_text(text: str, field_name: str) -> tuple[str, list[_Substitution]]:
    """Apply every glossary pattern to `text`. Returns (new_text, log)."""
    log: list[_Substitution] = []
    out = text
    for pat, term, plain in _PATTERNS:
        # Use a counting sub: collect matches first, then replace.
        matches = list(pat.finditer(out))
        if not matches:
            continue
        # Replace while preserving the first letter's case for the
        # FIRST occurrence (e.g. "Hypertension is..." -> "High blood pressure is...").
        def _repl(m: re.Match) -> str:
            tok = m.group(0)
            if tok[:1].isupper():
                return plain[:1].upper() + plain[1:]
            return plain
        out = pat.sub(_repl, out)
        log.append(_Substitution(field=field_name, original=term, plain=plain, count=len(matches)))
    return out, log


__all__ = ["GLOSSARY", "apply_to_text", "_Substitution"]
