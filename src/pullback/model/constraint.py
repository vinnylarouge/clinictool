"""Provenance and the constraint itself.

Every type here that touches a claim carries Provenance (invariant 1: provenance
or it does not ship). AxisResult keeps the two empty states distinct (invariant
7): an axis whose sources reported with nothing firing is checked-clear; an axis
whose sources have not reported is pending. Collapsing them would let the
dossier imply a safety it has not verified.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from pullback.model.dmd import DmdRef
from pullback.model.facets import Axis
from pullback.model.guard import Guard


@dataclass(frozen=True)
class Provenance:
    source: str  # registry key from docs/01-sources.md
    document_id: str  # emc product doc id, DSU issue, rule-set citation...
    version: str  # document revision or release tag
    retrieved_at: date
    locator: str  # section path + char offsets, or URL fragment
    url: str


class Authority(Enum):
    """Render order / trust badge. The system NEVER adjudicates between sources;
    this only orders the display and labels research-grade content."""

    REGULATOR = 1  # SPC, MHRA
    FORMULARY = 2  # BNF (once licensed)
    SPECIALIST = 3  # SPS, UKTIS, CredibleMeds, Maudsley, Renal Drug Database
    RESEARCH = 4  # open DDI sets: always labelled as research-grade


class Kind(Enum):
    CONTRAINDICATION = "contraindication"
    DOSE_ADJUST = "dose_adjust"
    INTERACTION = "interaction"
    MONITORING = "monitoring"
    ALTERNATIVE = "alternative"  # only ever source-attested (SPEC section 3)
    SIGNAL = "signal"
    EXCIPIENT_PRESENT = "excipient_present"
    SUPPLY_STATUS = "supply_status"
    INFO = "info"  # indications, plain facts


@dataclass(frozen=True)
class Span:
    """A verbatim quotation from a source. Never paraphrased in the clinical
    surface (invariant 2/3: the source speaks, not the system)."""

    text: str
    provenance: Provenance


@dataclass(frozen=True)
class Rule:
    """An encoded rule-set criterion (e.g. STOPP B1), cited."""

    label: str
    statement: str
    provenance: Provenance


@dataclass(frozen=True)
class LinkOut:
    """A deep link into a gated or view-only source, pre-resolved to this drug
    where the target scheme allows (SPEC section 8: link-outs are first-class)."""

    label: str
    url: str
    note: str
    provenance: Provenance


Payload = Span | Rule | LinkOut


@dataclass(frozen=True)
class Constraint:
    drug: DmdRef  # level explicitly tagged: ingredient vs product matters
    axis: Axis
    kind: Kind
    guard: Guard  # Always() for unconditional facts
    payload: Payload
    authority: Authority
    provenance: Provenance

    @property
    def convention(self) -> str | None:
        """The renal convention (eGFR/CrCl) this constraint's guard is stated in,
        surfaced so the dossier can show it and never silently reconcile."""

        return self.guard.convention()


@dataclass(frozen=True)
class AxisResult:
    """Per (drug, axis) cell. Keeps the two empty states distinct (invariant 7).

    - constraints non-empty: findings to render.
    - constraints empty AND checked_sources non-empty AND no pending: checked
      clear (those sources reported, nothing fired).
    - pending_sources non-empty: still waiting on an ambassador agent; the cell
      renders as pending, NOT as clear.
    """

    axis: Axis
    constraints: tuple[Constraint, ...]
    checked_sources: tuple[str, ...]  # reported in; "no constraint" is meaningful here
    pending_sources: tuple[str, ...] = ()  # ambassador agents still running

    @property
    def is_pending(self) -> bool:
        return len(self.pending_sources) > 0

    @property
    def is_checked_clear(self) -> bool:
        """Sources reported and nothing fired. Distinct from not-yet-checked."""

        return (
            not self.constraints
            and len(self.checked_sources) > 0
            and not self.pending_sources
        )

    @property
    def is_unreported(self) -> bool:
        """No source has reported on this axis at all."""

        return (
            not self.constraints
            and not self.checked_sources
            and not self.pending_sources
        )
