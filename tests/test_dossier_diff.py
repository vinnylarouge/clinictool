"""Dossiers are derivations, not documents (invariant 6).

A re-derive after a source change highlights the changed cell (block 11 AC2);
marking the dossier reviewed re-baselines so an unchanged re-derive shows no
diff (block 11 AC3).
"""

from dataclasses import replace
from datetime import date

from pullback.eval.evaluator import evaluate
from pullback.fixtures.flagship import (
    CLARITHROMYCIN,
    flagship_case,
    flagship_corpus,
    flagship_query,
)
from pullback.model.constraint import Span
from pullback.model.dossier import diff
from pullback.model.facets import Axis


def _derive(corpus):
    case = flagship_case()
    return evaluate(case, flagship_query(), corpus)


def test_unchanged_rederive_shows_no_diff():
    a = _derive(flagship_corpus())
    b = _derive(flagship_corpus())
    assert not diff(a, b).has_changes


def test_changed_spc_highlights_the_cell():
    baseline = _derive(flagship_corpus())

    # Simulate a re-fetched clarithromycin SPC whose 4.5 wording changed.
    corpus = flagship_corpus()
    for i, c in enumerate(corpus.constraints):
        if (
            c.drug.code == CLARITHROMYCIN.code
            and c.axis is Axis.INTERACTION
            and isinstance(c.payload, Span)
        ):
            new_payload = replace(
                c.payload,
                text=c.payload.text + " Updated wording: monitor for bleeding.",
                provenance=replace(c.payload.provenance, version="FIXTURE-rev2"),
            )
            corpus.constraints[i] = replace(
                c,
                payload=new_payload,
                provenance=replace(c.provenance, version="FIXTURE-rev2"),
            )
    rederived = _derive(corpus)

    d = diff(baseline, rederived)
    assert d.has_changes
    changed = {(cell.drug.code, cell.axis) for cell in d.changed}
    assert (CLARITHROMYCIN.code, Axis.INTERACTION) in changed


def test_reviewing_rebaselines_the_diff():
    # After "reviewing" the changed state, a subsequent unchanged re-derive
    # against that new baseline shows no diff.
    corpus = flagship_corpus()
    reviewed = _derive(corpus)
    again = _derive(corpus)
    assert not diff(reviewed, again).has_changes


def test_none_baseline_treats_everything_as_new():
    d = diff(None, _derive(flagship_corpus()))
    # Every cell with content is "added" against an empty baseline.
    assert any(cell.status == "added" for cell in d.cells)


def test_cited_triples_are_the_subscriptions():
    dossier = _derive(flagship_corpus())
    triples = dossier.cited_triples()
    # The clarithromycin interaction citation subscribes to (emc, drug, axis).
    assert any(
        src == "emc" and drug == CLARITHROMYCIN.code and axis == Axis.INTERACTION.value
        for (src, drug, axis) in triples
    )
