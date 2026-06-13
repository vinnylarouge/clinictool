"""Guard engine: firing, human-readable explanations (block 7 AC3), the renal
convention recorded on the guard (block 7 AC1), and JSON round-trip so the
constraint cache re-derives byte-for-byte.
"""

from pullback.model.dmd import DmdLevel, DmdRef
from pullback.model.facets import Case, Field, Impairment, Sex
from pullback.model.guard import (
    Always,
    And,
    CoMed,
    Ge,
    Guard,
    Gt,
    HasFlag,
    Le,
    Lt,
    Or,
    Pregnant,
    guard_from_dict,
)

APIXABAN = DmdRef("vtm-apixaban", DmdLevel.VTM, "apixaban")


def _case(**kw) -> Case:
    base = dict(case_id="c", alias="a", version=1)
    base.update(kw)
    return Case(**base)


def test_lt_fires_with_explanation():
    g = Lt(Field.EGFR, 30)
    out = g.evaluate(_case(egfr=24.0))
    assert out.fired
    assert "eGFR" in out.explanation and "24" in out.explanation and "< 30" in out.explanation


def test_threshold_does_not_fire_when_above():
    assert not Lt(Field.EGFR, 30).evaluate(_case(egfr=45.0)).fired


def test_unknown_field_does_not_fire_and_says_so():
    out = Lt(Field.CRCL, 30).evaluate(_case(crcl=None))
    assert not out.fired
    assert "unknown" in out.explanation.lower()


def test_renal_convention_is_recorded_on_the_guard():
    # The convention is exactly the field the comparison is stated in; never
    # auto-converted between eGFR and CrCl.
    assert Lt(Field.EGFR, 30).convention() == "eGFR"
    assert Lt(Field.CRCL, 30).convention() == "CrCl"
    assert Lt(Field.AGE, 65).convention() is None


def test_egfr_and_crcl_are_distinct_guards():
    # eGFR 24 fires an eGFR<30 guard; CrCl is separately None -> CrCl guard does
    # not fire. The two never reconcile silently.
    case = _case(egfr=24.0, crcl=None)
    assert Lt(Field.EGFR, 30).evaluate(case).fired
    assert not Lt(Field.CRCL, 30).evaluate(case).fired


def test_comed_fires_on_coprescription():
    case = _case(co_meds=(APIXABAN,))
    out = CoMed(APIXABAN).evaluate(case)
    assert out.fired
    assert "apixaban" in out.explanation.lower()


def test_hepatic_ordinal_comparison():
    # Ge over hepatic severity ranks Impairment ordinally.
    assert Ge(Field.HEPATIC, 3).evaluate(_case(hepatic=Impairment.SEVERE)).fired
    assert not Ge(Field.HEPATIC, 3).evaluate(_case(hepatic=Impairment.MILD)).fired


def test_always_fires_unconditionally():
    out = Always().evaluate(_case())
    assert out.fired and out.explanation == "unconditional"


def test_composites():
    case = _case(egfr=24.0, co_meds=(APIXABAN,))
    assert And(Lt(Field.EGFR, 30), CoMed(APIXABAN)).evaluate(case).fired
    assert Or(Gt(Field.EGFR, 90), CoMed(APIXABAN)).evaluate(case).fired
    assert not And(Gt(Field.EGFR, 90), CoMed(APIXABAN)).evaluate(case).fired


def test_guard_json_round_trip():
    guards = [
        Guard(Lt(Field.CRCL, 30)),
        Guard(CoMed(APIXABAN)),
        Guard(HasFlag("g6pd_deficient")),
        Guard(Pregnant()),
        Guard(And(Lt(Field.AGE, 80), Le(Field.WEIGHT, 60))),
        Guard(Or(CoMed(APIXABAN), HasFlag("porphyria"))),
        Guard(Always()),
    ]
    case = _case(crcl=22.0, age_years=78, weight_kg=54.0, co_meds=(APIXABAN,), pregnant=True)
    for g in guards:
        d = g.to_dict()
        restored = guard_from_dict(d)
        assert restored.to_dict() == d
        # Behaviour is preserved, not just structure.
        assert restored.evaluate(case).fired == g.evaluate(case).fired
