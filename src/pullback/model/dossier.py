"""Query, Dossier, and the diff that makes this a secretary rather than a search
box.

A Dossier is a derivation, not a document (invariant 6): it pins the case
version and corpus snapshot it was derived from. diff() compares two derivations
cell by cell so a re-derive after a source change can render "changed since last
review" (SPEC section 5.7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from pullback.model.constraint import AxisResult
from pullback.model.dmd import DmdRef
from pullback.model.facets import Axis


@dataclass(frozen=True)
class Query:
    """A per-case suitability query: the candidate drug(s) to evaluate, and
    optionally the axes of interest. Empty axes means "all axes"."""

    candidates: tuple[DmdRef, ...]
    axes: tuple[Axis, ...] = ()
    note: str = ""

    def axes_or_all(self) -> tuple[Axis, ...]:
        return self.axes if self.axes else tuple(Axis)


@dataclass(frozen=True)
class Dossier:
    dossier_id: str
    case_id: str
    case_version: int
    query: Query
    corpus_snapshot_id: str
    results: dict[DmdRef, dict[Axis, AxisResult]]  # drug -> axis -> result
    derived_at: date
    oldest_retrieval: date  # printed prominently in the footer

    def cited_triples(self) -> frozenset[tuple[str, str, str]]:
        """The (source, drug_code, axis) triples this dossier cites.

        These are the subscriptions: a source sync touching any of them marks
        the dossier dirty (SPEC section 5.7, invariant 6)."""

        triples: set[tuple[str, str, str]] = set()
        for drug, axes in self.results.items():
            for axis, result in axes.items():
                for c in result.constraints:
                    triples.add((c.provenance.source, drug.code, axis.value))
        return frozenset(triples)


# ----- diff -----


@dataclass(frozen=True)
class CellDiff:
    drug: DmdRef
    axis: Axis
    status: str  # "added", "removed", "changed", "unchanged"
    detail: str


@dataclass(frozen=True)
class DossierDiff:
    cells: tuple[CellDiff, ...] = field(default_factory=tuple)

    @property
    def changed(self) -> tuple[CellDiff, ...]:
        return tuple(c for c in self.cells if c.status != "unchanged")

    @property
    def has_changes(self) -> bool:
        return len(self.changed) > 0


def _cell_fingerprint(result: AxisResult) -> tuple:
    """A comparable, order-independent fingerprint of a cell's cited content.

    Keyed on each constraint's provenance (source, document_id, version,
    locator) and the verbatim/label text of its payload, so a re-fetched source
    whose wording changed produces a different fingerprint."""

    from pullback.model.constraint import LinkOut, Rule, Span

    items = []
    for c in result.constraints:
        p = c.provenance
        if isinstance(c.payload, Span):
            text = c.payload.text
        elif isinstance(c.payload, Rule):
            text = f"{c.payload.label}: {c.payload.statement}"
        elif isinstance(c.payload, LinkOut):
            text = f"{c.payload.label} -> {c.payload.url}"
        else:  # pragma: no cover - exhaustive
            text = ""
        items.append((p.source, p.document_id, p.version, p.locator, text))
    return tuple(sorted(items))


def diff(old: Dossier | None, new: Dossier) -> DossierDiff:
    """Diff new against old (the last reviewed baseline).

    A None baseline means everything is new; the dossier has never been
    reviewed. Cells are matched on (drug code, axis)."""

    cells: list[CellDiff] = []
    new_keys = {
        (drug.code, axis): (drug, axis, res)
        for drug, axes in new.results.items()
        for axis, res in axes.items()
    }
    old_keys = (
        {
            (drug.code, axis): res
            for drug, axes in old.results.items()
            for axis, res in axes.items()
        }
        if old is not None
        else {}
    )

    for key, (drug, axis, new_res) in new_keys.items():
        new_fp = _cell_fingerprint(new_res)
        if key not in old_keys:
            status = "added" if new_fp else "unchanged"
            detail = "new cell" if new_fp else "no content"
            cells.append(CellDiff(drug, axis, status, detail))
            continue
        old_fp = _cell_fingerprint(old_keys[key])
        if old_fp == new_fp:
            cells.append(CellDiff(drug, axis, "unchanged", ""))
        else:
            cells.append(
                CellDiff(drug, axis, "changed", "cited content changed since last review")
            )

    # Cells present before but absent now (a source dropped a finding).
    for key, old_res in old_keys.items():
        if key not in new_keys and _cell_fingerprint(old_res):
            # Reconstruct drug/axis from the old dossier.
            for drug, axes in old.results.items():  # type: ignore[union-attr]
                for axis, res in axes.items():
                    if (drug.code, axis) == key:
                        cells.append(
                            CellDiff(drug, axis, "removed", "finding no longer present")
                        )

    return DossierDiff(tuple(cells))
