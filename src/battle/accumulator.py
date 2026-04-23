from typing import Optional
from models import Move, Trainer, Accumulator
from core import game_print
from battle.damage import calculate_damage, get_type_multiplier

def handle_accumulator(
    move:         Move,
    attacker:     Trainer,
    defender:     Trainer,
    current_turn: int
) -> Optional[int]:
    if move.multi_turn is None:
        return None

    config = move.multi_turn.accumulator
    if config is None:
        return None

    # accumulate phase - not the release turn yet
    if attacker.locked_turns > 0:
        if config.type == "damage_taken":
            pass  # accumulated in apply_damage hook
        elif config.type == "turn_count":
            attacker.active().accumulator += 1
        return None  # still accumulating

    # release turn
    return release_accumulator(move, attacker, defender, config)

def release_accumulator(
    move:     Move,
    attacker: Trainer,
    defender: Trainer,
    config:   Accumulator
) -> int:
    accumulated = attacker.active().accumulator

    if config.release_message:
        game_print(f"{attacker.active().name} {config.release_message}!")

    damage = 0

    if config.type == "damage_taken":
        if config.release_formula == "double":
            damage = accumulated * 2

    elif config.type == "turn_count":
        base_damage, _ = calculate_damage(move, attacker, defender, 1)
        if config.release_formula == "exponential":
            damage = round(base_damage * (2 ** accumulated))
        elif config.release_formula == "double":
            damage = round(base_damage * (accumulated + 1))

    if not config.ignore_type:
        multiplier = get_type_multiplier(move.type[0], defender.active().type)
        damage     = round(damage * multiplier)
        if multiplier < 1:
            game_print("It's not very effective...")
        elif multiplier > 1:
            game_print("It's super effective!")

    defender.active().hp = max(0, defender.active().hp - damage)
    game_print(f"{defender.active().name} took {damage} damage!")
    attacker.active().accumulator = 0
    return damage