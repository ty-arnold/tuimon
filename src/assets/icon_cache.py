import json
import os

_CACHE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "cache", "icon_cache.json"
)

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
        if os.path.exists(_CACHE_PATH):
            with open(_CACHE_PATH) as f:
                _cache = json.load(f)
        else:
            _cache = {}
    return _cache


def get_icon(name: str) -> list[str]:
    """Return the 12×6 Rich-markup icon lines for name, or a fallback if not cached."""
    cache = _load()
    return cache.get(name.lower(), _FALLBACK)
