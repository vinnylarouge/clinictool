# 03. Regulatory position

This document is a design constraint, not legal advice. Before any deployment beyond personal research use, get proper regulatory advice. But the boundary shapes the architecture from day one, so it lives in the repo.

## The device boundary

Software that meets the definition of a medical device under UK MDR 2002 requires UKCA marking. The MHRA's standalone-software guidance (with its decision flowcharts) draws the operative line for tools like this between:

- **Reference retrieval**: software that finds, filters, and displays published information for a professional to interpret. The electronic-library function. Generally not a device.
- **Patient-specific calculation or recommendation**: software that computes a score, dose, risk, or directive for an individual patient for a medical purpose. Generally a device, with classification and conformity assessment to match.

Our hard invariants (CLAUDE.md) are engineered to keep the system on the retrieval side even though the doctor's need points at the boundary. The need is to see what a source flags as not okay and why, and what alternatives came up; the temptation is to let the software conclude. The invariants split that need from that temptation precisely: facet-guarded retrieval surfaces the source's own contraindication text beside the mechanical case fact, two independently-cited statements juxtaposed, and the clinician performs the inference; alternatives render only with a citation for the adjacency itself; nothing is scored or ranked. The act the software performs is the same act as a clinician turning to the renal-impairment paragraph and then glancing at the case bloods. iatroX is a useful UK precedent: a clinician-facing AI product that publicly positions its retrieval features as a referenced librarian rather than a calculator precisely to sit outside device classification, while acknowledging that an app which calculates or interprets patient data for a medical purpose is likely a device.

The sharpest line to hold, given the use case: presenting source X's statement "in severe renal impairment, drug B is preferred over drug A" as *X's cited claim with a link* is retrieval; the software generating "use B instead of A for this patient" is a recommendation and a device function, even if B genuinely is the better choice. The difference is who is speaking and whether a citation backs the adjacency, not whether the underlying clinical content is the same. This is why the architecture forbids the agent from ever originating an alternative.

Two honesty notes. First, labelling does not override function: writing "research aid only" on a tool that in fact outputs patient-specific recommendations does not change its status; the invariants must hold in the behaviour, not the disclaimer. Second, the line moves as features move. The features most likely to cross it, in rough order of regulatory gravity: any aggregate suitability score; dose calculation; ranking candidate drugs; auto-generated prose that asserts rather than quotes; ingestion of real patient records. Each of these is a stop-and-flag item in this repo.

## Alternatives

The decision-log entry D1 governs this. Restated as a rule the code enforces: an alternative drug may appear in a dossier if and only if a retrieved source attests the adjacency (names the alternative in the relevant clinical context) and that attestation is rendered as the source's cited claim, or the relation is a displayed mechanical fact (ATC class sibling, same-VTM form variant) explicitly labelled as mechanical and not as advice. Alternatives are never ordered, scored, or accompanied by any phrasing that prefers one over another in the system's own voice. The research agents may retrieve candidate alternatives; the system may never originate them. A candidate with no citable adjacency is dropped, not shown unsourced.

## The AI layer specifically

The MHRA's Software and AI as a Medical Device change programme is live and explicitly a moving framework; the AI Airlock regulatory sandbox completed its pilot phase in early 2025 and its findings feed an AI-specific framework expected to be published during 2026. Practical consequence for us: treat the v1 LLM-as-typesetter design (citation-enforced composition over retrieved spans, no open generation) as both an epistemic and a regulatory architecture, and re-check the published framework before shipping any generative surface to a third party.

## Clinical safety standards (separate from device law)

If this is ever deployed within an NHS organisation, DCB0129 (manufacturer) and DCB0160 (deploying organisation) clinical risk management standards apply, including a named Clinical Safety Officer and a hazard log. For the tinkering phase this is out of scope, but the constraint/provenance design doubles as the evidence trail a hazard log wants, so we lose nothing by building as if.

## Intellectual property, distinctly from device status

- SPC and PIL text is the marketing-authorisation holder's copyright even when served from regulator or compendium websites; local research-use handling of a small set is one thing, redistribution is another. Rendering spans with attribution inside a personal research tool sits at the conservative end; any multi-user deployment should revisit this with the emc commercial API as the clean route.
- BNF content is licensed property; the only legitimate programmatic route is the BNF syndication arrangement (docs/01-sources.md), and note its terms: AI use subject to approval of the specific use, model training prohibited.
- Open Government Licence covers gov.uk-published material such as Drug Safety Updates.

## Data protection

This is now a primary design constraint, not a deferred one, because the tool ingests real freeform patient history for a real clinician. The whole shape of invariant 4 is the data-protection architecture:

- **Local-only narrative.** Freeform history is parsed on the doctor's machine; the raw narrative never transits to any remote model or research agent. Only the minimised coded projection (numeric and enumerated facets, dm+d codes, coded conditions) goes outward, and only as far as each dispatched agent's single source requires. This is data minimisation and purpose limitation built into the data flow rather than promised in a policy.
- **Special-category data.** Health data about an identifiable individual is special-category under UK GDPR Article 9. Even a coded projection can be identifying in combination; treat all of it accordingly. Lawful basis for a clinician processing their own patients' data for direct care exists, but the basis, the controller relationship (is the clinician the controller, is their organisation), and retention all need to be settled with a real DPIA before this touches a second patient, let alone a second clinician.
- **Storage.** Narrative blobs encrypted at rest, keyed by a doctor-side alias not by patient identifiers, with hard delete. Dossiers and cases likewise. No telemetry that exfiltrates content.
- **Remote-model question.** The local parser should be a model that can run locally; if any step genuinely needs a hosted model, only the coded projection may be sent, the provider's data-handling terms (retention, training-use) must be checked against invariant 4, and zero-retention routing used. The hosted clinical-surface typesetter, if ever enabled, operates only over already-retrieved public source spans plus the coded projection, never the narrative.
- **Single-user reality.** For the actual near-term use (one trusted doctor, their own machine, their own patients), the exposure is contained and the architecture above is proportionate. Every step toward multi-user, cloud, or shared-corpus changes the analysis and triggers a fresh DPIA. That escalation is a stop-and-flag item.

## Standing disclaimer for any rendered surface

"Research aid for healthcare professionals. Collates published sources with links and retrieval dates. Not a substitute for the source documents or for clinical judgement. Verify against the linked originals before acting."
