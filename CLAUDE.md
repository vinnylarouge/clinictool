# pullback

A per-case medication suitability workbench for UK clinicians. Research aid, not a recommender.

Name rationale (rename freely): a suitability query is a cone over a diagram of distributed authorities (formulary, SPCs, specialist sources); the answer we want is the limit, and the projection maps are the provenance links. The app computes pullbacks over the medicines information landscape.

## Mission

Given a case (freeform patient history plus a query such as "suitability of clarithromycin") render a dossier that joins every relevant published constraint across the distributed UK sources, surfaces where sources flag problems and why, surfaces source-attested alternatives raised during research, and keeps the dossier current per patient as sources update. A secretary, not a registrar: it researches, files, cites, and notices changes; it never decides. Two retrieval tiers serve this: a local digitised reference bank traversed by a recursive language-model pattern, and dispatched research agents over the decentralised live sources (docs/02-architecture.md).

## Hard invariants (do not relax without a decision-log entry)

1. **Provenance or it does not ship.** Every rendered claim carries (source, document version or retrieval date, span locator, URL). No orphan text.
2. **The verdict sentence is never generated.** The system surfaces negative findings in the source's voice ("the SPC lists severe renal impairment as a contraindication") laid alongside mechanical facts about the case ("this case's eGFR is 24, within that band"), each independently cited. It may surface alternatives only where the adjacency is itself attested in a source: a guideline names the alternative, an SPC names it, an SPS Q&A names it, or a mechanical class relation is displayed and labelled as mechanical. It never composes the conjunction into advice: no "avoid", "unsuitable for this patient", "use Y instead", and no ranking of alternatives. Source-voiced findings plus displayed arithmetic, juxtaposed; the clinician utters the verdict. This is the regulatory load-bearing wall (see docs/03-regulatory.md).
3. **LLM as typesetter, not oracle.** Any generated prose must be composed exclusively from retrieved spans, with citation enforcement checked mechanically. No open-book generation in the clinical surface.
4. **Raw case text never leaves the device.** Freeform patient history is accepted as input but is parsed locally into the structured facet schema; only the minimised, coded projection (age, sex where relevant, eGFR and similar values, dm+d-coded medicines, coded conditions) may be sent to any remote model or research agent. Narrative history is encrypted at rest, deletable on command, and keyed by a doctor-side alias, never by patient identifiers. See docs/03-regulatory.md before relaxing anything here.
5. **Licence-aware ingestion.** Sources are ingested only via routes listed as permitted in docs/01-sources.md. No scraping against terms. Where content is view-only, we link out rather than ingest.
6. **Dossiers are derivations, not documents.** Every dossier records the exact corpus snapshot and case version it was derived from, and re-derives with a visible diff when either changes. Staleness is displayed, never hidden.

## Repo layout

```
CLAUDE.md            this file
docs/00-scope.md     problem, users, v0 cut, non-goals, kill criteria
docs/01-sources.md   the source registry: access routes, licence reality, v0 status
docs/02-architecture.md  entity spine, constraint algebra, synthesis, storage
docs/03-regulatory.md    the device boundary, clinical safety, IP, data protection
docs/04-spike-plan.md    ten evening-blocks to a demo and a go/no-go memo
docs/05-open-questions.md  threads requiring a human decision
docs/decision-log.md     dated decisions with rejected alternatives
src/                 (empty until spike day 1)
data/                gitignored; raw source documents with content hashes
```

## Tech defaults (boring on purpose)

- Python 3.12, uv for env management.
- DuckDB for the entity spine and constraint store; raw documents kept as files with SHA-256 content hashes in `data/raw/`.
- Parsing: lxml/selectolax for dm+d XML; pdfplumber or pymupdf for SPC PDFs where HTML is unavailable.
- v0 UI is a single static HTML render (Jinja template) per case. No framework until the matrix view earns one.
- Tests: pytest; golden-file tests on constraint extraction per drug.

## Conventions

- UK English throughout. Licence is the noun, license the verb.
- No em-dashes in any document or string. Use commas, colons, parentheses.
- Every schema type that touches a claim includes the `Provenance` record (docs/02-architecture.md).
- Decisions go in `docs/decision-log.md` (create on first decision): date, decision, alternatives rejected, who decided.

## Current phase

**Typed core slice in place; gated data sources not yet wired.** The domain model (`src/pullback/model/`), guard engine, evaluator, attested-alternatives rule, dossier diff, and Jinja matrix renderer are implemented and tested (`uv run pytest`, 39 tests). The flagship dossier renders end to end from an in-repo fixture corpus: `uv run pullback render-flagship` writes `out/flagship.html`. The fixtures are illustrative placeholders (clearly marked, with an honesty banner in the render), standing in only where gated sources are needed (decision-log D6).

Next concrete action: TRUD account registration and dm+d download (docs/04-spike-plan.md, block 1), then SPC acquisition (block 4). Real adapters emit the same `Constraint` objects into the same `Corpus` seam, so the evaluator and renderer do not change. Before writing ingestion code for any source, re-read its row in docs/01-sources.md and confirm the access route is still accurate.

## What Claude should do in this repo

- Treat docs/00 to 05 as the spec. Challenge them where they are wrong, but record challenges in the decision log rather than silently diverging.
- When implementing, prefer the smallest vertical slice that exercises provenance end to end over breadth of sources.
- When uncertain whether a feature crosses the device boundary, stop and flag it. The boundary analysis lives in docs/03-regulatory.md and is a design constraint, not an afterthought.
- Vincent's known failure mode is breadth without finished artefacts. The spike plan exists to force closure. Resist scope additions before the flagship case renders end to end.
