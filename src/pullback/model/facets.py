"""The facet vocabulary: what a case is, plus the only egress path.

Invariant 4 is enforced here at the type level: agents accept CaseProjection,
not Case, and CaseProjection has no alias or narrative field, so a narrative
leak is structurally impossible. project() is the single egress function.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Sex(Enum):
    F = "f"
    M = "m"
    UNSPECIFIED = "unspecified"


class Impairment(Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    UNKNOWN = "unknown"


class Route(Enum):
    ORAL = "oral"
    IV = "iv"
    ENTERAL_TUBE = "enteral_tube"
    OTHER = "other"


class Field(Enum):
    """Numeric/enumerated case fields a guard may test."""

    AGE = "age"
    EGFR = "egfr"
    CRCL = "crcl"
    WEIGHT = "weight"
    HEPATIC = "hepatic"


class Axis(Enum):
    INDICATION = "indication"  # SPC 4.1
    CONTRAINDICATION = "contraindication"  # SPC 4.3
    DOSE_RENAL = "dose_renal"  # SPC 4.2, Renal Drug Database (link)
    DOSE_HEPATIC = "dose_hepatic"  # SPC 4.2
    DOSE_GENERAL = "dose_general"  # SPC 4.2, BNF dose (once licensed)
    INTERACTION = "interaction"  # SPC 4.5, Stockley's/Liverpool (link)
    PREGNANCY = "pregnancy"  # SPC 4.6, UKTIS (link)
    LACTATION = "lactation"  # SPC 4.6, SPS (link)
    OLDER_ADULT = "older_adult"  # STOPP/START v3, ACB/AEC (v1)
    QT_RISK = "qt_risk"  # CredibleMeds (link), SPC 4.4
    EXCIPIENT = "excipient"  # SPC 6.1 + 2, dm+d AMP excipient data
    ADMINISTRATION = "administration"  # SPC 4.2, NEWT (link)
    MONITORING = "monitoring"  # SPC 4.4
    SAFETY_SIGNAL = "safety_signal"  # MHRA Drug Safety Update, Yellow Card (link)
    SUPPLY = "supply"  # SPS Medicine Supply Tool
    COST = "cost"  # dm+d price data


# Import after enums to avoid a cycle: DmdRef/Coded live in dmd.py.
from pullback.model.dmd import Coded, DmdRef  # noqa: E402


@dataclass(frozen=True)
class Case:
    """The durable, coded case. Reasoned over locally and projectable outward.

    The alias is a doctor-side label and is NEVER a patient identifier. Narrative
    history is not stored here; it lives in an encrypted blob keyed by alias
    (SPEC sections 5.2, 5.7) and never reaches this struct as plain text.
    """

    case_id: str
    alias: str  # doctor-side label, NEVER a patient identifier
    version: int
    age_years: int | None = None
    sex: Sex = Sex.UNSPECIFIED
    weight_kg: float | None = None
    # Renal function is carried in BOTH conventions and NEVER auto-converted
    # between them. Labs report eGFR (CKD-EPI, body-surface-area normalised).
    # Many SPCs, and the DOAC dose-reduction criteria specifically, are framed on
    # creatinine clearance (Cockcroft-Gault, CrCl). The two diverge in the
    # elderly and at extremes of weight, which can misclassify renal dose bands.
    # The dossier shows which convention each source's threshold is stated in and
    # never silently reconciles them.
    egfr: float | None = None  # mL/min/1.73m2
    crcl: float | None = None  # mL/min, Cockcroft-Gault
    hepatic: Impairment = Impairment.UNKNOWN
    pregnant: bool | None = None
    breastfeeding: bool | None = None
    co_meds: tuple[DmdRef, ...] = ()
    conditions: tuple[Coded, ...] = ()
    route: Route | None = None
    intolerances: tuple[str, ...] = ()  # excipient matching: lactose, soya, gelatine...
    flags: frozenset[str] = field(default_factory=frozenset)  # g6pd_deficient, porphyria...


@dataclass(frozen=True)
class CaseProjection:
    """The ONLY thing that may leave the device.

    A deliberate strict subset of Case: coded and numeric only. No alias, no
    narrative, no free text. Agents accept this type, not Case, so a narrative
    leak is structurally impossible (invariant 4).
    """

    age_years: int | None
    sex: Sex
    weight_kg: float | None
    egfr: float | None
    crcl: float | None
    hepatic: Impairment
    pregnant: bool | None
    breastfeeding: bool | None
    co_med_codes: tuple[str, ...]
    condition_codes: tuple[str, ...]
    route: Route | None
    intolerances: tuple[str, ...]
    flags: frozenset[str]


def project(case: Case) -> CaseProjection:
    """Drop alias and narrative; the only egress path (invariant 4).

    Medicines and conditions are reduced to their codes: the projection carries
    no display names, because a display name ("apixaban") is less identifying
    than free text but the contract is coded-only, and downstream agents resolve
    codes themselves.
    """

    return CaseProjection(
        age_years=case.age_years,
        sex=case.sex,
        weight_kg=case.weight_kg,
        egfr=case.egfr,
        crcl=case.crcl,
        hepatic=case.hepatic,
        pregnant=case.pregnant,
        breastfeeding=case.breastfeeding,
        co_med_codes=tuple(ref.code for ref in case.co_meds),
        condition_codes=tuple(coded.code for coded in case.conditions),
        route=case.route,
        intolerances=case.intolerances,
        flags=case.flags,
    )
