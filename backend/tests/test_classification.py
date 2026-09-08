from app.chess.classification import classify_by_cpl
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
