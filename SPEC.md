# pullback: specification and execution plan

A per-case medication suitability workbench for one UK clinician. A research secretary, not a registrar: it researches, joins, cites, and notices changes across the distributed UK medicines sources. It never decides.

This single document is the complete handoff. It is intended to become the repo's `CLAUDE.md` (or sit beside one). A competent engineer or a Claude Code session should be able to implement the whole of v0 from here without further input, except for the items in section 11, which require a human decision and must not be decided unilaterally.

Name rationale: a per-case suitability query is a cone over a diagram of distributed authorities; the dossier we want is the limit, and the provenance links are the projection maps. The app computes pullbacks. Rename freely.

---

## 0. How Claude Code should work in this repo

1. **Read section 2 (invariants) before writing any code.** They are load-bearing and several encode the regulatory and data-protection position. Violating one silently is the worst thing you can do here.
2. **Smallest vertical slice over breadth.** The goal of the spike is one rendered, re-derivable flagship dossier that exercises provenance end to end, not wide source coverage. Resist adding axes or sources before the flagship case renders. The maintainer's known failure mode is breadth without finished artefacts; the execution plan exists to force closure.
3. **Stop and flag at the device boundary.** Section 3 draws the line between retrieval (allowed) and recommendation or patient-specific calculation (a regulated medical-device function). If a feature might cross it, stop and surface the question rather than implementing. Candidate boundary-crossers, in rough order of gravity: any aggregate suitability score, dose calculation, ranking of drugs or alternatives, generated prose that asserts rather than quotes, ingestion of real patient narrative anywhere it could transit off-device.
4. **Record decisions, do not silently diverge.** If the spec is wrong, say so and add an entry to `docs/decision-log.md` (date, decision, alternatives rejected, rationale) rather than quietly building something else.
5. **Conventions.** Python 3.12, `uv` for env. UK English in all prose and strings (licence the noun, license the verb). No em-dashes anywhere; use commas, colons, parentheses, semicolons. Every type that touches a claim carries `Provenance`. Tests with `pytest`; golden-file tests for all extraction.
6. **Re-verify before ingesting.** Section 8 is the licensing critical path and was last checked June 2026. Before writing an adapter for any source, re-read its row and confirm the access route still holds.

---

## 1. Mission and the two use cases

### The problem

A UK clinician assessing whether a drug is sensible for a specific patient must join information that is authoritative but distributed. The BNF is the core reference but deliberately terse; the moment a case has more than one complicating facet (renal impairment plus an interacting co-prescription plus age over 75), the lookup fans out across the Summary of Product Characteristics (SPC), the Specialist Pharmacy Service, UKTIS for pregnancy, the Renal Drug Database, Maudsley for psychotropics, CredibleMeds for QT, MHRA Drug Safety Updates, and a long tail of niche references. Each has its own indexing, update cadence, and licence. The join is done by hand, per case, in browser tabs. That join is the product.

This is built as a bespoke instrument for one named clinician's recurring cognitive friction, not as a market wedge. Productisation is deferred until the instrument demonstrably removes the friction (decision-log D5).

### The two use cases, as two retrieval tiers

- **Resident tier.** A local digitised reference bank (the sources whose licence permits local storage: SPCs for the in-scope drugs, MHRA Drug Safety Updates, encoded rule sets) traversed by a recursive language-model pattern that surfaces relevant cited spans.
- **Ambassador tier.** For decentralised live sources that cannot or should not be held locally, dispatch per-source research agents that return cited constraints, giving the clinician a sourced perspective per axis.

Both tiers emit the same typed `Constraint` objects (section 4). They are two ways of computing the same cone.

### What the output does, and does not, do

The clinician's actual need: see what a source flags as not okay and why, and what nearby alternatives came up. The dossier serves this through two display constructs (section 5.5) that never cross into recommendation: source-voiced findings juxtaposed with mechanical case facts, and alternatives shown only where a source attests the adjacency. The clinician utters the verdict.

---

## 2. Hard invariants

Do not relax any of these without a `docs/decision-log.md` entry.

1. **Provenance or it does not ship.** Every rendered claim carries (source, document version or retrieval date, span locator, URL). No orphan text.

2. **The verdict sentence is never generated.** The system surfaces negative findings in the source's voice ("the SPC lists severe renal impairment as a contraindication") beside mechanical facts about the case ("this case's eGFR is 24, within that band"), each independently cited. It may surface alternatives only where the adjacency is itself attested in a source, or is a displayed mechanical relation (ATC sibling, same-VTM form variant) explicitly labelled as mechanical. It never composes the conjunction into advice: no "avoid", "unsuitable for this patient", "use Y instead", and no ranking of alternatives. The clinician performs the inference. This is the regulatory load-bearing wall (section 3).

3. **LLM as router and typesetter, never oracle.** In the clinical surface, models may (a) parse freeform input into the structured schema, (b) choose which branch of the reference tree to read. They may not author claims. Any optional generated prose must be composed exclusively from already-retrieved spans, with citation enforced mechanically (every output sentence string-aligns to a cited span or is rejected). Generation temperature of the clinical surface is effectively zero.

4. **Raw case narrative never leaves the device.** Freeform patient history is parsed locally into the structured facet schema; only the minimised coded projection (numeric and enumerated facets, dm+d codes, coded conditions, never the alias, never narrative) may reach a remote model or research agent. This is enforced at the type level: agents accept `CaseProjection`, not `Case`, and `CaseProjection` has no narrative or alias field to leak (section 4). Narrative is encrypted at rest under a doctor-side alias, never keyed by patient identifiers, and is deletable on command.

5. **Licence-aware ingestion.** Sources are ingested only via routes listed as permitted in section 8. No scraping against terms. Where content is view-only, link out rather than ingest.

6. **Dossiers are derivations, not documents.** Every dossier records the exact corpus snapshot and case version it was derived from, subscribes to the (source, drug, axis) triples it cites, and re-derives with a visible diff when either changes. Staleness is displayed, never hidden.

7. **Two empty states stay distinct.** An axis with no firing constraint after all its sources were checked (clear, per those sources) is rendered differently from an axis whose sources have not reported. Collapsing them would let the dossier imply a safety it has not verified. Enforced in the `AxisResult` type.

---

## 3. The regulatory boundary (a design constraint, not legal advice)

Get proper regulatory advice before any deployment beyond personal research use by the single intended clinician. The boundary nonetheless shapes the architecture from day one.

### The device line

Software meeting the definition of a medical device under UK MDR 2002 requires UKCA marking. The MHRA standalone-software guidance draws the operative line between **reference retrieval** (finding, filtering, and displaying published information for a professional to interpret: generally not a device) and **patient-specific calculation or recommendation** (computing a score, dose, risk, or directive for an individual for a medical purpose: generally a device). The invariants keep the system on the retrieval side even though the use case points at the boundary.

The sharpest line to hold: presenting source X's statement "in severe renal impairment, drug B is preferred over drug A" as *X's cited claim with a link* is retrieval; the system generating "use B instead of A for this patient" is a recommendation and a device function, even when B genuinely is the better choice. The difference is who is speaking and whether a citation backs the adjacency, not whether the underlying clinical content is the same. This is why the architecture forbids agents from ever originating an alternative. Labelling does not override function: writing "research aid only" on a tool that in fact emits patient-specific recommendations does not change its status. The invariants must hold in the behaviour.

iatroX is a useful UK precedent: a clinician-facing AI product that publicly positions its retrieval features as a referenced librarian rather than a calculator, precisely to sit outside device classification, while acknowledging that an app which calculates or interprets patient data for a medical purpose is likely a device.

### Alternatives (the rule the code enforces)

An alternative drug appears in a dossier if and only if a retrieved source attests the adjacency (names the alternative in the relevant clinical context), rendered as that source's cited claim, or the relation is a displayed mechanical fact (ATC class sibling, same-VTM form variant) explicitly labelled as mechanical and not as advice. Alternatives are never ordered, scored, or preferred in the system's own voice. Agents may retrieve candidate alternatives; they may never originate them. A candidate with no citable adjacency is dropped, not shown unsourced.

### The AI layer

The MHRA Software and AI as a Medical Device change programme is a live, moving framework; the AI Airlock regulatory sandbox completed its pilot phase in early 2025 and feeds an AI-specific framework expected during 2026. Treat the optional generative surface (citation-enforced composition over retrieved spans) as both an epistemic and a regulatory architecture, and re-check the published framework before shipping any generative surface to anyone but the single intended user.

### Clinical safety (separate from device law)

If ever deployed within an NHS organisation, DCB0129 (manufacturer) and DCB0160 (deploying organisation) apply, including a named Clinical Safety Officer and hazard log. Out of scope for the tinkering phase, but the constraint and provenance design doubles as the hazard-log evidence trail, so build as if.

### Intellectual property

SPC and PIL text is the marketing-authorisation holder's copyright even when served from regulator or compendium sites; local research-use handling of a small set is one thing, redistribution another. BNF content is licensed; the only legitimate programmatic route is BNF syndication (section 8), whose terms permit AI use subject to approval of the specific use and prohibit model training. Open Government Licence covers gov.uk material such as Drug Safety Updates.

### Data protection (now primary, because real patient data is in scope)

Invariant 4 is the data-protection architecture: local-only narrative, minimised coded projection outward, encrypted at rest under a doctor-side alias. Health data about an identifiable individual is special-category under UK GDPR Article 9; even a coded projection can be identifying in combination, so treat all of it accordingly. A lawful basis for a clinician processing their own patients' data for direct care exists, but the basis, the controller relationship, and retention must be settled with a real DPIA before this touches a second patient or a second clinician. For the near-term use (one trusted doctor, own machine, own patients) the exposure is contained and this architecture is proportionate. Every step toward multi-user, cloud, or shared-corpus triggers a fresh DPIA and is a stop-and-flag item.

### Standing disclaimer for any rendered surface

"Research aid for healthcare professionals. Collates published sources with links and retrieval dates. Not a substitute for the source documents or for clinical judgement. Verify against the linked originals before acting."

---

## 4. Domain model

The whole system is typed adapters emitting one constraint type over a shared index (the dm+d spine plus a facet vocabulary). Adapters agree on the index and on nothing else; that is the entire integration strategy.

```python
from dataclasses import dataclass
from datetime import date
from enum import Enum

# ----- identity: the dm+d spine -----

class DmdLevel(Enum):
    VTM = "vtm"   # virtual therapeutic moiety: the ingredient concept (apixaban)
    VMP = "vmp"   # ingredient + strength + form (apixaban 5mg tablets)
    AMP = "amp"   # an actual marketed product: excipients and the SPC attach here

@dataclass(frozen=True)
class DmdRef:
    code: str            # dm+d/SNOMED concept id
    level: DmdLevel
    name: str            # display name

@dataclass(frozen=True)
class Coded:
    code: str            # SNOMED or other coded condition
    system: str
    display: str

# ----- the facet vocabulary: what a case is -----

class Sex(Enum):
    F = "f"; M = "m"; UNSPECIFIED = "unspecified"

class Impairment(Enum):
    NONE = "none"; MILD = "mild"; MODERATE = "moderate"; SEVERE = "severe"; UNKNOWN = "unknown"

class Route(Enum):
    ORAL = "oral"; IV = "iv"; ENTERAL_TUBE = "enteral_tube"; OTHER = "other"

@dataclass(frozen=True)
class Case:
    case_id: str
    alias: str                       # doctor-side label, NEVER a patient identifier
    version: int
    age_years: int | None = None
    sex: Sex = Sex.UNSPECIFIED
    weight_kg: float | None = None
    # Renal function is carried in BOTH conventions and NEVER auto-converted between them.
    # Labs report eGFR (CKD-EPI, body-surface-area normalised). Many SPCs, and the DOAC
    # dose-reduction criteria specifically, are framed on creatinine clearance
    # (Cockcroft-Gault, CrCl). The two diverge in the elderly and at extremes of weight,
    # which can misclassify renal dose bands. The dossier shows which convention each
    # source's threshold is stated in and never silently reconciles them.
    egfr: float | None = None        # mL/min/1.73m2
    crcl: float | None = None        # mL/min, Cockcroft-Gault
    hepatic: Impairment = Impairment.UNKNOWN
    pregnant: bool | None = None
    breastfeeding: bool | None = None
    co_meds: tuple[DmdRef, ...] = ()
    conditions: tuple[Coded, ...] = ()
    route: Route | None = None
    intolerances: tuple[str, ...] = ()   # for excipient matching: lactose, soya, gelatine, ethanol...
    flags: frozenset[str] = frozenset()  # long tail: g6pd_deficient, porphyria, maoi_recent...

@dataclass(frozen=True)
class CaseProjection:
    # The ONLY thing that may leave the device. A deliberate strict subset of Case:
    # coded and numeric only. No alias, no narrative, no free text. Agents accept this
    # type, not Case, so a narrative leak is structurally impossible (invariant 4).
    age_years: int | None
    sex: Sex
    weight_kg: float | None
    egfr: float | None
    crcl: float | None
    hepatic: Impairment
    pregnant: bool | None
    breastfeeding: bool | None
    co_med_codes: tuple[str, ...]
    condition_codes: tuple[str, ...]
    route: Route | None
    intolerances: tuple[str, ...]
    flags: frozenset[str]

def project(case: Case) -> CaseProjection: ...   # drops alias, narrative; the only egress path

# ----- guards: when a constraint is live for a case -----
# A guard is a small serialisable typed predicate, not an opaque lambda, so the cell can
# render WHY it fired ("eGFR 24 < threshold 30") and so it is auditable.

class Field(Enum):
    AGE = "age"; EGFR = "egfr"; CRCL = "crcl"; WEIGHT = "weight"; HEPATIC = "hepatic"

@dataclass(frozen=True)
class GuardExpr: ...                  # base; concrete: Lt, Le, Ge, Gt(Field, value),
                                     # CoMed(DmdRef), HasFlag(str), Pregnant(),
                                     # Breastfeeding(), HasIntolerance(str), Always(),
                                     # And(...), Or(...)

@dataclass(frozen=True)
class GuardOutcome:
    fired: bool
    explanation: str                 # human-readable, for the cell: "case eGFR 24 mL/min < 30"

@dataclass(frozen=True)
class Guard:
    expr: GuardExpr
    def evaluate(self, case: Case) -> GuardOutcome: ...

# ----- the dossier axes -----

class Axis(Enum):
    INDICATION = "indication"            # SPC 4.1
    CONTRAINDICATION = "contraindication"# SPC 4.3
    DOSE_RENAL = "dose_renal"            # SPC 4.2, Renal Drug Database (link)
    DOSE_HEPATIC = "dose_hepatic"        # SPC 4.2
    DOSE_GENERAL = "dose_general"        # SPC 4.2, BNF dose (once licensed)
    INTERACTION = "interaction"          # SPC 4.5, Stockley's/Liverpool (link)
    PREGNANCY = "pregnancy"              # SPC 4.6, UKTIS (link)
    LACTATION = "lactation"              # SPC 4.6, SPS (link)
    OLDER_ADULT = "older_adult"          # STOPP/START v3, ACB/AEC (v1)
    QT_RISK = "qt_risk"                  # CredibleMeds (link), SPC 4.4
    EXCIPIENT = "excipient"              # SPC 6.1 + 2, dm+d AMP excipient data
    ADMINISTRATION = "administration"    # SPC 4.2, NEWT (link)
    MONITORING = "monitoring"            # SPC 4.4
    SAFETY_SIGNAL = "safety_signal"      # MHRA Drug Safety Update, Yellow Card (link)
    SUPPLY = "supply"                    # SPS Medicine Supply Tool
    COST = "cost"                        # dm+d price data

# ----- provenance and the constraint itself -----

@dataclass(frozen=True)
class Provenance:
    source: str          # registry key from section 8
    document_id: str     # emc product doc id, DSU issue, rule-set citation...
    version: str         # document revision or release tag
    retrieved_at: date
    locator: str         # section path + char offsets, or URL fragment
    url: str

class Authority(Enum):   # render order / trust badge; the system NEVER adjudicates between sources
    REGULATOR = 1        # SPC, MHRA
    FORMULARY = 2        # BNF (once licensed)
    SPECIALIST = 3       # SPS, UKTIS, CredibleMeds, Maudsley, Renal Drug Database
    RESEARCH = 4         # open DDI sets: always labelled as research-grade

class Kind(Enum):
    CONTRAINDICATION = "contraindication"
    DOSE_ADJUST = "dose_adjust"
    INTERACTION = "interaction"
    MONITORING = "monitoring"
    ALTERNATIVE = "alternative"          # only ever source-attested (section 3)
    SIGNAL = "signal"
    EXCIPIENT_PRESENT = "excipient_present"
    SUPPLY_STATUS = "supply_status"
    INFO = "info"                        # indications, plain facts

@dataclass(frozen=True)
class Span:
    text: str                            # verbatim from source; never paraphrased in the clinical surface
    provenance: Provenance

@dataclass(frozen=True)
class Rule:
    label: str                           # e.g. "STOPP B1"
    statement: str
    provenance: Provenance

@dataclass(frozen=True)
class LinkOut:
    label: str
    url: str                             # pre-resolved to this drug where the target's scheme allows
    note: str
    provenance: Provenance

@dataclass(frozen=True)
class Constraint:
    drug: DmdRef                         # level explicitly tagged: ingredient vs product matters
    axis: Axis
    kind: Kind
    guard: Guard                         # Always() for unconditional facts
    payload: Span | Rule | LinkOut
    authority: Authority
    provenance: Provenance

@dataclass(frozen=True)
class AxisResult:
    # Per (drug, axis) cell. Keeps the two empty states distinct (invariant 7).
    axis: Axis
    constraints: tuple[Constraint, ...]
    checked_sources: tuple[str, ...]     # reported in; "no constraint" is meaningful here
    pending_sources: tuple[str, ...]     # ambassador agents still running

@dataclass(frozen=True)
class Dossier:
    dossier_id: str
    case_id: str
    case_version: int
    query: "Query"
    corpus_snapshot_id: str
    results: dict[DmdRef, dict[Axis, AxisResult]]   # drug -> axis -> result
    derived_at: date
    oldest_retrieval: date               # printed prominently in the footer
```

### Evaluation semantics

Evaluating a candidate drug against a case: resolve the drug across the spine; collect every `Constraint` whose `guard.evaluate(case).fired` is true, plus unconditional ones; group by axis into `AxisResult`s; render with provenance and authority badge. No scoring, no aggregation across sources, no reconciliation when sources disagree. Disagreement is displayed, because surfacing that the SPC and the renal reference band renal function differently, or band it in different conventions (eGFR vs CrCl), is itself clinically useful.

### Categorical gloss (for the README, and because it dictates the integration strategy)

The sources form a diagram of partial constraint-presheaves over (DrugId x Facet-space). A case picks out a point of Facet-space. The dossier is the limit of the diagram restricted to (drug, case); the provenance links are the projection maps of the cone. The two tiers are two ways of computing the same cone: the resident tier evaluates the presheaves held locally; the ambassador tier evaluates the ones held remotely, sending only the case point outward and receiving constraint values back. Alternatives are morphisms in DrugId (ATC sibling, VTM-form variation, or a guideline-attested edge) along which the diagram is re-evaluated; the system only ever traverses an edge some source asserts exists, which is exactly why it can show alternatives without recommending them.

---

## 5. Architecture

### 5.1 Entity spine (dm+d)

dm+d's five-level model is the identity layer; everything hangs off it. Ingredient-level reasoning (interactions, class effects, pregnancy) attaches at VTM; dose and route at VMP; excipients, supply, and the SPC at AMP, because those are per-product facts. Most tools answer the lactose and gelatine questions badly precisely because they reason only at ingredient level. v0 needs name-to-VTM/VMP/AMP resolution via a trigram index over dm+d name fields plus a small abbreviation table. Cross-vocabulary maps (ATC for class queries, SNOMED for any future EHR alignment, RxNorm for US sources) are v1.

### 5.2 Input: freeform history to facet projection

The doctor pastes or dictates history in whatever shape it arrives. A local parser (a small model on the doctor's machine) extracts the `Case` and grounds every medicine mention to a dm+d ref and every condition to a coded term. This is where invariant 4 is enforced: narrative is processed in place; only `project(case)` crosses the wire. Two artefacts result: the `Case` (coded, reasoned over and projectable) and the encrypted `narrative_blob` (keyed by alias, never transmitted, deletable).

Parser output is shown back for confirmation before anything dispatches, because a misread eGFR poisons every downstream cell. Anything the parser cannot ground is flagged "unparsed, please confirm" rather than guessed; the parser fills enumerated slots and grounds codes, and never infers clinical judgements ("frail", "high risk"). The judgement stays downstream of retrieval, in the human.

### 5.3 Resident tier: the local reference bank with the recursive pattern

A digitised corpus that may legitimately live on disk (section 8 status INGEST). The recursive language-model pattern runs in two phases:

- **Ingest-time tree (RAPTOR).** Each document is decomposed along its native structure (SPCs along their regulator-mandated section skeleton: 4.1 indications, 4.2 posology, 4.3 contraindications, 4.4 warnings, 4.5 interactions, 4.6 pregnancy/lactation, 6.1 excipients; rule sets along their criteria) and a hierarchical summary tree is built bottom-up. Leaf nodes are verbatim spans with char offsets; internal nodes are summaries-of-summaries, each retaining pointers to the exact spans beneath. Chosen because clinical documents are deeply hierarchical and flat chunking destroys the section semantics the facet guards depend on.
- **Query-time recursive descent.** A query (case projection plus axis) enters at the relevant subtree root and descends only branches whose summaries are relevant, pulling leaf spans at the bottom. The descending model chooses which branch to read; it never authors. Every returned unit is a verbatim span with provenance, and the descent path is logged so retrieval is auditable.

### 5.4 Ambassador tier: dispatched research agents

For decentralised live sources (section 8 status LINK and the long tail), dispatch per-source agents. Each agent receives only the `CaseProjection` plus the resolved drug, is scoped to exactly one source by a hard domain allowlist (it cannot wander the open web), executes that source's retrieval (deep link, permitted form query, or permitted fetch), and returns `Constraint` records, never free prose. An agent that finds nothing returns an explicit "checked, nothing on this axis" so the dossier distinguishes "no constraint" from "not yet checked" (invariant 7). Agents run in parallel; the dossier renders progressively with per-source pending/done state visible. Ambassador facts carry a TTL; past it the cell shows "last checked N days ago, re-run" rather than presenting stale output as current.

```python
from typing import Protocol

class Agent(Protocol):
    source: str
    allowlist: tuple[str, ...]           # hard domain allowlist; enforced before any fetch
    def fetch(self, drug: DmdRef, projection: CaseProjection) -> AxisResult: ...
    # MUST populate checked_sources even when constraints is empty
```

### 5.5 Surfacing problems and alternatives without recommending

Two display constructs (governed by section 3 and decision-log D1):

- **Flagged finding.** Where a constraint's guard fires, the cell is marked and renders the source's own words for the problem ("severe renal impairment: contraindicated", SPC 4.3, linked) directly beside the mechanical case fact that tripped the guard ("case eGFR 24 mL/min, parsed from history dated ..."), with the guard's own `explanation` string making the trip visible. Two independently-cited statements in juxtaposition. The system asserts neither the conjunction nor its consequence.
- **Attested alternative.** An alternative renders only with a provenance for the adjacency itself: a guideline or SPC naming it in context (rendered as that source's cited claim), an SPS Q&A discussing the swap, or a displayed mechanical relation (ATC sibling, same-VTM form) explicitly labelled mechanical. Agents may retrieve candidates; they may never originate one; alternatives are never ranked. A candidate with no citable adjacency does not render.

### 5.6 Optional synthesis layer (off by default)

The default and trustworthy mode is the bare matrix of cited spans, which is already the deliverable. Optionally, behind a clear boundary, a typesetter pass arranges already-retrieved spans into per-axis prose where every output sentence must string-align to a cited span, mechanically rejected otherwise. The model orders sentences; it does not assert. Deferred past v0 (section 9).

### 5.7 Persistence and refresh: the secretary's memory

A `Case` is durable. A `Dossier` is a materialised view `(case_version, query, corpus_snapshot_id) -> results`, recording the (source, drug, axis) triples it cited. Resident sources sync on their declared cadence (MHRA Drug Safety Update monthly is the prime mover; SPC re-fetch with hash diff covers label changes); a sync that changes a cited document marks dependent dossiers dirty. A dirty dossier re-derives and renders a diff against its last-reviewed state ("clarithromycin SPC 4.5 updated since you last reviewed this patient; the apixaban interaction wording changed"). The doctor can mark a dossier "reviewed", snapshotting the acknowledged state so future diffs are against that baseline. This noticing, per specific patient, is what makes it a secretary rather than a search box, so the diff mechanism is in v0 even though the auto-refresh cron is v1.

### 5.8 UI

One screen. Case sketch pinned top. Candidate drug(s) as columns (the flagship wants clarithromycin and azithromycin side by side; comparison is where the matrix layout pays for itself). Axes as rows. Cells contain the retrieved span or link-out, source badge, authority tier, retrieval date, and (where firing) the flagged-finding juxtaposition. Distinct rendering for checked-clear vs not-yet-checked. The footer prints the oldest retrieval date among citations, prominently. Nothing is more than one click from its origin. v0 is a single static Jinja-rendered HTML page per case; no framework until the matrix earns one.

---

## 6. Storage schema

DuckDB for the spine and the constraint cache; `data/raw/` (gitignored) holds every fetched document with its SHA-256, fetch timestamp, and source URL, so any dossier re-derives byte-for-byte.

```sql
-- dm+d spine, loaded from TRUD XML (section 8). Columns trimmed to v0 needs.
CREATE TABLE dmd_vtm   (vtm_code TEXT PRIMARY KEY, name TEXT);
CREATE TABLE dmd_vmp   (vmp_code TEXT PRIMARY KEY, vtm_code TEXT, name TEXT,
                        strength TEXT, form TEXT);
CREATE TABLE dmd_amp   (amp_code TEXT PRIMARY KEY, vmp_code TEXT, name TEXT, supplier TEXT);
CREATE TABLE dmd_ingredient (vtm_code TEXT, ingredient_code TEXT, ingredient_name TEXT);
CREATE TABLE dmd_excipient  (amp_code TEXT, excipient_code TEXT, excipient_name TEXT,
                             present BOOLEAN);
CREATE TABLE dmd_price (vmpp_code TEXT, vmp_code TEXT, price_pence INTEGER);

-- resolution aids
CREATE TABLE name_alias (alias TEXT, target_code TEXT, level TEXT);  -- abbreviations, brand->generic
-- trigram index built in code over dmd_* name fields

-- fetched source documents (content-addressed)
CREATE TABLE raw_documents (
    document_id TEXT PRIMARY KEY,   -- stable id (emc product id, DSU issue slug)
    source TEXT,                    -- registry key
    url TEXT,
    sha256 TEXT,
    fetched_at TIMESTAMP,
    path TEXT,                      -- file under data/raw/
    version TEXT
);

-- cached extracted constraints (re-derivable; cache for speed and snapshotting)
CREATE TABLE constraints (
    constraint_id TEXT PRIMARY KEY,
    drug_code TEXT, drug_level TEXT,
    axis TEXT, kind TEXT,
    guard_json TEXT,                -- serialised Guard AST
    payload_json TEXT,              -- serialised Span|Rule|LinkOut
    authority INTEGER,
    provenance_json TEXT,
    source_document_id TEXT,
    corpus_snapshot_id TEXT
);

-- corpus snapshots: a named set of document versions, so a dossier pins what it saw
CREATE TABLE corpus_snapshots (snapshot_id TEXT PRIMARY KEY, created_at TIMESTAMP,
                               document_ids TEXT);  -- json array

-- cases (patient data; narrative encrypted)
CREATE TABLE cases (
    case_id TEXT, version INTEGER,
    alias TEXT,                     -- doctor-side, never a patient identifier
    facets_json TEXT,               -- the coded Case minus narrative
    narrative_blob BLOB,            -- encrypted at rest
    narrative_key_ref TEXT,         -- reference to local key, not the key
    created_at TIMESTAMP,
    PRIMARY KEY (case_id, version)
);

-- dossiers (materialised views with review/diff state)
CREATE TABLE dossiers (
    dossier_id TEXT PRIMARY KEY,
    case_id TEXT, case_version INTEGER,
    query_json TEXT,
    corpus_snapshot_id TEXT,
    results_json TEXT,
    derived_at TIMESTAMP,
    reviewed_snapshot_id TEXT,      -- the snapshot the doctor last acknowledged
    cited_triples_json TEXT         -- (source, drug, axis) subscriptions for dirty-marking
);

CREATE TABLE freshness (source TEXT PRIMARY KEY, last_sync TIMESTAMP, last_change_hash TEXT);
```

---

## 7. Module layout

```
CLAUDE.md                       this document (or a pointer to it)
pyproject.toml                  uv-managed
docs/decision-log.md            dated decisions
data/raw/                       gitignored: content-addressed source docs
data/pullback.duckdb            gitignored
src/pullback/
    model/
        dmd.py                  DmdRef, DmdLevel, Coded
        facets.py               Case, CaseProjection, project(), Sex, Impairment, Route, Field, Axis
        guard.py                GuardExpr + concretes, Guard, GuardOutcome, evaluate
        constraint.py           Provenance, Authority, Kind, Span, Rule, LinkOut, Constraint, AxisResult
        dossier.py              Query, Dossier, diff()
    spine/
        load.py                 TRUD XML -> DuckDB
        resolve.py              name -> DmdRef (trigram + aliases)
        excipients.py           AMP -> excipient constraints
        price.py                VMPP -> cost constraint
    parse/
        parser.py               freeform history -> Case (LOCAL model)
        ground.py               mention -> DmdRef, condition -> Coded
        confirm.py              produce the confirm-before-dispatch view
    resident/
        tree.py                 RAPTOR build over a RawDocument
        descend.py              query-time descent -> spans + path log
        spc.py                  SPC section adapter -> tree + guards
        dsu.py                  MHRA Drug Safety Update index adapter
        rules.py                STOPP/START v3, ACB (v1)
    ambassador/
        agent.py                Agent protocol, allowlist enforcement, parallel dispatch
        sps_supply.py           SPS Medicine Supply Tool agent
        crediblemeds.py         CredibleMeds category resolver
        links.py                templated LinkOut constructor for the long tail
    eval/
        evaluator.py            (Case, Query) -> Dossier
        alternatives.py         attested-alternative discovery (section 5.5)
    render/
        matrix.py               Dossier -> HTML
        templates/dossier.html.j2
    store/
        db.py                   DuckDB access, snapshots
        freshness.py            sync, dirty-marking, diff
        crypto.py               narrative encryption at rest
    cli.py                      ingest, build-tree, parse, run, render, refresh
tests/
    golden/                     per-drug extraction fixtures
    test_*.py
```

---

## 8. Source registry (the licensing critical path)

Statuses checked June 2026; re-verify a row before building its adapter. v0 status legend: SPINE (entity layer), INGEST (stored locally), LINK (deep link-out per drug), APPLY (licence application in flight, ingest later), OUT.

| Source | Holds | Access route | Licence reality | v0 |
|---|---|---|---|---|
| **dm+d** | The NHS drug entity model: VTM/VMP/AMP, ingredients, forms, excipient-bearing AMP detail, prices | NHS England TRUD, free account | Free under TRUD terms; the standard spine for every UK meds system | SPINE |
| **BNF / BNFC** | Core formulary: indications, doses, interactions, safety prose | Browse free at bnf.nice.org.uk. Programmatic: BNF has its OWN syndication API, separate from the NICE API | Application and licence; NICE-side syndication generally needs cyber security certification (Cyber Essentials class, or DSPT for public sector). AI use permitted subject to NICE approving the stated use; training models on it prohibited. A university-signed student route exists | APPLY |
| **NICE syndication API** | NICE guidance, quality standards; explicitly NOT BNF or CKS | Application, licence, API key | Test licences (about 3 months) for evaluation; international fees substantial | OUT (v1) |
| **emc** (Datapharm) | SPCs and PILs for 9,000+ UK products, published by MAHs post-approval | Free to view at medicines.org.uk. Programmatic: Datapharm sells a RESTful API mapping SPC/PIL raw documents to dm+d codes, content structured in FHIR | Web terms forbid bulk scraping; the commercial API is the clean route at scale. For a ten-drug spike, manual download for local research use is pragmatic | INGEST (manual, ten drugs) |
| **MHRA Products portal** | SPCs, PILs, PARs, served by the regulator | products.mhra.gov.uk, public | Government-hosted; SPC text remains MAH copyright. The public per-document mirror | LINK (alt to emc) |
| **MHRA Drug Safety Update** | Monthly safety bulletins: the live signal layer | gov.uk, public | Open Government Licence applies to gov.uk content generally | INGEST (index) |
| **SPS** (Specialist Pharmacy Service) | Administration advice, switching, shortages (Medicine Supply Tool), lactation, Medicines Q&As | sps.nhs.uk, free | NHS web content; confirm ingestion terms before any bulk use. Q&A structure also seeds the eval set | LINK + one agent |
| **UKTIS / bumps** | Teratology monographs and patient leaflets | Web; full UKTIS monographs need HCP registration | Registration-gated | LINK |
| **CredibleMeds QTdrugs** | Categorised QT risk lists | Free registration | Redistribution restricted; store category locally for personal research, render as link-out with category label | LINK |
| **STOPP/START v3** | ~190 explicit criteria for inappropriate prescribing in older adults | Published in European Geriatric Medicine (2023), criteria reproduced in open literature | Encode as rules with citation; verify reproduction terms | v1 INGEST |
| **Anticholinergic burden scales** (ACB, AEC) | Per-drug anticholinergic scores | Published literature and calculator sites | Encode scores with citation | v1 INGEST |
| **Liverpool interaction checkers** (hiv-, hep-, covid19-druginteractions.org) | Best-in-class domain interaction tools | Free web tools | Free to use, not redistribute | LINK |
| **NEWT guidelines** | Administration via enteral feeding tubes, crushing/dispersing | Subscription (modest) | Beloved niche resource; link-out | LINK |
| **Renal Drug Database** | Renal dosing reference | Commercial | Link-out only | LINK |
| **Maudsley Prescribing Guidelines** | Psychotropics | Book/commercial | Cite-and-link | LINK |
| **NAPOS drug database** (porphyria) | Per-drug porphyria safety classification | Free web | Link-out | LINK |
| **MedicinesComplete** (Stockley's, Martindale, BNF mirror) | The interactions gold standard | Commercial subscription | A future commercial decision, not a tinkering one | OUT |
| **FDB Multilex** | The interaction dataset inside most GP systems | Commercial | Incumbent infrastructure, not a source for us | OUT |
| **TOXBASE / Medusa** | Poisons / IV administration | NHS organisational registration | Closed to us | OUT |
| **OpenPrescribing** (Bennett Institute, Oxford) | English primary-care prescribing data; excellent open dm+d browser | Open API | Open | v1 (context) |
| **openFDA** | US labels, FAERS | Open API | Open | v1 (signal browsing, US caveats) |
| **DDInter 2.0 / TWOSIDES** | Open research drug-interaction datasets | Open downloads | Research licences; quality heterogeneous; NEVER present as authoritative alongside SPC text without the research-grade label | v1 candidate |

Three structural facts that shape the build:
1. **The spine is free, the prose is gated.** dm+d gives identity, structure, excipient-bearing product detail, and prices at zero cost; the valuable prose (BNF, Stockley's) is licensed. So link-outs are first-class: a row deep-linking into the right page of a gated source, pre-resolved to the right drug, is most of the value of ingestion at none of the licensing cost.
2. **SPCs are the legally authoritative per-product text and are publicly viewable.** A workbench on SPC 4.1 to 4.6 and 6.1, joined per case, is buildable today with no licence application; the BNF application runs in parallel and upgrades the product when it lands.
3. **The emc commercial API mapping SPC/PIL to dm+d codes is exactly the join we would otherwise build by hand.** If this stops being a tinkering project, that API is the first cheque to consider.

---

## 9. Execution plan

Twelve evening-sized blocks at tinkering pace. The point is closure: one rendered, re-derivable flagship dossier plus a go/no-go memo, even if half the cells are link-outs. Each block lists a deliverable and acceptance tests written as checkable assertions. Do not start a block before the previous block's acceptance tests pass.

### Drug set (ten, chosen to stress different axes)

apixaban, sertraline, clarithromycin, azithromycin, ramipril, metformin, ibuprofen, amitriptyline, alendronic acid, nitrofurantoin.

Rationale: clarithromycin vs azithromycin gives the flagship comparison (CYP3A4/P-gp vs not, QT both); apixaban and sertraline are the co-medications; metformin and nitrofurantoin have hard renal cliffs at specific thresholds (perfect for facet-guard extraction, and for exercising the eGFR-vs-CrCl distinction); amitriptyline lights anticholinergic burden and STOPP criteria; ibuprofen tests interaction text against both an anticoagulant and an ACE inhibitor; alendronic acid tests administration-constraint prose.

### Flagship case

Woman, 78, eGFR 24 mL/min, atrial fibrillation on apixaban, depression on sertraline, recent diagnosis warranting a macrolide; candidate clarithromycin with azithromycin as the attested-alternative comparator. Entered as a freeform paragraph, not a form. Lights up renal banding (and the eGFR/CrCl convention question, since at 78 and likely low weight the two diverge), a CYP3A4/P-gp interaction with bleeding risk, QT additivity with an SSRI, age criteria, and an alternative that sources discuss in exactly that renal/interaction context. If this dossier is not obviously better than the manual join, the project dies honestly.

### Blocks

**Block 1: TRUD and spine.** Register for TRUD, download the dm+d release, load XML into DuckDB.
- AC1: `resolve("apixaban")` returns a VTM with at least one VMP and at least one AMP.
- AC2: `excipients(resolve("apixaban 5mg tablets", level=AMP))` returns a non-empty list with a boolean present flag per excipient.
- AC3: `price(...)` returns an integer pence value for at least one VMPP of metformin.

**Block 2: name resolution.** Trigram index over dm+d names plus an abbreviation/brand alias table.
- AC1: all ten drugs resolve from plain text to the correct VTM.
- AC2: two deliberate misspellings ("clarithromcyin", "nitrofurantion") resolve correctly.
- AC3: a brand name resolves to its generic VTM.

**Block 3: freeform parser (local).** Small local model extracts the `Case` from realistic history text, grounds medicines to dm+d and conditions to coded terms, flags unparseable items, and emits the confirm view. Enforce that only `project(case)` is marked transmissible.
- AC1: the flagship paragraph yields a `Case` with apixaban and sertraline grounded as `co_meds`, `age_years == 78`, `egfr == 24`.
- AC2: `project(case)` contains no alias and no narrative field (assert at the type and value level).
- AC3: a deliberately ambiguous token (e.g. an unrecognised abbreviation) appears in the confirm view as "unparsed", not silently dropped or guessed.

**Block 4: SPC acquisition.** Manually download SPCs for the ten drugs (emc or MHRA portal), store in `data/raw/` with SHA-256, fetch timestamp, and source URL recorded in `raw_documents`.
- AC1: ten rows in `raw_documents`, each with a non-null sha256 and a resolvable local path.
- AC2: re-running acquisition is idempotent (same content -> same id, no duplicate).

**Block 5: section tree.** Decompose each SPC along the mandated heading skeleton into the RAPTOR summary tree; leaves are spans with char offsets, internal nodes summarise upward with pointers retained.
- AC1: golden-file tests for sections 4.1, 4.2, 4.3, 4.5, 4.6, 6.1 across all ten drugs.
- AC2: roughly 95 percent of the sixty target sections (ten drugs x six sections) extract cleanly; per-publisher quirks logged in `tests/golden/parsing-notes.md`.
- AC3: every leaf span round-trips to the exact source offset.

**Block 6: recursive descent.** Query-time descent over the tree returns cited spans per axis, with the descent path logged.
- AC1: (flagship case, clarithromycin, INTERACTION) descends into 4.5 and returns the apixaban-relevant and sertraline-relevant spans.
- AC2: the logged descent path shows unrelated branches (e.g. 4.6 pregnancy) were not read for that query.
- AC3: every returned unit is a verbatim `Span` carrying full `Provenance`.

**Block 7: facet guards.** Pattern rules over 4.2 (renal and hepatic thresholds) and 4.5 (co-medication and class matches) attach serialisable `Guard`s to spans, tagged with the renal convention (eGFR vs CrCl) the source states.
- AC1: metformin and nitrofurantoin renal cliffs fire at the correct threshold for the flagship case, and the constraint records which convention the SPC stated.
- AC2: clarithromycin's interaction spans fire against the flagship's `co_meds` (apixaban, sertraline); azithromycin's sparser equivalents fire correctly.
- AC3: each firing guard's `GuardOutcome.explanation` is human-readable ("case eGFR 24 mL/min < 30").

**Block 8: ambassador agent (one source).** Build one real dispatched agent over a single well-structured source (SPS Medicine Supply Tool, or a CredibleMeds category resolver), receiving only `CaseProjection`, returning `Constraint` records, reporting pending/done, and returning an explicit "checked, nothing found" when empty. Enforce the domain allowlist before any fetch.
- AC1: the agent contributes a real cited cell to the flagship dossier.
- AC2: a unit test asserts the payload handed to the agent is a `CaseProjection` with no narrative or alias.
- AC3: an empty result populates `checked_sources`, leaving the cell rendered as checked-clear, not pending.
- AC4: a fetch to a domain outside the allowlist raises rather than proceeds.

**Block 9: link-out adapter.** Templated deep links per drug for the remaining decentralised sources (UKTIS, NEWT, NAPOS, Liverpool, Renal Drug Database, CredibleMeds where not agented).
- AC1: link rows render for all ten drugs, pre-resolved to the drug where the target scheme allows.
- AC2: each `LinkOut` carries provenance (source key plus the constructed URL).

**Block 10: case store, evaluator, alternatives.** Persist cases and dossiers; constraint filtering and axis grouping into `AxisResult`s; flagged-finding construct; attested-alternative discovery (ATC sibling labelled mechanical, plus any alternative named in a retrieved SPC/DSU span).
- AC1: the flagship case evaluates against clarithromycin and azithromycin, producing a `Dossier` with both drug columns populated.
- AC2: azithromycin surfaces as an attested alternative with its adjacency cited, and is never accompanied by system-voiced preference or ranking.
- AC3: a cell where a guard fired renders the source span and the mechanical case fact as two separately-cited statements (assert both provenances present).
- AC4: a candidate alternative with no citable adjacency is absent from the dossier.

**Block 11: render and diff.** Jinja one-screen matrix: two drug columns, axis rows, provenance footers, authority badges, oldest-retrieval banner, distinct checked-clear vs not-checked rendering. Manual re-derive shows a diff when a re-fetched SPC or a new DSU issue changes a cited document.
- AC1: the flagship dossier renders to a single self-contained HTML page openable in a browser, every cell one click from its source.
- AC2: swapping a modified SPC into `data/raw/` and re-deriving highlights the changed cell as "changed since last review".
- AC3: marking the dossier reviewed re-baselines the diff (a subsequent unchanged re-derive shows no diff).

**Block 12: external eyes and memo.** Walk the design-partner clinician through the flagship dossier with their own real (suitably handled) case mix. Capture: what is missing, what is wrong, what they currently do instead, whether they would use it next week, and specifically whether the flagged-findings-plus-alternatives presentation gives them what a recommendation would without crossing into one. Write the go/no-go memo and seed further decision-log entries.
- AC1: a written memo exists with a go/no-go/pivot recommendation grounded in the reviewer's reaction.
- AC2: at least three concrete change requests captured as issues.

### Deliberately deferred (recorded temptations, not oversights)

The clinical-surface typesetter (generated prose, even citation-enforced): the bare cited matrix is the v0 deliverable. BNF application paperwork (start it in parallel; it gates nothing in the spike). Auto-refresh cron (block 11 proves the diff mechanism; the schedule comes later). Multi-source agent fan-out (one real agent in block 8 proves the loop; the rest stay link-outs). Paediatrics (BNFC is its own world). Dose calculators, scores, rankings, system-voiced verdicts (the device line). Multi-user or cloud anything. The full eval dataset (centrepiece of v1 if the spike goes; see section 11).

---

## 10. Definition of done and exit criteria

v0 is done when the flagship dossier renders end to end from a freeform paragraph, every cell is cited or an explicitly-checked blank, the eGFR/CrCl convention is visible wherever a renal threshold fires, azithromycin appears as a source-attested alternative without any recommendation, and a re-derive after a source change shows the diff.

- **Go signals:** the reviewer finds the dossier faster than their current join for at least one realistic case; SPC extraction held near 95 percent across the ten; the parser handled their real history without a poisoning error (or flagged what it could not parse); the one agent returned a genuinely useful cited cell; the flagged-findings-plus-alternatives layout gave them what they wanted without reading as a recommendation; at least one cell surprised them (the excipient row and the supply row are the likeliest).
- **No-go or pivot signals:** parsing brittleness dominating effort (pivot to the rules-engine cut: STOPP/START v3 plus ACB plus link-outs, which needs no document parsing); the parser too unreliable to trust the projection (fall back to a structured intake form, accepting the workflow cost); the agent loop too flaky to be worth the decentralised tier (fall back to link-outs only); reviewer indifference ("I'd still just open the BNF") on every case tried; an unforeseen licensing block on even view-and-link usage.
- **Fallback artefact, valuable even on a full pivot:** a published UK medicines case-join benchmark (cases with expected constraint hits and source-level answer keys, structurally modelled on SPS Medicines Q&As), usable to evaluate anyone's clinical retrieval system. A finished, citable object either way.

---

## 11. Open questions (human decisions; do not decide these unilaterally)

Ordered by how much they shape everything downstream.

1. **Licensing entity and timing.** Who applies for BNF syndication: the maintainer personally, OuLoPo, or via the university (the student/university route suggests an academic pathway, and a HAILab affiliation may be the lowest-friction signature)? Cyber security certification (Cyber Essentials class) is a prerequisite for NICE-side syndication; factor its cost into whichever entity applies. Apply during the spike or only after a go decision?
2. **Project identity, given a named single user.** The build is a bespoke instrument (decision-log D5). The live question is what to harvest: a clean time-to-answer / error-rate study (with-tool vs without, pharmacist-adjudicated) fits a clinical collaboration and produces a publication regardless of product outcome, but instrumenting for it from block 1 trades against build speed. Does v0 carry that instrumentation, or is the study a deliberate v1?
3. **Interactions content strategy.** SPC 4.5 extraction plus link-outs indefinitely, the BNF application as the upgrade path, Stockley's via MedicinesComplete if this commercialises, or the open research sets (DDInter/TWOSIDES) with explicit research-grade labelling? The agent tier changes the calculus: a well-scoped Liverpool-checker agent may cover the highest-value interaction domains without any bulk licence.
4. **Parser-trust threshold.** Where is the parser reliable enough to trust the projection it sends outward? Both a UX question (confirm-everything vs confirm-exceptions) and a safety one (a silently misread eGFR poisons the renal axis). The fallback is a structured intake form, at the cost of the friction the project exists to remove. Needs the design partner's real history text to calibrate.
5. **The agent tier and OuLoPo.** The ambassador-agent design (per-source scoped agents, projection-in, typed-constraints-out, citation-enforced, no origination) is structurally an OuLoPo coherence-over-sources harness with a clinical skin. Standalone tinkering repo, or an OuLoPo case study? Affects how much agent-framework effort is warranted and what gets written up.
6. **The eval dataset as a first-class artefact.** A published UK medicines case-join benchmark would be citable, useful to others, and finishable within weeks. Promote it from fallback to parallel deliverable? Interacts with question 2: the study and the benchmark share machinery.
7. **Open or closed.** The dm+d spine plus SPC extraction plus link-out registry plus the agent framework is publishable as open source without touching licensed content or patient data, and would be the strongest possible footing for the BNF application (demonstrable provenance discipline). Any reason to keep it closed?

---

## 12. Decision log (seed entries)

Maintained in `docs/decision-log.md`. Format: date, decision, alternatives rejected, rationale pointer.

- **D1 (2026-06-12): negative findings and attested alternatives, no verdicts.** Surface where sources flag a candidate and the cited reasons, and alternatives only where the adjacency is itself attested or a labelled mechanical relation; never generate the verdict sentence, never rank alternatives. Rejected: pure retrieval with no alternatives (leaves the clinician mid-task); model-originated alternatives (crosses the device line, epistemically worse). See section 3.
- **D2 (2026-06-12): freeform input, parsed locally, minimised projection outward.** A local model parses freeform history to the facet schema; only the coded projection reaches remote models or agents; raw narrative encrypted at rest under a doctor-side alias. Rejected: enumerated-form-only input (fights the workflow); sending raw history to hosted models (unacceptable for real patients). See sections 5.2, 3.
- **D3 (2026-06-12): persistent per-patient dossiers with refresh and diff.** A case is durable; a dossier is a materialised view subscribing to the triples it cites; source syncs mark it dirty; re-derivation shows a diff. Rejected: stateless one-shot lookups (misses the secretary's core value). See section 5.7.
- **D4 (2026-06-12): two retrieval tiers over one constraint schema.** Resident (local bank, recursive descent) and ambassador (dispatched per-source agents) both emit the same typed objects. Rejected: a single monolithic RAG index (loses document structure and the licence boundary between resident and remote content). See sections 5.3, 5.4.
- **D5 (2026-06-12): single design-partner orientation.** Built as a bespoke instrument for one named clinician's friction, their real case mix defining the gold set; productisation deferred until the friction is demonstrably removed. Rejected: wedge-first product framing (premature, and the maintainer's known failure mode is breadth before closure). See sections 1, 0.
