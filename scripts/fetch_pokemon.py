# scripts/fetch_pokemon.py
import requests
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pokemon.cache_manager import get_pokemon_cache, save_pokemon_cache

BASE_URL = "https://pokeapi.co/api/v2"

def fetch_and_cache_pokemon(name):
    cache = get_pokemon_cache()
    name  = name.lower()

    if name in cache:
        print(f"{name} already in cache, skipping.")
        return

    response = requests.get(f"{BASE_URL}/pokemon/{name}")
    if response.status_code != 200:
        print(f"Failed to fetch {name}: {response.status_code}")
        return

    data = response.json()

    # check generation
    species_response = requests.get(data["species"]["url"])
    species_data     = species_response.json()
    gen_introduced   = int(species_data["generation"]["url"].split("/")[-2])

    if gen_introduced > 3:
        print(f"{name} is not available in generation 3!")
        return

    formatted = {
        "name":         data["name"].capitalize(),
        "type":         [t["type"]["name"].capitalize() for t in data["types"]],
        "moves":        [m["move"]["name"] for m in data["moves"]],
        "hp":           next(s["base_stat"] for s in data["stats"] if s["stat"]["name"] == "hp"),
        "stat_attk":    next(s["base_stat"] for s in data["stats"] if s["stat"]["name"] == "attack"),
        "stat_def":     next(s["base_stat"] for s in data["stats"] if s["stat"]["name"] == "defense"),
        "stat_sp_attk": next(s["base_stat"] for s in data["stats"] if s["stat"]["name"] == "special-attack"),
        "stat_sp_def":  next(s["base_stat"] for s in data["stats"] if s["stat"]["name"] == "special-defense"),
        "stat_spd":     next(s["base_stat"] for s in data["stats"] if s["stat"]["name"] == "speed"),
        "stat_acc":     1.0,
        "stat_eva":     1.0,
    }

    cache[name] = formatted
    save_pokemon_cache(cache)
    print(f"Fetched and cached {name.capitalize()}!")

if __name__ == "__main__":
    pokemon_to_fetch = [
        "charizard",
        "blastoise",
        "alakazam",
        "pidgeot"
        # add any others you need here
    ]
    for name in pokemon_to_fetch:
        fetch_and_cache_pokemon(name)