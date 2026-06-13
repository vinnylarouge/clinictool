"""Render: the flagship dossier renders to one self-contained HTML page (block
11 AC1), with the disclaimer, both drug columns, the eGFR/CrCl convention
visible, and checked-clear distinct from not-yet-checked.
"""

from pullback.eval.evaluator import evaluate
from pullback.fixtures.flagship import flagship_case, flagship_corpus, flagship_query
from pullback.render.matrix import DISCLAIMER, render_dossier


def _html():
    case = flagship_case()
    dossier = evaluate(case, flagship_query(), flagship_corpus())
    return render_dossier(dossier, case)


def test_renders_self_contained_html():
    html = _html()
    assert html.lstrip().startswith("<!DOCTYPE html>")
    assert "<style>" in html  # CSS inlined, no external assets
    assert "src=" not in html  # no external scripts/images to fetch


def test_standing_disclaimer_is_present():
    assert DISCLAIMER in _html()


def test_both_drug_columns_render():
    html = _html()
    assert "clarithromycin" in html
    assert "azithromycin" in html


def test_egfr_and_crcl_both_shown():
    html = _html()
    assert "eGFR" in html and "CrCl" in html
    assert "never auto-converted" in html


def test_checked_clear_distinct_from_not_checked():
    html = _html()
    assert "checked, no constraint" in html  # CONTRAINDICATION
    assert "not yet checked" in html  # PREGNANCY
    assert "checking" in html  # SUPPLY pending


def test_fixture_banner_present():
    assert "Illustrative fixture data" in _html()


def test_attested_alternative_section_present_without_ranking():
    html = _html()
    assert "Attested alternatives" in html
    assert "Not ranked" in html
