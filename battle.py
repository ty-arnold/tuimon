from models import Pokemon, Trainer
from type_chart import type_chart
from print import *
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
        print(f"{attacker.party[attacker.selected_mon].name} used {move.name}!")

        for target_type, stat_changes in move.effects.items():
                if target_type == "self":
                        target = attacker.active()
                        multiplier = 1
                elif target_type == "opponent":
                        target = defender.active()
                        multiplier = get_type_multiplier(move.type[0], defender.active().type)
                elif target_type == "random":
                        target = random.choice([attacker.active(), defender.active()])
                        if target == attacker.active():
                              multiplier = 1
                        else:
                             multiplier = get_type_multiplier(move.type[0], defender.active().type) 

        old_stats = {stat: getattr(target, stat) for stat in stat_changes}

        for stat, value in stat_changes.items():
                current = getattr(target, stat)
                if stat == "hp":
                      setattr(target, stat, max(0, current + (value * multiplier)))
                else:
                      setattr(target, stat, current + value)

        if target_type == "opponent":
                if multiplier == 0:
                        print("It had no effect!")
                elif multiplier < 1:
                        print("It's not very effective...")
                elif multiplier > 1:
                        print("It's super effective!")

        messages = {
        "hp":           (" gained {diff} HP",          " took {diff} damage"),
        "max_hp":       ("'s max HP increased by {diff}", "'s max HP decreased by {diff}"),
        "stat_attk":    ("'s attack rose by {diff}",      "'s attack fell by {diff}"),
        "stat_def":     ("'s defense rose by {diff}",     "'s defense fell by {diff}"),
        "stat_sp_attk": ("'s sp. attack rose by {diff}",  "'s sp. attack fell by {diff}"),
        "stat_sp_def":  ("'s sp. defense rose by {diff}", "'s sp. defense fell by {diff}"),
        "stat_spd":     ("'s speed rose by {diff}",       "'s speed fell by {diff}")
        }

        for stat, old_value in old_stats.items():
                new_value = getattr(target, stat)
                diff = abs(new_value - old_value)
                up_message, down_message = messages[stat]
                if new_value > old_value:
                        print(f"{target.name}{up_message.format(diff=diff)}!")
                elif new_value < old_value:
                        print(f"{target.name}{down_message.format(diff=diff)}!")

        print_status(attacker, defender)

def get_type_multiplier(move_type, defender_types):
        multiplier = 1

        for defender_type in defender_types:
                multiplier *= type_chart.get(move_type, {}).get(defender_type, 1)
        return multiplier

def resolve_turn(player, player_choice, npc, npc_choice):
        if player.active().stat_spd > npc.active().stat_spd:
                first, first_choice, second, second_choice = player, player_choice, npc, npc_choice
        else:
                first, first_choice, second, second_choice = npc, npc_choice, player, player_choice

        second_mon_before = second.selected_mon

        apply_move(first_choice, first, second)
        winner = check_winner(player, npc)
        if winner:
                return True
        next_mon(player, npc)
        
        if second.selected_mon != second_mon_before:
               return None
        
        apply_move(second_choice, second, first)
        winner = check_winner(player, npc)
        if winner:
                return True
        next_mon(player, npc)
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
