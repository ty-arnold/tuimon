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

def resolve_turn(player: Trainer, player_choice: Move, npc: Trainer, npc_choice: Move) -> bool | None:
    player_can_act, player_cant_act_reason = check_can_act(player.active())
    npc_can_act,    npc_cant_act_reason    = check_can_act(npc.active())

    order = get_turn_order(player, player_choice, npc, npc_choice, player_can_act, npc_can_act)

    second_mon_before = order.second.selected_mon

    if order.first_can_act:
        apply_move(order.first_choice, order.first, order.second)
        clear_move_lock(order.first)
        winner = check_winner(player, npc)
        if winner:
            return True
        next_mon(player, npc)

    # checks if the second pokemon fainted - if so, skip its move turn
    if order.second.selected_mon != second_mon_before:
        return None
        
    if order.second_can_act:
        apply_move(order.second_choice, order.second, order.first)
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

def apply_move(move: Move, attacker: Trainer, defender: Trainer) -> None:
    logger.debug(f"Attacker: {attacker.active().name} HP: {attacker.active().hp}/{attacker.active().max_hp}")
    logger.debug(f"Defender: {defender.active().name} HP: {defender.active().hp}/{defender.active().max_hp}")

    old_stats = []
    damage = 0

    can_act, reason = check_can_act(attacker.active())
    if not can_act:
        print_cant_act(attacker, reason)
        return None
    
    move.pp -= 1
    if move.pp <= 0:
        game_print(f"{move.name} has no PP left!")

    game_print(f"{attacker.active().name} used {move.name}!")

    if move.multi_turn is not None: 
        if handle_multiturn(move, attacker):
            return None

    if defender.invulnerable_state is not None:
        if handle_invulnerability(move, defender):
            game_print(f"{attacker.active().name}'s attack missed!") 
            return None

    if not check_accuracy(move, attacker, defender):
        game_print(f"{attacker.active().name}'s attack missed!") 
        return None

    if move.category != "status":
        if move.min_hits is not None and move.max_hits is not None:
            # multi hit move
            roll         = random.randint(move.min_hits, move.max_hits)
            damage       = 0
            hits_landed  = 0

            for i in range(roll):
                hit_damage = apply_damage(move, attacker, defender)
                damage    += hit_damage
                hits_landed += 1

                # stop if defender faints mid-combo
                if not defender.active().is_alive():
                    break

            game_print(f"Hit {hits_landed} time(s)!")
        else:
            # single hit move
            damage = apply_damage(move, attacker, defender)

    if move.multi_turn is not None and move.multi_turn.get("charge_turn") == 2:
        attacker.locked_move  = move
        attacker.locked_turns = 1

    if move.lifesteal > 0 and damage > 0:
        apply_lifesteal(move, attacker, damage)

    if move.heal > 0:
        heal_amount = round(attacker.active().max_hp * move.heal)
        attacker.active().hp = min(attacker.active().max_hp, attacker.active().hp + heal_amount)
        logger.info(f"{attacker.active().name} restored {heal_amount} HP!")

    if move.recoil > 0:
        apply_recoil(move, attacker, damage)

    if move.stat_change:
        old_stats = apply_stat_change(move, attacker, defender, old_stats)
        print_stat_changes(old_stats)

    if move.status_effect is not None:
        result, effect = apply_status_effect_from_move(move, defender)
        print_status_effect(defender.active(), effect, result)

def handle_multiturn(move: Move, attacker: Trainer) -> bool:
    # handle recharge turn - charge_turn 2 means attack first then recharge
    if attacker.locked_move is not None and attacker.locked_move.multi_turn is not None:
        if attacker.locked_move.multi_turn.get("charge_turn") == 2:
            game_print(f"{attacker.active().name} {attacker.locked_move.multi_turn['charge_message']}")
            return True

    # handle normal charge turn - charge_turn 1 means charge first then attack
    if move.multi_turn is not None and attacker.locked_move is None:
        attacker.locked_move        = move
        attacker.locked_turns       = move.multi_turn["turns"] - 1
        attacker.invulnerable_state = move.multi_turn.get("invulnerable_state")

        if move.multi_turn.get("charge_turn") == 1:
            game_print(f"{attacker.active().name} {move.multi_turn['charge_message']}")
            return True

    return False

def handle_invulnerability(move: Move, defender: Trainer) -> bool:
    can_hit = defender.invulnerable_state in (move.hits_invulnerable or [])
    
    if can_hit:
        if defender.invulnerable_state == "flying":
            logger.info(f"It hit {defender.active().name} out of the sky!")
        else:
            logger.info(f"It hit {defender.active().name}!")
        return False

    # print invulnerable state message but NOT the missed message
    message = "is invulnerable!"
    if defender.locked_move is not None and defender.locked_move.multi_turn is not None:
        message = defender.locked_move.multi_turn.get("invulnerable_message", "is invulnerable!")
    logger.info(f"{defender.active().name} {message}")
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

def apply_damage(move: Move, attacker: Trainer, defender: Trainer) -> int:
    damage, multiplier = calculate_damage(move, attacker, defender)
    logger.debug(f"Damage calculated: {damage} (multiplier: {multiplier})")
    target = defender.active()

    target.hp = max(0, target.hp - damage)

    if multiplier == 0:
        game_print("But it had no effect...")
    elif multiplier < 1:
        game_print("But it's not very effective...")
    elif multiplier > 1:
        game_print("It's super effective!")
    
    game_print(f"{target.name} took {damage} damage!")  
    return damage  

def calculate_damage(move: Move, attacker: Trainer, defender: Trainer) -> tuple:
    if move.category == "physical":
        attack_stat = attacker.active().get_stat("stat_attk")
        defense_stat = defender.active().get_stat("stat_def")
    elif move.category == "special":
        attack_stat = attacker.active().get_stat("stat_sp_attk")
        defense_stat = defender.active().get_stat("stat_sp_def")
    else:
        return 0, 1
    
    logger.debug(f"calculate_damage: attack={attack_stat} defense={defense_stat}")
        
    multiplier = get_type_multiplier(move.type[0], defender.active().type)

    crit_chance = crit_rate_table.get(move.crit_rate, 1/16)
    critical    = 2 if random.random() < crit_chance else 1
    if critical == 2:
        game_print("Critical hit!")

    stab = 1.5 if attacker.active().type == move.type[0] else 1

    damage = round(
        (((2 * attacker.active().lvl * critical / 5) + 2) * move.power * (attack_stat / defense_stat) / 50 + 2)
        * multiplier * stab
    )
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
        trainer.locked_move        = None
        trainer.invulnerable_state = None

def next_mon(player: Trainer, npc: Trainer) -> None:
    if not player.party[player.selected_mon].is_alive():
        game_print(f"{player.party[player.selected_mon].name} fainted!")
        player.print_party()
        new_mon = get_party(player)
        if new_mon is not None:
            player.selected_mon = player.party.index(new_mon)

    if not npc.party[npc.selected_mon].is_alive():
        game_print(f"{npc.party[npc.selected_mon].name} fainted!")
        player.print_party()
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
