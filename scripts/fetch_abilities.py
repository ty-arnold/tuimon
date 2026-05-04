# scripts/fetch_abilities.py
import requests
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from pokemon.cache_manager import ensure_cache_dir

CACHE_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "abilities.json")

BASE_URL = "https://pokeapi.co/api/v2"


def fetch_all_abilities(limit=80):
    """Fetch all abilities from PokeAPI (up to limit)."""
    cache = load_ability_cache()
    count = 0

    response = requests.get(f"{BASE_URL}/ability?limit={limit}")
    if response.status_code != 200:
        print(f"Failed to fetch ability list: {response.status_code}")
        return

    results = response.json()["results"]

    for item in results:
        name = item["name"]
        if name in cache:
            continue

        detail = requests.get(item["url"]).json()

        # Check generation — only Gen 1-3 abilities
        gen = int(detail["generation"]["url"].split("/")[-2])
        if gen > 3:
            continue

        # Get English display name (e.g., "Volt Absorb" instead of "volt-absorb")
        display_name = name.replace("-", " ").title()
        for n in detail.get("names", []):
            if n["language"]["name"] == "en":
                display_name = n["name"]
                break

        # Get English flavor text
        entries = detail.get("flavor_text_entries", [])
        description = ""
        for entry in entries:
            if entry["language"]["name"] == "en":
                description = entry["flavor_text"].replace("\n", " ").replace("\f", " ")
                break

        # Short English effect (from effect_entries)
        effect_entries = detail.get("effect_entries", [])
        short_effect = ""
        for entry in effect_entries:
            if entry["language"]["name"] == "en":
                short_effect = entry.get("short_effect", "")
                break

        cache[name] = {
            "name": display_name,
            "description": description,
            "short_effect": short_effect,
        }
        save_ability_cache(cache)
        count += 1
        print(f"  Cached: {name} (Gen {gen})")

    print(f"\nSaved {len(cache)} abilities to cache ({count} new).")


def load_ability_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}


def save_ability_cache(data: dict) -> None:
    ensure_cache_dir()
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    fetch_all_abilities()
