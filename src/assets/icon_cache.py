import json
import os
from core.paths import CACHE_DIR

_cache: dict | None = None

_FALLBACK: list[str] = [
    "  ???  ",
    " (o o) ",
    " > - < ",
    " |___| ",
    "       ",
    "       ",
]


def _load() -> dict:
    global _cache
    if _cache is None:
        if os.path.exists(CACHE_DIR/"icon_cache.json"):
            with open(CACHE_DIR/"icon_cache.json") as f:
                _cache = json.load(f)
        else:
            _cache = {}
    return _cache


def get_icon(name: str) -> list[str]:
    """Return the 12×6 Rich-markup icon lines for name, or a fallback if not cached."""
    cache = _load()
    return cache.get(name.lower(), _FALLBACK)
