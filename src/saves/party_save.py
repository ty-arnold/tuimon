import json
import os

_SAVES_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "saves")
_PARTY_FILE = os.path.join(_SAVES_DIR, "party.json")


def load_party_data() -> list[dict]:
    """Return raw save data: list of {name, level, moves} dicts."""
    if not os.path.exists(_PARTY_FILE):
        return []
    with open(_PARTY_FILE) as f:
        content = f.read().strip()
        return json.loads(content) if content else []


def save_party_data(party: list[dict]) -> None:
    """Persist raw party data to disk immediately."""
    os.makedirs(_SAVES_DIR, exist_ok=True)
    with open(_PARTY_FILE, "w") as f:
        json.dump(party, f, indent=2)


def build_party_from_save():
    """Reconstruct a list of Pokemon objects from the save file. Returns [] if empty."""
    from pokemon.cache_manager import get_pokemon_cache, get_move_cache, dict_to_pokemon, dict_to_move

    party_data = load_party_data()
    if not party_data:
        return []

    poke_cache = get_pokemon_cache()
    move_cache = get_move_cache()
    party      = []

    for slot in party_data:
        name      = slot["name"].lower()
        poke_data = poke_cache.get(name)
        if poke_data is None:
            continue

        moveset = []
        for slug in slot.get("moves", []):
            move_data = move_cache.get(slug)
            if move_data:
                moveset.append(dict_to_move(move_data))

        party.append(dict_to_pokemon(poke_data, lvl=slot.get("level", 50), moveset=moveset))

    return party
