"""Thin wrapper around python-chess's UCI engine interface for Stockfish.

Design goals (per spec section 21 - performance):
  * One reusable engine process, not one-per-move.
  * Simple synchronous API: analyze(fen) -> EngineResult.
  * Never accepts arbitrary shell input; the binary path is server-controlled
    (app.config.settings.STOCKFISH_PATH), never taken from the request.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import chess
import chess.engine

from app.config import settings


class EngineUnavailableError(RuntimeError):
    """Raised when Stockfish cannot be found or fails to start."""


@dataclass
class EngineResult:
    # Evaluation from White's perspective, in pawns. None if it's a mate score
    # with no meaningful centipawn value.
    score_pawns: Optional[float]
    mate_in: Optional[int]  # positive = White mates, negative = Black mates
    best_move_uci: str
    best_move_san: str
    principal_variation_uci: list[str]
    principal_variation_san: list[str]


class StockfishEngine:
    """A single reusable Stockfish process, opened lazily and kept alive."""

    def __init__(self, depth: int | None = None):
        self.depth = depth or settings.ANALYSIS_DEPTH
        self._engine: chess.engine.SimpleEngine | None = None

    def _ensure_started(self) -> chess.engine.SimpleEngine:
        if self._engine is not None:
            return self._engine

        if not settings.engine_available:
            raise EngineUnavailableError(
                "Stockfish engine was not found. Install Stockfish and/or set "
                "STOCKFISH_PATH in your .env file."
            )

        try:
            self._engine = chess.engine.SimpleEngine.popen_uci(settings.STOCKFISH_PATH)
        except Exception as exc:
            raise EngineUnavailableError(f"Failed to start Stockfish: {exc}") from exc

        return self._engine

    def analyze(self, fen: str, depth: int | None = None, pv_length: int = 8) -> EngineResult:
        """Analyze a position and return the best line + evaluation.

        Evaluation and PV are always expressed relative to White (standard
        chess convention), regardless of whose turn it is - callers that need
        "current player" perspective flip the sign themselves.
        """
        engine = self._ensure_started()
        board = chess.Board(fen)
        use_depth = depth or self.depth

        # Terminal positions (checkmate/stalemate/draw) have no legal moves,
        # so asking the engine to search them is meaningless/undefined. Short
        # circuit with an explicit, unambiguous result instead.
        if board.is_checkmate():
            # The side to move is mated; the side that just moved delivered it.
            # mate_in convention: positive = White delivers mate, negative = Black.
            mate_in = 1 if board.turn == chess.BLACK else -1
            return EngineResult(
                score_pawns=None,
                mate_in=mate_in,
                best_move_uci="",
                best_move_san="",
                principal_variation_uci=[],
                principal_variation_san=[],
            )
        if board.is_stalemate() or board.is_insufficient_material() or not board.legal_moves:
            return EngineResult(
                score_pawns=0.0,
                mate_in=None,
                best_move_uci="",
                best_move_san="",
                principal_variation_uci=[],
                principal_variation_san=[],
            )

        try:
            info = engine.analyse(board, chess.engine.Limit(depth=use_depth), multipv=1)
        except chess.engine.EngineTerminatedError as exc:
            # Try to restart once - handles transient crashes.
            self._engine = None
            engine = self._ensure_started()
            try:
                info = engine.analyse(board, chess.engine.Limit(depth=use_depth), multipv=1)
            except Exception as exc2:
                raise EngineUnavailableError(f"Stockfish engine error: {exc2}") from exc2
        except Exception as exc:
            raise EngineUnavailableError(f"Stockfish analysis failed: {exc}") from exc

        if isinstance(info, list):
            info = info[0]

        pov_score = info["score"]  # chess.engine.PovScore, relative to side to move
        white_score = pov_score.white()

        mate_in = white_score.mate()
        score_pawns: Optional[float] = None
        if mate_in is None:
            score_pawns = white_score.score() / 100.0

        pv = info.get("pv", [])
        if not pv:
            # No legal moves (shouldn't happen for non-terminal positions).
            return EngineResult(
                score_pawns=score_pawns,
                mate_in=mate_in,
                best_move_uci="",
                best_move_san="",
                principal_variation_uci=[],
                principal_variation_san=[],
            )

        best_move = pv[0]
        best_move_san = board.san(best_move)

        pv_board = board.copy()
        pv_uci: list[str] = []
        pv_san: list[str] = []
        for mv in pv[:pv_length]:
            if mv not in pv_board.legal_moves:
                break
            pv_san.append(pv_board.san(mv))
            pv_uci.append(mv.uci())
            pv_board.push(mv)

        return EngineResult(
            score_pawns=score_pawns,
            mate_in=mate_in,
            best_move_uci=best_move.uci(),
            best_move_san=best_move_san,
            principal_variation_uci=pv_uci,
            principal_variation_san=pv_san,
        )

    def close(self) -> None:
        if self._engine is not None:
            try:
                self._engine.quit()
            except Exception:
                pass
            self._engine = None

    def __enter__(self) -> "StockfishEngine":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
