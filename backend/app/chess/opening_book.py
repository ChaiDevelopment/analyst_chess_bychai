"""A tiny local ECO opening book.

Free/local per spec section 18: no paid API. This is intentionally small -
enough to recognize common openings and tell whether early moves are "book".
For anything not covered, opening detection gracefully degrades to
"Opening detection coming soon" and book-move detection just returns False.

Keyed by the UCI move sequence (from the starting position) joined with
spaces, mapping to (ECO code, opening name).
"""
from __future__ import annotations

OPENINGS: dict[str, tuple[str, str]] = {
    "e2e4": ("B00", "King's Pawn Opening"),
    "e2e4 e7e5": ("C20", "King's Pawn Game"),
    "e2e4 e7e5 g1f3": ("C40", "King's Knight Opening"),
    "e2e4 e7e5 g1f3 b8c6": ("C44", "King's Knight Opening"),
    "e2e4 e7e5 g1f3 b8c6 f1b5": ("C60", "Ruy Lopez"),
    "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6": ("C68", "Ruy Lopez, Morphy Defense"),
    "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4": ("C77", "Ruy Lopez, Morphy Defense"),
    "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6": ("C84", "Ruy Lopez, Closed"),
    "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1": ("C84", "Ruy Lopez, Closed"),
    "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7": ("C84", "Ruy Lopez, Closed"),
    "e2e4 e7e5 g1f3 b8c6 f1c4": ("C50", "Italian Game"),
    "e2e4 e7e5 g1f3 b8c6 f1c4 f8c5": ("C53", "Italian Game, Giuoco Piano"),
    "e2e4 e7e5 g1f3 b8c6 d2d4": ("C44", "Scotch Game"),
    "e2e4 e7e5 f2f4": ("C30", "King's Gambit"),
    "e2e4 c7c5": ("B20", "Sicilian Defense"),
    "e2e4 c7c5 g1f3": ("B27", "Sicilian Defense"),
    "e2e4 c7c5 g1f3 d7d6": ("B50", "Sicilian Defense, Old Sicilian"),
    "e2e4 c7c5 g1f3 b8c6": ("B30", "Sicilian Defense"),
    "e2e4 c7c5 c2c3": ("B22", "Sicilian Defense, Alapin Variation"),
    "e2e4 e7e6": ("C00", "French Defense"),
    "e2e4 c7c6": ("B10", "Caro-Kann Defense"),
    "e2e4 d7d5": ("B01", "Scandinavian Defense"),
    "e2e4 g8f6": ("B00", "Alekhine's Defense"),
    "e2e4 d7d6": ("B07", "Pirc Defense"),
    "e2e4 g7g6": ("B06", "Modern Defense"),
    "d2d4": ("D00", "Queen's Pawn Opening"),
    "d2d4 d7d5": ("D00", "Queen's Pawn Game"),
    "d2d4 d7d5 c2c4": ("D06", "Queen's Gambit"),
    "d2d4 d7d5 c2c4 e7e6": ("D30", "Queen's Gambit Declined"),
    "d2d4 d7d5 c2c4 c7c6": ("D10", "Slav Defense"),
    "d2d4 d7d5 c2c4 d5c4": ("D20", "Queen's Gambit Accepted"),
    "d2d4 g8f6": ("A45", "Indian Defense"),
    "d2d4 g8f6 c2c4": ("A50", "Indian Game"),
    "d2d4 g8f6 c2c4 g7g6": ("E60", "King's Indian Defense"),
    "d2d4 g8f6 c2c4 e7e6": ("E00", "Queen's Indian / Nimzo-Indian setup"),
    "d2d4 g8f6 c2c4 e7e6 b1c3 f8b4": ("E20", "Nimzo-Indian Defense"),
    "d2d4 f7f5": ("A80", "Dutch Defense"),
    "c2c4": ("A10", "English Opening"),
    "g1f3": ("A04", "Reti Opening"),
    "g2g3": ("A00", "King's Fianchetto Opening"),
    "b2b3": ("A01", "Larsen's Opening"),
}

MAX_BOOK_PLY = 10  # only the first N plies can ever be "book"


def lookup_opening(uci_moves: list[str]) -> tuple[str | None, str | None]:
    """Return (eco, name) for the longest known prefix of this game, else (None, None)."""
    best: tuple[str, str] | None = None
    for length in range(1, min(len(uci_moves), MAX_BOOK_PLY) + 1):
        key = " ".join(uci_moves[:length])
        if key in OPENINGS:
            best = OPENINGS[key]
    return best if best else (None, None)


def is_book_move(uci_moves_up_to_and_including: list[str]) -> bool:
    """Whether the position after this move sequence is still a known book line."""
    if len(uci_moves_up_to_and_including) > MAX_BOOK_PLY:
        return False
    key = " ".join(uci_moves_up_to_and_including)
    return key in OPENINGS
