import json
import os
from models import Move

CACHE_DIR     = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "cache")
POKEMON_CACHE = os.path.join(CACHE_DIR, "pokemon_cache.json")
MOVE_CACHE    = os.path.join(CACHE_DIR, "move_cache.json")
ABILITY_CACHE = os.path.join(CACHE_DIR, "abilities.json")

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
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_move_cache():
    return load_cache(MOVE_CACHE)

def save_move_cache(data):
    save_cache(MOVE_CACHE, data)

def get_pokemon_cache():
    return load_cache(POKEMON_CACHE)

def save_pokemon_cache(data):
    save_cache(POKEMON_CACHE, data)

def move_to_dict(move: Move) -> dict:
    result = {
        "name":     move.name,
        "type":     move.type,
        "category": move.category,
        "power":    move.power,
        "acc":      move.acc,
        "pp":       move.pp,
    }

    if move.multi_turn is not None:
        mt: dict = {
            "turns":        move.multi_turn.turns,
            "charge_turn":  move.multi_turn.charge_turn,
            "charge_message": move.multi_turn.charge_message,
        }
        if move.multi_turn.invulnerable:
            mt["invulnerable"]         = move.multi_turn.invulnerable
        if move.multi_turn.invulnerable_state:
            mt["invulnerable_state"]   = move.multi_turn.invulnerable_state
        if move.multi_turn.invulnerable_message:
            mt["invulnerable_message"] = move.multi_turn.invulnerable_message
        if move.multi_turn.accumulator:
            mt["accumulator"]          = move.multi_turn.accumulator
        result["multi_turn"] = mt

    if move.weather is not None:
        result["weather"] = move.weather

    return result


def dict_to_move(data: dict) -> Move:
    from models import Move, MultiTurn, MoveEffect
    from data.status_effects import poison, paralysis, sleep, burn, freeze
    import copy

    multi_turn = None
    if data.get("multi_turn") is not None:
        mt = data["multi_turn"]
        multi_turn = MultiTurn(
            turns                = mt["turns"],
            charge_turn          = mt["charge_turn"],
            charge_message       = mt["charge_message"],
            invulnerable         = mt.get("invulnerable", False),
            invulnerable_state   = mt.get("invulnerable_state"),
            invulnerable_message = mt.get("invulnerable_message", ""),
            accumulator          = mt.get("accumulator")
        )

    move_effect = None
    if data.get("move_effect") is not None:
        me = data["move_effect"]
        move_effect = MoveEffect(
            effect_type  = me["effect_type"],
            target       = me.get("target", "self"),
            turns        = me.get("turns", 1),
            properties   = me.get("properties", {}),
            bypass_moves = me.get("bypass_moves", []),
            message      = me.get("message", ""),
            fail_message = me.get("fail_message", "")
        )

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
        name               = data["name"],
        type               = data["type"],
        category           = data["category"],
        power              = data["power"],
        pp                 = data["pp"],
        max_pp             = data.get("pp", 20),
        acc                = data.get("acc", None),
        stat_change        = data.get("stat_change",       {}),
        stat_change_chance = data.get("stat_change_chance", 1.0),
        recoil             = data.get("recoil",            0.0),
        lifesteal          = data.get("lifesteal",         0.0),
        heal               = data.get("heal",              0.0),
        min_hits           = data.get("min_hits",          None),
        max_hits           = data.get("max_hits",          None),
        crit_rate          = data.get("crit_rate",         0),
        flinch_chance      = data.get("flinch_chance",     0.0),
        priority           = data.get("priority",          0),
        multi_turn         = multi_turn,
        hits_invulnerable  = data.get("hits_invulnerable", []),
        status_effect      = status_effect,
        immune_types       = data.get("immune_types", []),
        immune_moves       = data.get("immune_moves", []),
        move_effect        = move_effect,
        weather            = data.get("weather", None),
        description        = data.get("description", ""),
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
    from data.abilities import Ability

    ability = None
    abilities_list = data.get("abilities", [])
    if abilities_list:
        ability_cache = get_ability_cache()
        ability_cache_lower = {k.lower(): v for k, v in ability_cache.items()}
        ability_name = abilities_list[0]  # use first (primary) ability
        ability_data = ability_cache_lower.get(ability_name.lower())
        if ability_data:
            ability = Ability(
                name=ability_data["name"],
                description=ability_data.get("short_effect", ""),
            )

    p = Pokemon(
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
    p.ability = ability
    return p


def get_ability_cache() -> dict:
    """Load ability data from cache file."""
    if not os.path.exists(ABILITY_CACHE):
        return {}
    with open(ABILITY_CACHE, "r") as f:
        return json.load(f)