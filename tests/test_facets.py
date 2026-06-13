"""Invariant 4: raw case narrative never leaves the device.

The projection is the only egress path and is structurally incapable of carrying
an alias or narrative (block 3 AC2).
"""

import dataclasses

from pullback.model.facets import Case, CaseProjection, Sex, project
from pullback.fixtures.flagship import flagship_case


def test_projection_has_no_alias_or_narrative_field():
    # Type-level guarantee: the projection schema simply has no such fields.
    field_names = {f.name for f in dataclasses.fields(CaseProjection)}
    assert "alias" not in field_names
    assert "narrative" not in field_names
    assert "case_id" not in field_names


def test_project_drops_alias_and_keeps_only_codes():
    case = flagship_case()
    proj = project(case)
    assert isinstance(proj, CaseProjection)
    # Value level: no attribute reachable that equals the doctor-side alias.
    assert case.alias not in vars(proj).values()
    # Co-meds reduced to codes, not names.
    assert proj.co_med_codes == tuple(m.code for m in case.co_meds)
    assert all(isinstance(code, str) for code in proj.co_med_codes)


def test_project_preserves_numeric_facets():
    case = flagship_case()
    proj = project(case)
    assert proj.age_years == 78
    assert proj.egfr == 24.0
    assert proj.crcl == 22.0
    assert proj.sex is Sex.F


def test_case_has_no_plaintext_narrative_field():
    # Narrative lives encrypted, keyed by alias, never in the coded Case.
    field_names = {f.name for f in dataclasses.fields(Case)}
    assert "narrative" not in field_names
