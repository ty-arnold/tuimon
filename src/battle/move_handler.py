import random
from typing import Optional
from models.move import Move
from models.trainer import Trainer
from models.pokemon import Pokemon
from models.status_effect import StatusEffect
from core.logger import logger
from battle.messages import msg
from models.turn_result import Message, HPChange, EffectChange, StatChange, StatusApplied, TurnEvent
from battle.damage import apply_damage, apply_lifesteal, get_type_multiplier
from battle.move_effects import is_protected, apply_move_effect
from battle.modifiers import apply_modifier
from battle.status_effects import apply_status_effect_from_move
from battle.accumulator import release_accumulator
from data.mult_tables import acc_table

def apply_move(
    move: Move, attacker: Trainer, defender: Trainer,
    current_turn: int, events: list[TurnEvent] | None = None,
    weather: str | None = None
) -> Optional[bool]:
    logger.debug(f"Attacker: {attacker.active().name} HP: {attacker.active().hp}/{attacker.active().max_hp}")
    logger.debug(f"Defender: {defender.active().name} HP: {defender.active().hp}/{defender.active().max_hp}")
    if events is not None:
        events.append(msg("move_used", pokemon=attacker.active().name, move=move.name))

    # 1. handle charge turn for multi turn moves
    if move.multi_turn is not None:
        if handle_multiturn(move, attacker, events=events):
            return None

    # 2. check if defender is protected
    if is_protected(defender, move):
        if events is not None:
            events.append(msg("blocked", pokemon=attacker.active().name))
        attacker.active().accumulator = 0
        defender.consecutive_protect  = 0
        return None
    else:
        defender.consecutive_protect = 0

    # 3. check invulnerability (fly, dig, etc)
    if defender.invulnerable_state is not None:
        if handle_invulnerability(move, attacker, defender, events=events):
            return None

    # 4. check accuracy
    if not check_accuracy(move, attacker, defender, weather):
        if events is not None:
            events.append(msg("missed", pokemon=attacker.active().name))
        attacker.active().accumulator = 0
        return None

    # 5. check type immunity
    if check_immunity(move, attacker, defender, events=events):
        attacker.active().accumulator = 0
        return None

    # 6. decrement pp
    from battle.abilities import apply_ability_pp_pressure
    move.pp -= 2 if apply_ability_pp_pressure(defender) else 1

    # 7. apply move effect for status moves
    if move.move_effect is not None:
        ended = apply_move_effect(move, attacker, defender, current_turn, events=events)
        if ended and move.category == "status":
            return None

    # 8. apply modifier
    if move.modifier is not None:
        apply_modifier(move, attacker.active(), current_turn, events=events)
        if move.category == "status":
            return None

    # 9. calculate and apply damage
    damage = 0
    if move.category != "status":
        if move.multi_turn is not None and move.multi_turn.accumulator is not None:
            if attacker.locked_turns == 0 and attacker.locked_move is not None:
                damage = release_accumulator(move, attacker, defender,
                                             move.multi_turn.accumulator, events=events)
                attacker.active().accumulator = 0
        else:
            if move.min_hits is not None and move.max_hits is not None:
                roll        = random.randint(move.min_hits, move.max_hits)
                hits_landed = 0
                for _ in range(roll):
                    hit_damage = apply_damage(move, attacker, defender, current_turn, events=events, weather=weather)
                    damage    += hit_damage
                    hits_landed += 1
                    if not defender.active().is_alive():
                        break
                if events is not None:
                    events.append(msg("hit_x_times", times=hits_landed))
            else:
                damage = apply_damage(move, attacker, defender, current_turn, events=events, weather=weather)

    # 9b. contact abilities (Static, Poison Point, Rough Skin, etc.)
    from battle.abilities import apply_contact_abilities
    apply_contact_abilities(attacker, defender, move, events)

    # 10. apply recoil
    from battle.abilities import check_ability_recoil_prevention
    if move.recoil > 0 and damage > 0 and not check_ability_recoil_prevention(attacker):
        recoil_damage  = round(damage * move.recoil)
        hp_before      = attacker.active().hp
        attacker.active().hp = max(0, attacker.active().hp - recoil_damage)
        if events is not None:
            events.append(HPChange(
                trainer=attacker.name, pokemon_name=attacker.active().name,
                old_hp=hp_before, new_hp=attacker.active().hp, max_hp=attacker.active().max_hp,
            ))
            events.append(msg("recoil", pokemon=attacker.active().name, hp=recoil_damage))

    # 11. apply lifesteal
    from battle.abilities import check_ability_liquid_ooze_defender
    if move.lifesteal > 0 and damage > 0:
        if check_ability_liquid_ooze_defender(defender, attacker, damage, move):
            if events is not None:
                events.append(Message(text=f"{attacker.active().name} was hurt by Liquid Ooze!"))
                events.append(HPChange(
                    trainer=attacker.name, pokemon_name=attacker.active().name,
                    old_hp=attacker.active().hp + round(damage * move.lifesteal),
                    new_hp=attacker.active().hp, max_hp=attacker.active().max_hp,
                ))
        else:
            hp_before = attacker.active().hp
            apply_lifesteal(move, attacker, damage, events=events)
            if events is not None:
                events.append(HPChange(
                    trainer=attacker.name, pokemon_name=attacker.active().name,
                    old_hp=hp_before, new_hp=attacker.active().hp, max_hp=attacker.active().max_hp,
                ))

    # 12. apply heal
    if move.heal > 0:
        heal_amount  = round(attacker.active().max_hp * move.heal)
        hp_before    = attacker.active().hp
        attacker.active().hp = min(attacker.active().max_hp,
                                   attacker.active().hp + heal_amount)
        if events is not None:
            events.append(HPChange(
                trainer=attacker.name, pokemon_name=attacker.active().name,
                old_hp=hp_before, new_hp=attacker.active().hp, max_hp=attacker.active().max_hp,
            ))
            events.append(msg("heal", pokemon=attacker.active().name, hp=heal_amount))

    # 13. apply stat changes
    if move.stat_change:
        old_stats = apply_stat_change(move, attacker, defender, [])
        if events is not None:
            _emit_stat_events(events, old_stats, attacker, defender)

    # 14. apply status effect
    if move.status_effect is not None:
        result, effect = apply_status_effect_from_move(move, defender, attacker, events=events)
        if effect is not None and events is not None:
            _emit_status_message(events, defender.active(), effect, result)

    # 15. lock recharge moves after attacking
    if move.multi_turn is not None and move.multi_turn.charge_turn == 2:
        attacker.locked_move  = move
        attacker.locked_turns = 1

def handle_multiturn(move: Move, attacker: Trainer, events: list[TurnEvent] | None = None) -> bool:
    logger.debug(f"DEBUG handle_charge_turn:")
    logger.debug(f"  move.name:          {move.name}")
    logger.debug(f"  locked_move:        {attacker.locked_move}")
    logger.debug(f"  locked_turns:       {attacker.locked_turns}")
    logger.debug(f"  move.multi_turn:    {move.multi_turn}")

    if attacker.locked_move is not None and attacker.locked_move.multi_turn is not None:
        logger.debug(f"  charge_turn:        {attacker.locked_move.multi_turn.charge_turn}")
        if attacker.locked_move.multi_turn.charge_turn == 2:
            if events is not None:
                events.append(msg("target_effect", target=attacker.active().name, message=attacker.locked_move.multi_turn.charge_message))
            return True

    if move.multi_turn is not None and attacker.locked_move is None:
        attacker.locked_move        = move
        attacker.locked_turns       = move.multi_turn.turns - 1
        attacker.invulnerable_state = move.multi_turn.invulnerable_state

        if attacker.invulnerable_state is not None:
            if events is not None:
                events.append(EffectChange(trainer=attacker.name))

        if move.multi_turn.charge_turn == 1:
            if events is not None:
                events.append(msg("target_effect", target=attacker.active().name, message=move.multi_turn.charge_message))
            return True

    return False


def check_accuracy(move: Move, attacker: Trainer, defender: Trainer, weather: str | None = None) -> bool:
    if move.acc is None:
        logger.debug(f"{move.name} never misses!")
        return True

    move_acc = move.acc * acc_table[attacker.active().stage_acc]
    eva_stage = defender.active().stage_eva

    from battle.abilities import modify_evasion_by_weather
    eva_stage = modify_evasion_by_weather(defender.active(), eva_stage, weather)
    evasion = acc_table[eva_stage]

    from battle.abilities import check_ability_accuracy_modifier
    move_acc *= check_ability_accuracy_modifier(attacker)

    if random.random() > move_acc * evasion:
        return False
    return True


def handle_invulnerability(
    move: Move, attacker: Trainer, defender: Trainer,
    events: list[TurnEvent] | None = None
) -> bool:
    can_hit = (
        defender.invulnerable_state is not None and
        defender.invulnerable_state in (move.hits_invulnerable or [])
    )

    if can_hit:
        if defender.invulnerable_state == "flying":
            if events is not None:
                events.append(msg("flying_hit", pokemon=defender.active().name))
        else:
            if events is not None:
                events.append(msg("invuln_hit", pokemon=defender.active().name))
        return False

    message = "is invulnerable!"
    if defender.locked_move is not None and defender.locked_move.multi_turn is not None:
        message = defender.locked_move.multi_turn.invulnerable_message or "is invulnerable!"

    if events is not None:
        events.append(msg("target_effect", target=defender.active().name, message=message))
        events.append(msg("missed", pokemon=attacker.active().name))
    return True


def check_immunity(
    move: Move, attacker: Trainer, defender: Trainer,
    events: list[TurnEvent] | None = None
) -> bool:
    """Returns True if the move is blocked, False if it can hit."""

    for immune_type in move.immune_types:
        if immune_type in defender.active().type:
            if events is not None:
                events.append(msg("doesnt_effect", pokemon=defender.active().name))
            return True

    for immune_move in move.immune_moves:
        if (defender.locked_move is not None and
                defender.locked_move.name.lower() == immune_move):
            if events is not None:
                events.append(msg("protect_self", pokemon=defender.active().name))
            return True

    # Check ability-based type immunity (Levitate, Volt Absorb, etc.)
    from battle.abilities import check_ability_type_immunity, is_sound_move, check_ability_blocks_sound, is_explosion_move, check_ability_blocks_explosion
    if check_ability_type_immunity(defender, move, events):
        return True

    if is_sound_move(move.name) and check_ability_blocks_sound(defender.active()):
        if events is not None:
            events.append(msg("doesnt_effect", pokemon=defender.active().name))
        return True

    if is_explosion_move(move.name) and check_ability_blocks_explosion(defender.active()):
        if events is not None:
            events.append(Message(text=msg("no_effect")))
        return True

    multiplier = get_type_multiplier(move.type[0], defender.active().type)
    if multiplier == 0:
        if events is not None:
            events.append(msg("no_effect"))
        return True

    return False

def apply_stat_change(move: Move, attacker: Trainer, defender: Trainer, old_stats) -> dict:
    # roll against stat change chance before applying
    from battle.abilities import check_ability_serene_grace, check_ability_shield_dust
    if check_ability_shield_dust(defender.active()):
        return old_stats
    chance = move.stat_change_chance * 2 if check_ability_serene_grace(attacker.active()) else move.stat_change_chance
    if chance < 1.0:
        if random.random() > chance:
            logger.debug(f"Stat change failed to trigger ({chance * 100}% chance)")
            return old_stats  # stat change didn't trigger, return unchanged

    for target_type, stat_changes in move.stat_change.items():
        target = None
        if target_type == "self":
            target = attacker.active()
        elif target_type == "opponent":
            target = defender.active()
        elif target_type == "random":
            target = random.choice([attacker.active(), defender.active()])

        if target is None:
            continue

        for stat, change in stat_changes.items():
            if change < 0 and target_type != "self":
                from battle.abilities import check_ability_prevents
                if stat in ("stat_attk", "stage_attk"):
                    if check_ability_prevents(target, "atk_drop"):
                        continue
                elif stat in ("acc", "stage_acc"):
                    if check_ability_prevents(target, "acc_drop"):
                        continue
                elif check_ability_prevents(target, "stat_drop_by_opponent"):
                    continue

            stage_attr = "stage_" + stat.replace("stat_", "")
            old_stage  = getattr(target, stage_attr)
            actual_change = target.apply_stage_change(stat, change)
            old_stats.append((stat, old_stage, target, actual_change))

    return old_stats


def clear_move_lock(trainer: Trainer, events: list[TurnEvent] | None = None) -> None:
    if trainer.locked_move is not None and trainer.locked_turns == 0:
        trainer.active().accumulator = 0
        had_invulnerable             = trainer.invulnerable_state is not None
        trainer.locked_move          = None
        trainer.invulnerable_state   = None
        if had_invulnerable:
            if events is not None:
                events.append(EffectChange(trainer=trainer.name))


STAT_NAMES = {
    "stat_attk":    "Attack",
    "stat_def":     "Defense",
    "stat_sp_attk": "Special Attack",
    "stat_sp_def":  "Special Defense",
    "stat_spd":     "Speed",
    "acc":          "Accuracy",
    "eva":          "Evasion",
}

STAT_MESSAGES = {
    "stat_attk":    ("'s attack rose",        "'s attack fell"),
    "stat_def":     ("'s defense rose",       "'s defense fell"),
    "stat_sp_attk": ("'s sp. attack rose",    "'s sp. attack fell"),
    "stat_sp_def":  ("'s sp. defense rose",   "'s sp. defense fell"),
    "stat_spd":     ("'s speed rose",         "'s speed fell"),
    "stat_acc":     ("'s accuracy rose",      "'s accuracy fell"),
    "stat_eva":     ("'s evasion rose",       "'s evasion fell"),
}

STAT_AMOUNTS = {1: "", 2: " sharply", 3: " drastically"}

STAT_ATTR_MAP = {
    "stat_attk":    "stage_attk",
    "stat_def":     "stage_def",
    "stat_sp_attk": "stage_sp_attk",
    "stat_sp_def":  "stage_sp_def",
    "stat_spd":     "stage_spd",
    "stat_acc":     "stage_acc",
    "stat_eva":     "stage_eva",
}


def _emit_stat_events(events: list, old_stats: list, attacker: Trainer, defender: Trainer) -> None:
    seen = set()
    for stat, _old_value, target, actual_change in old_stats:
        trainer = attacker if target is attacker.active() else defender
        pokemon_name = target.name
        trainer_name = trainer.name

        if stat in STAT_MESSAGES:
            if actual_change == 0:
                display_name = STAT_NAMES.get(stat, stat)
                events.append(msg(
                    "target_effect", color="status", target=pokemon_name,
                    message=f"{pokemon_name}'s {display_name} won't go any further!",
                ))
            else:
                up_msg, down_msg = STAT_MESSAGES[stat]
                direction = up_msg if actual_change > 0 else down_msg
                amount = STAT_AMOUNTS.get(abs(actual_change), " drastically")
                events.append(msg(
                    "target_effect", color="status", target=pokemon_name,
                    message=f"{pokemon_name}{direction}{amount}!",
                ))

            dedup_key = (trainer_name, stat)
            if dedup_key not in seen:
                seen.add(dedup_key)
                stage_attr = STAT_ATTR_MAP.get(stat, "stage_" + stat.replace("stat_", ""))
                stage_val = getattr(target, stage_attr, 0)
                events.append(StatChange(
                    trainer=trainer_name, pokemon_name=pokemon_name,
                    stat_name=stat, stage_change=actual_change,
                    was_capped=(actual_change == 0),
                ))


def _emit_status_message(events: list, target: Pokemon, effect: StatusEffect, result: str) -> None:
    name = effect.name.lower()

    if result == "afflicted":
        events.append(msg(f"status_{name}", pokemon=target.name))
    elif result == "already":
        if effect.is_major and target.major_status is not None:
            if target.major_status.name == effect.name:
                events.append(msg(f"status_already_{name}", pokemon=target.name))
            else:
                events.append(msg("status_already_major", pokemon=target.name))
        else:
            events.append(msg(f"status_already_{name}", pokemon=target.name))