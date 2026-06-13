"""pullback: a per-case medication suitability workbench for one UK clinician.

A research secretary, not a registrar: it researches, joins, cites, and notices
changes across the distributed UK medicines sources. It never decides.

See CLAUDE.md and SPEC.md for the load-bearing invariants. The most important,
encoded structurally in this package:

- Provenance or it does not ship (every claim carries a Provenance record).
- The verdict sentence is never generated (the evaluator never composes advice).
- Raw case narrative never leaves the device (CaseProjection has no narrative
  or alias field, so a leak is impossible at the type level).
- The two empty states stay distinct (AxisResult separates checked-clear from
  not-yet-reported).
"""

__version__ = "0.0.1"
