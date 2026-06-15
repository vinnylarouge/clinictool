"""Dossier -> HTML matrix.

One screen: case sketch pinned top, candidate drugs as columns, axes as rows.
Cells carry the retrieved span or link-out, source badge, authority tier,
retrieval date, and (where firing) the flagged-finding juxtaposition: the
source's own words beside the mechanical case fact that tripped the guard, each
independently cited. Distinct rendering for checked-clear vs not-yet-checked.
The footer prints the oldest retrieval date prominently. Nothing is more than
one click from its origin (SPEC section 5.8).

The renderer NEVER composes a verdict. It lays cited statements side by side and
labels mechanical relations as mechanical. The clinician utters the verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pullback.eval.alternatives import AttestedAlternative, attested_alternatives
from pullback.model.constraint import AxisResult, Constraint, LinkOut, Rule, Span
from pullback.model.dossier import Dossier, DossierDiff
from pullback.model.facets import Axis, Case

_TEMPLATE_DIR = Path(__file__).parent / "templates"

DISCLAIMER = (
    "Research aid for healthcare professionals. Collates published sources with "
    "links and retrieval dates. Not a substitute for the source documents or for "
    "clinical judgement. Verify against the linked originals before acting."
)

_AUTHORITY_LABEL = {1: "Regulator", 2: "Formulary", 3: "Specialist", 4: "Research"}


@dataclass
class _PayloadView:
    kind: str  # "span", "rule", "linkout"
    text: str
    label: str
    url: str
    note: str


@dataclass
class _ConstraintView:
    payload: _PayloadView
    source: str
    document_id: str
    version: str
    retrieved_at: str
    locator: str
    url: str
    authority: str
    convention: str | None
    fired_explanation: str  # the mechanical case fact, separately attributable
    is_alternative: bool
    is_mechanical_alt: bool


@dataclass
class _CellView:
    axis_label: str
    state: str  # "findings", "checked_clear", "pending", "unreported"
    constraints: list[_ConstraintView]
    checked_sources: list[str]
    pending_sources: list[str]
    changed: bool


def _payload_view(c: Constraint) -> _PayloadView:
    p = c.payload
    if isinstance(p, Span):
        return _PayloadView("span", p.text, "", "", "")
    if isinstance(p, Rule):
        return _PayloadView("rule", p.statement, p.label, "", "")
    if isinstance(p, LinkOut):
        return _PayloadView("linkout", "", p.label, p.url, p.note)
    raise TypeError(f"unknown payload {p!r}")  # pragma: no cover


def _constraint_view(c: Constraint, case: Case) -> _ConstraintView:
    from pullback.eval.alternatives import MECHANICAL_SOURCES
    from pullback.model.constraint import Kind

    outcome = c.guard.evaluate(case)
    is_alt = c.kind is Kind.ALTERNATIVE
    return _ConstraintView(
        payload=_payload_view(c),
        source=c.provenance.source,
        document_id=c.provenance.document_id,
        version=c.provenance.version,
        retrieved_at=c.provenance.retrieved_at.isoformat(),
        locator=c.provenance.locator,
        url=c.provenance.url,
        authority=_AUTHORITY_LABEL[c.authority.value],
        convention=c.convention,
        fired_explanation=outcome.explanation,
        is_alternative=is_alt,
        is_mechanical_alt=is_alt and c.provenance.source in MECHANICAL_SOURCES,
    )


def _cell_state(result: AxisResult) -> str:
    if result.constraints:
        return "findings"
    if result.is_pending:
        return "pending"
    if result.is_checked_clear:
        return "checked_clear"
    return "unreported"


def _cell_view(result: AxisResult, case: Case, changed: bool) -> _CellView:
    return _CellView(
        axis_label=result.axis.value.replace("_", " "),
        state=_cell_state(result),
        constraints=[_constraint_view(c, case) for c in result.constraints],
        checked_sources=list(result.checked_sources),
        pending_sources=list(result.pending_sources),
        changed=changed,
    )


def render_dossier(
    dossier: Dossier,
    case: Case,
    *,
    diff: DossierDiff | None = None,
) -> str:
    """Render the dossier to a single self-contained HTML string."""

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
    )
    template = env.get_template("dossier.html.j2")

    drugs = list(dossier.query.candidates)
    axes = dossier.query.axes_or_all()

    changed_keys: set[tuple[str, Axis]] = set()
    if diff is not None:
        for cell in diff.changed:
            changed_keys.add((cell.drug.code, cell.axis))

    # Build the matrix: rows = axes, columns = drugs.
    rows = []
    for axis in axes:
        row = {"axis_label": axis.value.replace("_", " "), "cells": []}
        for drug in drugs:
            result = dossier.results.get(drug, {}).get(axis)
            if result is None:
                result = AxisResult(axis=axis, constraints=(), checked_sources=())
            changed = (drug.code, axis) in changed_keys
            row["cells"].append(_cell_view(result, case, changed))
        rows.append(row)

    # Attested alternatives (across the whole corpus reachable from the dossier).
    all_constraints: list[Constraint] = [
        c
        for axes_map in dossier.results.values()
        for res in axes_map.values()
        for c in res.constraints
    ]
    alternatives: list[AttestedAlternative] = list(
        attested_alternatives(all_constraints, case)
    )

    # Honesty banner: are any cited documents illustrative fixtures?
    fixture_data = any(
        "FIXTURE" in c.provenance.version.upper() for c in all_constraints
    )

    return template.render(
        dossier=dossier,
        case=case,
        drugs=drugs,
        rows=rows,
        alternatives=alternatives,
        disclaimer=DISCLAIMER,
        diff=diff,
        has_diff=bool(diff and diff.has_changes),
        fixture_data=fixture_data,
    )
