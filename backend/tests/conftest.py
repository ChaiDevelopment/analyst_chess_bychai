import os
import sys
from pathlib import Path

# Make sure `app` is importable when running `pytest` from the backend/ dir.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("STOCKFISH_PATH", "/usr/games/stockfish")

import pytest


SAMPLE_PGN = """[Event "Casual Game"]
[Site "?"]
[Date "2026.09.08"]
[White "Player"]
[Black "Opponent"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7
"""

BLUNDER_PGN = """[Event "Test"]
[White "A"]
[Black "B"]
[Result "*"]

1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7#
"""


@pytest.fixture
def sample_pgn():
    return SAMPLE_PGN


@pytest.fixture
def blunder_pgn():
    return BLUNDER_PGN
