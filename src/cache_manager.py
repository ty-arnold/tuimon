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
        "name":              move.name,
        "type":              move.type,
        "category":          move.category,
        "power":             move.power,
        "acc":               move.acc,
        "pp":                move.pp,
        "stat_change":       move.stat_change,
        "recoil":            move.recoil,
        "lifesteal":         move.lifesteal,
        "heal":              move.heal,
        "min_hits":          move.min_hits,
        "max_hits":          move.max_hits,
        "crit_rate":         move.crit_rate,
        "flinch_chance":     move.flinch_chance,
        "priority":          move.priority,
        "hits_invulnerable": move.hits_invulnerable or [],
        "multi_turn":        move.multi_turn,
        "status_effect":     move.status_effect
    }

def dict_to_move(data):
    from models import Move
    from status_effects import poison, paralysis, sleep, burn, freeze
    import copy

    status_effect_map = {
        "Poison":    poison,
        "Paralysis": paralysis,
        "Sleep":     sleep,
        "Burn":      burn,
        "Freeze":    freeze,
    }

    status_effect = None
    if data.get("status_effect") is not None:
        se          = data["status_effect"]
        base_effect = status_effect_map.get(se["name"])
        if base_effect is not None:
            status_effect = copy.deepcopy(base_effect)
            status_effect.chance_to_apply = se["chance_to_apply"]

    return Move(
        name              = data["name"],
        type              = data["type"],
        category          = data["category"],
        power             = data["power"],
        acc               = data["acc"],
        pp                = data["pp"],
        stat_change       = data.get("stat_change",       {}),
        recoil            = data.get("recoil",            0.0),
        lifesteal         = data.get("lifesteal",         0.0),
        heal              = data.get("heal",              0.0),
        min_hits          = data.get("min_hits",          None),
        max_hits          = data.get("max_hits",          None),
        crit_rate         = data.get("crit_rate",         0),
        flinch_chance     = data.get("flinch_chance",     0.0),
        priority          = data.get("priority",          0),
        multi_turn        = data.get("multi_turn",        None),
        hits_invulnerable = data.get("hits_invulnerable", []),
        status_effect     = status_effect
    )

def status_effect_to_dict(effect):
    if effect is None:
        return None
    return {
        "name":            effect.name,
        "chance_to_apply": effect.chance_to_apply,
    }

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