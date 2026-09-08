"""
Central application configuration, loaded from environment variables (.env).

Nothing chess-specific lives here beyond the constants the rest of the app
needs to stay configurable, as required by the spec (ANALYSIS_DEPTH,
STOCKFISH_PATH, OPENAI_API_KEY, etc).
"""
import os
import shutil
from pathlib import Path

try:
    from dotenv import load_dotenv  # optional convenience, not a hard dependency

    load_dotenv()
except ImportError:  # pragma: no cover - python-dotenv is optional
    pass


def _find_stockfish() -> str | None:
    """Resolve a usable Stockfish binary path.

    Order: STOCKFISH_PATH env var -> `stockfish` on PATH -> a couple of
    common install locations (apt/homebrew put it in different spots).
    """
    configured = os.getenv("STOCKFISH_PATH", "").strip().strip('"')
    if configured:
        configured_path = Path(configured).expanduser()
        if configured_path.is_file():
            return str(configured_path)

    # A local development install can be kept inside backend/tools without
    # requiring a machine-specific .env path. The directory is gitignored.
    bundled_dir = Path(__file__).resolve().parents[1] / "tools" / "stockfish"
    if bundled_dir.is_dir():
        bundled_engine = next(bundled_dir.rglob("stockfish*.exe"), None)
        if bundled_engine and bundled_engine.is_file():
            return str(bundled_engine)

    for command in ("stockfish", "stockfish.exe"):
        on_path = shutil.which(command)
        if on_path:
            return on_path

    for candidate in (
        "/usr/games/stockfish",
        "/usr/local/bin/stockfish",
        "/usr/bin/stockfish",
        "/opt/homebrew/bin/stockfish",
        "C:/Program Files/Stockfish/stockfish.exe",
        "C:/Program Files/Stockfish/stockfish-windows-x86-64-avx2.exe",
    ):
        if Path(candidate).exists():
            return candidate

    return None


def _positive_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    """Read a bounded integer setting without making startup fragile."""
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return min(max(value, minimum), maximum)


class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
    STOCKFISH_PATH: str | None = _find_stockfish()
    ANALYSIS_DEPTH: int = _positive_int("ANALYSIS_DEPTH", 16, minimum=4, maximum=30)
    MAX_PLIES: int = _positive_int("MAX_PLIES", 300, minimum=1, maximum=2_000)
    MAX_PGN_CHARS: int = _positive_int("MAX_PGN_CHARS", 50_000, minimum=1_000, maximum=1_000_000)
    CORS_ORIGINS: list[str] = [
        # Browsers send Origin without a trailing slash. Normalizing here
        # prevents a common Railway-variable typo from silently blocking CORS.
        origin.strip().rstrip("/")
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,https://analyst-chess-bychai.vercel.app",
        ).split(",")
        if origin.strip()
    ]

    @property
    def ai_explanations_enabled(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def engine_available(self) -> bool:
        return self.STOCKFISH_PATH is not None


settings = Settings()
