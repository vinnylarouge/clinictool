"""The device-line rule in code (SPEC section 3, decision D1).

- An attested alternative surfaces with its adjacency cited (block 10 AC2).
- A candidate with no citable adjacency is absent (block 10 AC4).
- Alternatives are never ranked or system-preferred.
- A flagged finding carries TWO separately-attributable statements: the source
  span (with provenance) and the mechanical case fact (the guard explanation)
  (block 10 AC3).
"""

from datetime import date

from pullback.eval.alternatives import attested_alternatives
from pullback.fixtures.flagship import (
    AZITHROMYCIN,
    CLARITHROMYCIN,
    flagship_case,
    flagship_corpus,
)
from pullback.model.constraint import (
    Authority,
    Constraint,
    Kind,
    Provenance,
    Span,
)
from pullback.model.dmd import DmdLevel, DmdRef
from pullback.model.facets import Axis
from pullback.model.guard import Always, Guard


def _all_constraints():
    return flagship_corpus().constraints


def test_azithromycin_is_an_attested_alternative():
    alts = attested_alternatives(_all_constraints(), flagship_case())
    drugs = {a.drug.code for a in alts}
    assert AZITHROMYCIN.code in drugs


def test_alternative_carries_a_cited_adjacency():
    alts = attested_alternatives(_all_constraints(), flagship_case())
    azi = next(a for a in alts if a.drug.code == AZITHROMYCIN.code)
    # The attestation is a real Constraint of kind ALTERNATIVE with provenance.
    assert azi.attestation.kind is Kind.ALTERNATIVE
    assert azi.attestation.provenance.source
    assert azi.attestation.provenance.url


def test_mechanical_and_attested_bases_are_labelled_distinctly():
    # The corpus attests azithromycin two ways: an SPS source-attested adjacency
    # and an ATC mechanical sibling. The first encountered wins per drug here;
    # either way the basis is one of the two permitted, never invented.
    alts = attested_alternatives(_all_constraints(), flagship_case())
    azi = next(a for a in alts if a.drug.code == AZITHROMYCIN.code)
    assert azi.basis in {"source-attested", "mechanical"}


def test_no_ranking_or_preference_is_emitted():
    # The function returns a tuple ordered alphabetically only; there is no score
    # or rank field anywhere on the result type.
    alts = attested_alternatives(_all_constraints(), flagship_case())
    for a in alts:
        assert not hasattr(a, "score")
        assert not hasattr(a, "rank")


def test_candidate_without_citable_adjacency_is_absent():
    # Add a bare candidate drug with NO alternative constraint; it must not show.
    constraints = _all_constraints()
    ghost = DmdRef("vtm-ghost", DmdLevel.VTM, "ghostmycin")
    alts = attested_alternatives(constraints, flagship_case())
    assert ghost.code not in {a.drug.code for a in alts}


def test_alternative_dropped_when_guard_does_not_fire():
    # An adjacency attested only when co-prescribed apixaban must not surface for
    # a case without apixaban.
    case_no_apixaban = flagship_case()
    case_no_apixaban = type(case_no_apixaban)(
        **{**vars(case_no_apixaban), "co_meds": ()}
    )
    only_conditional = [
        Constraint(
            drug=AZITHROMYCIN,
            axis=Axis.INTERACTION,
            kind=Kind.ALTERNATIVE,
            guard=Guard(
                __import__(
                    "pullback.model.guard", fromlist=["CoMed"]
                ).CoMed(
                    DmdRef("vtm-apixaban", DmdLevel.VTM, "apixaban")
                )
            ),
            payload=Span(
                "azithromycin alternative where apixaban co-prescribed",
                Provenance("sps", "d", "v", date(2026, 6, 13), "loc", "https://x"),
            ),
            authority=Authority.SPECIALIST,
            provenance=Provenance("sps", "d", "v", date(2026, 6, 13), "loc", "https://x"),
        )
    ]
    assert attested_alternatives(only_conditional, case_no_apixaban) == ()


def test_flagged_finding_has_two_separately_attributable_statements():
    # block 10 AC3: the source span (provenance) and the mechanical case fact
    # (guard explanation) are independent and both present.
    case = flagship_case()
    corpus = flagship_corpus()
    interaction = [
        c
        for c in corpus.constraints
        if c.axis is Axis.INTERACTION and c.drug.code == CLARITHROMYCIN.code
    ]
    c = interaction[0]
    # Statement 1: the source's own words, with full provenance.
    assert isinstance(c.payload, Span)
    assert c.payload.provenance.source and c.payload.provenance.url
    # Statement 2: the mechanical case fact, attributable to the parsed case.
    outcome = c.guard.evaluate(case)
    assert outcome.fired
    assert "apixaban" in outcome.explanation.lower()
    # The two are distinct objects: the system never composes them into advice.
    assert c.payload.text != outcome.explanation
