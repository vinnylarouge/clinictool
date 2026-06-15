"""The flagship case and its illustrative corpus (SPEC section 9).

Woman, 78, eGFR 24 mL/min (CrCl 22 by Cockcroft-Gault, the two diverging at her
age and likely low weight), atrial fibrillation on apixaban, depression on
sertraline, a recent diagnosis warranting a macrolide. Candidate clarithromycin
with azithromycin as the attested-alternative comparator.

The corpus below lights up: a CYP3A4/P-gp interaction with bleeding risk, QT
additivity, a renal dose band stated in CrCl (so the eGFR/CrCl divergence is
visible and never silently reconciled), a checked-clear axis, a pending
ambassador axis, and an attested alternative shown two ways (a source-attested
SPS adjacency and a labelled mechanical ATC-sibling relation).

All identifiers and span text are illustrative fixtures (see fixtures/__init__).
"""

from __future__ import annotations

from datetime import date

from pullback.eval.evaluator import Corpus
from pullback.model.constraint import (
    Authority,
    Constraint,
    Kind,
    LinkOut,
    Provenance,
    Span,
)
from pullback.model.dmd import DmdLevel, DmdRef
from pullback.model.dossier import Query
from pullback.model.facets import Axis, Case, Field, Impairment, Route, Sex
from pullback.model.guard import Always, CoMed, Guard, Lt

# ----- illustrative dm+d refs (placeholders pending the real spine load) -----

CLARITHROMYCIN = DmdRef(code="fixture-vtm-clarithromycin", level=DmdLevel.VTM, name="clarithromycin")
AZITHROMYCIN = DmdRef(code="fixture-vtm-azithromycin", level=DmdLevel.VTM, name="azithromycin")
APIXABAN = DmdRef(code="fixture-vtm-apixaban", level=DmdLevel.VTM, name="apixaban")
SERTRALINE = DmdRef(code="fixture-vtm-sertraline", level=DmdLevel.VTM, name="sertraline")
METFORMIN = DmdRef(code="fixture-vtm-metformin", level=DmdLevel.VTM, name="metformin")
NITROFURANTOIN = DmdRef(code="fixture-vtm-nitrofurantoin", level=DmdLevel.VTM, name="nitrofurantoin")

_RETRIEVED = date(2026, 6, 13)


def _prov(source: str, doc: str, locator: str, url: str, version: str = "FIXTURE") -> Provenance:
    return Provenance(
        source=source,
        document_id=doc,
        version=version,
        retrieved_at=_RETRIEVED,
        locator=locator,
        url=url,
    )


# ----- the flagship case -----


def flagship_case() -> Case:
    return Case(
        case_id="flagship-001",
        alias="AF-macrolide-review",  # doctor-side label, not a patient identifier
        version=1,
        age_years=78,
        sex=Sex.F,
        weight_kg=54.0,
        egfr=24.0,  # mL/min/1.73m2 (CKD-EPI)
        crcl=22.0,  # mL/min (Cockcroft-Gault): diverges from eGFR at her age/weight
        hepatic=Impairment.NONE,
        pregnant=False,
        breastfeeding=False,
        co_meds=(APIXABAN, SERTRALINE),
        conditions=(),
        route=Route.ORAL,
        intolerances=(),
        flags=frozenset(),
    )


def flagship_query() -> Query:
    return Query(
        candidates=(CLARITHROMYCIN, AZITHROMYCIN),
        axes=(
            Axis.INTERACTION,
            Axis.QT_RISK,
            Axis.DOSE_RENAL,
            Axis.CONTRAINDICATION,
            Axis.OLDER_ADULT,
            Axis.PREGNANCY,
            Axis.SUPPLY,
        ),
        note="suitability of clarithromycin; azithromycin as comparator",
    )


# ----- the corpus -----


def flagship_corpus() -> Corpus:
    corpus = Corpus()

    # --- clarithromycin: interaction with apixaban (CYP3A4/P-gp, bleeding) ---
    corpus.add(
        Constraint(
            drug=CLARITHROMYCIN,
            axis=Axis.INTERACTION,
            kind=Kind.INTERACTION,
            guard=Guard(CoMed(APIXABAN)),
            payload=Span(
                text=(
                    "Clarithromycin is a strong inhibitor of CYP3A4 and "
                    "P-glycoprotein; co-administration with apixaban increases "
                    "apixaban exposure and the risk of bleeding."
                ),
                provenance=_prov(
                    "emc",
                    "fixture-clarithromycin-spc",
                    "SPC 4.5 (illustrative)",
                    "https://www.medicines.org.uk/emc",
                ),
            ),
            authority=Authority.REGULATOR,
            provenance=_prov(
                "emc",
                "fixture-clarithromycin-spc",
                "SPC 4.5 (illustrative)",
                "https://www.medicines.org.uk/emc",
            ),
        )
    )

    # --- clarithromycin: QT prolongation (unconditional drug property) ---
    corpus.add(
        Constraint(
            drug=CLARITHROMYCIN,
            axis=Axis.QT_RISK,
            kind=Kind.SIGNAL,
            guard=Guard(Always()),
            payload=Span(
                text=(
                    "Clarithromycin has been associated with QT interval "
                    "prolongation and ventricular arrhythmias; caution with other "
                    "QT-prolonging medicinal products."
                ),
                provenance=_prov(
                    "emc",
                    "fixture-clarithromycin-spc",
                    "SPC 4.4 (illustrative)",
                    "https://www.medicines.org.uk/emc",
                ),
            ),
            authority=Authority.REGULATOR,
            provenance=_prov(
                "emc",
                "fixture-clarithromycin-spc",
                "SPC 4.4 (illustrative)",
                "https://www.medicines.org.uk/emc",
            ),
        )
    )
    # CredibleMeds category as a link-out on the same axis (view-only source).
    corpus.add(
        Constraint(
            drug=CLARITHROMYCIN,
            axis=Axis.QT_RISK,
            kind=Kind.SIGNAL,
            guard=Guard(Always()),
            payload=LinkOut(
                label="CredibleMeds QT category (clarithromycin)",
                url="https://crediblemeds.org/",
                note="Render category as a link-out; redistribution restricted (docs/01-sources.md).",
                provenance=_prov(
                    "crediblemeds",
                    "fixture-crediblemeds-clarithromycin",
                    "QTdrugs list (illustrative)",
                    "https://crediblemeds.org/",
                ),
            ),
            authority=Authority.SPECIALIST,
            provenance=_prov(
                "crediblemeds",
                "fixture-crediblemeds-clarithromycin",
                "QTdrugs list (illustrative)",
                "https://crediblemeds.org/",
            ),
        )
    )

    # --- clarithromycin: renal dose band stated in CrCl (NOT eGFR) ---
    corpus.add(
        Constraint(
            drug=CLARITHROMYCIN,
            axis=Axis.DOSE_RENAL,
            kind=Kind.DOSE_ADJUST,
            guard=Guard(Lt(field=Field.CRCL, value=30)),
            payload=Span(
                text=(
                    "In severe renal impairment (creatinine clearance below "
                    "30 mL/min), the dose of clarithromycin should be reduced and "
                    "the duration of treatment limited."
                ),
                provenance=_prov(
                    "emc",
                    "fixture-clarithromycin-spc",
                    "SPC 4.2 (illustrative)",
                    "https://www.medicines.org.uk/emc",
                ),
            ),
            authority=Authority.REGULATOR,
            provenance=_prov(
                "emc",
                "fixture-clarithromycin-spc",
                "SPC 4.2 (illustrative)",
                "https://www.medicines.org.uk/emc",
            ),
        )
    )

    # --- azithromycin: QT property (the comparator's sparser signal) ---
    corpus.add(
        Constraint(
            drug=AZITHROMYCIN,
            axis=Axis.QT_RISK,
            kind=Kind.SIGNAL,
            guard=Guard(Always()),
            payload=Span(
                text=(
                    "Cases of QT prolongation and torsades de pointes have been "
                    "reported with azithromycin; consider risk in patients with "
                    "relevant pro-arrhythmic conditions."
                ),
                provenance=_prov(
                    "emc",
                    "fixture-azithromycin-spc",
                    "SPC 4.4 (illustrative)",
                    "https://www.medicines.org.uk/emc",
                ),
            ),
            authority=Authority.REGULATOR,
            provenance=_prov(
                "emc",
                "fixture-azithromycin-spc",
                "SPC 4.4 (illustrative)",
                "https://www.medicines.org.uk/emc",
            ),
        )
    )
    # --- azithromycin: contrasting interaction note (little CYP3A4 inhibition) ---
    corpus.add(
        Constraint(
            drug=AZITHROMYCIN,
            axis=Axis.INTERACTION,
            kind=Kind.INTERACTION,
            guard=Guard(Always()),
            payload=Span(
                text=(
                    "Azithromycin does not interact significantly with the hepatic "
                    "cytochrome P450 system and is not expected to cause the CYP3A4 "
                    "interactions seen with other macrolides."
                ),
                provenance=_prov(
                    "emc",
                    "fixture-azithromycin-spc",
                    "SPC 4.5 (illustrative)",
                    "https://www.medicines.org.uk/emc",
                ),
            ),
            authority=Authority.REGULATOR,
            provenance=_prov(
                "emc",
                "fixture-azithromycin-spc",
                "SPC 4.5 (illustrative)",
                "https://www.medicines.org.uk/emc",
            ),
        )
    )

    # --- attested alternative: azithromycin, two independently citable bases ---
    # (a) source-attested adjacency, conditional on the interacting co-med.
    corpus.add(
        Constraint(
            drug=AZITHROMYCIN,
            axis=Axis.INTERACTION,
            kind=Kind.ALTERNATIVE,
            guard=Guard(CoMed(APIXABAN)),
            payload=Span(
                text=(
                    "Where a macrolide is required for a patient taking a CYP3A4 "
                    "substrate such as a direct oral anticoagulant, azithromycin is "
                    "an alternative with substantially less CYP3A4 inhibition than "
                    "clarithromycin."
                ),
                provenance=_prov(
                    "sps",
                    "fixture-sps-macrolide-qa",
                    "SPS Medicines Q&A (illustrative)",
                    "https://www.sps.nhs.uk/",
                ),
            ),
            authority=Authority.SPECIALIST,
            provenance=_prov(
                "sps",
                "fixture-sps-macrolide-qa",
                "SPS Medicines Q&A (illustrative)",
                "https://www.sps.nhs.uk/",
            ),
        )
    )
    # (b) mechanical relation: ATC class sibling, explicitly labelled mechanical.
    corpus.add(
        Constraint(
            drug=AZITHROMYCIN,
            axis=Axis.INTERACTION,
            kind=Kind.ALTERNATIVE,
            guard=Guard(Always()),
            payload=LinkOut(
                label="ATC class sibling (J01FA macrolides)",
                url="https://www.whocc.no/atc_ddd_index/?code=J01FA",
                note="Mechanical relation only: same ATC class as clarithromycin. Not advice.",
                provenance=_prov(
                    "atc",
                    "fixture-atc-J01FA",
                    "ATC J01FA (mechanical)",
                    "https://www.whocc.no/atc_ddd_index/?code=J01FA",
                ),
            ),
            authority=Authority.RESEARCH,
            provenance=_prov(
                "atc",
                "fixture-atc-J01FA",
                "ATC J01FA (mechanical)",
                "https://www.whocc.no/atc_ddd_index/?code=J01FA",
            ),
        )
    )

    # --- reporting metadata: make the empty states distinct (invariant 7) ---
    for drug in (CLARITHROMYCIN, AZITHROMYCIN):
        # CONTRAINDICATION: the SPC reported, nothing fired -> checked-clear.
        corpus.mark_checked(drug, Axis.CONTRAINDICATION, "emc")
        # SUPPLY: an ambassador agent is still running -> pending, not clear.
        corpus.mark_pending(drug, Axis.SUPPLY, "sps")
        # OLDER_ADULT: checked against the (illustrative) rule set, nothing fired.
        corpus.mark_checked(drug, Axis.OLDER_ADULT, "stopp-start")
        # PREGNANCY is deliberately left unreported (no checked, no pending).

    return corpus
