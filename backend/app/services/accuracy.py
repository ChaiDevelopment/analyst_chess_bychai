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

    # Decay constant chosen so ~25 cpl average -> ~85, ~100 cpl -> ~55,
    # ~300+ cpl -> near 0. Purely heuristic, isolated here for easy tuning.
    score = 103.1668 * math.exp(-0.04354 * average_cpl) - 3.1668
    return max(0.0, min(100.0, round(score, 1)))
