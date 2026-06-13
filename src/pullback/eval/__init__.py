"""Evaluation: (Case, Query) -> Dossier.

No scoring, no aggregation across sources, no reconciliation when sources
disagree. Disagreement is displayed, because surfacing that the SPC and the
renal reference band renal function differently (eGFR vs CrCl) is itself
clinically useful (SPEC section 4, evaluation semantics).
"""

from pullback.eval.alternatives import attested_alternatives
from pullback.eval.evaluator import Corpus, evaluate

__all__ = ["Corpus", "evaluate", "attested_alternatives"]
