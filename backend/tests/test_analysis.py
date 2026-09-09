import pytest

from app.chess.pgn_parser import PGNParseError
from app.config import settings
from app.models.schemas import Classification
from app.services.analysis import analyze_pgn


pytestmark = pytest.mark.skipif(
    not settings.engine_available,
    reason="Stockfish is required for engine integration tests",
)


def test_analysis_runs_and_covers_every_move(sample_pgn):
    game_info, moves, summary = analyze_pgn(sample_pgn, depth=8)
    assert len(moves) == 10
    assert game_info.white == "Player"
    assert game_info.black == "Opponent"
    # every move should have gotten a classification
    for m in moves:
        assert m.classification is not None
        assert m.centipawn_loss >= 0


def test_evaluation_perspective_is_not_swapped(sample_pgn):
    """Evaluations are always reported from White's perspective, so they
    should stay in a sane, continuous range across the (fairly balanced)
    opening moves of the Ruy Lopez, not wildly flip sign each ply."""
    _, moves, _ = analyze_pgn(sample_pgn, depth=8)
    for m in moves:
        assert -3.0 <= m.evaluation_before <= 3.0
        assert -3.0 <= m.evaluation_after <= 3.0


def test_blunder_is_detected(blunder_pgn):
    _, moves, summary = analyze_pgn(blunder_pgn, depth=8)
    classifications = {m.san: m.classification for m in moves}
    # 4...Nf6?? hangs mate - must show up as a severe error, not "best"
    assert classifications["Nf6"] in (Classification.MISTAKE, Classification.BLUNDER)
    assert summary.black.stats.blunder + summary.black.stats.mistake >= 1


def test_checkmating_move_is_not_penalized(blunder_pgn):
    """The move that actually delivers checkmate should never itself be
    classified as a mistake/blunder - it's the best possible move."""
    _, moves, _ = analyze_pgn(blunder_pgn, depth=8)
    mating_move = moves[-1]
    assert mating_move.san == "Qxf7#"
    assert mating_move.classification in (
        Classification.BRILLIANT,
        Classification.BEST,
        Classification.GREAT,
        Classification.BOOK,
    )
    assert mating_move.centipawn_loss == 0


def test_cpl_never_negative(sample_pgn):
    _, moves, _ = analyze_pgn(sample_pgn, depth=8)
    for m in moves:
        assert m.centipawn_loss >= 0


def test_invalid_pgn_raises():
    with pytest.raises(PGNParseError):
        analyze_pgn("not a real pgn")


def test_summary_accuracy_in_range(sample_pgn):
    _, _, summary = analyze_pgn(sample_pgn, depth=8)
    assert 0 <= summary.white.accuracy <= 100
    assert 0 <= summary.black.accuracy <= 100
