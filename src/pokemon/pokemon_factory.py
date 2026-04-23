import requests
from models import Pokemon, Move
from pokemon import *
from core import game_print

BASE_URL = "https://pokeapi.co/api/v2"

stat_map = {
    "hp":              "hp",
    "attack":          "stat_attk",
    "defense":         "stat_def",
    "special-attack":  "stat_sp_attk",
    "special-defense": "stat_sp_def",
    "speed":           "stat_spd",
}

pokemon_registry = {}

_cache = {}

def fetch_pokemon_data(name):
    name = name.lower()

    # check cache first - note pokemon cache doesnt store moveset
    # since moves are chosen interactively each time
    cache = get_pokemon_cache()
    if name in cache:
        game_print(f"Loading {name.capitalize()} from cache...")
        return cache[name]  # return raw stat data, moveset chosen fresh each time

    try:
        response = requests.get(f"{BASE_URL}/pokemon/{name}")
        if response.status_code != 200:
            game_print(f"Could not find pokemon '{name}'. Please try again.")
            return None

        data = response.json()

        # check generation
        species_response = requests.get(data["species"]["url"])
        species_data     = species_response.json()
        gen_introduced   = int(species_data["generation"]["url"].split("/")[-2])

        if gen_introduced > 3:
            game_print(f"{name.capitalize()} is not available in generation 3!")
            return None

        # format and cache the stat data
        formatted = {
            "name":         data["name"].capitalize(),
            "type":         [t["type"]["name"].capitalize() for t in data["types"]],
            "moves":        [m["move"]["name"] for m in data["moves"]],  # for move validation
            "hp":           next(s["base_stat"] for s in data["stats"] if s["stat"]["name"] == "hp"),
            "stat_attk":    next(s["base_stat"] for s in data["stats"] if s["stat"]["name"] == "attack"),
            "stat_def":     next(s["base_stat"] for s in data["stats"] if s["stat"]["name"] == "defense"),
            "stat_sp_attk": next(s["base_stat"] for s in data["stats"] if s["stat"]["name"] == "special-attack"),
            "stat_sp_def":  next(s["base_stat"] for s in data["stats"] if s["stat"]["name"] == "special-defense"),
            "stat_spd":     next(s["base_stat"] for s in data["stats"] if s["stat"]["name"] == "speed"),
        }

        cache[name] = formatted
        save_pokemon_cache(cache)
        game_print(f"Fetched {name.capitalize()} from API and cached!")
        return formatted

    except requests.exceptions.ConnectionError:
        game_print("Could not connect to the PokeAPI. Check your internet connection.")
        return None

def create_pokemon_from_api(name, lvl=50):
    data = fetch_pokemon_data(name)
    if data is None:
        return None

    game_print(f"\n{data['name']} fetched! Now choose 4 moves.")
    moveset = build_moveset(data)

    return dict_to_pokemon(data, lvl=lvl, moveset=moveset)

def fetch_move_data(move_name):
    move_name = move_name.lower().replace(" ", "-").strip()

    # handle empty input
    if not move_name:
        game_print("Please enter a move name.")
        return None

    # check cache first
    cache = get_move_cache()
    if move_name in cache:
        game_print(f"Loading {move_name} from cache...")
        return dict_to_move(cache[move_name])

    # fetch from api
    try:
        response = requests.get(f"{BASE_URL}/move/{move_name}", timeout=5)
        
        if response.status_code == 404:
            game_print(f"Move '{move_name}' does not exist. Please try again.")
            return None
        elif response.status_code != 200:
            game_print(f"Error fetching move '{move_name}' (status code {response.status_code}). Please try again.")
            return None

        move = create_move_from_api(response.json())
        if move is not None:
            cache[move_name] = move_to_dict(move)
            save_move_cache(cache)
            game_print(f"Fetched {move_name} from API and cached!")

        return move

    except requests.exceptions.ConnectionError:
        game_print("Could not connect to the PokeAPI. Check your internet connection.")
        return None
    except requests.exceptions.Timeout:
        game_print(f"Request timed out fetching '{move_name}'. Please try again.")
        return None
    except Exception as e:
        game_print(f"Unexpected error fetching '{move_name}': {e}")
        return None

def build_moveset(pokemon_data, moveset_size=4):
    choice = input("Enter moves manually or type 'default' for default moves: ")
    
    if choice.lower() == "default":
        pokemon_name = pokemon_data["name"].lower()
        if pokemon_name in pokemon_registry:
            template = pokemon_registry[pokemon_name]
            game_print(f"Default moveset loaded from template!")
            return template["moveset"][:moveset_size]

        game_print(f"No template found for {pokemon_name.capitalize()}, loading moves from API...")
        default_moves = []
        for move in pokemon_data["moves"][:moveset_size]:
            move = fetch_move_data(move)
            if move is not None:
                default_moves.append(move)
        return default_moves

    moveset = []
    first_move = choice  # only used for the very first input
    while len(moveset) < moveset_size:
        if first_move is not None:
            move_name = first_move
            first_move = None  # reset immediately so it's never used again
        else:
            move_name = input(f"Choose move {len(moveset) + 1}/{moveset_size}: ")

        # handle empty input
        if not move_name or not move_name.strip():
            game_print("Please enter a move name.")
            continue

        if not check_pokemon_can_learn_move(pokemon_data, move_name):
            game_print(f"{pokemon_data['name']} cannot learn {move_name}!")
            continue

        move = fetch_move_data(move_name)
        if move is not None:
            game_print(f"{move.name} added to moveset!")
            moveset.append(move)

    return moveset

def check_pokemon_can_learn_move(pokemon_data, move_name):
    if not move_name:  # handle None or empty string
        return False
    move_name = move_name.lower().replace(" ", "-")
    return move_name in pokemon_data["moves"]

def create_move_from_api(move_data):

    category_map = {
        "physical": "physical",
        "special":  "special",
        "status":   "status"
    }

    # map api stat names to your stat attribute names
    stat_change_map = {
        "attack":          "stat_attk",
        "defense":         "stat_def",
        "special-attack":  "stat_sp_attk",
        "special-defense": "stat_sp_def",
        "speed":           "stat_spd",
        "accuracy":        "stat_acc",
        "evasion":         "stat_eva",
    }

    # map api move target to your target format
    target_map = {
        "selected-pokemon":         "opponent",
        "user":                     "self",
        "random-opponent":          "random",
        "all-opponents":            "opponent",
        "user-and-allies":          "self",
        "all-pokemon":              "opponent",
        "selected-pokemon-me-first":"opponent",
    }

    # build stat_change dictionary from api stat changes
    stat_change = {}
    for stat_change in move_data["stat_changes"]:
        stat_name = stat_change_map.get(stat_change["stat"]["name"])
        change    = stat_change["change"]  # positive or negative int
        target    = target_map.get(move_data["target"]["name"], "opponent")

        if stat_name is not None:
            if target not in stat_change:
                stat_change[target] = {}
            stat_change[target][stat_name] = change

    return Move(
        name     = move_data["name"].replace("-", " ").title(),
        type     = [move_data["type"]["name"].capitalize()],
        category = category_map.get(move_data["damage_class"]["name"], "status"),
        power    = move_data["power"] or 0,
        acc      = (move_data["accuracy"] or 100) / 100,
        pp       = move_data["pp"],
        stat_change  = stat_change,
        recoil   = 0.0,
    )

def create_pokemon(name, lvl=50, **overrides):
    # look up base template
    base = pokemon_registry.get(name.lower())
    if base is None:
        game_print(f"Pokemon '{name}' not found!")
        return None

    # merge base with any overrides
    return Pokemon(
        name         = overrides.get("name",         base["name"]),
        lvl          = lvl,
        type         = overrides.get("type",         base["type"]),
        stat_hp      = overrides.get("hp",           base["hp"]),
        moveset      = overrides.get("moveset",      base["moveset"]),
        stat_attk    = overrides.get("stat_attk",    base["stat_attk"]),
        stat_def     = overrides.get("stat_def",     base["stat_def"]),
        stat_sp_attk = overrides.get("stat_sp_attk", base["stat_sp_attk"]),
        stat_sp_def  = overrides.get("stat_sp_def",  base["stat_sp_def"]),
        stat_spd     = overrides.get("stat_spd",     base["stat_spd"]),
    )