import random
from typing import Optional
from models.move import Move
from models.trainer import Trainer
from models.pokemon import Pokemon
from data.type_chart  import TYPE_CHART
from data.mult_tables import crit_rate_table
from battle.modifiers import get_modifier_value
from battle.move_effects import get_screen_modifier
from core.logger import logger
from battle.messages import msg
from models.turn_result import Message, HPChange, TurnEvent


def get_type_multiplier(move_type: str, defender_types: list[str]) -> int:
    multiplier = 1

    for defender_type in defender_types:
        multiplier *= TYPE_CHART.get(move_type, {}).get(defender_type, 1)
    return multiplier


def apply_damage(
    move:         Move,
    attacker:     Trainer,
    defender:     Trainer,
    current_turn: int,
    events:       list[TurnEvent] | None = None,
    weather:      str | None = None
) -> int:
    power_modifier  = get_modifier_value("power_modifier",  move, attacker.active(), current_turn)
    damage_modifier = get_modifier_value("damage_modifier", move, attacker.active(), current_turn)
    acc_modifier    = get_modifier_value("accuracy_modifier", move, attacker.active(), current_turn)

    screen_modifier = get_screen_modifier(move, defender, current_turn)
    damage_modifier *= screen_modifier
    
    effective_power    = round(move.power * power_modifier)
    damage, multiplier = calculate_damage(move, attacker, defender, effective_power, events=events)
    damage             = round(damage * damage_modifier)

    target    = defender.active()

    # Ability damage modifiers
    from battle.abilities import check_ability_before_damage, modify_damage_by_ability, modify_damage_by_weather
    damage = check_ability_before_damage(defender, damage, events)
    dmg_mult = modify_damage_by_ability(attacker, defender, move, damage, events)
    dmg_mult *= modify_damage_by_weather(move.type[0], weather)
    damage = round(damage * dmg_mult)

    hp_before = target.hp
    target.hp = max(0, target.hp - damage)

    if events is not None:
        events.append(HPChange(
            trainer=defender.name,
            pokemon_name=target.name,
            old_hp=hp_before,
            new_hp=target.hp,
            max_hp=target.max_hp,
        ))

    if multiplier == 0:
        if events is not None:
            events.append(msg("no_effect"))
    elif multiplier < 1:
        if events is not None:
            events.append(msg("not_effective"))
    elif multiplier > 1:
        if events is not None:
            events.append(msg("super_effective"))

    if (defender.locked_move is not None and
        defender.locked_move.multi_turn is not None and
        defender.locked_move.multi_turn.accumulator is not None and
        defender.locked_move.multi_turn.accumulator.type == "damage_taken"):
        defender.active().accumulator += damage
        if events is not None:
            events.append(msg("storing_energy", pokemon=defender.active().name))
        
    if events is not None:
        events.append(msg("took_damage", pokemon=target.name, damage=damage))

    # Color Change: change type to the move's type when hit
    from battle.abilities import _name
    if damage > 0 and _name(target) == "Color Change" and move.type[0] not in target.type:
        target.type = [move.type[0]]
        if events is not None:
            events.append(Message(text=f"{target.name} became {move.type[0]} type!"))

    return damage 


def calculate_damage(
    move:           Move,
    attacker:       Trainer,
    defender:       Trainer,
    effective_power: Optional[int] = None,
    events:          list | None = None
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

    from battle.abilities import check_ability_prevents
    if check_ability_prevents(defender.active(), "crit"):
        critical = 1
    else:
        critical = 2 if random.random() < crit_chance else 1

    if critical == 2 and events is not None:
        events.append(msg("critical_hit"))

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


def apply_lifesteal(move: Move, attacker: Pokemon, damage: int, events: list[TurnEvent] | None = None) -> None:
    heal_amount = round(damage * move.lifesteal)
    attacker.active().hp = min(
        attacker.active().max_hp,
        attacker.active().hp + heal_amount
    )
    if events is not None:
        events.append(msg("drain", pokemon=attacker.active().name, hp=heal_amount))


def apply_recoil(move: Move, attacker: Pokemon, damage: int, events: list[TurnEvent] | None = None) -> None:
    recoil_damage = round(damage * move.recoil)
    attacker.active().hp = max(0, attacker.active().hp - recoil_damage)
    if events is not None:
        events.append(msg("recoil", pokemon=attacker.active().name, hp=recoil_damage))