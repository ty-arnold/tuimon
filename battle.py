from models import Pokemon, Trainer
from type_chart import type_chart
from print import *

def get_turn(trainer):
    action_selected = False
    move = None
    while not action_selected:
        action = display_actions(trainer)
        if action == 1:
            move = display_moves(trainer.party[trainer.selected_mon])
            if move is not None:
                action_selected = True
        elif action == 2:
            pokemon = display_party(trainer)
            if pokemon is not None:
                trainer.selected_mon = trainer.party.index(pokemon)
                action_selected = True
        elif action == 3:
            pass
    return move

def apply_move(move, attacker, defender):
        print(f"{attacker.party[attacker.selected_mon].name} used {move.name}!")
        if move.target == "self":
                target = attacker.party[attacker.selected_mon]
                multiplier = 1
        else:
                target = defender.party[defender.selected_mon]
                multiplier = get_type_multiplier(move.type[0], defender.party[defender.selected_mon].type)

        old_stats = {
        "hp":           target.hp,
        "max_hp":       target.max_hp,
        "stat_attk":    target.stat_attk,
        "stat_def":     target.stat_def,
        "stat_sp_attk": target.stat_sp_attk,
        "stat_sp_def":  target.stat_sp_def,
        "stat_spd":     target.stat_spd
        }

        messages = {
        "max_hp":       ("max HP increased",     "max HP decreased"),
        "stat_attk":    ("attack rose",          "attack fell"),
        "stat_def":     ("defense rose",         "defense fell"),
        "stat_sp_attk": ("sp. attack rose",      "sp. attack fell"),
        "stat_sp_def":  ("sp. defense rose",     "sp. defense fell"),
        "stat_spd":     ("speed rose",           "speed fell")
        }

        target.hp           += (move.stat_hp * multiplier)
        target.max_hp       += move.stat_max_hp
        target.stat_attk    += move.stat_attk
        target.stat_def     += move.stat_def
        target.stat_sp_attk += move.stat_sp_attk
        target.stat_sp_def  += move.stat_sp_def
        target.stat_spd     += move.stat_spd
        
        if target.hp > old_stats["hp"]:
                print(f"{target.name} gained {abs(move.stat_hp)} HP!")
        elif target.hp < old_stats["hp"]:
                print(f"{target.name} took {abs((move.stat_hp * multiplier))} Damage!")

        if move.target == "opponent":
                if multiplier == 0:
                        print("It had no effect!")
                elif multiplier < 1:
                        print("It's not very effective...")
                elif multiplier > 1:
                        print("It's super effective!")

        for stat, (up_message, down_message) in messages.items():
                new_value = getattr(target, stat)
                old_value = old_stats[stat]
                if new_value > old_value:
                        print(f"{target.name}'s {up_message}!")
                elif new_value < old_value:
                        print(f"{target.name}'s {down_message}!")

def get_type_multiplier(move_type, defender_types):
        multiplier = 1

        for defender_type in defender_types:
                multiplier *= type_chart.get(move_type, {}).get(defender_type, 1)
        return multiplier

def take_turn(attacker, attacker_choice, defender):
        apply_move(attacker_choice, attacker, defender)
        return check_winner(attacker, defender)

def resolve_turn(player, player_choice, npc, npc_choice):
        if player.party[player.selected_mon].stat_spd > npc.party[npc.selected_mon].stat_spd:
                first, first_choice, second, second_choice = player, player_choice, npc, npc_choice
        else:
                first, first_choice, second, second_choice = npc, npc_choice, player, player_choice

        winner = take_turn(first, first_choice, second)
        if winner:
                return winner
        return take_turn(second, second_choice, first)
                
def check_winner(player, npc):
        if not any(pokemon.is_alive() for pokemon in player.party):
                print(f"{npc.name} Wins!")
                return True
        if not any(pokemon.is_alive() for pokemon in npc.party):
                print(f"{player.name} Wins!")
                return True
        return None