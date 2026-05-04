"""Ability hook functions called at specific points in the battle engine."""


def check_ability_prevents(pokemon, what: str) -> bool:
    """Check if the Pokemon's ability prevents a specific effect.
    
    Args:
        pokemon: The Pokemon whose ability to check.
        what: The effect being prevented:
            "paralysis", "poison", "sleep", "freeze", "burn", "confusion",
            "flinch", "crit",
            "acc_drop", "atk_drop", "stat_drop_by_opponent"
    
    Returns True if the ability blocks the effect.
    """
    ability = getattr(pokemon, "ability", None)
    if ability is None:
        return False
    
    name = ability.name
    what = what.lower()
    match what:
        case "paralysis":
            return name == "Limber"
        case "poison":
            return name == "Immunity"
        case "sleep":
            return name in ("Insomnia", "Vital Spirit")
        case "freeze":
            return name in ("Magma Armor", "Water Veil")
        case "burn":
            return name == "Water Veil"
        case "confusion":
            return name == "Own Tempo"
        case "flinch":
            return name == "Inner Focus"
        case "crit":
            return name in ("Battle Armor", "Shell Armor")
        case "acc_drop":
            return name == "Keen Eye"
        case "atk_drop":
            return name == "Hyper Cutter"
        case "stat_drop_by_opponent":
            return name in ("Clear Body", "White Smoke")
    
    return False
