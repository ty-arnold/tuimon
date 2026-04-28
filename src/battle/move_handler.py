import random
from typing import Optional
from models import Move, Trainer
from core.logger import logger
from core import game_print, msg
from ui import print_stat_changes, print_status_effect
from battle.damage import apply_damage, apply_lifesteal, get_type_multiplier
from battle.move_effects import is_protected, apply_move_effect
from battle.modifiers import apply_modifier
from battle.status_effects import apply_status_effect_from_move
from core.game_print import record_stats_change, record_hp_change, record_effect_change
from battle.accumulator import release_accumulator
from data import acc_table

def apply_move(move: Move, attacker: Trainer, defender: Trainer, current_turn: int) -> Optional[bool]:
    logger.debug(f"Attacker: {attacker.active().name} HP: {attacker.active().hp}/{attacker.active().max_hp}")
    logger.debug(f"Defender: {defender.active().name} HP: {defender.active().hp}/{defender.active().max_hp}")
    game_print(msg("move_used", pokemon=attacker.active().name, move=move.name))

    # 1. handle charge turn for multi turn moves
    # must be first - if charging, nothing else happens
    if move.multi_turn is not None:
        if handle_multiturn(move, attacker):
            return None

    # 2. check if defender is protected
    # protect blocks everything except specific moves
    if is_protected(defender, move):
        game_print(msg("blocked", pokemon=attacker.active().name))
        attacker.active().accumulator = 0
        defender.consecutive_protect  = 0
        return None
    else:
        defender.consecutive_protect = 0

    # 3. check invulnerability (fly, dig, etc)
    # separate from protect since some moves can still hit
    if defender.invulnerable_state is not None:
        if handle_invulnerability(move, attacker, defender):
            return None

    # 4. check accuracy
    # only checked if target is not invulnerable
    if not check_accuracy(move, attacker, defender):
        game_print(msg("missed", pokemon=attacker.active().name))
        attacker.active().accumulator = 0
        return None

    # 5. check type immunity
    # after accuracy so misses dont trigger immunity messages
    if check_immunity(move, attacker, defender):
        attacker.active().accumulator = 0
        return None

    # 6. decrement pp
    # only after all failure checks pass
    move.pp -= 1

    # 7. apply move effect for status moves like protect, light screen
    if move.move_effect is not None:
        ended = apply_move_effect(move, attacker, defender, current_turn)
        if ended and move.category == "status":
            return None

    # 8. apply modifier if move has one like charge
    if move.modifier is not None:
        apply_modifier(move, attacker.active(), current_turn)
        if move.category == "status":
            return None

    # 9. calculate and apply damage
    damage = 0
    if move.category != "status":
        if move.multi_turn is not None and move.multi_turn.accumulator is not None:
            # check if this is the release turn
            if attacker.locked_turns == 0 and attacker.locked_move is not None:
                damage = release_accumulator(move, attacker, defender,
                                             move.multi_turn.accumulator)
                attacker.active().accumulator = 0
                # return check_winner(attacker, defender)
        else:
            # handle multi hit moves
            if move.min_hits is not None and move.max_hits is not None:
                roll        = random.randint(move.min_hits, move.max_hits)
                hits_landed = 0
                for _ in range(roll):
                    hit_damage = apply_damage(move, attacker, defender, current_turn)
                    damage    += hit_damage
                    hits_landed += 1
                    if not defender.active().is_alive():
                        break
                game_print(msg("hit_x_times", times=hits_landed))
            else:
                damage = apply_damage(move, attacker, defender, current_turn)

    # 10. apply recoil
    if move.recoil > 0 and damage > 0:
        recoil_damage  = round(damage * move.recoil)
        hp_before      = attacker.active().hp
        attacker.active().hp = max(0, attacker.active().hp - recoil_damage)
        record_hp_change(attacker.active().name, hp_before, attacker.active().hp, attacker.active().max_hp)
        game_print(msg("recoil", pokemon=attacker.active().name, hp=recoil_damage))

    # 11. apply lifesteal
    if move.lifesteal > 0 and damage > 0:
        hp_before = attacker.active().hp
        apply_lifesteal(move, attacker, damage)
        record_hp_change(attacker.active().name, hp_before, attacker.active().hp, attacker.active().max_hp)

    # 12. apply heal
    if move.heal > 0:
        heal_amount  = round(attacker.active().max_hp * move.heal)
        hp_before    = attacker.active().hp
        attacker.active().hp = min(attacker.active().max_hp,
                                   attacker.active().hp + heal_amount)
        record_hp_change(attacker.active().name, hp_before, attacker.active().hp, attacker.active().max_hp)
        game_print(msg("heal", pokemon=attacker.active().name, hp=heal_amount))

    # 13. apply stat changes
    if move.stat_change:
        old_stats = apply_stat_change(move, attacker, defender, [])
        print_stat_changes(old_stats)
        for _, _, target, _ in old_stats:
            name = attacker.name if target is attacker.active() else defender.name
            record_stats_change(name)

    # 14. apply status effect
    if move.status_effect is not None:
        result, effect = apply_status_effect_from_move(move, defender)
        if effect is not None:
            print_status_effect(defender.active(), effect, result)

    # 15. lock recharge moves after attacking
    if move.multi_turn is not None and move.multi_turn.charge_turn == 2:
        attacker.locked_move  = move
        attacker.locked_turns = 1

    # 16. check winner
    # return check_winner(attacker, defender)

def handle_multiturn(move: Move, attacker: Trainer) -> bool:
    logger.debug(f"DEBUG handle_charge_turn:")
    logger.debug(f"  move.name:          {move.name}")
    logger.debug(f"  locked_move:        {attacker.locked_move}")
    logger.debug(f"  locked_turns:       {attacker.locked_turns}")
    logger.debug(f"  move.multi_turn:    {move.multi_turn}")

    if attacker.locked_move is not None and attacker.locked_move.multi_turn is not None:
        logger.debug(f"  charge_turn:        {attacker.locked_move.multi_turn.charge_turn}")
        if attacker.locked_move.multi_turn.charge_turn == 2:
            game_print(msg("target_effect", target=attacker.active().name, message=attacker.locked_move.multi_turn.charge_message))
            return True

    if move.multi_turn is not None and attacker.locked_move is None:
        attacker.locked_move        = move
        attacker.locked_turns       = move.multi_turn.turns - 1
        attacker.invulnerable_state = move.multi_turn.invulnerable_state

        if attacker.invulnerable_state is not None:
            record_effect_change(trainer_name=attacker.name)

        if move.multi_turn.charge_turn == 1:
            game_print(msg("target_effect", target=attacker.active().name, message=move.multi_turn.charge_message))
            return True

    return False

def check_accuracy(move: Move, attacker: Trainer, defender: Trainer) -> bool:
    # acc of None means the move never misses
    if move.acc is None:
        logger.debug(f"{move.name} never misses!")
        return True

    move_acc = move.acc * acc_table[attacker.active().stage_acc]
    evasion  = acc_table[defender.active().stage_eva]
    if random.random() > move_acc * evasion:
        return False
    return True

def handle_invulnerability(move: Move, attacker: Trainer, defender: Trainer) -> bool:
    can_hit = (
        defender.invulnerable_state is not None and
        defender.invulnerable_state in (move.hits_invulnerable or [])
    )

    if can_hit:
        if defender.invulnerable_state == "flying":
            game_print(msg("flying_hit", pokemon=defender.active().name))
        else:
            game_print(msg("invuln_hit", pokemon=defender.active().name))
        return False

    message = "is invulnerable!"
    if defender.locked_move is not None and defender.locked_move.multi_turn is not None:
        message = defender.locked_move.multi_turn.invulnerable_message or "is invulnerable!"

    game_print(msg("target_effect", target=defender.active().name, message=message))
    game_print(msg("missed", pokemon=attacker.active().name))
    return True

def check_immunity(move: Move, attacker: Trainer, defender: Trainer) -> bool:
    """Returns True if the move is blocked, False if it can hit."""

    # check type immunities on the move itself
    for immune_type in move.immune_types:
        if immune_type in defender.active().type:
            game_print(msg("doesnt_effect", pokemon=defender.active().name))
            return True

    # check if defender is using a blocking move
    for immune_move in move.immune_moves:
        if (defender.locked_move is not None and
                defender.locked_move.name.lower() == immune_move):
            game_print(msg("self_protect", pokemon=defender.active().name))
            return True

    # check type chart immunity (0x effectiveness)
    multiplier = get_type_multiplier(move.type[0], defender.active().type)
    if multiplier == 0:
        game_print(msg("no_effect"))
        return True

    return False

def apply_stat_change(move: Move, attacker: Trainer, defender: Trainer, old_stats) -> dict:
    # roll against stat change chance before applying
    if move.stat_change_chance < 1.0:
        if random.random() > move.stat_change_chance:
            logger.debug(f"Stat change failed to trigger ({move.stat_change_chance * 100}% chance)")
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
            stage_attr = "stage_" + stat.replace("stat_", "")
            old_stage  = getattr(target, stage_attr)
            actual_change = target.apply_stage_change(stat, change)
            old_stats.append((stat, old_stage, target, actual_change))

    return old_stats

def clear_move_lock(trainer: Trainer) -> None:
    if trainer.locked_move is not None and trainer.locked_turns == 0:
        trainer.active().accumulator = 0
        had_invulnerable             = trainer.invulnerable_state is not None
        trainer.locked_move          = None
        trainer.invulnerable_state   = None
        if had_invulnerable:
            record_effect_change(trainer_name=trainer.name)