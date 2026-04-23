import random
from typing import Optional
from models import Move, Trainer
from data import type_chart, crit_rate_table
from battle.modifiers import get_modifier_value
from battle.move_effects import get_screen_modifier
from core.logger import logger
from core import game_print

def get_type_multiplier(move_type: str, defender_types: list[str]) -> int:
    multiplier = 1

    for defender_type in defender_types:
        multiplier *= type_chart.get(move_type, {}).get(defender_type, 1)
    return multiplier

def apply_damage(
    move:         Move,
    attacker:     Trainer,
    defender:     Trainer,
    current_turn: int
) -> int:
    power_modifier  = get_modifier_value("power_modifier",  move, attacker.active(), current_turn)
    damage_modifier = get_modifier_value("damage_modifier", move, attacker.active(), current_turn)
    acc_modifier    = get_modifier_value("accuracy_modifier", move, attacker.active(), current_turn)

    screen_modifier = get_screen_modifier(move, defender, current_turn)
    damage_modifier *= screen_modifier
    
    effective_power    = round(move.power * power_modifier)
    damage, multiplier = calculate_damage(move, attacker, defender, effective_power)
    damage             = round(damage * damage_modifier)

    target    = defender.active()
    target.hp = max(0, target.hp - damage)

    if multiplier == 0:
        game_print("It had no effect!")
    elif multiplier < 1:
        game_print("It's not very effective...")
    elif multiplier > 1:
        game_print("It's super effective!")

    if (defender.locked_move is not None and
        defender.locked_move.multi_turn is not None and
        defender.locked_move.multi_turn.accumulator is not None and
        defender.locked_move.multi_turn.accumulator.type == "damage_taken"):
        defender.active().accumulator += damage
        game_print(f"{defender.active().name} is storing energy!")
        
    game_print(f"{target.name} took {damage} damage!")

    return damage 

def calculate_damage(
    move:           Move,
    attacker:       Trainer,
    defender:       Trainer,
    effective_power: Optional[int] = None
) -> tuple[int, float]:

    if move.category == "physical":
        attack_stat  = attacker.active().get_stat("stat_attk")
        defense_stat = defender.active().get_stat("stat_def")
    elif move.category == "special":
        attack_stat  = attacker.active().get_stat("stat_sp_attk")
        defense_stat = defender.active().get_stat("stat_sp_def")
    else:
        return 0, 1.0

    multiplier  = get_type_multiplier(move.type[0], defender.active().type)
    
    # calculate critical hit chance based on move crit rate
    crit_chance = crit_rate_table.get(move.crit_rate, 1/16)
    critical    = 2 if random.random() < crit_chance else 1
    if critical == 2:
        logger.info("Critical hit!")

    # use effective_power if provided (from modifiers like charge)
    # otherwise use the move's base power
    power = effective_power if effective_power is not None else move.power

    logger.debug(f"calculate_damage: attack={attack_stat} defense={defense_stat}")
    logger.debug(f"calculate_damage: power={power} lvl={attacker.active().lvl}")
    logger.debug(f"calculate_damage: critical={critical} multiplier={multiplier}")

    damage = round(
        (((2 * attacker.active().lvl * critical / 5) + 2) * power * (attack_stat / defense_stat) / 50 + 2)
        * multiplier
    )

    logger.debug(f"calculate_damage: final damage={damage}")

    return damage, multiplier

def apply_lifesteal(move, attacker, damage) -> None:
    heal_amount = round(damage * move.lifesteal)
    attacker.active().hp = min(
        attacker.active().max_hp,
        attacker.active().hp + heal_amount
    )
    game_print(f"{attacker.active().name} drained {heal_amount} HP!")

def apply_recoil(move: Move, attacker: Trainer, damage: int) -> None:
    recoil_damage = round(damage * move.recoil)
    attacker.active().hp = max(0, attacker.active().hp - recoil_damage)
    game_print(f"{attacker.active().name} took {recoil_damage} recoil damage!")