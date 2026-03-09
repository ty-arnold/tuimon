from models import Pokemon, Trainer
from type_chart import type_chart
from print import *

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

        target.hp            = max(0,target.hp + (move.stat_hp * multiplier))
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

# def deal_damage:

# def apply_stats:

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
        print(f"DEBUG player party hp: {[p.hp for p in player.party]}")
        print(f"DEBUG npc party hp: {[p.hp for p in npc.party]}")
        print(f"DEBUG player alive: {[p.is_alive() for p in player.party]}")
        print(f"DEBUG npc alive: {[p.is_alive() for p in npc.party]}")
        if not any(pokemon.is_alive() for pokemon in player.party):
                print(f"{npc.name} Wins!")
                return True
        if not any(pokemon.is_alive() for pokemon in npc.party):
                print(f"{player.name} Wins!")
                return True
        return None
