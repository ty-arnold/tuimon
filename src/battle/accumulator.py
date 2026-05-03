from typing import Optional
from models import Move, Trainer, Accumulator
from core import msg
from models.turn_result import Message, TurnEvent
from battle.damage import calculate_damage, get_type_multiplier


def release_accumulator(
    move:     Move,
    attacker: Trainer,
    defender: Trainer,
    config:   Accumulator,
    events:   list | None = None
) -> int:
    accumulated = attacker.active().accumulator

    if config.release_message and events is not None:
        events.append(Message(text=msg("accumulator_release", pokemon=attacker.active().name, message=config.release_message)))

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
        if multiplier < 1 and events is not None:
            events.append(Message(text=msg("not_effective"), color="weak"))
        elif multiplier > 1 and events is not None:
            events.append(Message(text=msg("super_effective"), color="super"))

    defender.active().hp = max(0, defender.active().hp - damage)
    if events is not None:
        events.append(Message(text=msg("took_damage", pokemon=defender.active().name, damage=damage), color="damage"))
    attacker.active().accumulator = 0
    return damage