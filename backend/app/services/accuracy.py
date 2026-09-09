"""Accuracy scoring based on per-move practical winning chances."""
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


def accuracy_from_move_quality(move_qualities: list[float]) -> float:
    """Aggregate 0..100 per-move quality scores into an accuracy of 1..100.

    The harmonic mean makes a serious mistake hurt materially more than a
    handful of harmless near-best moves, while still rewarding consistent
    play. Book moves are excluded by the caller.
    """
    if not move_qualities:
        return 100.0
    bounded = [max(1.0, min(100.0, quality)) for quality in move_qualities]
    harmonic = len(bounded) / sum(1.0 / quality for quality in bounded)
    return round(max(1.0, min(100.0, harmonic)), 1)
