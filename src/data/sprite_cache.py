import json
import os

_CACHE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "cache", "sprite_cache.json"
)

_cache: dict | None = None

_FALLBACK: dict[str, list[str]] = {
    "front": [
        "   .---.  ",
        "  (o   o) ",
        "   > - <  ",
        "   |___|  ",
        "  /     \\ ",
    ],
    "back": [
        "   _____  ",
        "  /     \\ ",
        " |  ~~~  |",
        "  \\_____/ ",
        "  /     \\ ",
    ],
}


def _load() -> dict:
    global _cache
    if _cache is None:
        if os.path.exists(_CACHE_PATH):
            with open(_CACHE_PATH) as f:
                _cache = json.load(f)
        else:
            _cache = {}
    return _cache


def get_sprite(name: str, view: str = "front") -> list[str]:
    cache = _load()
    entry = cache.get(name.lower(), {})
    return entry.get(view, _FALLBACK.get(view, _FALLBACK["front"]))


def get_sprite_frames(name: str, view: str = "front") -> list[list[str]] | None:
    """Return animated frames for the given view, or None if no animation cached."""
    cache = _load()
    entry = cache.get(name.lower(), {})
    key   = f"{view}_anim"
    return entry.get(key)


def get_frame_ms(name: str) -> int:
    """Return the average frame duration in ms, defaulting to 150."""
    cache = _load()
    return cache.get(name.lower(), {}).get("frame_ms", 150)
