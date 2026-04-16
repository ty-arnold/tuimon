# scripts/fetch_gen3_moves.py
import requests
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cache_manager import get_move_cache, save_move_cache, status_effect_to_dict
from objects.status_effects import poison, paralysis, sleep, burn, freeze

BASE_URL  = "https://pokeapi.co/api/v2"
CACHE_DIR = "cache"

stat_change_map = {
    "attack":          "stat_attk",
    "defense":         "stat_def",
    "special-attack":  "stat_sp_attk",
    "special-defense": "stat_sp_def",
    "speed":           "stat_spd",
    "accuracy":        "stat_acc",
    "evasion":         "stat_eva",
}

target_map = {
    "selected-pokemon":          "opponent",
    "user":                      "self",
    "random-opponent":           "random",
    "all-opponents":             "opponent",
    "user-and-allies":           "self",
    "all-pokemon":               "opponent",
    "selected-pokemon-me-first": "opponent",
}

STATUS_EFFECT_MAP = {
    "paralysis": paralysis,
    "poison":    poison,
    "sleep":     sleep,
    "burn":      burn,
    "freeze":    freeze,
}

MULTI_TURN_OVERRIDES = {
    "fly": {
        "invulnerable":           True,
        "invulnerable_state":     "flying",
        "charge_message":         "flew up high!",
        "invulnerable_message":   "is high up in the air!"
    },
    "bounce": {
        "invulnerable":           True,
        "invulnerable_state":     "flying",
        "charge_message":         "sprang up!",
        "invulnerable_message":   "is high up in the air!"
    },
    "dig": {
        "invulnerable":           True,
        "invulnerable_state":     "underground",
        "charge_message":         "dug a hole!",
        "invulnerable_message":   "is underground!"
    },
    "dive": {
        "invulnerable":           True,
        "invulnerable_state":     "underwater",
        "charge_message":         "hid underwater!",
        "invulnerable_message":   "is hiding underwater!"
    },
    "skull-bash": {
        "invulnerable":           False,
        "invulnerable_state":     None,
        "charge_message":         "tucked in its head!",
        "invulnerable_message":   ""
    },
    "solar-beam": {
        "invulnerable":           False,
        "invulnerable_state":     None,
        "charge_message":         "absorbed light!",
        "invulnerable_message":   ""
    },
    "razor-wind": {
        "invulnerable":           False,
        "invulnerable_state":     None,
        "charge_message":         "whipped up a whirlwind!",
        "invulnerable_message":   ""
    },
    "sky-attack": {
        "invulnerable":           False,
        "invulnerable_state":     None,
        "charge_message":         "is glowing!",
        "invulnerable_message":   ""
    }
}

HITS_INVULNERABLE = {
    "thunder":      ["flying"],
    "hurricane":    ["flying"],
    "twister":      ["flying"],
    "gust":         ["flying"],
    "whirlpool":    ["underwater"],
    "surf":         ["underwater"],
    "earthquake":   ["underground"],
    "magnitude":    ["underground"],
    "fissure":      ["underground"],
}

def fetch_move_names_for_generation(gen):
    print(f"Fetching gen {gen} move list...")
    response = requests.get(f"{BASE_URL}/generation/{gen}")
    if response.status_code != 200:
        print(f"Failed to fetch gen {gen} data: {response.status_code}")
        return []
    data  = response.json()
    moves = [m["name"] for m in data["moves"]]
    print(f"Found {len(moves)} moves in gen {gen}")
    return moves

def fetch_all_move_names():
    all_moves = []
    for gen in [1, 2, 3]:
        moves = fetch_move_names_for_generation(gen)
        all_moves.extend(moves)

    # deduplicate while preserving order
    unique_moves = list(dict.fromkeys(all_moves))
    print(f"\nTotal unique moves across gen 1-3: {len(unique_moves)}")
    return unique_moves

def fetch_move_data(move_name):
    response = requests.get(f"{BASE_URL}/move/{move_name}")
    if response.status_code != 200:
        print(f"Failed to fetch move {move_name}: {response.status_code}")
        return None
    return response.json()

def convert_move(move_data):
    category_map = {
        "physical": "physical",
        "special":  "special",
        "status":   "status"
    }

    meta           = move_data.get("meta") or {}
    ailment        = meta.get("ailment", {}) or {}
    ailment_name   = ailment.get("name", "none")
    ailment_chance = meta.get("ailment_chance", 0)
    status_effect  = STATUS_EFFECT_MAP.get(ailment_name)

    # api returns 0 for guaranteed effects, treat as 1.0
    if ailment_chance == 0 and ailment_name != "none":
        ailment_chance = 1.0
    else:
        ailment_chance = ailment_chance / 100

    if status_effect is not None and ailment_chance > 0:
        import copy
        status_effect = copy.deepcopy(status_effect)
        status_effect.chance_to_apply = ailment_chance

    stat_change = {}
    for change in move_data.get("stat_changes", []):
        stat_name = stat_change_map.get(change["stat"]["name"])
        amount    = change["change"]
        target    = target_map.get(move_data["target"]["name"], "opponent")

        if stat_name is not None:
            if target not in stat_change:
                stat_change[target] = {}
            stat_change[target][stat_name] = amount

    # extract meta data safely
    meta          = move_data.get("meta") or {}
    min_turns     = meta.get("min_turns")
    max_turns     = meta.get("max_turns")
    drain         = meta.get("drain", 0)
    healing       = meta.get("healing", 0)
    min_hits      = meta.get("min_hits")
    max_hits      = meta.get("max_hits")
    crit_rate     = meta.get("crit_rate", 0)
    flinch_chance = meta.get("flinch_chance", 0) / 100
    recoil        = abs(drain) / 100 if drain < 0 else 0.0
    lifesteal     = drain / 100      if drain > 0 else 0.0
    heal          = healing / 100    if healing > 0 else 0.0
    move_name     = move_data["name"].lower()

    # set multi_turn if:
    # 1. move is in MULTI_TURN_OVERRIDES (manually defined multi turn moves)
    # 2. OR api indicates variable turn duration
    is_manual_multi_turn  = move_name in MULTI_TURN_OVERRIDES
    is_api_multi_turn     = min_turns is not None and min_turns > 1 and move_name in MULTI_TURN_OVERRIDES

    multi_turn = None
    if is_manual_multi_turn or is_api_multi_turn:
        multi_turn = {
            "turns":                2,  # default to 2 turns
            "invulnerable":         False,
            "invulnerable_state":   None,
            "charge_message":       "is preparing!",
            "invulnerable_message": "is invulnerable!"
        }
        # apply overrides
        multi_turn.update(MULTI_TURN_OVERRIDES[move_name])

        # override turns from api if available
        if min_turns is not None and min_turns > 1:
            multi_turn["turns"] = max_turns or min_turns

    return {
        "name":              move_data["name"].replace("-", " ").title(),
        "type":              [move_data["type"]["name"].capitalize()],
        "category":          category_map.get(move_data["damage_class"]["name"], "status"),
        "power":             move_data["power"] or 0,
        "acc":               (move_data["accuracy"] or 100) / 100,
        "pp":                move_data["pp"],
        "stat_change":       stat_change,
        "recoil":            recoil,
        "lifesteal":         lifesteal,
        "heal":              heal,
        "min_hits":          min_hits,
        "max_hits":          max_hits,
        "crit_rate":         crit_rate,
        "flinch_chance":     flinch_chance,
        "priority":          move_data.get("priority", 0),
        "multi_turn":        multi_turn,
        "hits_invulnerable": HITS_INVULNERABLE.get(move_name, []),
        "status_effect":     status_effect_to_dict(status_effect),
    }

def fetch_all_gen3_moves():
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache = get_move_cache()

    move_names = fetch_all_move_names()
    total      = len(move_names)
    skipped    = 0
    fetched    = 0
    failed     = 0

    print(f"\nStarting fetch for {total} moves...\n")

    for i, move_name in enumerate(move_names, 1):
        print(f"[{i}/{total}] Processing {move_name}...", end=" ")

        if move_name in cache:
            print("already cached, skipping.")
            skipped += 1
            continue

        move_data = fetch_move_data(move_name)
        if move_data is None:
            print("FAILED.")
            failed += 1
            continue

        cache[move_name] = convert_move(move_data)
        print("done.")
        fetched += 1

        # save every 10 moves in case of interruption
        if fetched % 10 == 0:
            save_move_cache(cache)
            print(f"--- Progress saved ({fetched} fetched so far) ---")

    # final save
    save_move_cache(cache)
    print(f"\nComplete!")
    print(f"Fetched:  {fetched}")
    print(f"Skipped:  {skipped}")
    print(f"Failed:   {failed}")
    print(f"Total moves in cache: {len(cache)}")

if __name__ == "__main__":
    fetch_all_gen3_moves()