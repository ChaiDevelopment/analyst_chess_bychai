"""The main analysis pipeline (spec sections 8, 9, 12, 16, 19).

PGN -> python-chess -> Stockfish -> per-position evaluation -> CPL ->
classification -> optional AI explanation -> summary/accuracy.
"""
from __future__ import annotations

import chess

from app.chess.classification import (
    ONLY_MOVE_GAP,
    UNIQUE_BEST_GAP,
    classify_move,
    detect_tactical_tags,
    win_probability,
)
from app.chess.opening_book import is_book_move, lookup_opening
from app.chess.pgn_parser import ParsedGame, parse_pgn
from app.config import settings
from app.engine.stockfish_engine import EngineResult, StockfishEngine
from app.models.schemas import (
    Classification,
    CandidateMove,
    CriticalMoment,
    GameInfo,
    GameSummary,
    MoveAnalysis,
    MoveStats,
    PlayerSummary,
    PositionAnalyzeResponse,
)
from app.services.accuracy import accuracy_from_move_quality
from app.services.explanation import explain_move


def _mate_magnitude(mate_in: int) -> float:
    """Pawn-equivalent magnitude for a mate score, signed by who mates.

    Kept in a realistic pawn range (similar to how chess.com caps its eval
    bar around +/-10) rather than an arbitrarily huge number, so that CPL
    and accuracy stay meaningful even across a mate transition.
    mate_in >= 0 (via our >=0 convention) means White delivers/delivered mate.
    """
    magnitude = 10.0 - min(abs(mate_in), 9) * 0.3  # ranges 10.0 down to 7.3
    return magnitude if mate_in >= 0 else -magnitude


def _eval_for_mover(score_pawns: float | None, mate_in: int | None, color: str) -> float:
    """Convert a White-perspective score into "from the mover's point of view"."""
    value = _mate_magnitude(mate_in) if mate_in is not None else (score_pawns or 0.0)
    return value if color == "white" else -value


def _white_perspective(score_pawns: float | None, mate_in: int | None) -> float:
    if mate_in is not None:
        return _mate_magnitude(mate_in)
    return score_pawns or 0.0


def _needs_multipv(
    *,
    is_book: bool,
    cpl: int,
    eval_before_for_mover: float,
    tactical_tags: list[str],
    board_before: chess.Board,
) -> bool:
    """Reserve the extra MultiPV search for plausible tactical candidates."""
    if is_book:
        return False
    if cpl >= 75 and eval_before_for_mover >= 1.5:
        return True
    # Do not skip MultiPV merely because a first shallow pass reports a
    # sizeable loss.  Those are exactly the positions where a quiet tactical
    # resource (for example ...Qf6 followed by a forcing attack) is most
    # likely to be mislabelled.
    if cpl >= 20:
        return True
    return (
        bool(tactical_tags)
        or abs(eval_before_for_mover) >= 1.5
        or board_before.legal_moves.count() <= 18
    )


def _append_multipv_tags(
    *,
    tags: list[str],
    board_before: chess.Board,
    move: chess.Move,
    mover_color: str,
    eval_before_for_mover: float,
    eval_after_for_mover: float,
    mate_after: int | None,
    multipv_result: EngineResult,
) -> tuple[list[str], bool, float]:
    """Turn a bounded MultiPV result into transparent classifier signals."""
    candidates = multipv_result.candidates
    if not candidates:
        return tags, False, 0.0

    is_best = candidates[0].move_uci == move.uci()
    if len(candidates) < 2:
        return tags, is_best, 0.0

    best_score = _eval_for_mover(
        candidates[0].score_pawns, candidates[0].mate_in, mover_color
    )
    second_score = _eval_for_mover(
        candidates[1].score_pawns, candidates[1].mate_in, mover_color
    )
    gap = max(0.0, best_score - second_score)
    enriched = list(tags)

    if is_best and gap >= UNIQUE_BEST_GAP:
        enriched.append("unique_best")
    if is_best and gap >= ONLY_MOVE_GAP:
        enriched.append("only_move")

    board_after = board_before.copy()
    board_after.push(move)
    quiet = not board_before.is_capture(move) and not board_after.is_check()
    if is_best and quiet and gap >= UNIQUE_BEST_GAP:
        enriched.append("quiet_tactical")

    # The selected MultiPV line contains the played move, opponent best
    # response, and continuation, avoiding another tactical deep search.
    if is_best and gap >= UNIQUE_BEST_GAP and len(multipv_result.principal_variation_san) >= 3:
        enriched.append("tactical_sequence")
    if is_best and mate_after is not None and _eval_for_mover(None, mate_after, mover_color) > 0:
        enriched.append("mating_threat")
    if is_best and gap >= UNIQUE_BEST_GAP and eval_after_for_mover - eval_before_for_mover >= 1.0:
        enriched.append("tactical_conversion")
    if (
        is_best
        and gap >= ONLY_MOVE_GAP
        and eval_before_for_mover <= -1.5
        and eval_after_for_mover >= eval_before_for_mover - 0.15
    ):
        enriched.append("defensive_resource")

    return list(dict.fromkeys(enriched)), is_best, round(gap, 2)


def _build_stats(moves: list[MoveAnalysis], color: str) -> tuple[MoveStats, float, float]:
    stats = MoveStats()
    losses: list[int] = []
    move_qualities: list[float] = []
    field_map = {
        Classification.BRILLIANT: "brilliant",
        Classification.GREAT: "great",
        Classification.BEST: "best",
        Classification.EXCELLENT: "excellent",
        Classification.GOOD: "good",
        Classification.BOOK: "book",
        Classification.INACCURACY: "inaccuracy",
        Classification.MISTAKE: "mistake",
        Classification.BLUNDER: "blunder",
        Classification.MISS: "miss",
    }
    for m in moves:
        if m.color != color:
            continue
        field = field_map[m.classification]
        setattr(stats, field, getattr(stats, field) + 1)
        losses.append(m.centipawn_loss)
        if m.classification != Classification.BOOK:
            before = m.evaluation_before if color == "white" else -m.evaluation_before
            after = m.evaluation_after if color == "white" else -m.evaluation_after
            move_qualities.append(100.0 - max(0.0, win_probability(before) - win_probability(after)))

    avg_cpl = sum(losses) / len(losses) if losses else 0.0
    acc = accuracy_from_move_quality(move_qualities)
    return stats, avg_cpl, acc


def analyze_pgn(
    pgn_text: str,
    depth: int | None = None,
    progress_cb=None,
) -> tuple[GameInfo, list[MoveAnalysis], GameSummary]:
    """Run the full pipeline and return (game_info, moves, summary).

    progress_cb, if given, is called as progress_cb(current_index, total)
    after each move is analyzed (spec section 21 - progress reporting).
    """
    parsed: ParsedGame = parse_pgn(pgn_text)
    total = len(parsed.moves)
    use_depth = depth or settings.ANALYSIS_DEPTH

    results: list[MoveAnalysis] = []
    uci_sequence: list[str] = []

    with StockfishEngine(depth=use_depth) as engine:
        # Evaluate the starting position once.
        prev_eval: EngineResult = engine.analyze(chess.STARTING_FEN, depth=use_depth)

        for parsed_move in parsed.moves:
            board_before = chess.Board(parsed_move.fen_before)
            move_obj = board_before.parse_san(parsed_move.san)

            # Position BEFORE the move was already evaluated as the previous
            # iteration's "after" (or the opening position for move 1). This
            # avoids analyzing every position twice.
            eval_before = prev_eval

            board_after = chess.Board(parsed_move.fen_after)
            eval_after = engine.analyze(parsed_move.fen_after, depth=use_depth)

            mover_color = parsed_move.color
            eval_before_mover = _eval_for_mover(
                eval_before.score_pawns, eval_before.mate_in, mover_color
            )
            eval_after_mover = _eval_for_mover(
                eval_after.score_pawns, eval_after.mate_in, mover_color
            )

            # Centipawn loss: how much worse the position got for the mover,
            # compared to what the engine thought was possible before the move.
            cpl_pawns = max(0.0, eval_before_mover - eval_after_mover)
            cpl = int(round(cpl_pawns * 100))

            uci_sequence.append(move_obj.uci())
            book = is_book_move(uci_sequence)

            tactical_tags = detect_tactical_tags(board_before, move_obj, board_after)

            is_best = move_obj.uci() == eval_before.best_move_uci
            uniqueness_gap = 0.0
            variation_before = eval_before.principal_variation_san
            if _needs_multipv(
                is_book=book,
                cpl=cpl,
                eval_before_for_mover=eval_before_mover,
                tactical_tags=tactical_tags,
                board_before=board_before,
            ):
                # Verify both the best line and the played line at the same
                # deeper depth. Comparing separately searched before/after
                # positions is prone to horizon noise and was the source of
                # false inaccuracies for tactical moves.
                verification_depth = max(use_depth, 18)
                multipv_before = engine.analyze(
                    parsed_move.fen_before, depth=verification_depth, multipv=3
                )
                played_line = engine.analyze(
                    parsed_move.fen_before,
                    depth=verification_depth,
                    root_moves=[move_obj],
                )
                verified_before_mover = _eval_for_mover(
                    multipv_before.score_pawns, multipv_before.mate_in, mover_color
                )
                verified_after_mover = _eval_for_mover(
                    played_line.score_pawns, played_line.mate_in, mover_color
                )
                cpl = int(round(max(0.0, verified_before_mover - verified_after_mover) * 100))
                eval_before_mover = verified_before_mover
                eval_after_mover = verified_after_mover
                # The root-move result is the engine's evaluation of the
                # actual resulting position, so expose it and reuse it for
                # the following ply.
                eval_before = multipv_before
                eval_after = played_line
                tactical_tags, multipv_is_best, uniqueness_gap = _append_multipv_tags(
                    tags=tactical_tags,
                    board_before=board_before,
                    move=move_obj,
                    mover_color=mover_color,
                    eval_before_for_mover=eval_before_mover,
                    eval_after_for_mover=eval_after_mover,
                    mate_after=eval_after.mate_in,
                    multipv_result=multipv_before,
                )
                is_best = multipv_is_best
                variation_before = multipv_before.principal_variation_san

            classification = classify_move(
                cpl=cpl,
                eval_before_for_mover=eval_before_mover,
                eval_after_for_mover=eval_after_mover,
                is_book=book,
                is_best_move=is_best,
                tactical_tags=tactical_tags,
                uniqueness_gap=uniqueness_gap,
                win_probability_loss=max(
                    0.0, win_probability(eval_before_mover) - win_probability(eval_after_mover)
                ),
            )

            explanation = explain_move(
                san=parsed_move.san,
                classification=classification,
                eval_before=_white_perspective(eval_before.score_pawns, eval_before.mate_in),
                eval_after=_white_perspective(eval_after.score_pawns, eval_after.mate_in),
                best_move_san=eval_before.best_move_san or parsed_move.san,
                centipawn_loss=cpl,
                tactical_tags=tactical_tags,
            )

            variation = []
            if classification in (
                Classification.MISTAKE,
                Classification.BLUNDER,
                Classification.BRILLIANT,
                Classification.GREAT,
                Classification.MISS,
                Classification.INACCURACY,
            ):
                variation = variation_before[:8]

            results.append(
                MoveAnalysis(
                    ply=parsed_move.ply,
                    move_number=parsed_move.move_number,
                    color=parsed_move.color,
                    san=parsed_move.san,
                    uci=parsed_move.uci,
                    fen_before=parsed_move.fen_before,
                    fen_after=parsed_move.fen_after,
                    evaluation_before=round(
                        _white_perspective(eval_before.score_pawns, eval_before.mate_in), 2
                    ),
                    evaluation_after=round(
                        _white_perspective(eval_after.score_pawns, eval_after.mate_in), 2
                    ),
                    mate_before=eval_before.mate_in,
                    mate_after=eval_after.mate_in,
                    best_move=eval_before.best_move_uci,
                    best_move_san=eval_before.best_move_san,
                    centipawn_loss=cpl,
                    classification=classification,
                    is_book=book,
                    tactical_tags=tactical_tags,
                    variation=variation,
                    explanation=explanation,
                )
            )

            prev_eval = eval_after

            if progress_cb:
                progress_cb(len(results), total)

    game_info = GameInfo(
        event=parsed.headers.get("Event"),
        site=parsed.headers.get("Site"),
        date=parsed.headers.get("Date"),
        white=parsed.headers.get("White"),
        black=parsed.headers.get("Black"),
        result=parsed.headers.get("Result"),
        total_plies=total,
    )

    eco, opening_name = lookup_opening(uci_sequence)
    if eco and opening_name:
        game_info.eco = eco
        game_info.opening = opening_name

    summary = build_summary(results, game_info)
    return game_info, results, summary


def analyze_position_move(fen: str, move_uci: str, depth: int | None = None) -> PositionAnalyzeResponse:
    """Review a move chosen on the interactive board.

    The best and played moves are searched from the identical root position,
    which makes this result suitable for immediate click-to-move feedback.
    """
    try:
        board_before = chess.Board(fen)
        move_obj = chess.Move.from_uci(move_uci)
    except ValueError as exc:
        raise ValueError("Invalid position or UCI move") from exc
    if move_obj not in board_before.legal_moves:
        raise ValueError("That move is not legal in this position")

    mover_color = "white" if board_before.turn == chess.WHITE else "black"
    san = board_before.san(move_obj)
    board_after = board_before.copy()
    board_after.push(move_obj)
    use_depth = depth or settings.ANALYSIS_DEPTH
    verification_depth = max(use_depth, 18)

    with StockfishEngine(depth=verification_depth) as engine:
        best_line = engine.analyze(fen, depth=verification_depth, multipv=3)
        played_line = engine.analyze(
            fen, depth=verification_depth, root_moves=[move_obj]
        )

    before_for_mover = _eval_for_mover(
        best_line.score_pawns, best_line.mate_in, mover_color
    )
    after_for_mover = _eval_for_mover(
        played_line.score_pawns, played_line.mate_in, mover_color
    )
    cpl = int(round(max(0.0, before_for_mover - after_for_mover) * 100))
    tags = detect_tactical_tags(board_before, move_obj, board_after)
    tags, is_best, uniqueness_gap = _append_multipv_tags(
        tags=tags,
        board_before=board_before,
        move=move_obj,
        mover_color=mover_color,
        eval_before_for_mover=before_for_mover,
        eval_after_for_mover=after_for_mover,
        mate_after=played_line.mate_in,
        multipv_result=best_line,
    )
    classification = classify_move(
        cpl=cpl,
        eval_before_for_mover=before_for_mover,
        eval_after_for_mover=after_for_mover,
        is_book=False,
        is_best_move=is_best,
        tactical_tags=tags,
        uniqueness_gap=uniqueness_gap,
        win_probability_loss=max(
            0.0, win_probability(before_for_mover) - win_probability(after_for_mover)
        ),
    )
    move = MoveAnalysis(
        ply=0,
        move_number=board_before.fullmove_number,
        color=mover_color,
        san=san,
        uci=move_uci,
        fen_before=fen,
        fen_after=board_after.fen(),
        evaluation_before=round(_white_perspective(best_line.score_pawns, best_line.mate_in), 2),
        evaluation_after=round(_white_perspective(played_line.score_pawns, played_line.mate_in), 2),
        mate_before=best_line.mate_in,
        mate_after=played_line.mate_in,
        best_move=best_line.best_move_uci,
        best_move_san=best_line.best_move_san,
        centipawn_loss=cpl,
        classification=classification,
        tactical_tags=tags,
        variation=best_line.principal_variation_san[:8],
        explanation=explain_move(
            san=san,
            classification=classification,
            eval_before=_white_perspective(best_line.score_pawns, best_line.mate_in),
            eval_after=_white_perspective(played_line.score_pawns, played_line.mate_in),
            best_move_san=best_line.best_move_san or san,
            centipawn_loss=cpl,
            tactical_tags=tags,
        ),
    )
    candidates = [
        CandidateMove(
            uci=candidate.move_uci,
            san=candidate.move_san,
            evaluation=round(_white_perspective(candidate.score_pawns, candidate.mate_in), 2),
            mate_in=candidate.mate_in,
            variation=candidate.principal_variation_san[:8],
        )
        for candidate in best_line.candidates
    ]
    return PositionAnalyzeResponse(move=move, candidates=candidates, engine_depth=verification_depth)


def build_summary(moves: list[MoveAnalysis], game_info: GameInfo) -> GameSummary:
    white_stats, white_avg_cpl, white_acc = _build_stats(moves, "white")
    black_stats, black_avg_cpl, black_acc = _build_stats(moves, "black")

    def swing_for(m: MoveAnalysis) -> float:
        before = m.evaluation_before if m.color == "white" else -m.evaluation_before
        after = m.evaluation_after if m.color == "white" else -m.evaluation_after
        return before - after  # positive = got worse for the mover

    biggest_mistake = None
    best_move_played = None
    most_critical = None

    mistakes_and_blunders = [m for m in moves if m.classification in (
        Classification.MISTAKE, Classification.BLUNDER, Classification.MISS
    )]
    if mistakes_and_blunders:
        worst = max(mistakes_and_blunders, key=lambda m: m.centipawn_loss)
        biggest_mistake = CriticalMoment(
            ply=worst.ply, move_number=worst.move_number, color=worst.color,
            san=worst.san, classification=worst.classification,
            evaluation_swing=round(swing_for(worst), 2),
        )

    brilliants = [m for m in moves if m.classification == Classification.BRILLIANT]
    greats = [m for m in moves if m.classification == Classification.GREAT]
    bests = [m for m in moves if m.classification == Classification.BEST]
    standout_pool = brilliants or greats or bests
    if standout_pool:
        best_pick = max(standout_pool, key=lambda m: swing_for(m) * -1)
        best_move_played = CriticalMoment(
            ply=best_pick.ply, move_number=best_pick.move_number, color=best_pick.color,
            san=best_pick.san, classification=best_pick.classification,
            evaluation_swing=round(swing_for(best_pick), 2),
        )

    if moves:
        most_swingy = max(moves, key=lambda m: abs(swing_for(m)))
        most_critical = CriticalMoment(
            ply=most_swingy.ply, move_number=most_swingy.move_number,
            color=most_swingy.color, san=most_swingy.san,
            classification=most_swingy.classification,
            evaluation_swing=round(swing_for(most_swingy), 2),
        )

    return GameSummary(
        white=PlayerSummary(
            accuracy=white_acc,
            average_centipawn_loss=round(white_avg_cpl, 1),
            stats=white_stats,
        ),
        black=PlayerSummary(
            accuracy=black_acc,
            average_centipawn_loss=round(black_avg_cpl, 1),
            stats=black_stats,
        ),
        biggest_mistake=biggest_mistake,
        best_move_played=best_move_played,
        most_critical_position=most_critical,
        opening=game_info.opening or "Opening detection coming soon",
        result=game_info.result,
    )
