# 05. Open questions

Decisions only a human can make, ordered by how much they shape everything downstream.

1. **Licensing entity and timing.** Who applies for BNF syndication: you personally, OuLoPo, or via the university (the student/university route in the syndication terms suggests an academic pathway exists; a HAILab affiliation may be the lowest-friction signature)? Cyber security certification is a prerequisite for NICE-side syndication generally, so factor a Cyber Essentials cost/effort line into whichever entity applies. Apply during the spike, or only after a go decision?

2. **Project identity, given a named single user.** D5 fixes the build as a bespoke instrument for one clinician. The live question is what to harvest from it: the clean time-to-answer / error-rate study (with-tool vs without, pharmacist-adjudicated) still fits the Handa collaboration and produces a publication regardless of product outcome, but instrumenting for it from block 1 trades against pure build speed. Decide whether v0 carries that instrumentation or whether the study is a deliberate v1.

3. **Interactions content strategy.** Live with SPC 4.5 extraction plus link-outs indefinitely, push the BNF application as the upgrade path, budget for Stockley's via MedicinesComplete if this ever commercialises, or invest in the open research sets (DDInter/TWOSIDES) with explicit research-grade labelling? Each implies a different v1. Note the agent tier changes this calculus: a well-scoped Liverpool-checker agent may cover the highest-value interaction domains without any bulk licence.

4. **Parser-trust threshold.** Where is the line at which the freeform parser is reliable enough to trust the projection it sends outward? This is both a UX question (confirm-everything vs confirm-exceptions) and a safety one (a silently misread eGFR poisons the renal axis). The fallback is a structured intake form; the cost is the workflow friction the whole project exists to remove. Needs the design partner's real history text to calibrate.

5. **The agent tier and OuLoPo.** The ambassador-agent design (per-source scoped agents, projection-in, typed-constraints-out, citation-enforced, no origination) is structurally an OuLoPo coherence-over-sources harness with a clinical skin. Standalone tinkering repo, or an OuLoPo case study? Affects where the agent-framework effort goes and what gets written up.

6. **The eval dataset as a first-class artefact.** A published UK medicines case-join benchmark (cases with expected constraint hits and source-level answer keys, real cases suitably de-identified or synthetic analogues) would be citable, useful to others, and a finished object within weeks. Promote it from fallback to parallel deliverable? Interacts with question 2: the study and the benchmark share machinery.

7. **Open or closed.** dm+d-spine plus SPC-extraction plus link-out registry plus the agent framework is publishable as open source without touching any licensed content or any patient data. Doing so would also be the strongest possible footing for the BNF application (demonstrable provenance discipline). Any reason to keep it closed?
