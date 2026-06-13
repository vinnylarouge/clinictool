"""Evaluator: the flagship evaluates both drug columns (block 10 AC1), the two
empty states stay distinct (invariant 7), and a firing renal constraint records
the convention the source stated (block 7 AC1).
"""

from pullback.eval.evaluator import evaluate
from pullback.fixtures.flagship import (
    AZITHROMYCIN,
    CLARITHROMYCIN,
    flagship_case,
    flagship_corpus,
    flagship_query,
)
from pullback.model.facets import Axis


def _flagship():
    case = flagship_case()
    return case, evaluate(case, flagship_query(), flagship_corpus())


def test_both_drug_columns_populated():
    _, dossier = _flagship()
    assert CLARITHROMYCIN in dossier.results
    assert AZITHROMYCIN in dossier.results


def test_clarithromycin_interaction_fires_against_apixaban():
    _, dossier = _flagship()
    cell = dossier.results[CLARITHROMYCIN][Axis.INTERACTION]
    texts = " ".join(
        c.payload.text for c in cell.constraints if hasattr(c.payload, "text")
    )
    assert "apixaban" in texts.lower()
    assert "cyp3a4" in texts.lower()


def test_two_empty_states_are_distinct():
    _, dossier = _flagship()
    contra = dossier.results[CLARITHROMYCIN][Axis.CONTRAINDICATION]
    pregnancy = dossier.results[CLARITHROMYCIN][Axis.PREGNANCY]
    supply = dossier.results[CLARITHROMYCIN][Axis.SUPPLY]

    # CONTRAINDICATION: a source reported, nothing fired -> checked-clear.
    assert contra.is_checked_clear
    assert not contra.is_unreported
    # PREGNANCY: nobody reported -> unreported (NOT clear).
    assert pregnancy.is_unreported
    assert not pregnancy.is_checked_clear
    # SUPPLY: an ambassador is still running -> pending (NOT clear).
    assert supply.is_pending
    assert not supply.is_checked_clear


def test_renal_constraint_records_crcl_convention():
    _, dossier = _flagship()
    cell = dossier.results[CLARITHROMYCIN][Axis.DOSE_RENAL]
    assert cell.constraints, "renal dose band should fire for this case"
    c = cell.constraints[0]
    # The SPC states the threshold in CrCl; the dossier surfaces that, and the
    # firing is against the case's CrCl (22), not its eGFR (24).
    assert c.convention == "CrCl"
    out = c.guard.evaluate(flagship_case())
    assert "CrCl" in out.explanation and "22" in out.explanation


def test_oldest_retrieval_is_min_over_citations():
    case, dossier = _flagship()
    # All fixture citations share one retrieval date.
    assert dossier.oldest_retrieval.isoformat() == "2026-06-13"


def test_snapshot_id_is_deterministic():
    case = flagship_case()
    q = flagship_query()
    a = evaluate(case, q, flagship_corpus())
    b = evaluate(case, q, flagship_corpus())
    assert a.corpus_snapshot_id == b.corpus_snapshot_id
