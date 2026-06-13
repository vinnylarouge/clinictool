# 04. Spike plan

Ten evening-sized blocks, two weeks at tinkering pace. The point is closure: a rendered flagship dossier and a one-page go/no-go memo, even if half the cells are link-outs.

## Drug set (ten, chosen to stress different axes)

apixaban, sertraline, clarithromycin, azithromycin, ramipril, metformin, ibuprofen, amitriptyline, alendronic acid, nitrofurantoin.

Rationale: clarithromycin vs azithromycin gives the flagship comparison (CYP3A4/P-gp vs not, QT both); apixaban and sertraline are the co-medications; metformin and nitrofurantoin have hard renal cliffs at specific eGFR values, perfect for facet-guard extraction; amitriptyline lights anticholinergic burden and STOPP criteria; ibuprofen tests interaction text against both an anticoagulant and an ACE inhibitor; alendronic acid tests administration-constraint prose.

## Blocks

Twelve now, because the freeform parser and the first real agent earn their own blocks. Still evening-sized; still aimed at one rendered, re-derivable flagship dossier plus a go/no-go memo.

1. **TRUD and spine.** Register, download dm+d, load XML into DuckDB. Deliverable: `resolve("apixaban")` returns the VTM and its VMPs/AMPs; `excipients(amp)` and `price(vmpp)` work.
2. **Name resolution.** Trigram index over dm+d names plus abbreviation table. Deliverable: the ten drugs resolve from free text, including two misspellings.
3. **Freeform parser, local.** Small local model extracts the facet valuation from realistic history text and grounds medicine mentions to dm+d, conditions to coded terms; unparseable items flagged not guessed; output shown for confirmation. Deliverable: the flagship history, pasted as a paragraph, yields the correct `Case` object with apixaban and sertraline grounded and eGFR 24 captured, and nothing but the coded projection is marked transmissible.
4. **SPC acquisition.** Manually download SPCs for the ten drugs (emc or MHRA portal), store in `data/raw/` with hashes and source URLs recorded. Deliverable: registry of ten documents with metadata.
5. **Section tree.** Decompose each SPC along the mandated heading skeleton into the ingest-time summary tree (leaves are spans with offsets, internal nodes summarise, pointers retained). Deliverable: golden-file tests per drug for sections 4.1, 4.2, 4.3, 4.5, 4.6, 6.1; per-publisher quirks logged.
6. **Recursive descent.** Query-time descent over the tree returning cited spans per axis, with the descent path logged. Deliverable: (flagship case, clarithromycin, interactions) descends 4.5 and returns the apixaban- and sertraline-relevant spans without reading unrelated branches.
7. **Facet guards.** Pattern rules over 4.2 (renal thresholds) and 4.5 (co-medication and class matches) attach guards to spans. Deliverable: metformin/nitrofurantoin renal cliffs fire at the right eGFR band edges; clarithromycin's interaction spans fire against the flagship's co-meds; each carries correct offsets and authority tier.
8. **Ambassador agent, one source.** Build one real dispatched agent over a single well-structured source (SPS Medicine Supply Tool, or a CredibleMeds category resolver), receiving only the projection, returning `Constraint` records, reporting pending/done, returning explicit "nothing found" when empty. Deliverable: the agent contributes a real cited cell to the flagship dossier, and the projection sent is inspected to confirm no narrative leaked.
9. **Link-out adapter.** Templated deep links per drug for the remaining decentralised sources (UKTIS, NEWT, NAPOS, Liverpool, Renal Drug Database). Deliverable: link rows render for all ten drugs.
10. **Case store, evaluator, alternatives.** Persist cases/dossiers; constraint filtering and axis grouping; flagged-finding construct (source span beside mechanical case fact); attested-alternative construct (ATC sibling labelled mechanical, plus any SPC/DSU-named alternative). Deliverable: flagship case evaluates against clarithromycin and azithromycin, azithromycin surfaced as an attested alternative with its adjacency cited, never as a recommendation.
11. **Render and diff.** Jinja one-screen matrix, two drug columns, provenance footers, authority badges, oldest-retrieval banner, distinct empty states (checked-clear vs not-checked). Manual re-derive shows a diff when a re-fetched SPC or new DSU issue changes a cited document. Deliverable: the dossier on the desk; re-running after swapping in a modified SPC shows the change highlighted.
12. **External eyes and memo.** Walk the design-partner clinician through the flagship dossier with their own real (suitably handled) case mix. Capture: what is missing, wrong, what they do instead, whether they would use it next week, and specifically whether the flagged-findings-plus-alternatives presentation gives them what a recommendation would without crossing into one. Write the go/no-go memo and seed further decision-log entries.

## Exit criteria

- Go signals: the external reviewer identifies the dossier as faster than their current join for at least one realistic case; SPC extraction held at roughly 95 percent clean sections across the ten; the freeform parser handled their real history text without a poisoning error (or flagged what it could not parse); the one ambassador agent returned a genuinely useful cited cell; the flagged-findings-plus-alternatives layout gave them what they wanted without reading as a recommendation; at least one cell surprised the reviewer (the excipient row and the supply row are the likeliest candidates).
- No-go or pivot signals: parsing brittleness dominating the effort (pivot to the rules-engine cut per docs/00-scope.md); the freeform parser unreliable enough that the doctor would not trust the projection (fall back to a structured intake form, accepting the workflow cost); the agent loop too flaky to be worth the decentralised tier (fall back to link-outs only); reviewer indifference ("I'd still just open the BNF") on every case tried; an unforeseen licensing block on even view-and-link usage.

## Deliberately deferred

The clinical-surface typesetter (generated prose, even citation-enforced): the bare cited matrix is the v0 deliverable and the trustworthy mode. BNF application paperwork (start it in parallel, but it gates nothing in the spike). Auto-refresh subscriptions (the manual re-derive-with-diff in block 11 proves the mechanism; the cron comes later). Multi-source agent fan-out (one real agent in block 8 proves the loop; the rest stay link-outs). Multi-user or cloud anything (single doctor, single machine). The full eval dataset (it becomes the centrepiece of v1 if the spike goes; see docs/05-open-questions.md).
