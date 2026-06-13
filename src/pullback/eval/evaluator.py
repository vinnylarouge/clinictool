"""The evaluator: filter constraints by guard firing, group into AxisResults,
assemble a Dossier. It never scores, ranks, reconciles, or composes advice.

The Corpus is the pluggable seam. v0 uses an in-memory Corpus populated from
fixtures (or, later, from the resident-tier extraction and ambassador agents).
Real adapters land here without changing the evaluator: they all emit the same
Constraint objects (decision D4, two tiers over one schema).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date

from pullback.model.constraint import AxisResult, Constraint
from pullback.model.dmd import DmdRef
from pullback.model.dossier import Dossier, Query
from pullback.model.facets import Axis, Case


def _drug_matches(constraint_drug: DmdRef, candidate: DmdRef) -> bool:
    """Does a constraint about constraint_drug apply to candidate?

    v0: exact code match, or a name fold (the fixtures and resolver normalise
    ingredient names). Cross-level VTM/VMP/AMP linkage via the spine is a spine
    concern (SPEC section 5.1); the evaluator stays agnostic and trusts the
    DmdRefs it is handed.
    """

    if constraint_drug.code == candidate.code:
        return True
    return constraint_drug.name.strip().lower() == candidate.name.strip().lower()


@dataclass
class Corpus:
    """An in-memory bag of constraints plus per-cell reporting metadata.

    constraints: every candidate Constraint, across drugs and axes.
    checked: (drug_code, axis) -> sources that reported (so empty is meaningful).
    pending: (drug_code, axis) -> ambassador sources still running.
    """

    constraints: list[Constraint] = field(default_factory=list)
    checked: dict[tuple[str, Axis], tuple[str, ...]] = field(default_factory=dict)
    pending: dict[tuple[str, Axis], tuple[str, ...]] = field(default_factory=dict)

    def add(self, constraint: Constraint) -> None:
        self.constraints.append(constraint)

    def mark_checked(self, drug: DmdRef, axis: Axis, *sources: str) -> None:
        key = (drug.code, axis)
        existing = self.checked.get(key, ())
        self.checked[key] = tuple(dict.fromkeys(existing + sources))

    def mark_pending(self, drug: DmdRef, axis: Axis, *sources: str) -> None:
        key = (drug.code, axis)
        existing = self.pending.get(key, ())
        self.pending[key] = tuple(dict.fromkeys(existing + sources))


def _snapshot_id(corpus: Corpus) -> str:
    """Deterministic id over the cited document versions, so a dossier pins what
    it saw (invariant 6). Stable across runs given the same corpus."""

    parts = sorted(
        f"{c.provenance.source}:{c.provenance.document_id}:{c.provenance.version}"
        for c in corpus.constraints
    )
    digest = hashlib.sha256("\n".join(parts).encode()).hexdigest()[:16]
    return f"snap-{digest}"


def evaluate(
    case: Case,
    query: Query,
    corpus: Corpus,
    *,
    dossier_id: str | None = None,
    derived_at: date | None = None,
    corpus_snapshot_id: str | None = None,
) -> Dossier:
    """Evaluate the query's candidate drugs against the case.

    For each candidate and each axis in scope: collect constraints about that
    drug whose guard fires for this case (Always() always fires), group them
    into an AxisResult carrying the checked and pending source sets. The two
    empty states stay distinct (invariant 7).
    """

    derived_at = derived_at or date.today()
    snapshot = corpus_snapshot_id or _snapshot_id(corpus)
    axes = query.axes_or_all()

    results: dict[DmdRef, dict[Axis, AxisResult]] = {}
    retrieval_dates: list[date] = []

    for candidate in query.candidates:
        per_axis: dict[Axis, AxisResult] = {}
        for axis in axes:
            firing: list[Constraint] = []
            for c in corpus.constraints:
                if c.axis is not axis:
                    continue
                if not _drug_matches(c.drug, candidate):
                    continue
                outcome = c.guard.evaluate(case)
                if outcome.fired:
                    firing.append(c)
                    retrieval_dates.append(c.provenance.retrieved_at)
            checked = corpus.checked.get((candidate.code, axis), ())
            pending = corpus.pending.get((candidate.code, axis), ())
            # A firing constraint's source counts as checked even if not listed.
            checked = tuple(
                dict.fromkeys(checked + tuple(c.provenance.source for c in firing))
            )
            per_axis[axis] = AxisResult(
                axis=axis,
                constraints=tuple(firing),
                checked_sources=checked,
                pending_sources=pending,
            )
        results[candidate] = per_axis

    oldest = min(retrieval_dates) if retrieval_dates else derived_at
    return Dossier(
        dossier_id=dossier_id or f"dossier-{case.case_id}-v{case.version}",
        case_id=case.case_id,
        case_version=case.version,
        query=query,
        corpus_snapshot_id=snapshot,
        results=results,
        derived_at=derived_at,
        oldest_retrieval=oldest,
    )
