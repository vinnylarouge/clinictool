# 00. Scope

## The problem, stated precisely

UK clinicians answering "is drug X sensible for this patient" must join information that is authoritative but distributed. The BNF is the core reference but is deliberately terse; the moment a case has more than one complicating facet (renal impairment plus an interacting co-prescription plus age over 75, say), the lookup fans out across the Summary of Product Characteristics (SPC) on emc, the Specialist Pharmacy Service, UKTIS for pregnancy, the Renal Drug Database, Maudsley for psychotropics, CredibleMeds for QT, MHRA Drug Safety Updates, and assorted niche references (NEWT for enteral tubes, NAPOS for porphyria). Each source has its own indexing, its own update cadence, and its own licence. The join is done by hand, per case, in browser tabs and ring binders. That join is the product.

## Why the incumbents leave the gap open

- **In-system decision support** (FDB Multilex powering alerts inside EMIS/SystmOne, OptimiseRx, ScriptSwitch) fires at the moment of prescribing with minimal context. The alert-fatigue literature consistently reports override rates around 90 percent. These systems answer "should this prescription be blocked" not "help me think about this case". They are also closed to tinkering.
- **MedicinesComplete** (Pharmaceutical Press: BNF, Stockley's, Martindale) is the reference library behind a subscription. It is source-siloed: the user still performs the cross-source join manually.
- **UpToDate/Lexicomp, Micromedex**: US-centred, expensive, and again organised by source and monograph rather than by case.
- **iatroX** (UK) demonstrates the retrieval-with-references positioning for guidelines and has publicly articulated the same regulatory stance we adopt (librarian, not calculator). It is guideline-centred rather than medicines-centred.
- **OpenEvidence** (US) is the existence proof that clinicians adopt an AI research aid at scale when it is grounded and cited. There is no UK-formulary-grounded, licence-aware equivalent organised around the per-case medicines join.

The wedge: **case-shaped retrieval across UK medicines sources with mechanical provenance.** Not another alert. Not another monograph viewer. A workbench.

## Primary user and the unit of work

One named clinician with a recurring cognitive friction: assessing medication suitability for real patients whose relevant facts are scattered across distributed sources. This is a bespoke instrument for that friction, not a market wedge (decision-log D5). The unit of work is a persistent `Case` (a real patient, history entered freeform) paired with a `query` (suitability of a candidate drug, or an open "anything I should know" sweep). The output is a `Dossier`: one screen, axes down the side, retrieved-and-cited spans in the cells, flagged findings where a source objects and why, source-attested alternatives where they arose, and a refresh state so the doctor learns when something moved for this patient. A secretary: it researches, files, cites, and notices changes. It never decides.

## Suitability axes (the rows of the dossier)

| Axis | Primary published locus | Notes |
|---|---|---|
| Licensed indications | SPC section 4.1 | Off-label flagging is exactly the kind of thing clinicians need surfaced, not decided |
| Contraindications | SPC 4.3 | |
| Dose and renal/hepatic adjustment | SPC 4.2, BNF dose section, Renal Drug Database (link-out) | eGFR banding differs between sources; show both, do not reconcile |
| Interactions vs current meds | SPC 4.5, BNF interactions, Stockley's (link-out), Liverpool checkers for HIV/hepatitis | Pairwise against the case's medicine list |
| Pregnancy and lactation | SPC 4.6, UKTIS monograph, bumps leaflet | |
| Older-age appropriateness | STOPP/START v3 criteria, anticholinergic burden scales (ACB/AEC) | These are published, computable rule sets; strong v1 candidates |
| QT and arrhythmia risk | CredibleMeds lists, SPC 4.4 | CredibleMeds redistribution is restricted; link-out with category |
| Excipients and intolerance | SPC 6.1 and 2 | Lactose, gelatine (religious and dietary), soya/arachis oil, ethanol, sodium load of effervescents. Weirdly hard to query anywhere today |
| Administration route constraints | SPC 4.2, NEWT guidelines (enteral tubes) | Crushing/dispersing is a daily pharmacist question |
| Monitoring burden | SPC 4.4, BNF | |
| Active safety signals | MHRA Drug Safety Update, Yellow Card iDAP | |
| Supply status | SPS Medicine Supply Tool, DHSC SSPs | A perfectly suitable drug that is unobtainable is unsuitable |
| Cost | dm+d price data | Comes free with the entity spine |
| Long tail | Porphyria (NAPOS database, UKPMIS), G6PD deficiency lists, MAOI washout periods | Cheap to link out, disproportionately valued when needed |

## v0 cut (the only version that exists until the flagship case renders end to end)

- Entity spine: dm+d loaded locally; drug resolution by name to VTM/VMP/AMP.
- Input: a working freeform-to-facet parser (local model) over realistic history text, grounding medicines to dm+d, with a confirm-before-dispatch step. Even a rough parser is in v0 because the freeform input is the doctor's actual workflow and the data-flow boundary depends on it existing.
- Resident tier: SPCs for ten hand-picked drugs (manual download) decomposed into the section tree, plus the MHRA Drug Safety Update index. Query-time descent returns cited spans per axis.
- Ambassador tier: at least one real dispatched agent (the cleanest target is a single well-structured source such as the SPS Medicine Supply Tool or a templated UKTIS/CredibleMeds link-resolver), to prove the projection-out, constraints-back loop and the pending/done rendering. Remaining decentralised sources are templated link-outs for now.
- Axes live in v0: indications, contraindications, interactions (SPC 4.5 text, pairwise against the case's medicines), renal lines from 4.2, pregnancy 4.6, excipients 6.1. Remaining axes render as link-out rows.
- Flagged findings: where a facet guard fires, render the source span beside the mechanical case fact. Attested alternatives: render only ATC-sibling mechanical relations (labelled) plus any alternative explicitly named in a retrieved SPC/DSU span; no agent-originated alternatives.
- Persistence: cases and dossiers stored; a manual "re-derive" that shows a diff when a re-fetched SPC or a new DSU issue changes a cited document. Full subscription/auto-refresh is v1; the diff mechanism is v0 because it is the secretary's defining trick.
- Extraction is deterministic (heading-anchored span extraction); the model's only jobs in v0 are parsing input and routing the descent, never authoring claims.
- Output: one persistent, re-derivable HTML dossier for the flagship case below.

**Flagship case:** woman, 78, eGFR 24 mL/min, atrial fibrillation on apixaban, depression on sertraline, recent diagnosis warranting a macrolide; candidate drug clarithromycin (with azithromycin as the attested-alternative comparator). Entered as freeform history, not a form. This case deliberately lights up renal banding, a CYP3A4/P-gp interaction with bleeding risk, QT additivity with an SSRI, age criteria, and an alternative (azithromycin) that sources discuss in exactly the renal/interaction context. If the dossier for this case is not obviously better than the manual join, the project dies honestly.

## Non-goals for v0 (each is a recorded temptation, not an oversight)

No BNF content ingestion (licence pending; see 01-sources). No paediatrics (BNFC is its own world). No dosing calculators. No aggregate suitability score, no ranking of drugs or alternatives, no system-voiced verdict (these are the device line; docs/03-regulatory.md). No cloud or multi-user deployment; this runs on one doctor's machine. No agent-originated alternatives; alternatives must be source-attested. No transmission of raw patient narrative to any remote service (invariant 4).

Note what is explicitly in scope and was not before: real patient data (handled by local parsing and minimised projection, not by pretending it is synthetic), and surfacing of negative findings and source-attested alternatives (handled by juxtaposition and citation, not by recommendation).

## Kill and pivot criteria

- If SPC section parsing proves too brittle across publishers to hit roughly 95 percent clean extraction on the ten-drug set within the spike, pivot v0 to the **rules-engine cut**: STOPP/START v3 plus ACB plus link-outs, which needs no document parsing at all.
- If the BNF syndication route looks closed to an entity like ours after one application cycle, the product remains viable on SPC plus specialist sources, but reassess whether the differentiation still clears the bar.
- Fallback artefact that is valuable even on full pivot: a published **UK medicines question benchmark** built from the structure of SPS Medicines Q&As, usable to evaluate anyone's clinical retrieval system. A finished paper-shaped object either way.
