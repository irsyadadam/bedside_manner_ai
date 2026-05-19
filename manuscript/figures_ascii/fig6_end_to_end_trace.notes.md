# fig6_end_to_end_trace — caption + design notes

## Caption draft

> **Figure 6. End-to-end trace, patient p001.** Selected patient
> utterances (left) and the response sections they bind to (right).
> Each utterance contributes to multiple parts of the
> `PatientConcernProfile`; each response section is then constructed
> from the corresponding profile elements and cited assertion clusters.
> Annotations show which NURSE and Four-Habits elements shape each
> response segment. The verbatim emotional quote from turn 1
> appears in the acknowledgment unchanged ("My wife is convinced it's
> cancer and honestly I am too"), and the red-flag-first ordering rule
> places the weight-loss workup as the *first* next-steps entry — but
> *after* the empathic acknowledgment, never before.

## Design decisions Claude made (review me)

- Chose four utterances from p001 rather than all five — turn 2 (onset
  details) doesn't contribute interesting new framework bindings, so
  it's omitted to keep the figure scannable.
- The "binds:" lists under each utterance are explicit fields names
  (e.g., `red_flags[0]`, `emotional_cues[0]`) — these match the
  schema in fig3, so a reader can cross-reference.
- Annotated each response section with the NURSE / Four Habits
  elements that triggered it. This is the manuscript's central
  empirical claim — that framework application is *traceable*, not
  vibes.

## Suggestions when polishing in Figma / TikZ

- Colored connector lines between left and right columns (one color
  per NURSE element, one per Four Habits element) would let the
  reader follow which element shaped which sentence at a glance.
- The verbatim emotional quote should appear in italics + quotes in
  BOTH columns to make the round-trip obvious.
- A horizontal line of NURSE icons across the top, lit up only for
  the elements actually applied (Name, Understand, Respect, Support
  — but not Explore, since unknowns=[] in this profile), tells the
  application story at a glance.
