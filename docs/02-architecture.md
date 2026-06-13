# 02. Architecture

## Entity spine

dm+d's five-level model is the identity layer; everything else hangs off it.

- **VTM** (virtual therapeutic moiety): the ingredient concept, e.g. apixaban. Ingredient-level reasoning (interactions, class effects, pregnancy) attaches here.
- **VMP** (virtual medicinal product): ingredient plus strength plus form, e.g. apixaban 5mg tablets. Dose and route reasoning attaches here.
- **AMP** (actual medicinal product): a specific marketed product. Excipients, supply status, and the SPC itself attach here, because excipients and licence text are per-product facts. The lactose question and the gelatine question are AMP questions, and this is why most tools answer them badly: they reason only at ingredient level.
- VMPP/AMPP (pack levels) carry pricing.

Cross-vocabulary maps (ATC for class queries, SNOMED for EHR alignment, RxNorm via UMLS for any US source) are v1; v0 needs only name-to-VTM/AMP resolution with a trigram index over dm+d name fields.

## The constraint algebra

Every adapter, regardless of source, emits values of one type:

```python
@dataclass(frozen=True)
class Provenance:
    source: str          # registry key from docs/01-sources.md
    document_id: str     # e.g. emc product document id, DSU issue
    version: str         # document revision or release tag
    retrieved_at: date
    locator: str         # section path + char offsets, or URL fragment
    url: str

class Authority(Enum):
    REGULATOR = 1        # SPC, MHRA: highest trust, render first
    FORMULARY = 2        # BNF (once licensed)
    SPECIALIST = 3       # SPS, UKTIS, CredibleMeds, Maudsley
    RESEARCH = 4         # open DDI sets: always labelled as such

@dataclass(frozen=True)
class Constraint:
    drug: DmdRef                 # VTM, VMP or AMP level, explicitly tagged
    axis: Axis                   # the enum of dossier rows (docs/00-scope.md)
    facet_guard: FacetPredicate  # when this constraint is live, e.g. eGFR < 30,
                                 # age >= 75, pregnant, co_med(VTM)
    kind: Kind                   # CONTRAINDICATION | DOSE_ADJUST | INTERACTION |
                                 # MONITORING | ALTERNATIVE | SIGNAL | ...
    payload: Span | Rule | LinkOut
    authority: Authority
    provenance: Provenance

@dataclass(frozen=True)
class AxisResult:             # per (drug, axis) cell, distinguishes the empty cases
    constraints: list[Constraint]
    checked_sources: list[str]   # so "no constraint found" != "not yet checked"
    pending_sources: list[str]   # ambassador agents still running
```

Two empty states must stay distinct everywhere: an axis with no firing constraint after all its sources were checked (genuinely clear, per those sources) versus an axis whose sources have not reported yet. Collapsing them would let the dossier imply safety it has not verified, which is the worst failure this tool can have.

A **case** is a facet valuation: `{age: 78, egfr: 24, pregnant: false, co_meds: [apixaban, sertraline], route: oral}`, projected from freeform history by the local parser (see below). Evaluating a candidate drug against a case is: resolve the drug across the spine, collect all constraints whose `facet_guard` is satisfied by the valuation (plus all unconditional ones), group by axis, render with provenance and authority tier. No scoring, no aggregation across sources, no reconciliation when sources disagree: disagreement is displayed, because surfacing that the SPC and the renal reference band eGFR differently is itself clinically useful information.

The categorical gloss, for the README and for honesty about what this is: the sources form a diagram of partial constraint-presheaves over (DrugId x Facet-space); a case picks out a point of Facet-space; the dossier is the limit of the diagram restricted to (drug, case), and the provenance links are precisely the projection maps of the cone. The app computes pullbacks. Hence the name. This is not decoration: it dictates that adapters must agree on the index category (the spine plus the facet vocabulary) and on nothing else, which is the whole integration strategy. The two tiers are two ways of computing the same cone: the resident tier evaluates the presheaves it holds locally; the ambassador tier evaluates the ones held remotely, sending only the case point outward and receiving constraint values back. Alternatives are morphisms in DrugId (ATC sibling, VTM-form variation, or a guideline-attested edge) along which the diagram is re-evaluated; the system only ever traverses an edge that some source asserts exists, which is exactly why it can show alternatives without recommending them.

## Adapters (v0 set)

- `dmd`: loads TRUD XML into DuckDB; emits the spine plus price and excipient constraints (axis: excipients, cost).
- `spc`: heading-anchored extraction over emc/MHRA SPC documents. SPCs have a regulator-mandated section skeleton (4.1 indications, 4.2 posology, 4.3 contraindications, 4.4 warnings, 4.5 interactions, 4.6 pregnancy/lactation, 6.1 excipients), which is what makes deterministic extraction plausible: anchor on the numbered headings, capture spans, attach light facet guards via pattern rules (eGFR/CrCl mentions in 4.2 guard on renal facets; named co-medications and class names in 4.5 guard on `co_med`).
- `dsu`: MHRA Drug Safety Update index keyed by ingredient; emits safety-signal constraints.
- `links`: pure LinkOut constructor per registry row (UKTIS, SPS, CredibleMeds, NEWT, NAPOS, Liverpool, Renal Drug Database), templated by VTM or AMP as each target's URL scheme allows.

v1 adapters: `stoppstart` and `acb` (published rule sets, the cleanest computable constraints in the whole landscape), `openprescribing` (context), `ddi-open` (DDInter/TWOSIDES, clearly labelled as research-grade).

## Interactions: the honest plan

Pairwise interaction checking against the case's medicine list is the axis users will judge us on, and the gold content (Stockley's, FDB) is gated. v0 strategy: extract SPC 4.5 for the candidate drug, then pattern-match the case's co-medications (by VTM name, synonyms from dm+d, and class terms via ATC once mapped) against that section, rendering the matched spans. This finds what the manufacturer's own label says about the specific pair, which is authoritative, per-licence, and frequently what the clinician actually needs to cite. It will miss class-level interactions phrased obliquely; that gap is recorded, displayed ("checked against SPC 4.5 only"), and is the strongest argument for the BNF licence application.

## Input: freeform history to facet projection

The doctor pastes or dictates patient history in whatever shape it arrives (a clinic letter, a problem list, a medication list with renal bloods, scribbled context). A **local** parser, a small model running on the doctor's machine, extracts the structured facet valuation and grounds every medicine mention to a dm+d VTM/AMP and every condition to a coded term. This is where invariant 4 is enforced: the narrative is processed in place, and the only thing that crosses the wire to any remote model or research agent is the minimised coded projection. Two artefacts result: the `Case` (coded, the thing that gets reasoned over and sent outward) and the `narrative_blob` (encrypted at rest, keyed by a doctor-side alias, never transmitted, deletable). Parser output is shown back to the doctor for confirmation before anything dispatches, because a misread eGFR poisons every downstream cell; correction is a click and re-grounds.

Freeform-to-structured is itself a small interpretation step that could drift toward "the model decided this patient is frail". It does not get to: the parser only fills enumerated slots and grounds codes, and anything it cannot ground is flagged "unparsed, please confirm" rather than guessed. The judgement stays downstream of retrieval, in the human.

## Two retrieval tiers, one constraint type

The mission's two use cases are two tiers over the same `Constraint` schema.

**Resident tier: the local reference bank.** A digitised corpus that can legitimately live on disk (SPCs for the in-scope drugs, MHRA Drug Safety Updates, encoded rule sets like STOPP/START v3 and the anticholinergic scales, and any source whose licence permits local storage). The recursive language-model pattern works in two phases:

- *Ingest-time tree.* Each document is decomposed along its native structure (SPCs along their mandated section skeleton; rule sets along criteria) and a hierarchical summary tree is built bottom-up: leaf nodes are spans, internal nodes are summaries-of-summaries, each node retaining pointers to the exact spans beneath it. This is the RAPTOR pattern (recursive abstractive summarisation over a tree), chosen because clinical documents are deeply hierarchical and flat chunking destroys the section semantics that section 4.x anchoring depends on.
- *Query-time recursive descent.* A query (case projection plus axis) enters at a relevant subtree root and descends only the branches whose summaries are relevant, pulling leaf spans at the bottom. The model that does the descent is choosing which branch to read, never authoring claims: every returned unit is a verbatim span with its provenance, and the descent transcript is itself logged so the retrieval path is auditable. This is the recursive pattern doing routing, not generation.

**Ambassador tier: dispatched research agents.** For the decentralised live sources that cannot or should not be held locally (UKTIS monographs behind HCP registration, SPS pages, CredibleMeds categories, Liverpool checkers, supply tools, the long tail), the system dispatches per-source research agents. Each agent receives only the facet projection plus the resolved drug, is scoped to exactly one source with a hard allowlist (it cannot wander the open web), executes that source's retrieval (deep link, form query, or permitted fetch), and returns `Constraint` records, never free prose. An agent that finds nothing returns an explicit "checked, nothing on this axis" so the dossier can distinguish "no constraint" from "not yet checked". Agents run in parallel; a dossier renders progressively as they report, with per-source pending/done state visible.

The authority tier of every constraint is stamped on it: regulator-authoritative (SPC), formulary (BNF once licensed), specialist-reference (SPS, UKTIS), research-grade (open DDI sets), so the render can visually rank trust without the system ever adjudicating between sources.

## Surfacing problems and alternatives without recommending

The doctor's actual need, in their words, is to see *what is not okay and why*, and *what nearby options came up*. Two display constructs serve this without a verdict:

- **Flagged finding.** Where a constraint's `facet_guard` fires against the case, the cell is marked and renders the source's own words for the problem ("severe renal impairment: contraindicated", SPC 4.3, with link) directly beside the mechanical case fact that tripped the guard ("case eGFR 24 mL/min, parsed from history dated ..."). Two independently-cited statements in juxtaposition. The system asserts neither the conjunction nor its consequence; the adjacency is the information, and the clinician draws the inference. No "therefore avoid".
- **Attested alternative.** Alternatives appear only with a provenance for the *adjacency itself*. Permitted sources of adjacency: a guideline or SPC that names the alternative in context ("in renal impairment, X is preferred", rendered as that source's claim with its link); an SPS Q&A that discusses the swap; or a displayed mechanical relation (same ATC class sibling, or same dm+d VTM in a different form) explicitly labelled as a mechanical relation, not a recommendation. The agent may *retrieve* candidate alternatives; it may never *originate* one, and alternatives are never ranked. An alternative with no citable adjacency does not render.

This keeps the regulatory wall intact (docs/03-regulatory.md): the model routes and retrieves, the sources speak, the arithmetic is shown, the doctor decides.

## Persistence and refresh: the secretary's memory

A `Case` is durable, not a throwaway query. A `Dossier` is a materialised view: `(case_version, query, corpus_snapshot_id) -> rendered constraints`, and it records the set of (source, drug, axis) triples it cited. The refresh machinery:

- Resident sources sync on their declared cadence (DSU monthly, SPC re-fetch periodically); each sync that changes a cited document hashes the change and marks dependent dossiers **dirty**.
- A dirty dossier re-derives and renders a **diff** against its last-reviewed state: "clarithromycin SPC 4.5 updated since you last reviewed this patient; the apixaban interaction wording changed". This is the feature that makes it a secretary rather than a search box: it notices, for this specific patient, that something a clinician would want to revisit has moved.
- The doctor can mark a dossier "reviewed", snapshotting the acknowledged state so future diffs are against that baseline.
- Ambassador-tier facts carry a TTL; past it the cell shows "last checked N days ago, re-run" rather than presenting stale agent output as current.

## Synthesis layer

The clinical surface composes no novel claims. Optional, off by default, behind a clear boundary: a typesetter pass that arranges already-retrieved spans into per-axis prose where every output sentence must string-align to a cited span, mechanically rejected otherwise (temperature effectively zero, the model orders sentences, it does not assert). The default and the trustworthy mode is the bare matrix of cited spans, which is already the deliverable.

## Storage and freshness

DuckDB for spine and constraints; `data/raw/` holds every fetched document with SHA-256 hash, fetch timestamp, and the URL used, so any dossier can be re-derived byte-for-byte. Each source row in the registry declares a cadence; a `freshness` table records last sync, and the dossier footer prints the oldest retrieval date among its citations, prominently. Staleness displayed beats staleness hidden.

## UI sketch

One screen. Case sketch pinned top. Candidate drug(s) as columns (the flagship case wants clarithromycin and azithromycin side by side; comparison is where the matrix layout pays for itself). Axes as rows. Cells contain the retrieved span or link-out, source badge, date. Click-through opens the source at the locator. Nothing is more than one click from its origin.
