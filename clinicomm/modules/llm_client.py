"""LLM client abstraction.

Two concrete clients:
  - VLLMClient  : OpenAI-compatible HTTP call to the local vLLM server
                  started by scripts/start_vllm_server.sh.
  - MockLLMClient: in-process heuristic mock — used by Phase 7's --demo
                  flag so a dry-run trace runs without the vLLM server.
                  The mock does NOT replace the real model; it just
                  exercises the agent loop deterministically.

A real LLM call goes through `complete(system, user, ...)` and returns
the raw assistant text (string). The caller parses JSON.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Protocol

log = logging.getLogger(__name__)


class LLMClient(Protocol):
    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        response_format_json: bool = False,
    ) -> str: ...

    # Optional async variant. Implementations that don't override it
    # fall back to wrapping the sync complete() via asyncio.to_thread
    # (the default below). Used by Module III's concurrent extraction.
    async def complete_async(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        response_format_json: bool = False,
    ) -> str: ...


async def _sync_to_async(
    client,
    system: str,
    user: str,
    **kwargs,
) -> str:
    """Default async wrapper for sync-only clients (mocks, mostly)."""
    import asyncio

    return await asyncio.to_thread(client.complete, system, user, **kwargs)


# --------------------------------------------------------------------------
# vLLM (production)
# --------------------------------------------------------------------------


class VLLMClient:
    """Talks to a running vLLM OpenAI-compatible server.

    Construct with the llm: block from pipeline.yaml. Exposes BOTH a
    sync `complete()` (used by Module I and IV's single calls) and an
    async `complete_async()` (used by Module III to issue all
    per-document extraction calls concurrently via asyncio.gather).
    """

    def __init__(self, cfg: dict) -> None:
        # Lazy import so MockLLMClient users don't need openai installed
        # (though we ship it anyway for parity).
        try:
            from openai import AsyncOpenAI, OpenAI
        except ImportError as e:  # noqa: BLE001
            raise RuntimeError(
                "openai package is required for VLLMClient; "
                "ensure pyproject deps include openai>=1.40"
            ) from e

        self.client = OpenAI(
            base_url=cfg["base_url"],
            api_key=cfg.get("api_key") or "EMPTY",
        )
        self.async_client = AsyncOpenAI(
            base_url=cfg["base_url"],
            api_key=cfg.get("api_key") or "EMPTY",
        )
        self.model = cfg["model"]
        self.default_max_tokens = int(cfg.get("max_tokens", 4096))
        self.default_temperature = float(cfg.get("temperature", 0.2))
        self.default_top_p = float(cfg.get("top_p", 0.95))

    def _build_kwargs(
        self,
        system: str,
        user: str,
        max_tokens: int | None,
        temperature: float | None,
        response_format_json: bool,
    ) -> dict:
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": (
                self.default_temperature if temperature is None else temperature
            ),
            "top_p": self.default_top_p,
        }
        if response_format_json:
            kwargs["response_format"] = {"type": "json_object"}
        return kwargs

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        response_format_json: bool = False,
    ) -> str:
        resp = self.client.chat.completions.create(
            **self._build_kwargs(system, user, max_tokens, temperature, response_format_json)
        )
        return resp.choices[0].message.content or ""

    async def complete_async(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        response_format_json: bool = False,
    ) -> str:
        resp = await self.async_client.chat.completions.create(
            **self._build_kwargs(system, user, max_tokens, temperature, response_format_json)
        )
        return resp.choices[0].message.content or ""


# --------------------------------------------------------------------------
# Mock (offline trace)
# --------------------------------------------------------------------------


class MockLLMClient:
    """Tiny rule-based mock that produces a *plausible* PatientConcernProfile
    for the canned utterances in m1_intake.DEMO_UTTERANCES.

    Not a model — it just exercises the agent's extract / next-prompt /
    completion loop end-to-end without needing the GPU.

    State: the mock accumulates a profile dict across calls so that
    later turns see earlier extractions (mirrors the real LLM's
    behavior when given the running profile each call).
    """

    def __init__(self) -> None:
        self.call_count = 0
        self._state: dict = {
            "problems": [],
            "medications": [],
            "allergies": [],
            "relevant_history": [],
            "patient_goals": [],
            "emotional_cues": [],
            "red_flags": [],
            "unknowns": [],
            "turn_count": 0,
            "completion_status": "in_progress",
        }

    def _ensure_problem(self, label: str) -> dict:
        for p in self._state["problems"]:
            if p["label"].lower() == label.lower():
                return p
        new = {
            "label": label,
            "onset": None,
            "severity": None,
            "timing": None,
            "associated_symptoms": [],
            "interventions_tried": [],
            "status": "unknown",
        }
        self._state["problems"].append(new)
        return new

    def _quote_substring(self, user_turn: str, needle: str) -> str:
        # Return a substring of user_turn around `needle`, lowercase-insensitive.
        lo = user_turn.lower().find(needle.lower())
        if lo < 0:
            return needle
        # Expand to nearest sentence-ish boundary on each side.
        start = max(0, user_turn.rfind(".", 0, lo) + 1)
        end_dot = user_turn.find(".", lo + len(needle))
        end = end_dot if end_dot != -1 else len(user_turn)
        return user_turn[start:end].strip()

    def complete(
        self,
        system: str,  # noqa: ARG002 — unused; mock is rule-based
        user: str,
        *,
        max_tokens: int | None = None,  # noqa: ARG002
        temperature: float | None = None,  # noqa: ARG002
        response_format_json: bool = False,  # noqa: ARG002
    ) -> str:
        """`user` is the runtime-substituted text containing the current
        profile JSON and the latest utterance. We pull the latest
        utterance out with a regex matching the marker the IntakeAgent
        adds, then update self._state by heuristic.
        """
        self.call_count += 1
        m = re.search(
            r"LATEST_PATIENT_TURN:\s*(.+?)(?:\n\n|$)", user, re.DOTALL
        )
        turn = m.group(1).strip() if m else user.strip()
        lower = turn.lower()

        # --- problems --------------------------------------------------
        # Crude trigger words → problem labels. Add only on first mention.
        triggers = {
            "fatigue": ["tired", "exhausted", "fatigue", "no energy"],
            "weight loss": ["lost weight", "losing weight", "weight loss", "pounds"],
            "headache": ["headache", "head hurts", "pounding head"],
            "cough": ["cough"],
            "shortness of breath": ["short of breath", "shortness of breath", "can't breathe"],
            "chest pain": ["chest pain", "chest hurts", "pressure in my chest"],
            "abdominal pain": ["stomach pain", "abdominal pain", "belly hurts"],
            "depressed mood": ["feeling down", "depressed", "no joy", "hopeless"],
        }
        for label, keys in triggers.items():
            if any(k in lower for k in keys):
                self._ensure_problem(label)

        # --- onset / severity / timing patterns ------------------------
        # Match "for the past X", "since X", "started X ago", numeric severity.
        onset_match = re.search(
            r"(for the past[^.,;]{0,40}|since[^.,;]{0,40}|started[^.,;]{0,40}|"
            r"about [a-z]+ (?:days?|weeks?|months?|years?) ago)",
            lower,
        )
        severity_match = re.search(r"(\d{1,2})\s*(?:out of|\/)\s*10", lower) or re.search(
            r"\b(mild|moderate|severe|terrible|unbearable|awful)\b", lower
        )
        timing_match = re.search(
            r"(every\s+(?:day|night|morning|hour|week)|"
            r"throughout the day|after meals|in the morning|all the time)",
            lower,
        )

        for p in self._state["problems"]:
            if any(k in lower for k in triggers.get(p["label"], [p["label"]])):
                if p["onset"] is None and onset_match:
                    p["onset"] = onset_match.group(1).strip()
                if p["severity"] is None and severity_match:
                    p["severity"] = severity_match.group(0).strip()
                if p["timing"] is None and timing_match:
                    p["timing"] = timing_match.group(1).strip()

        # --- emotional cues -------------------------------------------
        cue_signals = {
            "worry": ["worried", "wondering", "anxious", "stress"],
            "fear": ["scared", "afraid", "terrified", "cancer", "die"],
            "frustration": ["frustrated", "fed up", "annoyed", "tired of"],
            "sadness": ["sad", "down", "low", "hopeless"],
            "isolation": ["alone", "no one", "isolated"],
        }
        already_quoted = {ec["evidence_quote"] for ec in self._state["emotional_cues"]}
        for cue, keys in cue_signals.items():
            for k in keys:
                if k in lower:
                    quote = self._quote_substring(turn, k)
                    if quote and quote not in already_quoted:
                        self._state["emotional_cues"].append(
                            {"cue": cue, "evidence_quote": quote}
                        )
                        already_quoted.add(quote)
                        break

        # --- red flags -------------------------------------------------
        red_flag_signals = {
            "unexplained weight loss": ["lost weight", "losing weight", "pounds without trying"],
            "suicidal ideation": ["hurting myself", "ending it", "kill myself", "no point"],
            "syncope": ["passed out", "fainted", "blacked out"],
            "hemoptysis": ["coughing up blood", "blood in sputum"],
            "neurologic deficit": ["sudden weakness", "numb on one side", "slurred speech"],
            "severe chest pain": ["crushing chest", "chest pain radiating"],
        }
        already_flags = {rf["evidence"] for rf in self._state["red_flags"]}
        for flag, keys in red_flag_signals.items():
            for k in keys:
                if k in lower:
                    q = self._quote_substring(turn, k)
                    if q not in already_flags:
                        self._state["red_flags"].append({"flag": flag, "evidence": q})
                        already_flags.add(q)
                        break

        # --- patient goals --------------------------------------------
        for phrase in ["i just want", "i want to", "i'd like to", "hoping to", "i need to"]:
            idx = lower.find(phrase)
            if idx >= 0:
                end = lower.find(".", idx)
                end = end if end > 0 else len(turn)
                goal = turn[idx:end].strip().rstrip(",")
                if goal and goal not in self._state["patient_goals"]:
                    self._state["patient_goals"].append(goal)

        # --- medications / allergies (very light extraction) ----------
        for med_kw in ["taking ", "i take ", "i'm on "]:
            i = lower.find(med_kw)
            if i >= 0:
                seg = turn[i + len(med_kw) : i + len(med_kw) + 80].split(".")[0].strip()
                if seg and seg not in self._state["medications"]:
                    self._state["medications"].append(seg)
                break

        # --- unknowns recomputation ------------------------------------
        unknowns: list[str] = []
        for i, p in enumerate(self._state["problems"]):
            for k in ("onset", "severity", "timing"):
                if p[k] is None:
                    unknowns.append(f"problems[{i}].{k}")
        # red-flag screen: assume the system has only "asked" once a
        # red flag has been mentioned OR the patient explicitly answered
        # the screen prompt. For the mock we treat the screen as
        # incomplete until at least one red-flag mention has happened.
        if not self._state["red_flags"] and not any(
            kw in lower for kw in ["no chest pain", "nothing like that", "no, none of that"]
        ):
            unknowns.append("red_flag_screen_complete")
        if not self._state["patient_goals"]:
            unknowns.append("patient_goals")
        if not self._state["medications"]:
            unknowns.append("medications")
        self._state["unknowns"] = unknowns

        # --- completion status / turn_count ---------------------------
        self._state["turn_count"] += 1
        if not unknowns:
            self._state["completion_status"] = "ready_for_handoff"
        else:
            self._state["completion_status"] = "in_progress"

        return json.dumps(self._state)

    async def complete_async(self, system, user, **kw):  # noqa: D401
        return self.complete(system, user, **kw)


# --------------------------------------------------------------------------
# Mock for Module III (Phase 9): assertion extraction + conflict resolution
# --------------------------------------------------------------------------


class MockReasoningLLM:
    """Heuristic mock for Phase 9 dry-runs. Two prompts to handle:

      - assertion_extraction.txt   -> emit a small bag of plausible
                                       ClinicalAssertion records keyed
                                       on doc title + addresses_concern
      - conflict_resolution.txt    -> deterministic recency tiebreak

    Detection is by markers in the system prompt header (see
    assertion_extraction.txt / conflict_resolution.txt).
    """

    def __init__(self) -> None:
        self.call_count = 0

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,  # noqa: ARG002
        temperature: float | None = None,  # noqa: ARG002
        response_format_json: bool = False,  # noqa: ARG002
    ) -> str:
        self.call_count += 1
        # Markers are uniquely placed in the actual prompt bodies; search
        # the whole string rather than only a fixed head window (the
        # leading "# ..." header comments are long).
        if "ASSERTION EXTRACTOR" in system:
            return self._mock_extract(user)
        if "CONFLICT RESOLVER" in system:
            return self._mock_resolve(user)
        return "{}"

    # -- extraction --------------------------------------------------------

    def _mock_extract(self, user: str) -> str:
        # Pull pmid / title / addresses_concern_candidates out of the
        # user payload. We use forgiving regex against the markers the
        # runtime injects from m3_reasoning.py.
        pmid_m = re.search(r'"pmid"\s*:\s*"(\d+)"', user)
        title_m = re.search(r'"title"\s*:\s*"([^"]+)"', user)
        pubyear_m = re.search(r'"pub_year"\s*:\s*(\d{4})', user)
        pubtypes_m = re.search(r'"pub_types"\s*:\s*\[(.*?)\]', user, re.DOTALL)
        cand_m = re.search(
            r"ADDRESSES_CONCERN_CANDIDATES.*?\[(.*?)\]", user, re.DOTALL
        )
        pmid = pmid_m.group(1) if pmid_m else "0"
        title = title_m.group(1) if title_m else ""
        pub_year = pubyear_m.group(1) if pubyear_m else "?"
        pubtypes_raw = pubtypes_m.group(1) if pubtypes_m else ""
        first_pubtype = (
            re.findall(r'"([^"]+)"', pubtypes_raw)[:1] or ["Journal Article"]
        )[0]
        candidates = re.findall(r'"([^"]+)"', cand_m.group(1) if cand_m else "")

        title_lower = title.lower()
        assertions: list[dict] = []

        # 1. Always emit a base recommendation tied to the first
        #    candidate concern (or null).
        addresses = candidates[0] if candidates else None
        assertions.append(
            {
                "assertion_id": f"{pmid}_0",
                "assertion_text": (
                    f"Per this {pub_year} {first_pubtype.lower()}, "
                    f"consider the approach described in: "
                    f"\"{title[:90]}\""
                ),
                "assertion_type": "recommendation",
                "confidence": 0.72,
                "source_pmid": pmid,
                "source_chunk_id": None,
                "addresses_concern": addresses,
                "evidence_quote": (title[:200] or "(mock evidence quote)"),
            }
        )

        # 2. If title smells communication-ish, add a directive.
        if any(
            k in title_lower
            for k in ("communic", "patient-centered", "shared decision", "empathy", "literacy")
        ):
            assertions.append(
                {
                    "assertion_id": f"{pmid}_1",
                    "assertion_text": (
                        "Use patient-centered communication strategies "
                        "(plain language, teach-back, shared decision-making) "
                        "when discussing this concern."
                    ),
                    "assertion_type": "communication_directive",
                    "confidence": 0.80,
                    "source_pmid": pmid,
                    "source_chunk_id": None,
                    "addresses_concern": None,
                    "evidence_quote": title[:200] or "(mock evidence quote)",
                }
            )
        # 3. If title smells screening-ish, add a monitoring assertion.
        if any(k in title_lower for k in ("screen", "monitor", "follow-up", "surveillance")):
            assertions.append(
                {
                    "assertion_id": f"{pmid}_{len(assertions)}",
                    "assertion_text": (
                        f"Periodic screening / monitoring is supported by "
                        f"this {first_pubtype.lower()}."
                    ),
                    "assertion_type": "monitoring",
                    "confidence": 0.70,
                    "source_pmid": pmid,
                    "source_chunk_id": None,
                    "addresses_concern": addresses,
                    "evidence_quote": title[:200] or "(mock evidence quote)",
                }
            )
        # 4. If title smells guideline-ish, add a finding.
        if any(
            k in title_lower
            for k in ("systematic review", "meta-analysis", "guideline", "consensus")
        ):
            assertions.append(
                {
                    "assertion_id": f"{pmid}_{len(assertions)}",
                    "assertion_text": (
                        f"This {first_pubtype.lower()} synthesizes evidence "
                        f"relevant to the patient's concerns."
                    ),
                    "assertion_type": "finding",
                    "confidence": 0.78,
                    "source_pmid": pmid,
                    "source_chunk_id": None,
                    "addresses_concern": addresses,
                    "evidence_quote": title[:200] or "(mock evidence quote)",
                }
            )
        return json.dumps({"assertions": assertions})

    # -- conflict resolution ----------------------------------------------

    def _mock_resolve(self, user: str) -> str:
        # Cluster JSON contains assertions[] each with pub_year. Pick
        # the most recent; tiebreak by authority_score. Emit alternatives
        # for the rest.
        # We expect the cluster_json to be present somewhere in user.
        m = re.search(r"CLUSTER.*?(\{.*\})\s*AUTHORITY_TABLE", user, re.DOTALL)
        if not m:
            return json.dumps(
                {
                    "primary_assertion_id": "",
                    "primary_rationale": "(mock) malformed cluster_json",
                    "resolution_rule": "recency",
                    "alternatives": [],
                }
            )
        try:
            cluster = json.loads(m.group(1))
        except json.JSONDecodeError:
            return json.dumps(
                {
                    "primary_assertion_id": "",
                    "primary_rationale": "(mock) cluster_json parse error",
                    "resolution_rule": "recency",
                    "alternatives": [],
                }
            )

        assertions = cluster.get("assertions", []) or []
        if not assertions:
            return json.dumps(
                {
                    "primary_assertion_id": "",
                    "primary_rationale": "(mock) empty cluster",
                    "resolution_rule": "recency",
                    "alternatives": [],
                }
            )

        def key(a: dict) -> tuple[int, float, float]:
            return (
                int(a.get("pub_year") or 0),
                float(a.get("authority_score") or 0.0),
                float(a.get("confidence") or 0.0),
            )

        winner = max(assertions, key=key)
        primary_id = winner["assertion_id"]
        rationale = (
            f"Recency: pub_year={winner.get('pub_year')} wins among "
            f"{[a.get('pub_year') for a in assertions]}; "
            "authority and confidence used as tiebreakers if needed."
        )
        alternatives = [
            {
                "assertion_id": a["assertion_id"],
                "retain_reason": (
                    f"Older ({a.get('pub_year')}) than the selected primary "
                    f"({winner.get('pub_year')}); retained for context."
                ),
            }
            for a in assertions
            if a["assertion_id"] != primary_id
        ]
        return json.dumps(
            {
                "primary_assertion_id": primary_id,
                "primary_rationale": rationale,
                "resolution_rule": "recency",
                "alternatives": alternatives,
            }
        )

    async def complete_async(self, system, user, **kw):  # noqa: D401
        return self.complete(system, user, **kw)


# --------------------------------------------------------------------------
# Mock for Module IV (Phase 10): response generation
# --------------------------------------------------------------------------


class MockResponseLLM:
    """Template-based response composer. Detects the RESPONSE COMPOSER
    system prompt and emits a PatientResponse-shaped JSON that:

      - opens with a NURSE 'Name + Understand' acknowledgment quoting
        an emotional cue verbatim, if nurse_triggered;
      - emits one ConcernExplanation per concern_path, citing the
        top cluster that addresses that path (or a global cluster);
      - puts a red-flag entry first in next_steps when red_flag_triggered.

    Useful for end-to-end traces without the GPU. Real LLM will produce
    much better prose; this is a wiring check.
    """

    def __init__(self) -> None:
        self.call_count = 0

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int | None = None,  # noqa: ARG002
        temperature: float | None = None,  # noqa: ARG002
        response_format_json: bool = False,  # noqa: ARG002
    ) -> str:
        self.call_count += 1
        if "RESPONSE COMPOSER" not in system:
            return "{}"
        return self._mock_response(user)

    async def complete_async(self, system, user, **kw):  # noqa: D401
        return self.complete(system, user, **kw)

    @staticmethod
    def _parse_user(user: str) -> dict:
        """Extract the PatientConcernProfile, StructuredContext, and
        concern_paths from the runtime-formatted user payload."""
        out: dict = {"profile": None, "context": None, "concern_paths": [], "nurse": False, "redflag": False}

        # Find each named section. The runtime joins them with
        # "PATIENT_PROFILE:\n{json}\n\nSTRUCTURED_CONTEXT:\n{json}\n\nCONCERN_PATHS...".
        for label, key in [
            ("PATIENT_PROFILE", "profile"),
            ("STRUCTURED_CONTEXT", "context"),
            ("CONCERN_PATHS", "concern_paths"),
        ]:
            m = re.search(
                rf"{label}[^\n]*:\s*(\[.*?\]|\{{.*?\}})\s*(?=\n\n[A-Z_]+:|\nFLAGS:|$)",
                user,
                re.DOTALL,
            )
            if m:
                try:
                    out[key] = json.loads(m.group(1))
                except json.JSONDecodeError:
                    pass

        m = re.search(r"nurse_triggered:\s*(true|false|True|False)", user)
        if m:
            out["nurse"] = m.group(1).lower() == "true"
        m = re.search(r"red_flag_triggered:\s*(true|false|True|False)", user)
        if m:
            out["redflag"] = m.group(1).lower() == "true"
        return out

    def _mock_response(self, user: str) -> str:
        parsed = self._parse_user(user)
        profile = parsed["profile"] or {}
        context = parsed["context"] or {}
        concern_paths = parsed["concern_paths"] or []
        nurse_on = parsed["nurse"]
        red_on = parsed["redflag"]

        # --- acknowledgment ---
        nurse_applied: list[str] = []
        habits_applied: list[str] = ["Invest in the beginning"]
        if nurse_on and (profile.get("emotional_cues") or []):
            cue = profile["emotional_cues"][0]
            evidence = cue.get("evidence_quote", "")
            ack = (
                f"I can hear how much this has been weighing on you — "
                f"you said, \"{evidence}\". That's a real thing to be "
                f"carrying, and I want to take it seriously while we "
                f"figure out what's going on."
            )
            nurse_applied.extend(["Name", "Understand", "Respect"])
            habits_applied.append("Demonstrate empathy")
        else:
            ack = (
                "Thanks for talking through what's been going on. "
                "Let's go through what we know and what to do next."
            )

        # Always add Elicit the patient's perspective if goals are present.
        if profile.get("patient_goals"):
            habits_applied.append("Elicit the patient's perspective")

        # --- per-concern explanations ---
        clusters = context.get("clusters", []) or []
        # Index clusters by addresses_concern (also keep a "global" bucket).
        by_addr: dict[str, list[dict]] = {}
        for c in clusters:
            key = c.get("addresses_concern") or "_global"
            by_addr.setdefault(key, []).append(c)

        sections = []
        all_cluster_ids: list[str] = []
        all_pmids: list[str] = []
        for path in concern_paths:
            label = self._label_for_path(profile, path)
            matching = by_addr.get(path, [])
            if not matching:
                # fall back to any cluster (global) so we cite something
                matching = by_addr.get("_global", [])[:1]
            cites = []
            for c in matching[:2]:
                cid = c.get("cluster_id", "")
                prim = (c.get("primary_assertion") or {}).get("assertion_id", "")
                pmids = c.get("supporting_pmids") or []
                cites.append({"cluster_id": cid, "primary_assertion_id": prim, "pmids": pmids})
                if cid and cid not in all_cluster_ids:
                    all_cluster_ids.append(cid)
                for p in pmids:
                    if p not in all_pmids:
                        all_pmids.append(p)
            if matching:
                primary_text = (matching[0].get("primary_assertion") or {}).get(
                    "assertion_text", ""
                )
                explanation = (
                    f"For your {label}: based on current guidance, "
                    f"{primary_text}"
                )
            else:
                explanation = (
                    f"For your {label}: we don't have a specific guideline "
                    "that matches this exact picture, so we'll talk it "
                    "through together."
                )
            sections.append(
                {
                    "concern_label": label,
                    "profile_path": path,
                    "explanation": explanation,
                    "citations": cites,
                }
            )

        # --- next steps ---
        next_steps: list[str] = []
        if red_on and (profile.get("red_flags") or []):
            rf = profile["red_flags"][0]
            next_steps.append(
                f"Because of the {rf.get('flag', 'concerning finding')}, "
                "we'll start the workup today rather than wait — that "
                "includes bloodwork and a few tests to rule out the "
                "things you're most worried about."
            )
            habits_applied.append("Demonstrate empathy")
        next_steps.append(
            "We'll go through what each step is for, so you can decide "
            "what feels right."
        )
        next_steps.append(
            "I'll have someone follow up with you in the next few days "
            "to check in and answer any questions that come up."
        )
        nurse_applied.append("Support")

        # --- closing ---
        teach_back = (
            "I want to make sure I explained this clearly — can you "
            "tell me, in your own words, what we're going to do next "
            "and why?"
        )
        habits_applied.append("Invest in the end")
        follow_up = (
            "Let's plan to see each other again in 2–4 weeks. In the "
            "meantime, if anything gets worse — especially any of the "
            "warning signs we talked about — please call us right away."
        )

        out = {
            "acknowledgment": ack,
            "clinical_information_per_concern": sections,
            "next_steps": next_steps,
            "teach_back_prompt": teach_back,
            "follow_up_invitation": follow_up,
            "nurse_elements_applied": _dedup(nurse_applied),
            "four_habits_elements_applied": _dedup(habits_applied),
            "all_cluster_ids_used": all_cluster_ids,
            "all_pmids_used": all_pmids,
        }
        return json.dumps(out)

    @staticmethod
    def _label_for_path(profile: dict, path: str) -> str:
        m = re.match(r"problems\[(\d+)\]", path)
        if m:
            i = int(m.group(1))
            problems = profile.get("problems") or []
            if 0 <= i < len(problems):
                return problems[i].get("label") or path
        m = re.match(r"patient_goals\[(\d+)\]", path)
        if m:
            i = int(m.group(1))
            goals = profile.get("patient_goals") or []
            if 0 <= i < len(goals):
                return f"goal: \"{goals[i]}\""
        return path


def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# --------------------------------------------------------------------------
# Mock for the naive baseline (Phase 12 comparison)
# --------------------------------------------------------------------------


class MockBaselineLLM:
    """Stand-in for the unsteered baseline. Returns a single short
    paragraph that vaguely acknowledges the patient and proposes a
    generic workup — deliberately *without* citations, NURSE labels,
    structured fields, or red-flag prioritization. Mirrors the kind of
    output an LLM with a minimal system prompt would produce.
    """

    def __init__(self) -> None:
        self.call_count = 0

    def complete(
        self,
        system: str,  # noqa: ARG002
        user: str,
        *,
        max_tokens: int | None = None,  # noqa: ARG002
        temperature: float | None = None,  # noqa: ARG002
        response_format_json: bool = False,  # noqa: ARG002
    ) -> str:
        self.call_count += 1
        # Pull a fragment of the first patient turn so the mock isn't
        # literally identical across patients.
        m = re.search(r"Patient:\s*(.+?)(?:\n|$)", user)
        first = (m.group(1) if m else "").strip()
        snippet = (first[:80] + "...") if len(first) > 80 else first
        return (
            "Thank you for sharing what's been going on — I can tell this "
            "has been a lot to carry. From what you described "
            f"(\"{snippet}\"), the right next step is to start with some "
            "basic workup so we can figure out what's contributing. I'd "
            "suggest we do some bloodwork and a focused exam, and then "
            "follow up in a couple of weeks to go over the results "
            "together. In the meantime, please reach out if anything "
            "gets worse or if new symptoms come up, and we'll handle "
            "it from there."
        )

    async def complete_async(self, system, user, **kw):  # noqa: D401
        return self.complete(system, user, **kw)
