from models import Pokemon, Trainer
from type_chart import type_chart
from print import *
from mult_tables import *
import random

def get_turn(trainer):
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
                if pokemon is not None:
                        trainer.selected_mon = trainer.party.index(pokemon)
        elif action == 3:
                pass
    return move

def get_party(trainer):
    while True:
        try:
            cancel = len(trainer.party) + 1
            choice = int(input("Select a Pokemon: "))
            if choice == cancel and trainer.active().is_alive() == True:
                return None
            selected_mon = trainer.party[choice - 1]
            if not selected_mon.is_alive():
                print(f"{selected_mon.name} has already fainted! Please select Pokemon.")
                continue
            if choice - 1 == trainer.selected_mon:
                print(f"{selected_mon.name} is already selected!")
                return None
            print(f"You selected {selected_mon.name}!")
            trainer.selected_mon = choice - 1
            return selected_mon
        except (ValueError, IndexError):
            print("Invalid choice, please select again")

def get_move(pokemon):
    try:
        while True:
            try:
                cancel = len(pokemon.moveset) + 1
                choice = int(input("Select a Move: "))
                if choice == cancel:
                    return None
                selected_move = pokemon.moveset[choice - 1]
                print(f"You selected {selected_move.name}!")
                return pokemon.moveset[choice - 1]
            except (ValueError, IndexError):
                print("Invalid choice, please select again")
                pokemon.list_moves()

    except KeyboardInterrupt:
        print("\\nGame Over!")
        sys.exit(0)

def apply_move(move, attacker, defender):
    old_stats = []
    damage = float

    can_act, reason = check_can_act(attacker.active())
    if not can_act:
        print_cant_act(attacker, reason)
        return None

    print(f"{attacker.active().name} used {move.name}!")

    if check_accuracy(move, attacker, defender) is not True:
        return None

    if move.category != "status":
        damage = apply_damage(move, attacker, defender)

    if move.recoil > 0:
        apply_recoil(move, attacker, damage)

    if move.effects:
        old_stats = apply_stats(move, attacker, defender, old_stats)
        print_stat_changes(old_stats)

    if move.status_effect is not None:
        afflicted, effect = apply_status_effect(move, defender)
        print_status_effect(defender.active(), effect, afflicted)

def check_accuracy(move, attacker, defender):
    move_acc = move.acc * acc_table[attacker.active().stage_acc]
    evasion  = acc_table[defender.active().stage_eva]
    if random.random() > move_acc * evasion:
        print(f"{attacker.active().name}'s attack missed!")
        return False
    else:
        return True

def apply_damage(move, attacker, defender):
    damage, multiplier = calculate_damage(move, attacker, defender)
    target = defender.active()

    target.hp = max(0, target.hp - damage)

    if multiplier == 0:
        print("It had no effect!")
    elif multiplier < 1:
        print("It's not very effective...")
    elif multiplier > 1:
        print("It's super effective!")
    
    print(f"{target.name} took {damage} damage!")  
    return damage  

def calculate_damage(move, attacker, defender):
    if move.category == "physical":
        attack_stat = attacker.active().get_stat("stat_attk")
        defense_stat = defender.active().get_stat("stat_def")
    elif move.category == "special":
        attack_stat = attacker.active().get_stat("stat_attk")
        defense_stat = defender.active().get_stat("stat_def")
    else:
        return 0, 1
        
    multiplier = get_type_multiplier(move.type[0], defender.active().type)

    critical = 2 if random.random() < (1/16) else 1
    if critical == 2:
        print("Critical hit!")

    stab = 1.5 if attacker.active().type == move.type[0] else 1

    damage = int(
        (((2 * attacker.active().lvl * critical / 5) + 2) * move.power * (attack_stat / defense_stat) / 50 + 2)
        * multiplier * stab
    )
    return damage, multiplier

def get_type_multiplier(move_type, defender_types):
    multiplier = 1

    for defender_type in defender_types:
        multiplier *= type_chart.get(move_type, {}).get(defender_type, 1)
    return multiplier

def apply_recoil(move, attacker, damage):
    recoil_damage = int(damage * move.recoil)
    attacker.active().hp = max(0, attacker.active().hp - recoil_damage)
    print(f"{attacker.active().name} took {recoil_damage} recoil damage!")

def apply_stats(move, attacker, defender, old_stats):
    for target_type, stat_changes in move.effects.items():
        target = None
        if target_type == "self":
            target = attacker.active()
        elif target_type == "opponent":
            target = defender.active()
        elif target_type == "random":
            target = random.choice([attacker.active(), defender.active()])

        for stat, change in stat_changes.items():
            old_stage = getattr(target, f"stage_{stat.replace('stat_', '')}")
            actual_change = target.apply_stage_change(stat, change)
            old_stats.append((stat, old_stage, target, actual_change))

    return old_stats

def apply_status_effect(move, defender):
    effect = move.status_effect
    if not any(e.name == effect.name for e in defender.active().status_effect):
        if random.random() < effect.chance_to_apply:
            defender.active().apply_status_effect(effect)
            return True, effect   # afflicted successfully
        else:
            return False, effect  # failed to apply
    else:
        return False, effect      # already afflicted

def process_status_effects(pokemon):
    effects_to_remove = []
    removal_messages = {
        "Poison":    " was cured of poison!",
        "Paralysis": " was cured of paralysis!",
        "Sleep":     " woke up!",
        "Burn":      " was cured of its burn!",
        "Freeze":    " thawed out!",
    }

    for effect in pokemon.status_effect:
        if effect.check_should_end():
            effects_to_remove.append(effect)
            continue  

        match effect.name:
            case "Poison":
                print(f"{pokemon.name} was hurt by poison!")
                pokemon.hp = max(0, (pokemon.hp - (pokemon.hp * 0.1)))
            case "Burn":
                print(f"{pokemon.name} was hurt by burn!")
                pokemon.hp = max(0, (pokemon.hp - (pokemon.hp * 0.1)))

    for effect in effects_to_remove:
        pokemon.remove_status_effect(effect)
        message = removal_messages.get(effect.name, " is no longer affected!")
        print(f"{pokemon.name}{message}")
                              
def check_can_act(pokemon):
    for effect in pokemon.status_effect:
        if not effect.can_act():
            return False, effect.name
    return True, None

def resolve_turn(player, player_choice, npc, npc_choice):
    player_can_act = check_can_act(player.active())
    npc_can_act = check_can_act(npc.active())

    if player.active().get_stat("stat_spd") > npc.active().get_stat("stat_spd"):
        first, first_choice, second, second_choice = player, player_choice, npc, npc_choice
        first_can_act, second_can_act = player_can_act, npc_can_act
    else:
        first, first_choice, second, second_choice = npc, npc_choice, player, player_choice
        first_can_act, second_can_act = npc_can_act, player_can_act

    second_mon_before = second.selected_mon

    if first_can_act:
        apply_move(first_choice, first, second)
        winner = check_winner(player, npc)
        if winner:
            return True
        next_mon(player, npc)
        
    if second.selected_mon != second_mon_before:
        return None
        
    if second_can_act:
        apply_move(second_choice, second, first)
        winner = check_winner(player, npc)
        if winner:
            return True
        next_mon(player, npc)

    process_status_effects(first.active())
    process_status_effects(second.active())
    winner = check_winner(player, npc)
    if winner:
        return True
    return None

def next_mon(player, npc):
    if not player.party[player.selected_mon].is_alive():
        print(f"{player.party[player.selected_mon].name} fainted!")
        player.print_party()
        new_mon = get_party(player)
        if new_mon is not None:
            player.selected_mon = player.party.index(new_mon)

    if not npc.party[npc.selected_mon].is_alive():
        print(f"{npc.party[npc.selected_mon].name} fainted!")
        player.print_party()
        new_mon = get_party(npc)
        if new_mon is not None:
            npc.selected_mon = npc.party.index(new_mon)
                
def check_winner(player, npc):
    if not any(pokemon.is_alive() for pokemon in player.party):
        print(f"{npc.name} Wins!")
        return True
    if not any(pokemon.is_alive() for pokemon in npc.party):
        print(f"{player.name} Wins!")
        return True
    return None
