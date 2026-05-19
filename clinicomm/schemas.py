"""Pydantic v2 schemas for every artifact passed between modules.

Single source of truth. If you add a field, also extend the parser that
writes it and the consumer that reads it.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


# ----- Phase 3: parsed PubMed records ---------------------------------


class AbstractSection(BaseModel):
    """One labeled section of a structured abstract.

    For unstructured abstracts there is exactly one section with
    `section_label = None`.
    """
    model_config = ConfigDict(extra="forbid")

    section_label: str | None = None
    text: str


class MeshHeading(BaseModel):
    model_config = ConfigDict(extra="forbid")

    descriptor: str
    qualifiers: list[str] = Field(default_factory=list)
    # True if the DescriptorName OR any QualifierName carries MajorTopicYN="Y".
    major_topic: bool = False


class Author(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    affiliation: str | None = None
    # True if this entry was a <CollectiveName> (an organization, not a person).
    is_collective: bool = False


class ParsedDocument(BaseModel):
    """Normalized PubMed record. One per PMID. Phase 3 output."""
    model_config = ConfigDict(extra="forbid")

    pmid: str
    doi: str | None = None
    title: str
    abstract: list[AbstractSection] = Field(default_factory=list)
    journal: str | None = None
    # ISO-ish: "YYYY", "YYYY-MM", or "YYYY-MM-DD". Falls back to raw
    # MedlineDate string when only that is present.
    pub_date: str | None = None
    pub_types: list[str] = Field(default_factory=list)
    mesh_headings: list[MeshHeading] = Field(default_factory=list)
    authors: list[Author] = Field(default_factory=list)
    # First CollectiveName encountered, when present. For guideline papers
    # this is typically the issuing society (e.g., "American Heart Association").
    issuing_body: str | None = None


# ----- Phase 7: patient concern profile (Module I) --------------------
#
# This shape MUST match the JSON skeleton declared in
# config/prompts/intake_system.txt. If you change one, change the other.


class Problem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    onset: str | None = None
    severity: str | None = None
    timing: str | None = None
    associated_symptoms: list[str] = Field(default_factory=list)
    interventions_tried: list[str] = Field(default_factory=list)
    # Controlled vocabulary; "unknown" until the patient signals a trajectory.
    status: str = "unknown"


class EmotionalCue(BaseModel):
    """Captured for downstream NURSE 'Name'. evidence_quote MUST be a
    verbatim substring of the patient's utterance — never paraphrased.
    """
    model_config = ConfigDict(extra="forbid")

    cue: str
    evidence_quote: str


class RedFlag(BaseModel):
    """A safety-screen positive. Drives Four Habits 'Demonstrate empathy'
    + an urgent next step in Module IV. evidence is a verbatim quote.
    """
    model_config = ConfigDict(extra="forbid")

    flag: str
    evidence: str


class PatientConcernProfile(BaseModel):
    """Module I output. Sole input to Module II retrieval.

    `unknowns` carries JSON paths still needing follow-up (e.g.
    "problems[0].onset", "patient_goals", "red_flag_screen_complete").
    next_prompt() consumes this list to pick the next question.

    `completion_status` flips to "ready_for_handoff" only when every
    problem has onset+severity+timing populated AND the red-flag screen
    has been performed at least once AND patient_goals has >=1 entry.
    """
    model_config = ConfigDict(extra="forbid")

    problems: list[Problem] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    relevant_history: list[str] = Field(default_factory=list)
    patient_goals: list[str] = Field(default_factory=list)
    emotional_cues: list[EmotionalCue] = Field(default_factory=list)
    red_flags: list[RedFlag] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    turn_count: int = 0
    completion_status: str = "in_progress"


# ----- Phase 4: chunks ------------------------------------------------


class Chunk(BaseModel):
    """One indexable unit. Phase 4 output; Phase 5 embedding input."""
    model_config = ConfigDict(extra="forbid")

    chunk_id: str          # f"{pmid}_{position:03d}"
    pmid: str
    # None when the source abstract was unstructured (sliding-window chunks).
    section_label: str | None
    position: int          # 0-indexed within the document
    text: str
    token_count: int       # measured with the embedding model's tokenizer


# ----- Phase 8: retrieval (Module II) ---------------------------------


class SubQuery(BaseModel):
    """One query into the vector index, traceable back to the profile.

    `source` ∈ {"problem", "goal", "global_context"} — drives Module II's
    coverage logic (a document covers a sub-query if it appears in that
    sub-query's top-k seeds).
    """
    model_config = ConfigDict(extra="forbid")

    source: str
    source_index: int      # index within profile.problems / profile.patient_goals
    addresses: str | None  # JSON path back to the profile element, e.g. "problems[0]"
    text: str              # natural-language query passed to BGE


class RetrievedChunk(BaseModel):
    """One chunk hit from Chroma, with which sub-queries pulled it in."""
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    pmid: str
    section_label: str | None
    text: str
    semantic_similarity: float
    matched_sub_query_indices: list[int] = Field(default_factory=list)


class RankedDocument(BaseModel):
    """One document in the final ranked set. Module II → Module III."""
    model_config = ConfigDict(extra="forbid")

    pmid: str
    title: str
    journal: str | None = None
    pub_year: int | None = None
    pub_date: str | None = None
    pub_types: list[str] = Field(default_factory=list)
    issuing_body: str | None = None

    # Retrieval provenance.
    chunks: list[RetrievedChunk] = Field(default_factory=list)
    full_text: str = ""        # concatenated chunk text (Module III input)
    addresses_concerns: list[str] = Field(default_factory=list)  # profile paths covered

    # Rerank score breakdown (final score = weighted sum).
    semantic_similarity: float = 0.0
    recency_score: float = 0.0
    authority_score: float = 0.0
    coverage_bonus: float = 0.0
    total_score: float = 0.0


class RankedDocumentSet(BaseModel):
    """Module II output. The sole input to Module III reasoning."""
    model_config = ConfigDict(extra="forbid")

    sub_queries: list[SubQuery]
    documents: list[RankedDocument]
    rerank_weights: dict[str, float]
    top_k_chunks_per_query: int
    final_n_documents: int
    # "stub" until Phase 9+ adds an actual document graph.
    expansion_used: str = "stub"


# ----- Phase 9: graph-RAG reasoning (Module III) ----------------------


class ClinicalAssertion(BaseModel):
    """One claim extracted from one document. The unit Module III
    clusters and Module IV cites. assertion_id is f"{pmid}_{position}".
    """
    model_config = ConfigDict(extra="forbid")

    assertion_id: str
    assertion_text: str
    # Controlled vocabulary — assertion_extraction.txt enumerates these.
    assertion_type: str
    confidence: float          # in [0, 1]
    source_pmid: str
    source_chunk_id: str | None = None
    addresses_concern: str | None = None
    evidence_quote: str = ""   # verbatim substring of source abstract


class AssertionCluster(BaseModel):
    """A set of assertions that share (type, addresses_concern) and were
    grouped by assertion_text embedding similarity >= cluster_threshold.

    Convergent => all assertions agree, no LLM call needed; the
    highest-confidence assertion is the primary by default.
    Divergent  => conflict_resolution LLM call selected the primary,
                  and resolution_rule + resolution_rationale are set.
    """
    model_config = ConfigDict(extra="forbid")

    cluster_id: str
    assertion_type: str
    addresses_concern: str | None
    primary_assertion: ClinicalAssertion
    supporting_pmids: list[str]
    alternative_assertions: list[ClinicalAssertion] = Field(default_factory=list)
    convergent: bool
    confidence: float
    resolution_rule: str | None = None
    resolution_rationale: str | None = None


class StructuredContextArtifact(BaseModel):
    """Module III output. The sole input to Module IV response generation.

    `clusters` is ordered: convergent first within each
    addresses_concern group, then divergent. `notes` records
    manuscript-relevant limitations (abstracts-only granularity, etc).
    """
    model_config = ConfigDict(extra="forbid")

    clusters: list[AssertionCluster]
    n_documents_processed: int
    n_assertions_extracted: int
    n_clusters: int
    n_convergent_clusters: int
    n_divergent_clusters: int
    cluster_similarity_threshold: float
    notes: list[str] = Field(default_factory=list)


# ----- Phase 10: patient response (Module IV) -------------------------


class ResponseCitation(BaseModel):
    """One claim → supporting cluster + its PMIDs."""
    model_config = ConfigDict(extra="forbid")

    cluster_id: str
    primary_assertion_id: str
    pmids: list[str] = Field(default_factory=list)


class ConcernExplanation(BaseModel):
    """The clinical explanation for one element of the patient's profile
    (a problem or a goal). Plain-language only.
    """
    model_config = ConfigDict(extra="forbid")

    concern_label: str
    profile_path: str
    explanation: str
    citations: list[ResponseCitation] = Field(default_factory=list)


class GlossarySubstitution(BaseModel):
    """One post-generation jargon → plain-English substitution log entry."""
    model_config = ConfigDict(extra="forbid")

    field: str         # which PatientResponse field was modified
    original: str
    plain: str
    count: int = 1     # how many occurrences in that field


class PatientResponse(BaseModel):
    """Module IV output. The final patient-facing artifact (structured).

    Section order (matches what the patient hears):
      acknowledgment  →  clinical_information_per_concern[]
      →  next_steps[]  →  teach_back_prompt  →  follow_up_invitation
    """
    model_config = ConfigDict(extra="forbid")

    acknowledgment: str
    clinical_information_per_concern: list[ConcernExplanation]
    next_steps: list[str]
    teach_back_prompt: str
    follow_up_invitation: str

    # Annotation — which framework elements were applied. Phase 12's
    # trace appendix reads these per turn.
    nurse_elements_applied: list[str] = Field(default_factory=list)
    four_habits_elements_applied: list[str] = Field(default_factory=list)

    # Aggregate provenance (across all citations).
    all_cluster_ids_used: list[str] = Field(default_factory=list)
    all_pmids_used: list[str] = Field(default_factory=list)

    # Populated by the post-generation glossary pass, not the LLM.
    glossary_substitutions: list[GlossarySubstitution] = Field(default_factory=list)
