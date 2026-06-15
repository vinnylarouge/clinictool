# Interface feedback: pullback v0

Reviewed against the flagship dossier render (`out/flagship.html`) and the onboarding wizard (`onboarding.html.j2`), reading every template, renderer, and model type. Perspective: a clinician who needs to use this tool mid-workflow, under time pressure, with high stakes.

---

## 1. First impressions and onboarding

The onboarding page is one of the strongest parts. The "How you will use it" card is genuinely well-written: it explains the three-step workflow in the clinician's language, not the developer's. The legend ("Reading a cell") is the right idea, explaining the novel semiotics before the user encounters them. Two problems:

**The onboarding and the dossier are visually disconnected.** The onboarding page teaches a vocabulary (badges, fired findings, checked vs. pending) using prose, but the dossier page has no inline affordances for the same vocabulary. A clinician who reads the onboarding once, then opens a dossier three days later, has to remember what the grey minus sign means versus the green tick versus the amber ellipsis. These symbols are learned and then assumed, with no hover tooltip, no inline legend, no contextual help. The onboarding page should not be a separate ceremony; its legend should be *inside* the dossier, collapsible, so a user can re-read it in situ.

**The disclaimer appears three times.** Once as a blue banner at the top, once as grey text at the bottom, and the onboarding page has it in both positions too. Repeating the same sentence verbatim three times across two pages trains the eye to skip it. If the disclaimer is load-bearing (and it is, given the regulatory boundary), show it prominently once, at the top, and do not repeat it verbatim elsewhere. The footer can carry it as a shorter, quieter reference ("See disclaimer above").

**"pullback" as a title means nothing to a clinician.** The h1 says "Welcome to pullback" and the dossier says "pullback dossier". The name is an inside joke about category theory. The user does not know what a pullback is and will not be charmed by it. If the name is staying, at least lead with the value proposition: "pullback: medication suitability research" or just "Medication suitability dossier" on the dossier page. The alias ("AF-macrolide-review") is more informative than the product name.

## 2. The dossier matrix: visual hierarchy

The matrix is the core interface. It does many things right: sticky headers, clear drug names as columns, axis labels as rows, distinct cell states. The information architecture (drugs x axes) is the right primitive. But the hierarchy inside each cell is flat, and when a cell has multiple findings, it becomes a wall of text with no scannable structure.

**Findings within a cell lack visual weight differentiation.** Consider the "interaction" cell for azithromycin: it contains a Regulator finding (the SPC interaction note), a Specialist attested alternative, and a Research mechanical relation. These are three fundamentally different kinds of information, but they look nearly identical: a small badge, a block of quoted text, and a line of grey metadata. The badge colours are distinguishable (navy, green, grey-brown) but at 0.68rem they are tiny and the labels are abbreviated. A clinician scanning the matrix cannot tell at a glance which cells contain a finding that fires against this patient versus which cells contain informational context. The fired findings (the ones with the red "case fact" line) are the most clinically urgent, but they have the same visual weight as everything else.

**Suggestion: separate fired findings from context.** Fired findings (where the guard matched this case) should be visually dominant: a subtle red or amber left border, or a tinted background, rather than sharing the same grey `border-left: 3px solid var(--line)` as non-fired findings. The red `mechfact` text is a start, but it reads as an annotation rather than the primary signal. The finding that this patient's CrCl is below the dose threshold should be the loudest thing in that cell, not a quiet red footnote below the quote.

**The "case fact" label is unclear.** The prefix "case fact:" in italicised grey before the red text reads as technical jargon. A clinician would understand "applies to this patient:" or even just a bold "This patient: CrCl 22 mL/min < 30". The current phrasing forces the reader to decode "case fact" as "the reason this is relevant to the patient I am looking at", which is a non-obvious mapping.

**The axis column is too narrow for its content.** At `width: 9rem`, axis labels like "contraindication" or "dose renal" fit, but the column has no breathing room. The capitalisation via `text-transform: capitalize` is fine, but "qt risk" becomes "Qt Risk", which looks odd; "QT risk" would be more natural. Consider a mapping for display names rather than mechanically capitalising the enum value.

## 3. Cell states: the three empties

The distinction between checked-clear, pending, and not-yet-checked is one of the most important design decisions in the system (invariant 7). The current rendering:

- **Checked clear:** green tick + "checked, no constraint (emc)" 
- **Pending:** amber ellipsis + "checking (sps)"
- **Not yet checked:** grey minus + "not yet checked"

This is good in principle but fragile in practice. The three states look too similar at scan speed: a small coloured symbol followed by a short line of grey text. When the matrix has 14 rows and 2 columns, the clinician's eye needs to immediately distinguish "safe" (checked clear) from "unknown" (not yet checked) from "wait" (pending). These are dramatically different clinical meanings, but their visual presentations differ only in a single character and a subtle colour shift.

**Suggestion: use background tinting for empty cells, not just text.** A checked-clear cell could have a very faint green wash (`background: #f0faf5`). A not-yet-checked cell could have a faint warm grey or a subtle dashed border to communicate incompleteness. A pending cell could pulse gently or have a dotted border. The goal is to make the matrix scannable from arm's length: green cells are done, grey cells are gaps, amber cells are in-flight.

## 4. The case bar

The facet display at the top (`age 78 | sex f | weight 54.0 kg | eGFR 24.0 mL/min/1.73m2 | ...`) is functionally correct but reads as a data dump rather than a patient sketch.

**"sex f" is too terse.** The value `f` comes straight from the enum. Display "Female" or "F" with the word visible on hover. Similarly, "hepatic none" would read better as "Hepatic: normal" or "No hepatic impairment".

**Co-meds have no visual distinction from other facets.** Apixaban and sertraline are displayed as `co-med apixaban` in the same grey pill as `age 78`. But the co-meds are the facts most likely to trigger interaction findings. They should stand out: a slightly different pill colour, or an icon, or grouping them under a subheading. When a clinician glances at the case bar, they need to see "this patient is on apixaban" as quickly as they see "this patient has an eGFR of 24".

**The renal convention banner is excellent but could be integrated better.** The grey banner explaining eGFR vs. CrCl is one of the strongest pieces of clinical communication in the interface: it acknowledges a real source of confusion and explains the system's handling transparently. But as a standalone banner between the case bar and the matrix, it breaks the reading flow. Consider making this a tooltip or expandable note attached to the eGFR/CrCl facets themselves, so it is available on demand rather than always consuming vertical space.

## 5. Provenance and citation density

The provenance metadata per finding is thorough (source, locator, version, retrieval date, link). It is also dense: `emc . SPC 4.5 (illustrative) . FIXTURE . retrieved 2026-06-13` is a lot of text at 0.72rem for information that most of the time is not the focus of attention.

**Suggestion: collapse metadata into a single linked source name, expandable on click.** The primary citation display could be just the linked source name and retrieval date: `emc, retrieved 2026-06-13`. The locator, version, and document ID could appear on hover or in a popover. This reduces per-finding visual noise by roughly 40% while preserving full provenance on demand. The current approach treats every citation as if the user is auditing provenance on every read, but the common case is scanning for clinical signals.

**The "FIXTURE" version tag is visually noisy.** In the demo render, every finding says "FIXTURE" in the metadata. This is correct for honesty, but combined with the fixture banner at the top, it creates visual clutter. Consider rendering fixture versions in a quieter way (lighter colour, smaller text) so the eye skips them during scanning. The banner already declares the data is illustrative; repeating "FIXTURE" on every line is redundant signalling.

## 6. Alternatives display

The attested-alternatives section at the bottom of the matrix is well-positioned and correctly caveated. The "Not ranked, not preferred, not advice" disclaimer is the right tone. Two issues:

**Alternatives appear in two places.** In-cell (within the azithromycin interaction column) and in the summary block at the bottom. This duplication is intentional (the cell shows the context, the summary collects them), but the visual connection between the two is not obvious. When a clinician reads the summary block and sees "azithromycin, source-attested, Specialist", they cannot easily trace back to which cell this came from without scanning the entire matrix. Consider linking the summary entry to its source cell, or adding the axis label to the summary entry.

**The "mechanical" vs "attested" distinction could use colour.** The `altlabel` badges distinguish these with different background colours (green-tinted for attested, grey for mechanical), which is correct. But the words "mechanical" and "attested" are clinical-informatics jargon. Consider "named by source" vs. "same drug class" as plain-English labels, or at minimum provide a tooltip explaining what "mechanical" means.

## 7. Typography and polish

**The font stack is system fonts, which is correct.** No web fonts to load, no FOUT, instant render. Good.

**Line height of 1.4 is slightly tight for the density of clinical text.** The quoted SPC passages are multi-sentence blocks that benefit from more vertical breathing room. Consider 1.55 or 1.6 for the `.quote` class specifically.

**No print stylesheet.** A clinician might print a dossier. The current CSS has no `@media print` rules, so sticky headers, background colours on badges, and layout all depend on browser defaults. At minimum, badge colours should be forced visible in print, the table should not break across pages mid-row, and the disclaimer banner should appear on every printed page.

**No dark mode.** Not urgent, but the CSS variables are already in place in `:root`, so adding a `@media (prefers-color-scheme: dark)` block would be low effort and would benefit clinicians using the tool in low-light environments (night shifts, on-call rooms).

## 8. Navigation and orientation

**There is no navigation.** The dossier is a single page, which is fine for v0, but there is no "back to case list" link, no breadcrumb, no sense of where this page sits in a workflow. The header says "pullback dossier . AF-macrolide-review" but does not link to anything. For the single-case demo this is acceptable, but as soon as a second case exists, the lack of navigation will be disorienting.

**The header metadata is developer-facing.** "case flagship-001 v . dossier dossier-flagship-001-v1 . corpus snapshot snap-e9cbaae29f043c84 . derived 2026-06-13" is useful for debugging but meaningless to a clinician. The clinician cares about: which patient (the alias), which drug query, how fresh the data is. Consider restructuring the header: the alias and query as the primary information, the dossier/corpus/derivation metadata as a collapsible "technical details" block.

**There is a bug in the version display.** The header shows "case flagship-001 v" with a trailing space and no version number. The template has `v{{ case.case_version }}` but `case.version` is an `int` (value `1`), and the property name in `Case` is `version`, yet the template references `case.case_version`. The attribute name mismatch means the version is silently rendered as empty. This is a code bug, not just a display issue: `case_version` is a different attribute from `version`.

## 9. Interaction patterns

**The wizard's radio-button provider selection is well-done.** The provider cards with data-handling notes are the right pattern: the user sees exactly what data goes where before committing. The live show/hide of the API key field based on provider selection is responsive and clear.

**The wizard has no progress indicator.** It is a single-page form, so arguably a progress bar is unnecessary, but the user does not know if there is a "next step" after saving. The success state ("You are set up") is clear, but the transition from form to success is a full-page reload with no animation or transition. For a form that handles a secret (the API key), the user might wonder whether the save actually worked. A brief visual confirmation (a checkmark animation, a green flash) would increase confidence.

**The advanced fields (base URL, model) are correctly hidden in a details/summary.** Good for not overwhelming the non-technical user. The placeholder values updating on provider selection is a nice touch.

## 10. What would make it feel clinical-grade

The current interface feels like a competent developer prototype: functionally correct, visually clean, but not yet tuned for the cognitive demands of clinical work. To feel like a tool a clinician would trust and reach for under pressure:

**Add a "severity at a glance" stripe.** The leftmost column (axis labels) could carry a background tint or an icon summarising the cell state across all drugs in that row: red if any cell has a fired finding, green if all are clear, grey if any are unchecked. This gives the clinician a single-column scan to find the rows that need attention.

**Anchor the case bar.** The facet pills scroll away as the user reads the matrix. The case context (especially renal function and co-meds) should be visible at all times, perhaps as a sticky bar below the header, because the clinician is constantly cross-referencing "does this threshold apply to my patient's eGFR?".

**Timestamp the dossier derivation prominently.** The "derived 2026-06-13" is buried in the header metadata. If a clinician reopens a dossier the next day, they need to see "this was derived 18 hours ago" at a glance, preferably as a relative time ("derived today" or "derived 3 days ago") with the absolute date on hover.

**Consider a two-drug comparison view that highlights differences.** The matrix already supports two drugs as columns (clarithromycin vs. azithromycin), but differences between the two are not highlighted. A cell where clarithromycin has a fired finding but azithromycin does not could carry a subtle visual signal: "this axis is where these two drugs diverge for this patient". The clinician's core question is "is the alternative safer on the dimensions that matter?", and the current matrix requires them to assemble that answer row by row.

## Summary

The architectural decisions are right: drugs as columns, axes as rows, three distinct empty states, provenance on everything, alternatives only where attested. The regulatory care is visible in the design and feels load-bearing, not decorative. The core weaknesses are all in the visual hierarchy: fired findings do not visually dominate, empty states are not scannable, metadata is uniformly dense rather than progressive, and the case context scrolls away. These are all fixable with CSS and template changes, without touching the model or evaluation layers.
