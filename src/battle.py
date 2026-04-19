from type_chart import type_chart
from game_print import game_print
from print import print_actions, print_cant_act, print_stat_changes, print_status_effect
from models import *
from mult_tables import *
import random, copy
from logger import logger

def get_turn(trainer: Trainer) -> Move | None:
    if trainer.locked_move is not None:
        move = trainer.locked_move  # store before potentially resetting
        trainer.locked_turns -= 1
        # don't clear here - let resolve_turn handle it after damage
        return move

    action_selected = False
    move = None

    while not action_selected:
        action = print_actions(trainer)
        if action == 1:
            trainer.active().print_moves()
            move = get_move(trainer.party[trainer.selected_mon])
            if move is not None:
                action_selected = True
        elif action == 2:
            trainer.print_party()
            pokemon = get_party(trainer)
        elif action == 3:
            # placeholder for items :)
            pass
    return move

def get_party(trainer: Trainer) -> Pokemon | None:
    while True:
        try:
            cancel = len(trainer.party) + 1
            choice = int(input("Select a Pokemon: "))

            # check cancel first before any indexing
            if choice == cancel:
                if trainer.active().is_alive():
                    return None
                else:
                    game_print("You must select a pokemon!")
                    continue

            selected_mon = trainer.party[choice - 1]
            if not selected_mon.is_alive():
                game_print(f"{selected_mon.name} has already fainted! Please select another Pokemon.")
                continue
            if choice - 1 == trainer.selected_mon:
                game_print(f"{selected_mon.name} is already selected!")
                return None
            game_print(f"You selected {selected_mon.name}!")
            trainer.selected_mon = choice - 1
            return selected_mon
        except (ValueError, IndexError):
            game_print("Invalid choice, please select again")

def resolve_turn(player: Trainer, player_choice: Move, npc: Trainer, npc_choice: Move, current_turn: int) -> bool | None:
    player_can_act, player_cant_act_reason = check_can_act(player.active())
    npc_can_act,    npc_cant_act_reason    = check_can_act(npc.active())

    order = get_turn_order(player, player_choice, npc, npc_choice, player_can_act, npc_can_act)

    second_mon_before = order.second.selected_mon

    if order.first_can_act:
        apply_move(order.first_choice, order.first, order.second, current_turn)
        clear_move_lock(order.first)
        winner = check_winner(player, npc)
        if winner:
            return True
        next_mon(player, npc)

    # checks if the second pokemon fainted - if so, skip its move turn
    if order.second.selected_mon != second_mon_before:
        return None
        
    if order.second_can_act:
        apply_move(order.second_choice, order.second, order.first, current_turn)
        clear_move_lock(order.second)
        winner = check_winner(player, npc)
        if winner:
            return True
        next_mon(player, npc)

    process_status_effects(order.first.active())
    process_status_effects(order.second.active())
    winner = check_winner(player, npc)
    if winner:
        return True
    return None
    
def get_turn_order(
    player:        Trainer,
    player_choice: Move,
    npc:           Trainer,
    npc_choice:    Move,
    player_can_act: bool,
    npc_can_act:    bool
) -> TurnOrder:

    player_goes_first = _determine_first(player, player_choice, npc, npc_choice)

    if player_goes_first:
        return TurnOrder(
            first          = player,
            first_choice   = player_choice,
            second         = npc,
            second_choice  = npc_choice,
            first_can_act  = player_can_act,
            second_can_act = npc_can_act
        )
    else:
        return TurnOrder(
            first          = npc,
            first_choice   = npc_choice,
            second         = player,
            second_choice  = player_choice,
            first_can_act  = npc_can_act,
            second_can_act = player_can_act
        )

def _determine_first(player: Trainer, player_choice: Move, npc: Trainer, npc_choice: Move) -> bool:
    # priority takes precedence over speed
    if player_choice.priority != npc_choice.priority:
        return player_choice.priority > npc_choice.priority

    # equal priority - check speed
    player_spd = player.active().get_stat("stat_spd")
    npc_spd    = npc.active().get_stat("stat_spd")

    if player_spd != npc_spd:
        return player_spd > npc_spd

    # speed tie - randomize
    return random.random() > 0.5

def get_move(pokemon: Pokemon) -> Move | None:
    while True:
        try:
            cancel = len(pokemon.moveset) + 1
            choice = int(input("Select a Move: "))
            if choice == cancel:
                return None
            selected_move = pokemon.moveset[choice - 1]
            if selected_move.pp <= 0:
                game_print(f"{selected_move.name} has no PP left! Choose another move.")
                continue
            game_print(f"You selected {selected_move.name}!")
            return pokemon.moveset[choice - 1]
        except (ValueError, IndexError):
            game_print("Invalid choice, please select again")
            pokemon.print_moves()

def apply_move(move: Move, attacker: Trainer, defender: Trainer, current_turn: int) -> Optional[bool]:
    logger.debug(f"Attacker: {attacker.active().name} HP: {attacker.active().hp}/{attacker.active().max_hp}")
    logger.debug(f"Defender: {defender.active().name} HP: {defender.active().hp}/{defender.active().max_hp}")
    game_print(f"{attacker.active().name} used {move.name}!")

    # 1. handle charge turn for multi turn moves
    # must be first - if charging, nothing else happens
    if move.multi_turn is not None:
        if handle_multiturn(move, attacker):
            return None

    # 2. check if defender is protected
    # protect blocks everything except specific moves
    if is_protected(defender, move):
        game_print(f"{attacker.active().name}'s attack was blocked!")
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
        game_print(f"{attacker.active().name}'s attack missed!")
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
                game_print(f"Hit {hits_landed} time(s)!")
            else:
                damage = apply_damage(move, attacker, defender, current_turn)

    # 10. apply recoil
    if move.recoil > 0 and damage > 0:
        recoil_damage = round(damage * move.recoil)
        attacker.active().hp = max(0, attacker.active().hp - recoil_damage)
        game_print(f"{attacker.active().name} took {recoil_damage} recoil damage!")

    # 11. apply lifesteal
    if move.lifesteal > 0 and damage > 0:
        apply_lifesteal(move, attacker, damage)

    # 12. apply heal
    if move.heal > 0:
        heal_amount = round(attacker.active().max_hp * move.heal)
        attacker.active().hp = min(attacker.active().max_hp,
                                   attacker.active().hp + heal_amount)
        game_print(f"{attacker.active().name} restored {heal_amount} HP!")

    # 13. apply stat changes
    if move.stat_change:
        old_stats = apply_stat_change(move, attacker, defender, [],)
        print_stat_changes(old_stats)

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
    if attacker.locked_move is not None and attacker.locked_move.multi_turn is not None:
        if attacker.locked_move.multi_turn.charge_turn == 2:
            game_print(f"{attacker.active().name} {attacker.locked_move.multi_turn.charge_message}")
            return True

    if move.multi_turn is not None and attacker.locked_move is None:
        attacker.locked_move        = move
        attacker.locked_turns       = move.multi_turn.turns - 1
        attacker.invulnerable_state = move.multi_turn.invulnerable_state

        if move.multi_turn.charge_turn == 1:
            game_print(f"{attacker.active().name} {move.multi_turn.charge_message}")
            return True

    return False

def handle_invulnerability(move: Move, attacker: Trainer, defender: Trainer) -> bool:
    can_hit = (
        defender.invulnerable_state is not None and
        defender.invulnerable_state in (move.hits_invulnerable or [])
    )

    if can_hit:
        if defender.invulnerable_state == "flying":
            game_print(f"It hit {defender.active().name} out of the sky!")
        else:
            game_print(f"It hit {defender.active().name}!")
        return False

    message = "is invulnerable!"
    if defender.locked_move is not None and defender.locked_move.multi_turn is not None:
        message = defender.locked_move.multi_turn.invulnerable_message or "is invulnerable!"

    game_print(f"{defender.active().name} {message}")
    game_print(f"{attacker.active().name}'s attack missed!")
    return True

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

def check_immunity(move: Move, attacker: Trainer, defender: Trainer) -> bool:
    """Returns True if the move is blocked, False if it can hit."""

    # check type immunities on the move itself
    for immune_type in move.immune_types:
        if immune_type in defender.active().type:
            game_print(f"It doesn't affect {defender.active().name}!")
            return True

    # check if defender is using a blocking move
    for immune_move in move.immune_moves:
        if (defender.locked_move is not None and
                defender.locked_move.name.lower() == immune_move):
            game_print(f"{defender.active().name} protected itself!")
            return True

    # check type chart immunity (0x effectiveness)
    multiplier = get_type_multiplier(move.type[0], defender.active().type)
    if multiplier == 0:
        game_print("It had no effect!")
        return True

    return False

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

def get_type_multiplier(move_type: str, defender_types: list[str]) -> int:
    multiplier = 1

    for defender_type in defender_types:
        multiplier *= type_chart.get(move_type, {}).get(defender_type, 1)
    return multiplier

def apply_recoil(move: Move, attacker: Trainer, damage: int) -> None:
    recoil_damage = round(damage * move.recoil)
    attacker.active().hp = max(0, attacker.active().hp - recoil_damage)
    game_print(f"{attacker.active().name} took {recoil_damage} recoil damage!")

def apply_lifesteal(move, attacker, damage) -> None:
    heal_amount = round(damage * move.lifesteal)
    attacker.active().hp = min(
        attacker.active().max_hp,
        attacker.active().hp + heal_amount
    )
    game_print(f"{attacker.active().name} drained {heal_amount} HP!")

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

def apply_status_effect_from_move(move: Move, defender: Trainer) -> tuple[str, Optional[StatusEffect]]:
    import copy
    
    if move.status_effect is None:
        return "failed", None
    
    effect = copy.deepcopy(move.status_effect)
    
    if random.random() < effect.chance_to_apply:
        success = defender.active().apply_status_effect(effect)
        if success:
            return "afflicted", effect
        else:
            return "already", effect  # blocked because major status already exists
    return "failed", effect

def process_effect(pokemon: Pokemon, effect: StatusEffect) -> bool:
    # Process a single status effect. Returns True if the effect should be removed
    if effect.check_should_end():
        return True

    # Confusion is handled in check_can_act since it influences attackers chance to attack
    match effect.name:
        case "Poison" | "Curse":
            if effect.damage is not None:
                damage = round(pokemon.max_hp * effect.damage)
                pokemon.hp = max(0, pokemon.hp - damage)
                game_print(f"{pokemon.name} was hurt by {effect.name.lower()}!")
                game_print(f"{pokemon.name} took {damage} damage!")
        case "Burn":
            if effect.damage is not None:
                damage = round(pokemon.max_hp * effect.damage)
                pokemon.hp = max(0, pokemon.hp - damage)
                game_print(f"{pokemon.name} was hurt by its burn!")
                game_print(f"{pokemon.name} took {damage} damage!")
            else:
                game_print(f"{pokemon.name} is confused!")

    return False

def remove_expired_effects(pokemon: Pokemon, effects_to_remove: list[StatusEffect]) -> None:
    # Remove expired effects and print removal messages
    removal_messages = {
        "Poison":    " was cured of poison!",
        "Paralysis": " was cured of paralysis!",
        "Sleep":     " woke up!",
        "Burn":      " was cured of its burn!",
        "Freeze":    " thawed out!",
        "Confusion": " snapped out of confusion!",
        "Curse":     " is no longer cursed!",
    }
    for effect in effects_to_remove:
        pokemon.remove_status_effect(effect)
        message = removal_messages.get(effect.name, " is no longer affected!")
        game_print(f"{pokemon.name}{message}")

def get_all_effects(pokemon: Pokemon) -> list[StatusEffect]:
    # Get all active status effects for a pokemon
    return ([pokemon.major_status] if pokemon.major_status else []) + pokemon.minor_status

def process_status_effects(pokemon: Pokemon) -> None:
    effects_to_remove = []

    for effect in get_all_effects(pokemon):
        if process_effect(pokemon, effect):
            effects_to_remove.append(effect)

    remove_expired_effects(pokemon, effects_to_remove)

def apply_modifier(move: Move, pokemon: Pokemon, current_turn: int) -> None:
    if move.modifier is None:
        return
    modifier              = copy.deepcopy(move.modifier)
    modifier.expires_turn = current_turn + 1 if move.modifier.expires_turn == 0 else move.modifier.expires_turn
    pokemon.add_modifier(modifier)
    game_print(f"{pokemon.name} is affected by {modifier.name}!")

def get_modifier_value(
    attr:         str,
    move:         Move,
    pokemon:      Pokemon,
    current_turn: int
) -> float:
    total = 1.0
    expired = []

    for modifier in pokemon.get_active_modifiers(current_turn):
        if not modifier.applies_to(move):
            continue
        value = getattr(modifier, attr, 1.0)
        total *= value

        # consume single turn modifiers after use
        if modifier.expires_turn != -1 and current_turn >= modifier.expires_turn:
            expired.append(modifier)
            if modifier.consume_message:
                game_print(modifier.consume_message)

    for modifier in expired:
        pokemon.remove_modifier(modifier)

    return total

def clear_expired_effects(trainer: Trainer, current_turn: int) -> None:
    expired = [e for e in trainer.active_effects
               if e.effect_type != "protect" and e.turns <= current_turn]
    for effect in expired:
        trainer.active_effects.remove(effect)
        game_print(f"The effect wore off!")

    # always clear protect at end of turn
    trainer.active_effects = [e for e in trainer.active_effects
                              if e.effect_type != "protect"]

def clear_switch_effects(trainer: Trainer) -> None:
    """Clear effects that should end on switch."""
    trainer.active_effects = [
        e for e in trainer.active_effects
        if not e.properties.get("clears_on_switch", True)
    ]

def clear_expired_modifiers(pokemon: Pokemon, current_turn: int) -> None:
    pokemon.clear_expired_modifiers(current_turn)

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
                game_print(f"{trainer.active().name} {effect.fail_message}")
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
    game_print(f"{trainer.active().name} {effect.message}")
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
        game_print("But it failed!")
        return True

    screen        = copy.deepcopy(effect)
    screen.turns  = current_turn + effect.turns  # store expiry turn
    trainer.active_effects.append(screen)
    game_print(f"{trainer.active().name} {effect.message}")
    return True

def handle_mist_effect(
    effect:       MoveEffect,
    trainer:      Trainer,
    current_turn: int
) -> bool:
    if any(e.effect_type == "mist" for e in trainer.active_effects):
        game_print("But it failed!")
        return True

    mist       = copy.deepcopy(effect)
    mist.turns = current_turn + effect.turns
    trainer.active_effects.append(mist)
    game_print(f"{trainer.active().name} {effect.message}")
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
            game_print(f"The screen wore off!")

    for effect in expired:
        defender.active_effects.remove(effect)

    return modifier

def blocks_stat_changes(trainer: Trainer) -> bool:
    """Check if mist is preventing stat changes."""
    return any(
        e.effect_type == "mist" and e.properties.get("blocks_stat_changes")
        for e in trainer.active_effects
    )
                              
def check_can_act(pokemon: Pokemon) -> tuple[bool, Optional[str]]:
    all_effects = get_all_effects(pokemon)
    for effect in all_effects:
        if effect.name == "Confusion":
            if random.random() < 0.5:  # 50% chance to hurt itself
                damage = round(pokemon.max_hp * 0.1)
                pokemon.hp = max(0, pokemon.hp - damage)
                game_print(f"{pokemon.name} hurt itself in confusion!")
                game_print(f"{pokemon.name} took {damage} damage!")
                return False, "Confusion"  # skip attack this turn
            else:
                game_print(f"{pokemon.name} is confused!")
        elif not effect.can_act():
            return False, effect.name
    return True, None

def clear_move_lock(trainer: Trainer) -> None:
    if trainer.locked_move is not None and trainer.locked_turns == 0:
        trainer.active().accumulator = 0
        trainer.locked_move          = None
        trainer.invulnerable_state   = None

def next_mon(player: Trainer, npc: Trainer) -> None:
    if not player.active().is_alive():
        game_print(f"{player.active().name} fainted!")
        player.active().clear_all_modifiers()  # default clears switchable ones
        new_mon = get_party(player)
        if new_mon is not None:
            player.selected_mon = player.party.index(new_mon)

    if not npc.active().is_alive():
        game_print(f"{npc.active().name} fainted!")
        npc.active().clear_all_modifiers()
        new_mon = get_party(npc)
        if new_mon is not None:
            npc.selected_mon = npc.party.index(new_mon)
                
def check_winner(player: Trainer, npc: Trainer) -> Trainer | None:
    if not any(pokemon.is_alive() for pokemon in player.party):
        game_print(f"{npc.name} Wins!")
        return npc      # return trainer object instead of True
    if not any(pokemon.is_alive() for pokemon in npc.party):
        game_print(f"{player.name} Wins!")
        return player   # return trainer object instead of True
    return None
