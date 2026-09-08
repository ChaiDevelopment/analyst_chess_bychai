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
BRILLIANT_MAX_CPL = 10  # move must be (near-)best in engine terms
BRILLIANT_MIN_EVAL_AFTER = -0.5  # don't call a move brilliant if it's losing badly
BRILLIANT_SACRIFICE_MIN_LOSS = 200  # centipawns of *material* given up, roughly


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
    eval_after_for_mover: float,
    is_book: bool,
    is_best_move: bool,
    tactical_tags: list[str],
) -> Classification:
    """Combine CPL, book status and tactical signals into a final classification.

    eval_after_for_mover: evaluation after the move, from the perspective of
    the player who just moved (positive = good for them).
    """
    if is_book:
        return Classification.BOOK

    base = classify_by_cpl(cpl)

    # BRILLIANT heuristic (spec section 10): near-best move, involves a
    # material sacrifice, and doesn't leave the mover in a bad position.
    if (
        cpl <= BRILLIANT_MAX_CPL
        and "sacrifice" in tactical_tags
        and eval_after_for_mover >= BRILLIANT_MIN_EVAL_AFTER
        and base in (Classification.BEST, Classification.EXCELLENT)
    ):
        return Classification.BRILLIANT

    return base
