"""Human-readable move explanations.

Per spec sections 14 & 32: OpenAI is STRICTLY an optional "explanation
layer". It never decides best move / classification / evaluation / accuracy
- those always come from Stockfish + the classification engine. If
OPENAI_API_KEY is unset, or the call fails for any reason, we fall back to a
deterministic template built from engine data so the app still works fully.
"""
from __future__ import annotations

from app.config import settings
from app.models.schemas import Classification

SYSTEM_PROMPT = (
    "You are a chess coach. Explain this chess mistake to a beginner. "
    "Be concise, accurate, and only use the provided engine analysis. "
    "Do not invent variations. In 3-5 sentences, cover: what happened, "
    "why it's good or bad, what was better, and a simple lesson."
)

_NOTEWORTHY = {
    Classification.BRILLIANT,
    Classification.MISTAKE,
    Classification.BLUNDER,
    Classification.INACCURACY,
}


def _template_explanation(
    san: str,
    classification: Classification,
    eval_before: float,
    eval_after: float,
    best_move_san: str,
    tactical_tags: list[str],
) -> str:
    swing = round(eval_after - eval_before, 2)
    tags_txt = ", ".join(t.replace("_", " ") for t in tactical_tags) or "no notable tactics"

    if classification == Classification.BRILLIANT:
        return (
            f"{san} is a brilliant move! It involves a material investment "
            f"({tags_txt}) but Stockfish confirms the resulting position stays "
            f"excellent for the player who moved. This kind of move is hard to "
            f"find over the board - well played."
        )

    if classification == Classification.BLUNDER:
        return (
            f"{san} is a blunder. The evaluation swung by {abs(swing)} pawns in "
            f"the opponent's favor. Stockfish's preferred move here was "
            f"{best_move_san} instead. Losing this much evaluation in one move "
            f"usually means a piece or the game itself is now in serious danger - "
            f"always double check what your opponent threatens before committing."
        )

    if classification == Classification.MISTAKE:
        return (
            f"{san} is a mistake, losing about {abs(swing)} pawns of evaluation. "
            f"{best_move_san} was stronger. Look for what this move allows the "
            f"opponent to do next time - that's usually where the problem is."
        )

    if classification == Classification.INACCURACY:
        return (
            f"{san} is an inaccuracy - not losing outright, but "
            f"{best_move_san} kept a firmer grip on the position. "
            f"Small slips like this add up over a game."
        )

    return (
        f"{san} was evaluated by Stockfish; the engine's top choice here was "
        f"{best_move_san}."
    )


def _openai_explanation(
    san: str,
    classification: Classification,
    eval_before: float,
    eval_after: float,
    best_move_san: str,
    centipawn_loss: int,
    tactical_tags: list[str],
) -> str | None:
    if not settings.ai_explanations_enabled:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        payload = {
            "move": san,
            "best_move": best_move_san,
            "evaluation_before": eval_before,
            "evaluation_after": eval_after,
            "centipawn_loss": centipawn_loss,
            "classification": classification.value,
            "tactical_context": ", ".join(tactical_tags) or "none",
        }

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": str(payload)},
            ],
            max_tokens=200,
            temperature=0.4,
        )
        text = response.choices[0].message.content
        return text.strip() if text else None
    except Exception:
        # Any failure (missing key, network, rate limit, bad response) -> fall
        # back to the template. The app must keep working without OpenAI.
        return None


def explain_move(
    *,
    san: str,
    classification: Classification,
    eval_before: float,
    eval_after: float,
    best_move_san: str,
    centipawn_loss: int,
    tactical_tags: list[str],
    only_noteworthy: bool = True,
) -> str | None:
    """Return an explanation string, or None if this move isn't worth explaining."""
    if only_noteworthy and classification not in _NOTEWORTHY:
        return None

    ai_text = _openai_explanation(
        san, classification, eval_before, eval_after, best_move_san,
        centipawn_loss, tactical_tags,
    )
    if ai_text:
        return ai_text

    return _template_explanation(
        san, classification, eval_before, eval_after, best_move_san, tactical_tags
    )
