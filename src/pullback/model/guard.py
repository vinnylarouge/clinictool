"""Guards: small serialisable typed predicates, not opaque lambdas.

A guard renders WHY it fired ("case eGFR 24 mL/min < 30") so the cell is
explainable and the firing is auditable (SPEC section 4). Guards are an AST of
frozen dataclasses with a stable JSON form, because a Guard is persisted as
guard_json in the constraint cache and must round-trip exactly.

Renal convention note: a threshold over Field.EGFR and one over Field.CRCL are
distinct guards. The Field a comparison carries IS the convention the source
stated; the system never auto-converts between eGFR and CrCl (invariant in the
Case docstring). The convention surfaces in the explanation and via
GuardExpr.convention().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pullback.model.dmd import DmdLevel, DmdRef
from pullback.model.facets import Case, Field, Impairment

if TYPE_CHECKING:  # pragma: no cover
    pass


@dataclass(frozen=True)
class GuardOutcome:
    fired: bool
    explanation: str  # human-readable, for the cell: "case eGFR 24 mL/min < 30"


# Field display metadata for explanations.
_FIELD_LABEL = {
    Field.AGE: "age",
    Field.EGFR: "eGFR",
    Field.CRCL: "CrCl",
    Field.WEIGHT: "weight",
    Field.HEPATIC: "hepatic impairment",
}
_FIELD_UNIT = {
    Field.AGE: "years",
    Field.EGFR: "mL/min/1.73m2",
    Field.CRCL: "mL/min",
    Field.WEIGHT: "kg",
    Field.HEPATIC: "",
}
# The renal conventions, for convention() reporting.
_CONVENTION = {Field.EGFR: "eGFR", Field.CRCL: "CrCl"}


def _field_value(case: Case, fld: Field) -> Any:
    match fld:
        case Field.AGE:
            return case.age_years
        case Field.EGFR:
            return case.egfr
        case Field.CRCL:
            return case.crcl
        case Field.WEIGHT:
            return case.weight_kg
        case Field.HEPATIC:
            return case.hepatic
    raise ValueError(f"unknown field {fld!r}")  # pragma: no cover


def _fmt(fld: Field, value: Any) -> str:
    unit = _FIELD_UNIT[fld]
    label = _FIELD_LABEL[fld]
    if isinstance(value, Impairment):
        return f"{label} {value.value}"
    if unit:
        return f"{label} {value} {unit}"
    return f"{label} {value}"


class GuardExpr:
    """Base for all guard expressions.

    Concrete subclasses: Lt, Le, Ge, Gt (Field comparisons), CoMed, HasFlag,
    Pregnant, Breastfeeding, HasIntolerance, Always, And, Or.
    """

    def evaluate(self, case: Case) -> GuardOutcome:  # pragma: no cover - abstract
        raise NotImplementedError

    def convention(self) -> str | None:
        """The renal convention this guard is stated in, if any.

        Returns "eGFR" or "CrCl" for a comparison over a renal field, else None.
        Composite guards report a convention only if exactly one is present.
        """

        return None

    def to_dict(self) -> dict[str, Any]:  # pragma: no cover - abstract
        raise NotImplementedError


# ----- numeric / ordinal comparisons over a Field -----

# Ordinal rank for Impairment, so Ge/Gt etc. work on hepatic severity too.
_IMPAIRMENT_RANK = {
    Impairment.UNKNOWN: -1,
    Impairment.NONE: 0,
    Impairment.MILD: 1,
    Impairment.MODERATE: 2,
    Impairment.SEVERE: 3,
}


def _as_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Impairment):
        rank = _IMPAIRMENT_RANK[value]
        return None if rank < 0 else float(rank)
    return float(value)


@dataclass(frozen=True)
class _Cmp(GuardExpr):
    field: Field
    value: float
    _op_symbol = "?"

    def _test(self, lhs: float, rhs: float) -> bool:  # pragma: no cover - abstract
        raise NotImplementedError

    def evaluate(self, case: Case) -> GuardOutcome:
        raw = _field_value(case, self.field)
        lhs = _as_number(raw)
        if lhs is None:
            return GuardOutcome(
                fired=False,
                explanation=f"case {_FIELD_LABEL[self.field]} unknown, guard "
                f"({self._op_symbol} {self.value}) not evaluable",
            )
        fired = self._test(lhs, float(self.value))
        rhs_display = self._rhs_display()
        return GuardOutcome(
            fired=fired,
            explanation=f"case {_fmt(self.field, raw)} {self._op_symbol} {rhs_display}",
        )

    def _rhs_display(self) -> str:
        if self.field is Field.HEPATIC:
            # value encodes an Impairment rank; show its name where possible.
            for imp, rank in _IMPAIRMENT_RANK.items():
                if rank == int(self.value):
                    return imp.value
        return str(self.value)

    def convention(self) -> str | None:
        return _CONVENTION.get(self.field)

    def to_dict(self) -> dict[str, Any]:
        return {"op": type(self).__name__, "field": self.field.value, "value": self.value}


@dataclass(frozen=True)
class Lt(_Cmp):
    _op_symbol = "<"

    def _test(self, lhs: float, rhs: float) -> bool:
        return lhs < rhs


@dataclass(frozen=True)
class Le(_Cmp):
    _op_symbol = "<="

    def _test(self, lhs: float, rhs: float) -> bool:
        return lhs <= rhs


@dataclass(frozen=True)
class Ge(_Cmp):
    _op_symbol = ">="

    def _test(self, lhs: float, rhs: float) -> bool:
        return lhs >= rhs


@dataclass(frozen=True)
class Gt(_Cmp):
    _op_symbol = ">"

    def _test(self, lhs: float, rhs: float) -> bool:
        return lhs > rhs


# ----- predicates over the rest of the case -----


@dataclass(frozen=True)
class CoMed(GuardExpr):
    """Fires when the case is co-prescribed the named drug.

    Matches by dm+d code. Ingredient-level (VTM) guards match a co-med at any
    level that shares the VTM where that linkage is supplied; for v0 we match on
    exact code OR name fold, with the resolver expected to normalise to VTM.
    """

    ref: DmdRef

    def evaluate(self, case: Case) -> GuardOutcome:
        for co in case.co_meds:
            if co.code == self.ref.code or co.name.lower() == self.ref.name.lower():
                return GuardOutcome(
                    fired=True,
                    explanation=f"case is co-prescribed {co.name}",
                )
        return GuardOutcome(
            fired=False,
            explanation=f"case is not co-prescribed {self.ref.name}",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "op": "CoMed",
            "ref": {"code": self.ref.code, "level": self.ref.level.value, "name": self.ref.name},
        }


@dataclass(frozen=True)
class HasFlag(GuardExpr):
    flag: str

    def evaluate(self, case: Case) -> GuardOutcome:
        fired = self.flag in case.flags
        verb = "has" if fired else "does not have"
        return GuardOutcome(fired=fired, explanation=f"case {verb} flag '{self.flag}'")

    def to_dict(self) -> dict[str, Any]:
        return {"op": "HasFlag", "flag": self.flag}


@dataclass(frozen=True)
class HasIntolerance(GuardExpr):
    intolerance: str

    def evaluate(self, case: Case) -> GuardOutcome:
        fired = self.intolerance.lower() in (i.lower() for i in case.intolerances)
        verb = "reports" if fired else "does not report"
        return GuardOutcome(
            fired=fired, explanation=f"case {verb} intolerance '{self.intolerance}'"
        )

    def to_dict(self) -> dict[str, Any]:
        return {"op": "HasIntolerance", "intolerance": self.intolerance}


@dataclass(frozen=True)
class Pregnant(GuardExpr):
    def evaluate(self, case: Case) -> GuardOutcome:
        if case.pregnant is None:
            return GuardOutcome(False, "case pregnancy status unknown")
        return GuardOutcome(
            fired=case.pregnant,
            explanation="case is pregnant" if case.pregnant else "case is not pregnant",
        )

    def to_dict(self) -> dict[str, Any]:
        return {"op": "Pregnant"}


@dataclass(frozen=True)
class Breastfeeding(GuardExpr):
    def evaluate(self, case: Case) -> GuardOutcome:
        if case.breastfeeding is None:
            return GuardOutcome(False, "case breastfeeding status unknown")
        return GuardOutcome(
            fired=case.breastfeeding,
            explanation="case is breastfeeding"
            if case.breastfeeding
            else "case is not breastfeeding",
        )

    def to_dict(self) -> dict[str, Any]:
        return {"op": "Breastfeeding"}


@dataclass(frozen=True)
class Always(GuardExpr):
    """Unconditional fact: fires for every case (SPEC: Always() guard)."""

    def evaluate(self, case: Case) -> GuardOutcome:
        return GuardOutcome(fired=True, explanation="unconditional")

    def to_dict(self) -> dict[str, Any]:
        return {"op": "Always"}


# ----- composites -----


@dataclass(frozen=True)
class And(GuardExpr):
    parts: tuple[GuardExpr, ...]

    def __init__(self, *parts: GuardExpr) -> None:
        object.__setattr__(self, "parts", tuple(parts))

    def evaluate(self, case: Case) -> GuardOutcome:
        outcomes = [p.evaluate(case) for p in self.parts]
        fired = all(o.fired for o in outcomes)
        joined = " and ".join(o.explanation for o in outcomes)
        return GuardOutcome(fired=fired, explanation=f"({joined})")

    def convention(self) -> str | None:
        return _single_convention(self.parts)

    def to_dict(self) -> dict[str, Any]:
        return {"op": "And", "parts": [p.to_dict() for p in self.parts]}


@dataclass(frozen=True)
class Or(GuardExpr):
    parts: tuple[GuardExpr, ...]

    def __init__(self, *parts: GuardExpr) -> None:
        object.__setattr__(self, "parts", tuple(parts))

    def evaluate(self, case: Case) -> GuardOutcome:
        outcomes = [p.evaluate(case) for p in self.parts]
        fired = any(o.fired for o in outcomes)
        # Explain via the part(s) that fired, else the whole disjunction.
        firing = [o.explanation for o in outcomes if o.fired]
        joined = " or ".join(firing) if firing else " or ".join(o.explanation for o in outcomes)
        return GuardOutcome(fired=fired, explanation=f"({joined})")

    def convention(self) -> str | None:
        return _single_convention(self.parts)

    def to_dict(self) -> dict[str, Any]:
        return {"op": "Or", "parts": [p.to_dict() for p in self.parts]}


def _single_convention(parts: tuple[GuardExpr, ...]) -> str | None:
    conventions = {c for p in parts if (c := p.convention()) is not None}
    return next(iter(conventions)) if len(conventions) == 1 else None


# ----- the Guard wrapper -----


@dataclass(frozen=True)
class Guard:
    """Wraps a GuardExpr. Always() for unconditional facts (SPEC section 4)."""

    expr: GuardExpr

    def evaluate(self, case: Case) -> GuardOutcome:
        return self.expr.evaluate(case)

    def convention(self) -> str | None:
        return self.expr.convention()

    def to_dict(self) -> dict[str, Any]:
        return self.expr.to_dict()


# ----- deserialisation (guard_json -> Guard), so the cache round-trips -----

_CMP_OPS = {"Lt": Lt, "Le": Le, "Ge": Ge, "Gt": Gt}


def expr_from_dict(d: dict[str, Any]) -> GuardExpr:
    op = d["op"]
    if op in _CMP_OPS:
        return _CMP_OPS[op](field=Field(d["field"]), value=float(d["value"]))
    if op == "CoMed":
        r = d["ref"]
        return CoMed(DmdRef(code=r["code"], level=DmdLevel(r["level"]), name=r["name"]))
    if op == "HasFlag":
        return HasFlag(d["flag"])
    if op == "HasIntolerance":
        return HasIntolerance(d["intolerance"])
    if op == "Pregnant":
        return Pregnant()
    if op == "Breastfeeding":
        return Breastfeeding()
    if op == "Always":
        return Always()
    if op == "And":
        return And(*[expr_from_dict(p) for p in d["parts"]])
    if op == "Or":
        return Or(*[expr_from_dict(p) for p in d["parts"]])
    raise ValueError(f"unknown guard op {op!r}")


def guard_from_dict(d: dict[str, Any]) -> Guard:
    return Guard(expr_from_dict(d))
