"""Attested-alternative discovery (SPEC sections 3, 5.5; decision D1).

The rule the code enforces: an alternative drug appears if and only if a
retrieved source attests the adjacency (names it in the relevant clinical
context), rendered as that source's cited claim, OR the relation is a displayed
mechanical fact (ATC class sibling, same-VTM form variant) explicitly labelled
mechanical. Alternatives are NEVER ordered, scored, or preferred in the system's
own voice. Agents may retrieve candidates; they may never originate one. A
candidate with no citable adjacency is dropped, not shown unsourced.

This module therefore never sorts by preference. The only ordering it applies is
an alphabetical one, purely for stable rendering, and that is not a ranking.
"""

from __future__ import annotations

from dataclasses import dataclass

from pullback.model.constraint import Constraint, Kind
from pullback.model.dmd import DmdRef
from pullback.model.facets import Case

# Sources whose adjacency claim is a mechanical relation, not a clinical
# judgement. These must be labelled "mechanical" in the surface so the reader
# knows the system is displaying arithmetic about the drug graph, not advice.
MECHANICAL_SOURCES = frozenset({"dmd", "atc"})


@dataclass(frozen=True)
class AttestedAlternative:
    drug: DmdRef
    attestation: Constraint  # kind == ALTERNATIVE; carries the cited adjacency
    basis: str  # "source-attested" or "mechanical"

    @property
    def is_mechanical(self) -> bool:
        return self.basis == "mechanical"


def _basis(constraint: Constraint) -> str:
    return (
        "mechanical"
        if constraint.provenance.source in MECHANICAL_SOURCES
        else "source-attested"
    )


def attested_alternatives(
    constraints: list[Constraint],
    case: Case,
) -> tuple[AttestedAlternative, ...]:
    """Collect alternatives whose adjacency is attested, for this case.

    Only kind == ALTERNATIVE constraints qualify, and only when their guard
    fires for the case (an adjacency may be conditional, e.g. attested only in
    severe renal impairment). Deduplicated by drug code. Returned in alphabetical
    order for stable rendering; this ordering is explicitly NOT a preference.
    """

    found: dict[str, AttestedAlternative] = {}
    for c in constraints:
        if c.kind is not Kind.ALTERNATIVE:
            continue
        if not c.guard.evaluate(case).fired:
            continue
        # First attestation per drug wins; deterministic by input order.
        if c.drug.code not in found:
            found[c.drug.code] = AttestedAlternative(
                drug=c.drug, attestation=c, basis=_basis(c)
            )
    return tuple(sorted(found.values(), key=lambda a: a.drug.name.lower()))
