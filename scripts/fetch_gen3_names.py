#!/usr/bin/env python3
"""
Fetch all gen 1–3 Pokémon names from PokeAPI and write them to
cache/gen3_names.json as a sorted list of lowercase slugs.

Usage:
    python scripts/fetch_gen3_names.py
"""
import json
import os
import sys
import urllib.request

CACHE_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")
NAMES_FILE = os.path.join(CACHE_DIR, "gen3_names.json")
GEN3_LIMIT = 386   # national dex 1–386 covers gens 1, 2, 3
API_URL    = f"https://pokeapi.co/api/v2/pokemon?limit={GEN3_LIMIT}&offset=0"


def fetch_names() -> list[str]:
    print(f"Fetching {GEN3_LIMIT} Pokémon names from PokeAPI…", flush=True)
    req = urllib.request.Request(API_URL, headers={"User-Agent": "tuimon/0.1 (pokemon-tui)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    names = [entry["name"] for entry in data["results"]]
    print(f"  Got {len(names)} names.")
    return sorted(names)


def main() -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Check if already cached
    if os.path.exists(NAMES_FILE):
        with open(NAMES_FILE) as f:
            existing = json.loads(f.read())
        if len(existing) >= GEN3_LIMIT:
            print(f"Cache already has {len(existing)} names — skipping fetch.")
            print(f"  Delete {NAMES_FILE} to force a re-fetch.")
            sys.exit(0)

    names = fetch_names()

    with open(NAMES_FILE, "w") as f:
        json.dump(names, f, indent=2)

    print(f"Saved {len(names)} names to {NAMES_FILE}")


if __name__ == "__main__":
    main()
