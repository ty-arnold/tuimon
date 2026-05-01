"""
Fetch Pokemon sprites from PokeAPI, convert to small Rich-markup half-block icons,
and cache to cache/icon_cache.json.

Usage:
    uv run python scripts/fetch_icons.py pikachu
    uv run python scripts/fetch_icons.py pikachu blastoise charizard
    uv run python scripts/fetch_icons.py --all        # cache every pokemon in pokemon_cache.json
    uv run python scripts/fetch_icons.py --force pikachu  # re-cache even if present
"""

import io
import json
import sys
import os
import requests
from PIL import Image

POKEAPI    = "https://pokeapi.co/api/v2/pokemon"
CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "icon_cache.json")
POK_CACHE  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "pokemon_cache.json")

ICON_W, ICON_H = 12, 6


# ── Fetching ──────────────────────────────────────────────────────────────────

def fetch_icon_url(name: str) -> str:
    resp = requests.get(f"{POKEAPI}/{name.lower()}", timeout=10)
    resp.raise_for_status()
    return resp.json()["sprites"]["front_default"]


def download_image(url: str) -> Image.Image:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return Image.open(io.BytesIO(resp.content))


# ── Conversion ────────────────────────────────────────────────────────────────

def _hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def crop_to_content(img: Image.Image) -> Image.Image:
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def image_to_rich_markup(img: Image.Image, width: int, height: int) -> list[str]:
    img  = crop_to_content(img)
    img  = img.resize((width, height * 2), Image.NEAREST)
    rows = []

    for row in range(height):
        line = ""
        for col in range(width):
            top = img.getpixel((col, row * 2))
            bot = img.getpixel((col, row * 2 + 1))

            top_vis = top[3] > 32
            bot_vis = bot[3] > 32

            if not top_vis and not bot_vis:
                line += " "
            elif top_vis and not bot_vis:
                c = _hex(*top[:3])
                line += f"[{c}]▀[/{c}]"
            elif not top_vis and bot_vis:
                c = _hex(*bot[:3])
                line += f"[{c}]▄[/{c}]"
            else:
                fg = _hex(*top[:3])
                bg = _hex(*bot[:3])
                line += f"[{fg} on {bg}]▀[/{fg} on {bg}]"
        rows.append(line)

    return rows


# ── Cache ─────────────────────────────────────────────────────────────────────

def load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    return {}


def save_cache(cache: dict) -> None:
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def cache_icon(name: str, cache: dict, force: bool = False) -> bool:
    key = name.lower()
    if key in cache and not force:
        print(f"  {name}: already cached, skipping")
        return False

    try:
        url  = fetch_icon_url(key)
        img  = download_image(url).convert("RGBA")
        rows = image_to_rich_markup(img, ICON_W, ICON_H)
        cache[key] = rows
        print(f"  {name}: cached ({ICON_W}×{ICON_H})")
        return True
    except Exception as e:
        print(f"  {name}: failed — {e}")
        return False


# ── Preview (ANSI, for terminal testing) ─────────────────────────────────────

def rich_to_ansi_approx(rows: list[str]) -> list[str]:
    import re
    out = []
    for row in rows:
        line = re.sub(r"\[#([0-9a-f]{6}) on #([0-9a-f]{6})\](.)\[/[^\]]+\]",
                      lambda m: f"\033[38;2;{int(m[1][0:2],16)};{int(m[1][2:4],16)};{int(m[1][4:6],16)}m"
                                f"\033[48;2;{int(m[2][0:2],16)};{int(m[2][2:4],16)};{int(m[2][4:6],16)}m"
                                f"{m[3]}\033[0m", row)
        line = re.sub(r"\[#([0-9a-f]{6})\](.)\[/#[0-9a-f]{6}\]",
                      lambda m: f"\033[38;2;{int(m[1][0:2],16)};{int(m[1][2:4],16)};{int(m[1][4:6],16)}m"
                                f"{m[2]}\033[0m", line)
        out.append(line)
    return out


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args  = sys.argv[1:]
    force = "--force" in args
    args  = [a for a in args if a != "--force"]

    if not args:
        print("Usage: fetch_icons.py [--force] <name> [name ...] | --all")
        sys.exit(1)

    cache = load_cache()

    if "--all" in args:
        # Use gen3_names as the authoritative source (covers all 386)
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
        from pokemon.gen3_names import get_gen3_names
        names = get_gen3_names()
        print(f"Caching icons for {len(names)} pokemon...")
        for name in names:
            cache_icon(name, cache, force=force)
        save_cache(cache)
        print(f"\nDone. {len(cache)} icons in cache.")
    else:
        for name in args:
            cache_icon(name, cache, force=force)
        save_cache(cache)

        # preview the last one in terminal
        key = args[-1].lower()
        if key in cache:
            lines = rich_to_ansi_approx(cache[key])
            print(f"\n  {key.capitalize()} ({ICON_W}×{ICON_H})\n")
            for line in lines:
                print("  " + line)
            print()
