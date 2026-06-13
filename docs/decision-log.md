# Decision log

Format: date, decision, alternatives rejected, rationale pointer.

## 2026-06-12, D1: negative findings and attested alternatives, no verdicts

The product surfaces (a) where sources flag a candidate as problematic and the cited reasons, and (b) alternatives, but only where the adjacency relation is itself attested in a source or is a displayed mechanical relation (ATC sibling, labelled as such). The system never generates the verdict sentence and never ranks alternatives. Rejected: pure retrieval with no alternatives (leaves the clinician mid-task); model-originated suggestion of alternatives (crosses the device line and is epistemically worse). See docs/03-regulatory.md, "Alternatives".

## 2026-06-12, D2: freeform case input, parsed locally, minimised projection outward

Input is freeform patient history plus a query type. A local model parses it to the structured facet schema, grounding medicine mentions to dm+d; only the coded projection ever reaches remote models or agents. Raw narrative is encrypted at rest under a doctor-side alias. Rejected: enumerated-form-only input (fights the actual workflow); sending raw history to hosted models (unacceptable for real patients, and this tool is for a real doctor).

## 2026-06-12, D3: persistent per-patient dossiers with refresh and diff semantics

A case is a persistent object; a dossier is a materialised view over (case version, query, corpus snapshot). Dossiers subscribe to the (drug, axis, source) triples they cite; source syncs mark them dirty; re-derivation renders a diff ("changed since last review"). MHRA Drug Safety Update monthly is the prime mover; SPC re-fetch with hash diff covers label changes. Rejected: stateless one-shot lookups (misses the secretary's core value of noticing changes).

## 2026-06-12, D4: two retrieval tiers over one constraint schema

Resident tier: local reference bank with an ingest-time summary tree and query-time recursive descent, citation-enforced. Ambassador tier: dispatched research agents over decentralised live sources, receiving only the facet projection, returning Constraint records labelled by authority tier. Both tiers emit the same typed objects. Rejected: a single monolithic RAG index (loses document structure and the licence boundary between resident and remote content).

## 2026-06-12, D5: single design partner orientation

The project is built as a bespoke instrument for one named clinician's recurring friction, with their real case mix (suitably handled) defining the gold set and the bank's seed corpus. Productisation questions are deferred until the instrument demonstrably removes the friction. Rejected: wedge-first product framing (premature; also Vincent's known failure mode is breadth before closure).

## 2026-06-13, D6: typed core and renderer built first, on illustrative fixtures, ahead of the gated data sources

The first implementation slice is the typed spine of the whole system: the domain model (model/), the guard engine, the evaluator, the attested-alternatives rule, the dossier diff, and the Jinja matrix renderer, wired to a small in-repo fixture corpus so the flagship dossier renders end to end with provenance. The spike plan's blocks 1 to 9 are gated on resources not reachable from an autonomous session (a TRUD account for the dm+d spine, manual SPC downloads, a local parsing model, live network agents), so building those first was not possible. Building the typed core first is, and it is the layer everything else plugs into: real adapters emit the same Constraint objects into the same Corpus seam without touching the evaluator or renderer.

The fixtures carry illustrative dm+d codes (prefixed "fixture-") and short illustrative SPC span text, every provenance marked "FIXTURE", and the render shows an honesty banner so fixture content can never be mistaken for ingested authoritative content. This keeps invariant 1 (provenance or it does not ship) and invariant 5 (licence-aware ingestion: nothing real was scraped) intact.

Rejected: stubbing the core and waiting for the real data (leaves nothing runnable and unverifiable, and the maintainer's failure mode is breadth without a finished artefact). Rejected: fabricating realistic-looking real dm+d codes and full SPC text (would be dishonest provenance and a copyright question; the fixtures are deliberately and visibly illustrative). See SPEC sections 4, 5.5, 5.8, 9; CLAUDE.md "What Claude should do in this repo".

Next concrete action when resources are available: spike block 1 (TRUD registration and dm+d load into DuckDB), then block 4 (SPC acquisition), at which point the fixture corpus is replaced by the resident-tier extraction feeding the same Corpus.
