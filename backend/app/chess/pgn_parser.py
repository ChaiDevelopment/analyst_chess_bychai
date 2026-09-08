"""PGN parsing utilities built on top of python-chess.

Responsible ONLY for turning raw PGN text into a validated list of moves
(with SAN/UCI/FEN before+after) plus game headers. No engine calls here.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import chess
import chess.pgn

from app.config import settings


class PGNParseError(ValueError):
    """Raised when the supplied PGN cannot be parsed or contains illegal moves."""


@dataclass
class ParsedMove:
    ply: int
    move_number: int
    color: str
    san: str
    uci: str
    fen_before: str
    fen_after: str


@dataclass
class ParsedGame:
    headers: dict
    moves: list[ParsedMove]
    final_fen: str


def parse_pgn(pgn_text: str) -> ParsedGame:
    if not pgn_text or not pgn_text.strip():
        raise PGNParseError("PGN is empty. Paste a game before analyzing.")

    if len(pgn_text) > settings.MAX_PGN_CHARS:
        raise PGNParseError(
            f"PGN is too long ({len(pgn_text)} characters). "
            f"Max allowed is {settings.MAX_PGN_CHARS}."
        )

    stream = io.StringIO(pgn_text)
    try:
        game = chess.pgn.read_game(stream)
    except Exception as exc:  # python-chess can raise a variety of errors
        raise PGNParseError(f"Could not parse PGN: {exc}") from exc

    if game is None:
        raise PGNParseError("Invalid PGN: no game found in the supplied text.")

    # python-chess silently stops parsing (logging an error) when it hits an
    # illegal/unparseable move rather than raising - surface that as a
    # PGNParseError instead of quietly returning a truncated game.
    if game.errors:
        raise PGNParseError(f"Invalid PGN: {game.errors[0]}")

    board = game.board()
    moves: list[ParsedMove] = []
    ply = 0

    node = game
    while node.variations:
        next_node = node.variations[0]
        move = next_node.move

        if move not in board.legal_moves:
            move_number = ply // 2 + 1
            color = "White" if ply % 2 == 0 else "Black"
            raise PGNParseError(
                f"Invalid PGN: illegal move found at move {move_number} ({color}): "
                f"{board.san(move) if move in board.legal_moves else move.uci()}"
            )

        fen_before = board.fen()
        san = board.san(move)
        uci = move.uci()
        board.push(move)
        fen_after = board.fen()

        ply += 1
        moves.append(
            ParsedMove(
                ply=ply,
                move_number=(ply + 1) // 2,
                color="white" if ply % 2 == 1 else "black",
                san=san,
                uci=uci,
                fen_before=fen_before,
                fen_after=fen_after,
            )
        )

        if ply > settings.MAX_PLIES:
            raise PGNParseError(
                f"Game is too long ({ply}+ plies). Max supported is {settings.MAX_PLIES}."
            )

        node = next_node

    if not moves:
        raise PGNParseError("Invalid PGN: no legal moves were found in the game.")

    return ParsedGame(headers=dict(game.headers), moves=moves, final_fen=board.fen())
