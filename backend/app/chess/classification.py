"""Deterministic move-classification engine.

This is intentionally simple and heuristic (spec section 10). It is NOT
claimed to reproduce Chess.com's proprietary classifier - it is a
best-effort, explainable MVP built from Stockfish centipawn loss plus a
few tactical signals.

Thresholds are centralised here so they're trivial to tune later.
"""
from __future__ import annotations

import chess

from app.models.schemas import Classification

# --- CPL thresholds (centipawns), inclusive upper bounds -------------------
THRESHOLDS = {
    Classification.BEST: 10,
    Classification.EXCELLENT: 25,
    Classification.GOOD: 50,
    Classification.INACCURACY: 100,
    Classification.MISTAKE: 200,
    # anything above MISTOKE's bound -> BLUNDER
}

# Brilliant-move heuristic tuning knobs.
# A shallow/medium engine search can differ by a few tenths between the
# before/after searches. 30 CPL is still near-best, but never sufficient on
# its own: the MultiPV/tactical score below remains mandatory for Brilliant.
BRILLIANT_MAX_CPL = 30
BRILLIANT_MIN_EVAL_AFTER = -0.5  # don't call a move brilliant if it's losing badly
MISS_MIN_CPL = 75
MISS_MIN_OPPORTUNITY = 1.5  # pawn advantage available before the missed move
UNIQUE_BEST_GAP = 0.8  # pawns between Stockfish PV1 and PV2
ONLY_MOVE_GAP = 1.5


def classify_by_cpl(cpl: int) -> Classification:
    """Classification driven purely by centipawn loss (no tactical bonus)."""
    if cpl <= THRESHOLDS[Classification.BEST]:
        return Classification.BEST
    if cpl <= THRESHOLDS[Classification.EXCELLENT]:
        return Classification.EXCELLENT
    if cpl <= THRESHOLDS[Classification.GOOD]:
        return Classification.GOOD
    if cpl <= THRESHOLDS[Classification.INACCURACY]:
        return Classification.INACCURACY
    if cpl <= THRESHOLDS[Classification.MISTAKE]:
        return Classification.MISTAKE
    return Classification.BLUNDER


def _material_value(piece_type: int) -> int:
    return {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0,
    }.get(piece_type, 0)


def looks_like_sacrifice(board_before: chess.Board, move: chess.Move) -> bool:
    """Very rough heuristic: does the moving piece land on a square attacked
    by the opponent, undefended in a way that loses material, while giving
    up more value than it immediately captures?
    """
    piece = board_before.piece_at(move.from_square)
    if piece is None:
        return False

    captured = board_before.piece_at(move.to_square)
    gained = _material_value(captured.piece_type) if captured else 0
    moving_value = _material_value(piece.piece_type)

    board_after = board_before.copy()
    board_after.push(move)

    # Is the piece now attacked by the opponent, and not adequately defended?
    attacker_color = not piece.color
    if not board_after.is_attacked_by(attacker_color, move.to_square):
        return False

    defenders = board_after.attackers(piece.color, move.to_square)
    attackers = board_after.attackers(attacker_color, move.to_square)
    if len(defenders) >= len(attackers):
        return False  # adequately defended, not really a sac

    # It's a "sacrifice" if the piece risked is worth meaningfully more than
    # what was immediately captured.
    return (moving_value - gained) >= 2


def detect_tactical_tags(
    board_before: chess.Board,
    move: chess.Move,
    board_after: chess.Board,
) -> list[str]:
    """Basic tactical detection per spec section 11, built from
    chess.Board/python-chess only (no external services)."""
    tags: list[str] = []

    if board_after.is_checkmate():
        tags.append("checkmate")
    elif board_after.is_check():
        tags.append("check")

    if board_before.is_capture(move):
        tags.append("capture")

    if board_before.piece_at(move.to_square) is not None:
        captured = board_before.piece_at(move.to_square)
        moving = board_before.piece_at(move.from_square)
        if captured and moving and _material_value(captured.piece_type) > _material_value(
            moving.piece_type
        ):
            tags.append("winning_material")

    if looks_like_sacrifice(board_before, move):
        tags.append("sacrifice")

    if board_before.is_check() and len(list(board_before.legal_moves)) <= 2:
        tags.append("forced_move")

    # Hanging piece: after the move, does the mover leave a piece en prise
    # for free (defenders < attackers) anywhere on the board?
    mover_color = board_before.turn
    for square, piece in board_after.piece_map().items():
        if piece.color != mover_color or piece.piece_type == chess.KING:
            continue
        attackers = board_after.attackers(not mover_color, square)
        if not attackers:
            continue
        defenders = board_after.attackers(mover_color, square)
        if len(attackers) > len(defenders):
            tags.append("hanging_piece")
            break

    return tags


def classify_move(
    *,
    cpl: int,
    eval_before_for_mover: float,
    eval_after_for_mover: float,
    is_book: bool,
    is_best_move: bool,
    tactical_tags: list[str],
    uniqueness_gap: float = 0.0,
) -> Classification:
    """Combine CPL, book status and tactical signals into a final classification.

    eval_after_for_mover: evaluation after the move, from the perspective of
    the player who just moved (positive = good for them).
    """
    if is_book:
        return Classification.BOOK

    base = classify_by_cpl(cpl)

    tag_set = set(tactical_tags)
    unique_best = "unique_best" in tag_set or uniqueness_gap >= UNIQUE_BEST_GAP
    only_move = "only_move" in tag_set or uniqueness_gap >= ONLY_MOVE_GAP

    # Several independent engine/tactical signals are required. This permits
    # quiet tactical moves, defensive resources, and forcing moves while
    # keeping Brilliant deliberately rare.
    brilliant_score = 0
    brilliant_score += 2 if "sacrifice" in tag_set else 0
    brilliant_score += 2 if only_move else 0
    brilliant_score += 1 if unique_best else 0
    brilliant_score += 2 if "quiet_tactical" in tag_set else 0
    brilliant_score += 2 if "mating_threat" in tag_set else 0
    brilliant_score += 2 if "checkmate" in tag_set else 0
    brilliant_score += 1 if "tactical_sequence" in tag_set else 0
    brilliant_score += 1 if "tactical_conversion" in tag_set else 0
    brilliant_score += 1 if "defensive_resource" in tag_set else 0
    brilliant_score += 1 if "winning_material" in tag_set else 0

    if (
        is_best_move
        and cpl <= BRILLIANT_MAX_CPL
        and eval_after_for_mover >= BRILLIANT_MIN_EVAL_AFTER
        and brilliant_score >= 4
    ):
        return Classification.BRILLIANT

    # Great needs a meaningful engine distinction or a verified tactical/only
    # move signal, but not the higher combined Brilliant score.
    if is_best_move and cpl <= THRESHOLDS[Classification.BEST] and (
        only_move
        or (unique_best and bool(tag_set & {"quiet_tactical", "tactical_conversion", "defensive_resource"}))
        or bool(tag_set & {"checkmate", "winning_material", "forced_move"})
    ):
        return Classification.GREAT

    # Miss = a player had a clearly favourable chance but chose a materially
    # weaker continuation. It takes priority over generic error categories so
    # the summary exposes missed opportunities separately.
    if (
        not is_best_move
        and eval_before_for_mover >= MISS_MIN_OPPORTUNITY
        and cpl >= MISS_MIN_CPL
        and uniqueness_gap >= UNIQUE_BEST_GAP
    ):
        return Classification.MISS

    return base
