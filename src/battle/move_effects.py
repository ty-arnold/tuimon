import random, copy
from models import Move, Trainer, MoveEffect
from core.logger import logger
from core import game_print, msg
from core.game_print import record_effect_change


def apply_move_effect(
    move:         Move,
    attacker:     Trainer,
    defender:     Trainer,
    current_turn: int
) -> bool:
    """
    Applies the move's effect to the correct target.
    Returns True if the move should end after this (status moves).
    """
    if move.move_effect is None:
        return False

    effect  = move.move_effect
    target  = attacker if effect.target == "self" else defender

    record_effect_change(trainer_name=attacker.name)

    match effect.effect_type:
        case "protect":
            return handle_protect_effect(effect, attacker, current_turn)
        case "screen":
            return handle_screen_effect(effect, target, current_turn)
        case "mist":
            return handle_mist_effect(effect, target, current_turn)
        case _:
            logger.debug(f"Unknown effect type: {effect.effect_type}")
            return False

def clear_expired_effects(trainer: Trainer, current_turn: int) -> None:
    expired = [e for e in trainer.active_effects
               if e.effect_type != "protect" and e.turns <= current_turn]
    for effect in expired:
        trainer.active_effects.remove(effect)
        game_print(msg("effect_wore_off"))

    # always clear protect at end of turn
    trainer.active_effects = [e for e in trainer.active_effects
                              if e.effect_type != "protect"]

def clear_switch_effects(trainer: Trainer) -> None:
    """Clear effects that should end on switch."""
    trainer.active_effects = [
        e for e in trainer.active_effects
        if not e.properties.get("clears_on_switch", True)
    ]
    
def handle_protect_effect(
    effect:       MoveEffect,
    trainer:      Trainer,
    current_turn: int
) -> bool:
    # check consecutive use reduction
    if effect.properties.get("consecutive_reduction"):
        if trainer.consecutive_protect > 0:
            chance = 1 / (2 ** trainer.consecutive_protect)
            if random.random() > chance:
                game_print(msg("target_effect", pokemon=trainer.active().name, message=effect.fail_message))
                trainer.consecutive_protect = 0
                return True

    trainer.active_effects.append(
        MoveEffect(
            effect_type  = "protect",
            target       = "self",
            turns        = 1,
            bypass_moves = effect.bypass_moves,
            message      = effect.message,
            properties   = effect.properties
        )
    )
    trainer.consecutive_protect += 1
    game_print(msg("target_effect", target=trainer.active().name, message=effect.message))
    return True

def handle_screen_effect(
    effect:       MoveEffect,
    trainer:      Trainer,
    current_turn: int
) -> bool:
    # check if screen already active
    if any(e.effect_type == "screen" and
           e.properties.get("category_condition") == effect.properties.get("category_condition")
           for e in trainer.active_effects):
        game_print(msg("but_it_failed"))
        return True

    screen        = copy.deepcopy(effect)
    screen.turns  = current_turn + effect.turns  # store expiry turn
    trainer.active_effects.append(screen)
    game_print(msg("target_effect", target=trainer.active().name, message=effect.message))
    return True

def handle_mist_effect(
    effect:       MoveEffect,
    trainer:      Trainer,
    current_turn: int
) -> bool:
    if any(e.effect_type == "mist" for e in trainer.active_effects):
        game_print(msg("but_it_failed"))
        return True

    mist       = copy.deepcopy(effect)
    mist.turns = current_turn + effect.turns
    trainer.active_effects.append(mist)
    game_print(msg("target_effect", target=trainer.active().name, message=effect.message))
    return True

def is_protected(trainer: Trainer, move: Move) -> bool:
    """Check if trainer is protected against this move."""
    for effect in trainer.active_effects:
        if effect.effect_type != "protect":
            continue
        if move.name.lower().replace(" ", "-") in effect.bypass_moves:
            return False
        return True
    return False

def get_screen_modifier(
    move:         Move,
    defender:     Trainer,
    current_turn: int
) -> float:
    """Get damage modifier from active screens."""
    modifier = 1.0
    expired  = []

    for effect in defender.active_effects:
        if effect.effect_type != "screen":
            continue
        category = effect.properties.get("category_condition")
        if category is not None and move.category != category:
            continue
        modifier *= effect.properties.get("damage_modifier", 1.0)
        if effect.turns <= current_turn:
            expired.append(effect)
            game_print(msg("screen_wore_off"))

    for effect in expired:
        defender.active_effects.remove(effect)

    return modifier

def blocks_stat_changes(trainer: Trainer) -> bool:
    """Check if mist is preventing stat changes."""
    return any(
        e.effect_type == "mist" and e.properties.get("blocks_stat_changes")
        for e in trainer.active_effects
    )