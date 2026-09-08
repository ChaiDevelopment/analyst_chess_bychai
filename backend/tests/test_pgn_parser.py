import pytest

from app.chess.pgn_parser import PGNParseError, parse_pgn


def test_parses_valid_pgn(sample_pgn):
    game = parse_pgn(sample_pgn)
    assert len(game.moves) == 10
    assert game.moves[0].san == "e4"
    assert game.moves[0].color == "white"
    assert game.moves[1].san == "e5"
    assert game.moves[1].color == "black"
    assert game.headers["White"] == "Player"


def test_empty_pgn_raises():
    with pytest.raises(PGNParseError):
        parse_pgn("")


def test_whitespace_only_pgn_raises():
    with pytest.raises(PGNParseError):
        parse_pgn("   \n\n  ")


def test_garbage_pgn_raises():
    with pytest.raises(PGNParseError):
        parse_pgn("this is not a chess game at all, just text")


def test_illegal_move_raises():
    # Black's king cannot legally move to e2 here - illegal move.
    with pytest.raises(PGNParseError):
        parse_pgn("1. e4 e5 2. Nf3 Nc6 3. Nc3 Ke2#")


def test_moves_have_correct_fen_progression(sample_pgn):
    game = parse_pgn(sample_pgn)
    first = game.moves[0]
    assert first.fen_before.startswith(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w"
    )
    assert "e4" in first.san
    # fen_after should have the e4 pawn moved
    assert first.fen_after != first.fen_before
