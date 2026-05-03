import random
from typing import Optional
from models import Move, Pokemon, Trainer, StatusEffect
from core import msg
from models.turn_result import Message, HPChange, StatusApplied, StatusRemoved, TurnEvent


def apply_status_effect_from_move(
    move: Move, defender: Trainer, events: list[TurnEvent] | None = None
) -> tuple[str, Optional[StatusEffect]]:
    import copy
    
    if move.status_effect is None:
        return "failed", None
    
    effect = copy.deepcopy(move.status_effect)
    
    if random.random() < effect.chance_to_apply:
        success = defender.active().apply_status_effect(effect)
        if success:
            if events is not None:
                events.append(StatusApplied(trainer=defender.name))
            return "afflicted", effect
        else:
            return "already", effect  # blocked because major status already exists
    return "failed", effect


def process_effect(pokemon: Pokemon, effect: StatusEffect, events: list[TurnEvent] | None = None) -> bool:
    # Process a single status effect. Returns True if the effect should be removed
    if effect.check_should_end():
        return True

    # Confusion is handled in check_can_act since it influences attackers chance to attack
    match effect.name:
        case "Poison" | "Curse":
            if effect.damage is not None:
                damage    = round(pokemon.max_hp * effect.damage)
                hp_before = pokemon.hp
                pokemon.hp = max(0, pokemon.hp - damage)
                if events is not None:
                    events.append(msg("generic_effect", pokemon=pokemon.name, effect=effect.name.lower()))
                    events.append(HPChange(
                        trainer="", pokemon_name=pokemon.name,
                        old_hp=hp_before, new_hp=pokemon.hp, max_hp=pokemon.max_hp,
                    ))
                    events.append(msg("took_damage", pokemon=pokemon.name, damage=damage))
        case "Burn":
            if effect.damage is not None:
                damage    = round(pokemon.max_hp * effect.damage)
                hp_before = pokemon.hp
                pokemon.hp = max(0, pokemon.hp - damage)
                if events is not None:
                    events.append(msg("burn_damage", pokemon=pokemon.name))
                    events.append(HPChange(
                        trainer="", pokemon_name=pokemon.name,
                        old_hp=hp_before, new_hp=pokemon.hp, max_hp=pokemon.max_hp,
                    ))
                    events.append(msg("took_damage", pokemon=pokemon.name, damage=damage))
            else:
                if events is not None:
                    events.append(msg("is_confused", pokemon=pokemon.name))

    return False


def remove_expired_effects(pokemon: Pokemon, effects_to_remove: list[StatusEffect],
                           events: list[TurnEvent] | None = None, trainer_name: str = "") -> None:
    removal_messages = {
        "Poison":    "was cured of poison!",
        "Paralysis": "was cured of paralysis!",
        "Sleep":     "woke up!",
        "Burn":      "was cured of its burn!",
        "Freeze":    "thawed out!",
        "Confusion": "snapped out of confusion!",
        "Curse":     "is no longer cursed!",
    }
    for effect in effects_to_remove:
        pokemon.remove_status_effect(effect)
        message = removal_messages.get(effect.name, " is no longer affected!")
        if events is not None:
            events.append(msg("target_effect", target=pokemon.name, message=message))
            events.append(StatusRemoved(trainer=trainer_name))


def get_all_effects(pokemon: Pokemon) -> list[StatusEffect]:
    # Get all active status effects for a pokemon
    return ([pokemon.major_status] if pokemon.major_status else []) + pokemon.minor_status


def process_status_effects(pokemon: Pokemon, events: list[TurnEvent] | None = None,
                            trainer_name: str = "") -> None:
    effects_to_remove = []

    for effect in get_all_effects(pokemon):
        if process_effect(pokemon, effect, events):
            effects_to_remove.append(effect)

    remove_expired_effects(pokemon, effects_to_remove, events, trainer_name)