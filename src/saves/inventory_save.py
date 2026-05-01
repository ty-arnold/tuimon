import json
import os

_SAVES_DIR      = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "saves")
_INVENTORY_FILE = os.path.join(_SAVES_DIR, "inventory.json")


def load_inventory() -> list[dict]:
    """Return list of {name, level, moves} dicts. Auto-seeds from gen3_names if missing."""
    if os.path.exists(_INVENTORY_FILE):
        with open(_INVENTORY_FILE) as f:
            content = f.read().strip()
            return json.loads(content) if content else []

    return _seed_inventory()


def save_inventory(inventory: list[dict]) -> None:
    os.makedirs(_SAVES_DIR, exist_ok=True)
    with open(_INVENTORY_FILE, "w") as f:
        json.dump(inventory, f, indent=2)


def _seed_inventory() -> list[dict]:
    from pokemon.gen3_names import get_gen3_names
    inventory = [{"name": name, "level": 50, "moves": []} for name in get_gen3_names()]
    save_inventory(inventory)
    return inventory
