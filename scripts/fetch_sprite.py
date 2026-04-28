"""
Fetch Pokemon sprites from PokeAPI, convert to Rich-markup half-block art,
and cache to cache/sprite_cache.json.

Usage:
    uv run python scripts/fetch_sprite.py pikachu
    uv run python scripts/fetch_sprite.py pikachu blastoise charizard
    uv run python scripts/fetch_sprite.py --all        # cache every pokemon in pokemon_cache.json
"""

import io
import json
import sys
import os
import requests
from PIL import Image

POKEAPI    = "https://pokeapi.co/api/v2/pokemon"
CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "sprite_cache.json")
POK_CACHE  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "pokemon_cache.json")

FRONT_W, FRONT_H = 24, 12
BACK_W,  BACK_H  = 30, 15


# ── Fetching ──────────────────────────────────────────────────────────────────

def fetch_sprite_urls(name: str) -> tuple[str, str, str | None, str | None, int]:
    resp = requests.get(f"{POKEAPI}/{name.lower()}", timeout=10)
    resp.raise_for_status()
    data   = resp.json()
    front  = data["sprites"]["front_default"]
    back   = data["sprites"]["back_default"]
    if not front:
        raise ValueError(f"No front_default sprite for {name}")
    if not back:
        raise ValueError(f"No back_default sprite for {name}")

    anim   = (data["sprites"]
              .get("versions", {})
              .get("generation-v", {})
              .get("black-white", {})
              .get("animated", {}))
    front_anim = anim.get("front_default")
    back_anim  = anim.get("back_default")
    return front, back, front_anim, back_anim


def download_image(url: str) -> Image.Image:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return Image.open(io.BytesIO(resp.content))


def extract_gif_frames(gif: Image.Image) -> tuple[list[Image.Image], int]:
    """Return (frames as RGBA Images, average frame duration in ms)."""
    frames    = []
    durations = []
    try:
        while True:
            frames.append(gif.copy().convert("RGBA"))
            durations.append(gif.info.get("duration", 100))
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
    avg_ms = int(sum(durations) / len(durations)) if durations else 100
    return frames, avg_ms


# ── Conversion ────────────────────────────────────────────────────────────────

def _hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def crop_to_content(img: Image.Image) -> Image.Image:
    """Crop transparent padding so all sprites anchor to their actual content."""
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def image_to_rich_markup(img: Image.Image, width: int, height: int) -> list[str]:
    """
    Crop to content, resize to (width, height*2), and encode two pixel rows
    per character using ▀/▄ with Rich colour markup. Transparent pixels become spaces.
    """
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


def cache_pokemon(name: str, cache: dict) -> bool:
    key = name.lower()
    if key in cache:
        print(f"  {name}: already cached, skipping")
        return False

    try:
        front_url, back_url, front_anim_url, back_anim_url = fetch_sprite_urls(key)
        front_rows = image_to_rich_markup(download_image(front_url).convert("RGBA"), FRONT_W, FRONT_H)
        back_rows  = image_to_rich_markup(download_image(back_url).convert("RGBA"),  BACK_W,  BACK_H)
        entry = {"front": front_rows, "back": back_rows}

        if front_anim_url and back_anim_url:
            front_gif                = download_image(front_anim_url)
            back_gif                 = download_image(back_anim_url)
            front_frames, front_ms   = extract_gif_frames(front_gif)
            back_frames,  back_ms    = extract_gif_frames(back_gif)
            entry["front_anim"]      = [image_to_rich_markup(f, FRONT_W, FRONT_H) for f in front_frames]
            entry["back_anim"]       = [image_to_rich_markup(f, BACK_W,  BACK_H)  for f in back_frames]
            entry["frame_ms"]        = (front_ms + back_ms) // 2
            print(f"  {name}: cached — static + {len(front_frames)} anim frames @ {entry['frame_ms']}ms")
        else:
            print(f"  {name}: cached — static only (no Gen 5 anim)")

        cache[key] = entry
        return True
    except Exception as e:
        print(f"  {name}: failed — {e}")
        return False


# ── Preview (ANSI, for terminal testing) ─────────────────────────────────────

def rich_to_ansi_approx(rows: list[str]) -> list[str]:
    """Very rough Rich→ANSI for terminal preview only."""
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
    args = sys.argv[1:]

    if not args:
        print("Usage: fetch_sprite.py <name> [name ...] | --all")
        sys.exit(1)

    cache = load_cache()

    if "--all" in args:
        if not os.path.exists(POK_CACHE):
            print(f"Pokemon cache not found at {POK_CACHE}")
            sys.exit(1)
        with open(POK_CACHE) as f:
            names = list(json.load(f).keys())
        print(f"Caching {len(names)} pokemon...")
        for name in names:
            cache_pokemon(name, cache)
        save_cache(cache)
        print(f"\nDone. {len(cache)} sprites in cache.")
    else:
        for name in args:
            cache_pokemon(name, cache)
        save_cache(cache)

        # preview the last one in terminal
        key = args[-1].lower()
        if key in cache:
            front = rich_to_ansi_approx(cache[key]["front"])
            back  = rich_to_ansi_approx(cache[key]["back"])
            gap   = "    "
            print(f"\n  {'front':<{FRONT_W + len(gap)}}back")
            print(f"  {key.capitalize():<{FRONT_W + len(gap)}}{key.capitalize()}\n")
            for f, b in zip(front, back):
                print("  " + f + gap + b)
            print()
