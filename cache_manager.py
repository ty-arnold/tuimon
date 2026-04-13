import json
import os

CACHE_DIR     = "cache"
POKEMON_CACHE = os.path.join(CACHE_DIR, "pokemon_cache.json")
MOVE_CACHE    = os.path.join(CACHE_DIR, "move_cache.json")

def ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def load_cache(filepath):
    ensure_cache_dir()
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_cache(filepath, data):
    ensure_cache_dir()
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def get_move_cache():
    return load_cache(MOVE_CACHE)

def save_move_cache(data):
    save_cache(MOVE_CACHE, data)

def get_pokemon_cache():
    return load_cache(POKEMON_CACHE)

def save_pokemon_cache(data):
    save_cache(POKEMON_CACHE, data)

def move_to_dict(move):
    return {
        "name":     move.name,
        "type":     move.type,
        "category": move.category,
        "power":    move.power,
        "acc":      move.acc,
        "pp":       move.pp,
        "effects":  move.effects,
        "recoil":   move.recoil,
    }

def dict_to_move(data):
    from objects.moves import Move
    return Move(
        name     = data["name"],
        type     = data["type"],
        category = data["category"],
        power    = data["power"],
        acc      = data["acc"],
        pp       = data["pp"],
        effects  = data["effects"],
        recoil   = data["recoil"],
    )

def pokemon_to_dict(pokemon):
    return {
        "name":         pokemon.name,
        "type":         pokemon.type,
        "hp":           pokemon.hp,
        "stat_attk":    pokemon.stat_attk,
        "stat_def":     pokemon.stat_def,
        "stat_sp_attk": pokemon.stat_sp_attk,
        "stat_sp_def":  pokemon.stat_sp_def,
        "stat_spd":     pokemon.stat_spd,
        "stat_acc":     pokemon.stat_acc,
        "stat_eva":     pokemon.stat_eva,
        "moves":        pokemon.moves
    }

def dict_to_pokemon(data, lvl=50, moveset=None):
    from models import Pokemon
    return Pokemon(
        name         = data["name"],
        lvl          = lvl,
        type         = data["type"],
        stat_hp      = data["hp"],
        moveset      = moveset or [],
        stat_attk    = data["stat_attk"],
        stat_def     = data["stat_def"],
        stat_sp_attk = data["stat_sp_attk"],
        stat_sp_def  = data["stat_sp_def"],
        stat_spd     = data["stat_spd"],
    )