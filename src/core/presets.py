from typing import Optional
from pokemon.cache_manager import get_move_cache, dict_to_move, get_pokemon_cache, dict_to_pokemon
from models import Trainer, Pokemon
from pokemon.pokemon_factory import create_pokemon_from_api
from core.logger import logger

move_cache    = get_move_cache()
pokemon_cache = get_pokemon_cache()

def get_move(name):
    key = name.lower().replace(" ", "-")
    if key not in move_cache:
        print(f"Move '{name}' not found in cache!")
        return None
    return dict_to_move(move_cache[key])

def get_pokemon(name: str, lvl: int = 50, move_names: Optional[list[str]] = None) -> Optional[Pokemon]:
    key = name.lower()
    if key not in pokemon_cache:
        print(f"Pokemon '{name}' not found in cache!")
        return None

    moveset = []
    if move_names:
        for move_name in move_names:
            move = get_move(move_name)
            if move is not None:
                moveset.append(move)

    return dict_to_pokemon(pokemon_cache[key], lvl=lvl, moveset=moveset)

# --- define preset teams ---

def get_test_player() -> Trainer:
    party = [
        get_pokemon("pidgeot", lvl=50, move_names=[
            "fly",
            "sand-attack",
            "razor-leaf",
            "toxic"
        ]),
        get_pokemon("nidorino", lvl=50, move_names=[
            "double-kick",
            "horn-attack",
            "thunder-wave",
            "toxic"
        ]),
        get_pokemon("lapras", lvl=50, move_names=[
            "fly",
            "dig",
            "growl",
            "toxic"
        ]),
        get_pokemon("nidoking", lvl=50, move_names=[
            "double-kick",
            "horn-attack",
            "thunder-wave",
            "toxic"
        ]),
        get_pokemon("charizard", lvl=50, move_names=[
            "fly",
            "dig",
            "growl",
            "toxic"
        ]),
        get_pokemon("alakazam", lvl=50, move_names=[
            "double-kick",
            "horn-attack",
            "thunder-wave",
            "toxic"
        ])
    ]
    # filter out any None values and assert party is valid
    valid_party = [p for p in party if p is not None]
    assert len(valid_party) > 0, "Failed to create player party - no valid pokemon!"
    
    return Trainer(
        name         = "Ash",
        party        = valid_party
    )

def get_test_npc() -> Trainer:
    party = [
            get_pokemon("alakazam", lvl=50, move_names=[
                "double-kick",
                "horn-attack",
                "thunder-wave",
                "toxic"
            ]),
            get_pokemon("blastoise", lvl=50, move_names=[
                "toxic",
                "toxic",
                "toxic",
                "toxic"
            ]),
            get_pokemon("charizard", lvl=50, move_names=[
                "flamethrower",
                "fly",
                "slash",
                "fire-spin"
            ])
        ]
    valid_party = [p for p in party if p is not None]
    assert len(valid_party) > 0, "Failed to create player party - no valid pokemon!"
    
    return Trainer(
        name         = "Gary",
        party        = valid_party
    )