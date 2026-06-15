"""The domain model: typed adapters emitting one constraint type over a shared
index (the dm+d spine plus a facet vocabulary).

Adapters agree on the index and on nothing else; that is the entire integration
strategy (SPEC section 4).
"""

from pullback.model.constraint import (
    Authority,
    AxisResult,
    Constraint,
    Kind,
    LinkOut,
    Provenance,
    Rule,
    Span,
)
from pullback.model.dmd import Coded, DmdLevel, DmdRef
from pullback.model.dossier import Dossier, Query, diff
from pullback.model.facets import (
    Axis,
    Case,
    CaseProjection,
    Field,
    Impairment,
    Route,
    Sex,
    project,
)
from pullback.model.guard import (
    Always,
    And,
    Breastfeeding,
    CoMed,
    Ge,
    GuardExpr,
    GuardOutcome,
    Gt,
    Guard,
    HasFlag,
    HasIntolerance,
    Le,
    Lt,
    Or,
    Pregnant,
)

__all__ = [
    # dmd
    "Coded",
    "DmdLevel",
    "DmdRef",
    # facets
    "Axis",
    "Case",
    "CaseProjection",
    "Field",
    "Impairment",
    "Route",
    "Sex",
    "project",
    # guard
    "Always",
    "And",
    "Breastfeeding",
    "CoMed",
    "Ge",
    "GuardExpr",
    "GuardOutcome",
    "Gt",
    "Guard",
    "HasFlag",
    "HasIntolerance",
    "Le",
    "Lt",
    "Or",
    "Pregnant",
    # constraint
    "Authority",
    "AxisResult",
    "Constraint",
    "Kind",
    "LinkOut",
    "Provenance",
    "Rule",
    "Span",
    # dossier
    "Dossier",
    "Query",
    "diff",
]
