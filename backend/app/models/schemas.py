"""Pydantic schemas shared by the API layer and the analysis pipeline."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Classification(str, Enum):
    BOOK = "BOOK"
    BRILLIANT = "BRILLIANT"
    GREAT = "GREAT"
    BEST = "BEST"
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    INACCURACY = "INACCURACY"
    MISTAKE = "MISTAKE"
    BLUNDER = "BLUNDER"
    MISS = "MISS"


class AnalyzeRequest(BaseModel):
    pgn: str = Field(..., min_length=1, description="Raw PGN text of the game")
    depth: Optional[int] = Field(
        None, ge=4, le=30, description="Override the default analysis depth"
    )


class PositionAnalyzeRequest(BaseModel):
    """One user-selected move from the interactive analysis board."""

    fen: str = Field(..., min_length=1)
    move: str = Field(..., min_length=4, max_length=5, pattern=r"^[a-h][1-8][a-h][1-8][qrbn]?$")
    depth: Optional[int] = Field(None, ge=4, le=30)


class GameInfo(BaseModel):
    event: Optional[str] = None
    site: Optional[str] = None
    date: Optional[str] = None
    white: Optional[str] = None
    black: Optional[str] = None
    result: Optional[str] = None
    eco: Optional[str] = None
    opening: Optional[str] = None
    total_plies: int = 0


class MoveAnalysis(BaseModel):
    ply: int
    move_number: int
    color: str  # "white" | "black"
    san: str
    uci: str
    fen_before: str
    fen_after: str
    evaluation_before: float  # pawns, from White's perspective
    evaluation_after: float  # pawns, from White's perspective
    mate_before: Optional[int] = None
    mate_after: Optional[int] = None
    best_move: str
    best_move_san: str
    centipawn_loss: int
    classification: Classification
    is_book: bool = False
    tactical_tags: list[str] = Field(default_factory=list)
    variation: list[str] = Field(default_factory=list)
    explanation: Optional[str] = None


class MoveStats(BaseModel):
    brilliant: int = 0
    great: int = 0
    best: int = 0
    excellent: int = 0
    good: int = 0
    book: int = 0
    inaccuracy: int = 0
    mistake: int = 0
    blunder: int = 0
    miss: int = 0


class PlayerSummary(BaseModel):
    accuracy: float
    average_centipawn_loss: float
    stats: MoveStats


class CriticalMoment(BaseModel):
    ply: int
    move_number: int
    color: str
    san: str
    classification: Classification
    evaluation_swing: float


class GameSummary(BaseModel):
    white: PlayerSummary
    black: PlayerSummary
    biggest_mistake: Optional[CriticalMoment] = None
    best_move_played: Optional[CriticalMoment] = None
    most_critical_position: Optional[CriticalMoment] = None
    opening: str = "Opening detection coming soon"
    result: Optional[str] = None


class AnalyzeResponse(BaseModel):
    game: GameInfo
    moves: list[MoveAnalysis]
    summary: GameSummary
    ai_explanations_enabled: bool
    engine_depth: int


class CandidateMove(BaseModel):
    uci: str
    san: str
    evaluation: float
    mate_in: Optional[int] = None
    variation: list[str] = Field(default_factory=list)


class PositionAnalyzeResponse(BaseModel):
    move: MoveAnalysis
    candidates: list[CandidateMove] = Field(default_factory=list)
    engine_depth: int


class HealthResponse(BaseModel):
    status: str
    engine_available: bool
    ai_explanations_enabled: bool


class ErrorResponse(BaseModel):
    detail: str
