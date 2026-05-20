"""Smoke tests for Phase 13 plumbing.

Run:  uv run python tests/test_phase13_smoke.py

These tests don't need any external datasets, vLLM, or GPU. They check
that the modules import cleanly, schemas are coherent, and metrics
return well-formed results on synthetic inputs. Real network-touching
tests (downloading the datasets, etc.) are out of scope here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import pytest  # type: ignore  # noqa: F401 — optional; script runs without it
except ImportError:
    pytest = None  # type: ignore


# Make `clinicomm` importable when running this file directly.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# --------------------------------------------------------------------------
# Imports
# --------------------------------------------------------------------------


def test_imports():
    from clinicomm.datasets import (
        ExternalTranscript, Turn,
    )
    from clinicomm.datasets import mts_dialog, primock57, aci_bench  # noqa: F401
    from clinicomm import external_metrics  # noqa: F401
    from clinicomm.baseline import (
        NaiveLLMBaseline, StrongPromptLLMBaseline,
        STRONG_PROMPT_BASELINE_SYSTEM,
    )  # noqa: F401
    assert ExternalTranscript is not None


# --------------------------------------------------------------------------
# ExternalTranscript + speaker strategies
# --------------------------------------------------------------------------


def test_external_transcript_middle_strategy():
    from clinicomm.datasets import ExternalTranscript, Turn

    t = ExternalTranscript(
        id="x1",
        dataset="test",
        scenario="demo",
        turns=[
            Turn(role="clinician", text="What brings you in today?", raw_role="Doctor"),
            Turn(role="patient", text="I've been so tired for a month.", raw_role="Patient"),
            Turn(role="clinician", text="Any other symptoms?", raw_role="Doctor"),
            Turn(role="patient", text="Headaches in the morning.", raw_role="Patient"),
        ],
    )

    utts_middle = t.to_patient_utterances("middle")
    assert len(utts_middle) == 2
    assert "Clinician asked" in utts_middle[0]
    assert "tired for a month" in utts_middle[0]

    utts_patient_only = t.to_patient_utterances("patient_only")
    assert len(utts_patient_only) == 2
    assert "Clinician asked" not in utts_patient_only[0]

    utts_interleaved = t.to_patient_utterances("interleaved")
    assert len(utts_interleaved) == 4
    assert utts_interleaved[0].startswith("[Clinician]")
    assert utts_interleaved[1].startswith("[Patient]")


def test_external_transcript_roundtrip():
    from clinicomm.datasets import ExternalTranscript, Turn

    t = ExternalTranscript(
        id="x1", dataset="test", scenario="s",
        turns=[Turn(role="patient", text="hi", raw_role="P")],
        gold_sections={"HPI": "..."},
    )
    s = t.to_json()
    t2 = ExternalTranscript.from_json(s)
    assert t2.id == t.id
    assert t2.turns[0].text == "hi"
    assert t2.gold_sections == {"HPI": "..."}


# --------------------------------------------------------------------------
# MTS dialogue parser
# --------------------------------------------------------------------------


def test_mts_parse_dialogue():
    from clinicomm.datasets.mts_dialog import _parse_dialogue

    raw = (
        "Doctor: How are you feeling?\n"
        "Patient: Not great, really tired.\n"
        "I've lost weight too.\n"          # continuation
        "Doctor: How much weight?\n"
        "Patient: About 10 pounds.\n"
    )
    turns = _parse_dialogue(raw)
    assert len(turns) == 4
    assert turns[0].role == "clinician"
    assert turns[1].role == "patient"
    assert "lost weight too" in turns[1].text


def test_mts_section_normalize():
    from clinicomm.datasets.mts_dialog import _normalize_section_label

    assert _normalize_section_label("HISTORY OF PRESENT ILLNESS") == "HPI"
    assert _normalize_section_label("genhx") == "HPI"
    assert _normalize_section_label("MEDICATIONS") == "MEDICATIONS"
    assert _normalize_section_label("ALLERGIES") == "ALLERGIES"


# --------------------------------------------------------------------------
# ACI SOAP parser
# --------------------------------------------------------------------------


def test_aci_parse_soap_note():
    from clinicomm.datasets.aci_bench import parse_soap_note

    note = (
        "SUBJECTIVE\n"
        "Patient reports fatigue and 10-lb weight loss over 1 month.\n"
        "\n"
        "OBJECTIVE\n"
        "Vitals stable. Exam unremarkable.\n"
        "\n"
        "ASSESSMENT AND PLAN\n"
        "1. Fatigue — order CBC, CMP, TSH.\n"
        "2. Follow up in 2 weeks.\n"
    )
    out = parse_soap_note(note)
    assert "SUBJECTIVE" in out
    assert "OBJECTIVE" in out
    assert "ASSESSMENT_PLAN" in out
    assert "fatigue" in out["SUBJECTIVE"].lower()
    assert "CBC" in out["ASSESSMENT_PLAN"]


def test_aci_parse_dialogue():
    from clinicomm.datasets.aci_bench import parse_dialogue

    raw = (
        "[Doctor] What brings you in today?\n"
        "[Patient] I've been short of breath for two weeks.\n"
        "[Doctor] Any chest pain?\n"
        "[Patient] No, just tightness.\n"
    )
    turns = parse_dialogue(raw)
    assert len(turns) == 4
    assert turns[0].role == "clinician"
    assert turns[1].role == "patient"


# --------------------------------------------------------------------------
# PriMock VTT parser
# --------------------------------------------------------------------------


def test_primock_parse_vtt():
    from clinicomm.datasets.primock57 import parse_vtt

    vtt = (
        "WEBVTT\n"
        "\n"
        "00:00:01.000 --> 00:00:05.000\n"
        "<v Doctor>What seems to be the problem?</v>\n"
        "\n"
        "00:00:05.000 --> 00:00:10.000\n"
        "<v Patient>I've had a cough for three weeks.</v>\n"
    )
    turns = parse_vtt(vtt)
    assert len(turns) == 2
    assert turns[0].role == "clinician"
    assert turns[1].role == "patient"
    assert "cough" in turns[1].text


def test_primock_parse_vtt_plain_speakers():
    """Fallback: Doctor:/Patient: lines without VTT speaker tags."""
    from clinicomm.datasets.primock57 import parse_vtt

    vtt = (
        "WEBVTT\n"
        "00:00:01.000 --> 00:00:05.000\n"
        "Doctor: What seems to be the problem?\n"
        "00:00:05.000 --> 00:00:10.000\n"
        "Patient: I've had a cough for three weeks.\n"
    )
    turns = parse_vtt(vtt)
    assert len(turns) == 2
    assert turns[0].role == "clinician"


# --------------------------------------------------------------------------
# external_metrics: field extraction F1
# --------------------------------------------------------------------------


def test_field_extraction_f1_medications_set():
    from clinicomm.external_metrics import field_extraction_f1_one
    from clinicomm.schemas import PatientConcernProfile

    profile = PatientConcernProfile(
        medications=["lisinopril 10 mg daily", "metformin 500 mg BID"],
    )
    # Gold has same two meds; perfect set match after normalization
    res = field_extraction_f1_one(
        gold_section="MEDICATIONS",
        gold_text="Lisinopril 10 mg po daily, Metformin 500 mg BID",
        profile=profile,
    )
    assert res is not None
    p, r, f, strategy = res
    assert strategy == "set"
    assert f > 0.5  # both meds normalize to "lisinopril" and "metformin"


def test_field_extraction_f1_allergies_negation():
    from clinicomm.external_metrics import field_extraction_f1_one
    from clinicomm.schemas import PatientConcernProfile

    # NKDA gold + empty extracted = perfect match by convention
    profile = PatientConcernProfile(allergies=[])
    res = field_extraction_f1_one(
        gold_section="ALLERGIES",
        gold_text="NKDA",
        profile=profile,
    )
    assert res is not None
    p, r, f, _ = res
    assert f == 1.0


def test_field_extraction_f1_hpi_token():
    from clinicomm.external_metrics import field_extraction_f1_one
    from clinicomm.schemas import PatientConcernProfile, Problem

    profile = PatientConcernProfile(
        problems=[Problem(label="fatigue", onset="1 month", timing="daily")],
    )
    res = field_extraction_f1_one(
        gold_section="HPI",
        gold_text="Patient reports fatigue lasting one month, daily.",
        profile=profile,
    )
    assert res is not None
    p, r, f, _ = res
    assert f > 0.3


# --------------------------------------------------------------------------
# external_metrics: hallucination rate
# --------------------------------------------------------------------------


def test_hallucination_rate_clean():
    from clinicomm.external_metrics import hallucination_rate
    from clinicomm.schemas import PatientConcernProfile, Problem

    transcript = "I have been so tired for a month and I take lisinopril for blood pressure."
    profile = PatientConcernProfile(
        problems=[Problem(label="fatigue")],
        medications=["lisinopril"],
    )
    out = hallucination_rate(profile=profile, transcript_text=transcript)
    # 'fatigue' word doesn't appear but its token overlap with 'tired' fails;
    # 'lisinopril' appears verbatim.
    assert out["n_atoms"] == 2
    assert out["by_field_strict"]["medication"] == 0.0


def test_hallucination_rate_invented():
    from clinicomm.external_metrics import hallucination_rate
    from clinicomm.schemas import PatientConcernProfile, Problem

    transcript = "I have had a headache."
    profile = PatientConcernProfile(
        problems=[Problem(label="metastatic pancreatic carcinoma")],
        medications=["chemotherapy"],
    )
    out = hallucination_rate(profile=profile, transcript_text=transcript)
    # Neither atom is anchored in the transcript under strict scoring.
    assert out["rate_strict"] == 1.0
    assert out["rate"] == 1.0  # backwards-compat alias
    assert len(out["examples_strict"]) == 2
    # Without an embed_model the semantic check is skipped and falls back to strict.
    assert out["semantic_available"] is False


# --------------------------------------------------------------------------
# external_metrics: safety audit
# --------------------------------------------------------------------------


def test_safety_audit_red_flag_pass():
    from clinicomm.external_metrics import safety_audit
    from clinicomm.schemas import PatientConcernProfile, RedFlag

    profile = PatientConcernProfile(
        red_flags=[RedFlag(flag="suicidal ideation", evidence="I've thought about ending it")],
    )
    response_text = (
        "I can hear how heavy this has been. I want to make sure you're safe — "
        "please go to the emergency room today, and we'll work with your doctor "
        "on next steps. I'd like to check in with you within 2 days."
    )
    out = safety_audit(response_text=response_text, profile=profile)
    assert out.has_escalation_when_red_flag is True
    assert out.no_autonomous_diagnosis is True
    assert out.has_followup_timeframe is True
    assert out.has_clinician_loop is True
    assert out.all_pass is True


def test_safety_audit_autonomous_dx_fail():
    from clinicomm.external_metrics import safety_audit
    from clinicomm.schemas import PatientConcernProfile

    response_text = (
        "You have iron-deficiency anemia. Take ferrous sulfate 325 mg three times "
        "a day for 3 months."
    )
    out = safety_audit(response_text=response_text, profile=PatientConcernProfile())
    assert out.no_autonomous_diagnosis is False
    assert out.all_pass is False


# --------------------------------------------------------------------------
# external_metrics: rouge / topic-coverage
# --------------------------------------------------------------------------


def test_topic_coverage():
    from clinicomm.external_metrics import topic_coverage

    gold = "Fatigue, weight loss, headaches."
    resp = "We'll look into the fatigue and the headaches. The weight loss matters too."
    cov = topic_coverage(resp, gold)
    assert cov >= 1.0  # every content keyword in gold appears in response


def test_rouge_l_smoke():
    from clinicomm.external_metrics import rouge_l

    res = rouge_l("The patient has fatigue.", "The patient reports fatigue.")
    if not res.get("available"):
        # rouge_score not installed — that's OK, just verify the contract.
        assert "reason" in res
    else:
        assert 0 <= res["f1"] <= 1


# --------------------------------------------------------------------------
# external_metrics: kappa + trust calibration
# --------------------------------------------------------------------------


def test_cohens_kappa_perfect():
    from clinicomm.external_metrics import cohens_kappa

    assert cohens_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0


def test_cohens_kappa_random():
    from clinicomm.external_metrics import cohens_kappa

    # Mostly disagreeing
    k = cohens_kappa([1, 1, 1, 0, 0, 0], [0, 0, 0, 1, 1, 1])
    assert k < 0


def test_trust_calibration_bins_shape():
    from clinicomm.external_metrics import trust_calibration_bins

    rows = [{"confidence": 0.1, "all_pass": False},
            {"confidence": 0.2, "all_pass": False},
            {"confidence": 0.8, "all_pass": True},
            {"confidence": 0.9, "all_pass": True}]
    out = trust_calibration_bins(rows, n_bins=5)
    assert len(out["bin_centers"]) == 5
    assert len(out["bin_accuracy"]) == 5
    assert sum(out["bin_n"]) == 4


# --------------------------------------------------------------------------
# baseline.py: strong prompt
# --------------------------------------------------------------------------


def test_strong_prompt_baseline_uses_distinct_system_prompt():
    from clinicomm.baseline import (
        BASELINE_SYSTEM_PROMPT,
        STRONG_PROMPT_BASELINE_SYSTEM,
    )
    assert BASELINE_SYSTEM_PROMPT != STRONG_PROMPT_BASELINE_SYSTEM
    assert "NURSE" in STRONG_PROMPT_BASELINE_SYSTEM
    assert "Four Habits" in STRONG_PROMPT_BASELINE_SYSTEM
    assert "PMID" in STRONG_PROMPT_BASELINE_SYSTEM


def test_strip_reasoning_full_block():
    from clinicomm.baseline import _strip_reasoning

    raw = "<think>I should empathize first.</think>\n\nI hear you. Let's plan."
    out = _strip_reasoning(raw)
    assert out == "I hear you. Let's plan."


def test_strip_reasoning_missing_open_tag():
    """R1-distill sometimes drops the opening <think> tag — we must still
    strip the leading reasoning content that ends with </think>."""
    from clinicomm.baseline import _strip_reasoning

    raw = (
        "Okay, so I need to write an empathetic response. The patient has "
        "diarrhea for three days. I should acknowledge their symptoms.\n"
        "</think>\n\n"
        "I'm really sorry to hear about the discomfort you've been experiencing."
    )
    out = _strip_reasoning(raw)
    assert out.startswith("I'm really sorry")
    assert "Okay, so I need" not in out
    assert "</think>" not in out


def test_strip_reasoning_no_reasoning_passes_through():
    from clinicomm.baseline import _strip_reasoning
    raw = "I hear you. Let's plan next steps within 2 weeks."
    out = _strip_reasoning(raw)
    assert out == raw


# --------------------------------------------------------------------------
# Rubric
# --------------------------------------------------------------------------


def test_rubric_items_well_formed():
    from clinicomm.external_metrics import RUBRIC_ITEMS

    seen = set()
    for it in RUBRIC_ITEMS:
        assert it["id"] not in seen, f"duplicate rubric id {it['id']}"
        seen.add(it["id"])
        for k in ("id", "framework", "element", "definition",
                  "positive_anchor", "negative_anchor"):
            assert k in it
        assert len(it["definition"]) > 20


# --------------------------------------------------------------------------
# Plain runner (if pytest isn't installed)
# --------------------------------------------------------------------------


def _run_all():
    g = globals()
    fns = [(n, f) for n, f in g.items() if n.startswith("test_") and callable(f)]
    passed = 0
    failed = []
    for name, fn in fns:
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL  {name}: {e}")
            failed.append((name, e))
    print(f"\n{passed}/{len(fns)} passed.")
    if failed:
        for n, e in failed:
            print(f"  - {n}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_run_all())
