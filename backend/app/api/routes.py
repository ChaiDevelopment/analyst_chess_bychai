from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.chess.pgn_parser import PGNParseError, parse_pgn
from app.config import settings
from app.engine.stockfish_engine import EngineUnavailableError
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, HealthResponse
from app.services.analysis import analyze_pgn

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        engine_available=settings.engine_available,
        ai_explanations_enabled=settings.ai_explanations_enabled,
    )


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    # Validate client input before checking optional server infrastructure.
    # This ensures malformed PGN consistently returns a useful 400 response,
    # even on a machine where Stockfish has not been installed yet.
    try:
        parse_pgn(request.pgn)
    except PGNParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not settings.engine_available:
        raise HTTPException(
            status_code=503,
            detail=(
                "Stockfish engine is not available on this server. Install "
                "Stockfish and/or set STOCKFISH_PATH in your .env file."
            ),
        )

    depth = request.depth or settings.ANALYSIS_DEPTH

    try:
        game_info, moves, summary = analyze_pgn(request.pgn, depth=depth)
    except PGNParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EngineUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # last-resort guard: never let the backend crash
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    return AnalyzeResponse(
        game=game_info,
        moves=moves,
        summary=summary,
        ai_explanations_enabled=settings.ai_explanations_enabled,
        engine_depth=depth,
    )
