# presets.py
from cache_manager import get_move_cache, dict_to_move, get_pokemon_cache, dict_to_pokemon
from models import Trainer
from pokemon_factory import create_pokemon_from_api

move_cache    = get_move_cache()
pokemon_cache = get_pokemon_cache()

def get_move(name):
    key = name.lower().replace(" ", "-")
    if key not in move_cache:
        game_print(f"Move '{name}' not found in cache!")
        return None
    return dict_to_move(move_cache[key])

def get_pokemon(name, lvl=50, move_names=None):
    key = name.lower()
    if key not in pokemon_cache:
        game_print(f"Pokemon '{name}' not found in cache!")
        create_pokemon_from_api(name)
        return None

    moveset = []
    if move_names:
        for move_name in move_names:
            move = get_move(move_name)
            if move is not None:
                moveset.append(move)

    return dict_to_pokemon(pokemon_cache[key], lvl=lvl, moveset=moveset)

# --- define preset teams ---

def get_test_player():
    return Trainer(
        name        = "Ash",
        party       = [
            get_pokemon("pidgeot", lvl=50, move_names=[
                "fly",
                "quick-attack",
                "gust",
                "growl"
            ]),
            get_pokemon("gengar", lvl=50, move_names=[
                "shadow-ball",
                "hypnosis",
                "lick",
                "confuse-ray"
            ])
        ],
    )

def get_test_npc():
    return Trainer(
        name        = "Gary",
        party       = [
            get_pokemon("blastoise", lvl=50, move_names=[
                "toxic",
                "ice-beam",
                "gust",
                "withdraw"
            ]),
            get_pokemon("charizard", lvl=50, move_names=[
                "flamethrower",
                "fly",
                "slash",
                "fire-spin"
            ])
        ],
    )