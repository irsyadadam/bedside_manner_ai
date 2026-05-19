# fig2_intake_state_machine — caption + design notes

## Caption draft

> **Figure 2. Module I state machine.** Each patient turn drives a
> single transition cycle: `AWAITING_TURN → UPDATING_PROFILE (one LLM
> call) → CHECKING_COMPLETION → {EMITTING_PROFILE | SELECTING_NEXT_PROMPT
> → AWAITING_TURN}`. Completion requires three gates: every problem
> populated with onset, severity, and timing; the red-flag safety
> screen performed at least once; and at least one patient goal
> captured. While intake is active, the system emits **only templated
> questions** — never LLM-generated prose — preserving the proposal's
> "withhold-responses-during-intake" property. A per-template ask
> counter (default cap 2) prevents looping on a gap the patient
> declines to fill.

## Design decisions Claude made (review me)

- The two terminal states (EMITTING vs SELECTING) are deliberately
  placed at the same vertical level so the figure reads as a fork,
  not a chain. The SELECTING branch loops back to AWAITING_TURN.
- The completion gates A/B/C are listed inline in the state box rather
  than rendered as separate decision diamonds. They're a *conjunction*,
  not a sequence of decisions, so showing them in one box is more honest.
- The circuit-breaker (asked_count ≥ max_attempts) is documented inside
  SELECTING_NEXT_PROMPT because that's where it actually fires. In code
  it lives on the IntakeAgent instance.
- "NO LLM" / "ONE LLM call" annotations exist in every state because
  this distinction is the manuscript's whole point — the LLM is used
  for *extraction*, not for *speaking to the patient*.

## Suggestions when polishing in Figma / TikZ

- Make the AWAITING_TURN ↔ SELECTING_NEXT_PROMPT cycle visually
  prominent (thicker arrow, color the loop) — it's the typical path
  for ~80% of turns.
- The "withhold clinical responses" property could become a colored
  band around the diagram (e.g., "intake mode") with a bracket showing
  where it lifts (only at EMITTING_PROFILE).
- Consider showing the three completion gates as small icons next to
  the CHECKING_COMPLETION box (problem-list / shield / target) for
  visual recall in the Results section.
