from app.services.accuracy import accuracy_from_average_cpl, accuracy_from_move_quality


def test_zero_cpl_is_perfect():
    assert accuracy_from_average_cpl(0) == 100.0


def test_accuracy_decreases_with_higher_cpl():
    a1 = accuracy_from_average_cpl(10)
    a2 = accuracy_from_average_cpl(50)
    a3 = accuracy_from_average_cpl(200)
    assert a1 > a2 > a3


def test_normal_average_cpl_does_not_collapse_to_zero():
    assert accuracy_from_average_cpl(25) == 86.1
    assert accuracy_from_average_cpl(100) == 54.9


def test_accuracy_is_clamped_between_0_and_100():
    assert 0.0 <= accuracy_from_average_cpl(0) <= 100.0
    assert 0.0 <= accuracy_from_average_cpl(100000) <= 100.0
    assert accuracy_from_average_cpl(100000) == 0.0


def test_game_accuracy_is_one_to_one_hundred_and_penalises_errors():
    assert accuracy_from_move_quality([100, 100]) == 100.0
    assert 1.0 <= accuracy_from_move_quality([100, 1]) < 100.0
