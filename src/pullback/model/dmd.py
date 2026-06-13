"""Identity: the dm+d spine.

dm+d's level model is the identity layer; everything hangs off it. Ingredient
level reasoning (interactions, class effects, pregnancy) attaches at VTM; dose
and route at VMP; excipients, supply, and the SPC at AMP, because those are
per-product facts (SPEC section 5.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DmdLevel(Enum):
    VTM = "vtm"  # virtual therapeutic moiety: the ingredient concept (apixaban)
    VMP = "vmp"  # ingredient + strength + form (apixaban 5mg tablets)
    AMP = "amp"  # an actual marketed product: excipients and the SPC attach here


@dataclass(frozen=True)
class DmdRef:
    code: str  # dm+d/SNOMED concept id
    level: DmdLevel
    name: str  # display name

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.name} [{self.level.value}:{self.code}]"


@dataclass(frozen=True)
class Coded:
    code: str  # SNOMED or other coded condition
    system: str
    display: str
