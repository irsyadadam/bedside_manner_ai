# fig3_schema_illustration — caption + design notes

## Caption draft

> **Figure 3. `PatientConcernProfile` populated for synthetic patient
> p001.** The 52-year-old contractor's profile after a five-turn
> intake. Three problems (`fatigue`, `unintentional weight loss`,
> `morning headache`), each with onset, severity, timing, and
> trajectory. Two emotional cues with verbatim patient quotes
> ("My wife is convinced it's cancer and honestly I am too";
> "I just want to know what's going on") provide the substrate for
> Module IV's NURSE acknowledgment. One red flag (unexplained weight
> loss) triggers the empathy-before-urgency rule. Three goals capture
> the patient's stated values. `completion_status = "ready_for_handoff"`
> indicates all three completion gates (descriptors, red-flag screen,
> ≥ 1 goal) are satisfied.

## Design decisions Claude made (review me)

- Used patient p001 because it's the canonical demo throughout the
  paper and its emotional_cues / red_flags are concrete enough to
  carry the figure on their own.
- Inline arrow callouts (▲▲▲) emphasize the verbatim-quote requirement.
  This is the single most-load-bearing design constraint in the schema
  and is easy for a reader to skim past in plain text.
- Listed completion_status last — it's the trigger Module II reads.
  Putting it near the bottom keeps it visually adjacent to its
  semantics ("emit downstream").

## Suggestions when polishing in Figma / TikZ

- Render `problems` as cards / tiles instead of indented bullets; the
  manuscript reader can then see "three concerns" at a glance.
- Bold-face the VERBATIM evidence_quote substrings against the rest of
  the text — these are the only fields where typesetting can encode a
  semantic constraint (no paraphrase).
- A small marker (red exclamation) next to red_flags[0] makes the
  safety-precedence story easier to point at in a slide.
