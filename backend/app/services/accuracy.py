"""Accuracy scoring.

Spec section 17: build a simple accuracy score from average centipawn loss,
kept in its own function so the formula is trivial to swap out later.
This is NOT claimed to match Chess.com's (undisclosed) accuracy formula.
"""
from __future__ import annotations

import math


def accuracy_from_average_cpl(average_cpl: float) -> float:
    """Map an average centipawn loss to a 0-100 accuracy score.

    Uses an exponential decay curve (loosely inspired by public discussion of
    how accuracy-style scores behave: small losses barely move the score,
    large losses drop it fast) then clamps to [0, 100].
    """
    if average_cpl <= 0:
        return 100.0

    # A gentle decay keeps a normal human game meaningful: ~25 CPL -> 86,
    # ~100 CPL -> 55, ~300 CPL -> 17. The prior coefficient made even
    # ordinary games collapse to 0.0 accuracy.
    score = 100.0 * math.exp(-0.006 * average_cpl)
    return max(0.0, min(100.0, round(score, 1)))
