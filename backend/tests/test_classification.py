from app.chess.classification import classify_by_cpl, classify_move
from app.models.schemas import Classification


def test_cpl_zero_is_best():
    assert classify_by_cpl(0) == Classification.BEST


def test_cpl_boundaries():
    assert classify_by_cpl(10) == Classification.BEST
    assert classify_by_cpl(11) == Classification.EXCELLENT
    assert classify_by_cpl(25) == Classification.EXCELLENT
    assert classify_by_cpl(26) == Classification.GOOD
    assert classify_by_cpl(50) == Classification.GOOD
    assert classify_by_cpl(51) == Classification.INACCURACY
    assert classify_by_cpl(100) == Classification.INACCURACY
    assert classify_by_cpl(101) == Classification.MISTAKE
    assert classify_by_cpl(200) == Classification.MISTAKE
    assert classify_by_cpl(201) == Classification.BLUNDER


def test_cpl_large_is_blunder():
    assert classify_by_cpl(9999) == Classification.BLUNDER


def test_forcing_engine_best_move_is_great():
    assert classify_move(
        cpl=0,
        eval_before_for_mover=0.0,
        eval_after_for_mover=1.0,
        is_book=False,
        is_best_move=True,
        tactical_tags=["winning_material"],
    ) == Classification.GREAT


def test_missed_favourable_opportunity_is_miss():
    assert classify_move(
        cpl=100,
        eval_before_for_mover=2.0,
        eval_after_for_mover=1.0,
        is_book=False,
        is_best_move=False,
        tactical_tags=[],
        uniqueness_gap=0.9,
    ) == Classification.MISS


def test_quiet_unique_tactical_move_can_be_brilliant():
    assert classify_move(
        cpl=0,
        eval_before_for_mover=0.2,
        eval_after_for_mover=1.2,
        is_book=False,
        is_best_move=True,
        tactical_tags=["unique_best", "quiet_tactical", "tactical_sequence"],
        uniqueness_gap=1.0,
    ) == Classification.BRILLIANT
