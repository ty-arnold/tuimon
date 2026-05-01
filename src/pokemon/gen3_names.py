# pokemon/gen3_names.py
"""
Provides the complete list of gen 1–3 Pokémon name slugs from the local cache.

If the cache file is missing the list is fetched from PokeAPI on demand and
saved so subsequent calls are instant.
"""
import json
import os
import urllib.request

_CACHE_DIR  = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "cache",
)
_NAMES_FILE = os.path.join(_CACHE_DIR, "gen3_names.json")
_GEN3_LIMIT = 386
_API_URL    = f"https://pokeapi.co/api/v2/pokemon?limit={_GEN3_LIMIT}&offset=0"

_names_cache: list[str] | None = None


def get_gen3_names() -> list[str]:
    """Return sorted list of all gen 1–3 Pokémon name slugs."""
    global _names_cache
    if _names_cache is not None:
        return _names_cache

    if os.path.exists(_NAMES_FILE):
        with open(_NAMES_FILE) as f:
            content = f.read().strip()
        if content:
            _names_cache = json.loads(content)
            return _names_cache

    # Cache file missing — fetch and save
    _names_cache = _fetch_and_save()
    return _names_cache


def _fetch_and_save() -> list[str]:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    req = urllib.request.Request(_API_URL, headers={"User-Agent": "tuimon/0.1 (pokemon-tui)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    names = sorted(entry["name"] for entry in data["results"])
    with open(_NAMES_FILE, "w") as f:
        json.dump(names, f, indent=2)
    return names


def filter_gen3_names(query: str, limit: int = 12) -> list[str]:
    """Return up to *limit* names that contain *query* (case-insensitive)."""
    q = query.lower().strip()
    if not q:
        return []
    return [n for n in get_gen3_names() if q in n][:limit]
