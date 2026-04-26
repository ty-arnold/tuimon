# scripts/fetch_gen3_moves.py
import sys
import os
import requests
import copy
from typing import Optional

# add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

# import only what the script actually needs
from models import MultiTurn, Accumulator
from pokemon import get_move_cache, save_move_cache, status_effect_to_dict
from data import *
from overrides.move_overrides import *

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
    "confusion": confusion,
    "curse":     curse
}

HITS_INVULNERABLE = {
    "thunder":    {"states": ["flying"],       "damage_modifier": {}},
    "hurricane":  {"states": ["flying"],       "damage_modifier": {}},
    "gust":       {"states": ["flying"],       "damage_modifier": {"flying": 2.0}},
    "twister":    {"states": ["flying"],       "damage_modifier": {"flying": 2.0}},
    "whirlpool":  {"states": ["underwater"],   "damage_modifier": {"underwater": 2.0}},
    "surf":       {"states": ["underwater"],   "damage_modifier": {"underwater": 2.0}},
    "earthquake": {"states": ["underground"],  "damage_modifier": {"underground": 2.0}},
    "magnitude":  {"states": ["underground"],  "damage_modifier": {"underground": 2.0}},
    "fissure":    {"states": ["underground"],  "damage_modifier": {}},
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

def convert_move(move_data: dict) -> Optional[dict]:
    from dataclasses import asdict, replace

    category_map = {
        "physical": "physical",
        "special":  "special",
        "status":   "status"
    }

    # skip moves introduced after gen 3
    gen_url    = move_data.get("generation", {}).get("url", "")
    gen_number = int(gen_url.split("/")[-2]) if gen_url else 0
    if gen_number > 3:
        return None

    move_name = move_data["name"].lower()

    # build stat_change dictionary
    stat_change = {}
    for change in move_data.get("stat_changes", []):
        stat_name = stat_change_map.get(change["stat"]["name"])
        amount    = change["change"]
        
        # positive changes target self, negative changes target opponent
        if amount > 0:
            target = "self"
        else:
            target = target_map.get(move_data["target"]["name"], "opponent")

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
    stat_chance   = meta.get("stat_chance", 0)
    recoil        = abs(drain) / 100 if drain < 0 else 0.0
    lifesteal     = drain / 100      if drain > 0 else 0.0
    heal          = healing / 100    if healing > 0 else 0.0

    # extract status effect from ailment
    ailment        = meta.get("ailment", {}) or {}
    ailment_name   = ailment.get("name", "none")
    ailment_chance = meta.get("ailment_chance", 0)
    if ailment_chance == 0 and ailment_name != "none":
        ailment_chance = 1.0
    else:
        ailment_chance = ailment_chance / 100
    status_effect = STATUS_EFFECT_MAP.get(ailment_name)
    if status_effect is not None and ailment_chance > 0:
        status_effect = copy.deepcopy(status_effect)
        status_effect.chance_to_apply = ailment_chance

    # build multi turn data
    is_manual_multi_turn = move_name in MULTI_TURN_OVERRIDES
    is_api_multi_turn    = min_turns is not None and min_turns > 1 and move_name in MULTI_TURN_OVERRIDES

    multi_turn = None
    if is_manual_multi_turn or is_api_multi_turn:
        if move_name in MULTI_TURN_OVERRIDES:
            multi_turn = MULTI_TURN_OVERRIDES[move_name]
            if min_turns is not None and min_turns > 1:
                multi_turn = replace(multi_turn, turns=max_turns or min_turns)
        else:
            multi_turn = MultiTurn(
                turns          = max_turns or min_turns or 2,
                charge_turn    = 1,
                charge_message = "is preparing!",
            )

    move_effect = None
    if move_name in MOVE_EFFECT_OVERRIDES:
        from dataclasses import asdict
        move_effect = asdict(MOVE_EFFECT_OVERRIDES[move_name])

    description = ""
    for entry in move_data.get("effect_entries", []):
        if entry.get("language", {}).get("name") == "en":
            description = entry.get("short_effect", "")
            # replace $effect_chance with actual value if present
            effect_chance = move_data.get("effect_chance")
            if effect_chance and "$effect_chance" in description:
                description = description.replace(
                    "$effect_chance",
                    str(effect_chance)
                )
            break

    # build required fields
    result: dict = {
        "name":     move_data["name"].replace("-", " ").title(),
        "type":     [move_data["type"]["name"].capitalize()],
        "category": category_map.get(move_data["damage_class"]["name"], "status"),
        "power":    move_data["power"] or 0,
        "acc":      None if move_data["accuracy"] is None else move_data["accuracy"] / 100,
        "pp":       move_data["pp"],
    }

    # only add optional fields if non default
    if stat_change:
        result["stat_change"]        = stat_change
    if recoil > 0.0:
        result["recoil"]             = recoil
    if lifesteal > 0.0:
        result["lifesteal"]          = lifesteal
    if heal > 0.0:
        result["heal"]               = heal
    if min_hits is not None:
        result["min_hits"]           = min_hits
    if max_hits is not None:
        result["max_hits"]           = max_hits
    if crit_rate > 0:
        result["crit_rate"]          = crit_rate
    if flinch_chance > 0.0:
        result["flinch_chance"]      = flinch_chance
    if move_data.get("priority", 0) != 0:
        result["priority"]           = move_data["priority"]
    if stat_chance > 0:
        result["stat_change_chance"] = stat_chance / 100
    if multi_turn is not None:
        result["multi_turn"]         = asdict(multi_turn)
    if HITS_INVULNERABLE.get(move_name):
        result["hits_invulnerable"]  = HITS_INVULNERABLE[move_name]["states"]
    if HITS_INVULNERABLE.get(move_name, {}).get("damage_modifier"):
        result["damage_modifier"]    = HITS_INVULNERABLE[move_name]["damage_modifier"]
    if IMMUNE_TYPE_OVERRIDES.get(move_name):
        result["immune_types"]       = IMMUNE_TYPE_OVERRIDES[move_name]
    if status_effect is not None:
        result["status_effect"]      = status_effect_to_dict(status_effect)
    if move_effect is not None:
        result["move_effect"] = move_effect
    if description:
        result["description"] = description

    return result

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