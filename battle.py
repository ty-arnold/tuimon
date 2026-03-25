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
        print(f"{attacker.active().name} used {move.name}!")

        if random.random() > move.acc:
                print(f"{attacker.active().name}'s attack missed!")
                return None

        old_stats = []

        if move.category != "status":
                damage, multiplier = calculate_damage(move, attacker, defender)
                target = defender.active()

                old_stats.append(("hp", target.hp, target))
                target.hp = max(0, target.hp - damage)

                if multiplier == 0:
                        print("It had no effect!")
                elif multiplier < 1:
                        print("It's not very effective...")
                elif multiplier > 1:
                        print("It's super effective!")

                if move.recoil > 0:
                        recoil_damage = int(damage * move.recoil)
                        old_stats.append(("recoil_hp", attacker.active().hp, attacker.active()))
                        attacker.active().hp = max(0, attacker.active().hp - recoil_damage)
                        print(f"{attacker.active().name} took {recoil_damage} recoil damage!")

        for target_type, stat_changes in move.effects.items():
                if target_type == "self":
                        target = attacker.active()
                elif target_type == "opponent":
                        target = defender.active()
                elif target_type == "random":
                        target = random.choice([attacker.active(), defender.active()])

                for stat, value in stat_changes.items():
                        old_stats.append((stat, getattr(target, stat), target))
                        current = getattr(target, stat)
                        if stat == "hp":
                                setattr(target, stat, max(0, int(current + value)))
                        else:
                                setattr(target, stat, int(current + value))

        damage_messages = {
                "hp":           (" gained {diff} HP",               " took {diff} damage"),
                "max_hp":       ("'s max HP increased by {diff}",   "'s max HP decreased by {diff}"),
                "stat_attk":    ("'s attack rose by {diff}",        "'s attack fell by {diff}"),
                "stat_def":     ("'s defense rose by {diff}",       "'s defense fell by {diff}"),
                "stat_sp_attk": ("'s sp. attack rose by {diff}",    "'s sp. attack fell by {diff}"),
                "stat_sp_def":  ("'s sp. defense rose by {diff}",   "'s sp. defense fell by {diff}"),
                "stat_spd":     ("'s speed rose by {diff}",         "'s speed fell by {diff}")
        }

        for stat, old_value, target in old_stats:
                new_value = getattr(target, stat)
                diff = abs(new_value - old_value)
                up_message, down_message = damage_messages[stat]
                if new_value > old_value:
                        print(f"{target.name}{up_message.format(diff=diff)}!")
                elif new_value < old_value:
                        print(f"{target.name}{down_message.format(diff=diff)}!")

        if move.status_effect is not None:
                effect = move.status_effect
                status_messages = {
                "Poison":    " was poisoned!",
                "Paralysis": " was paralyzed!",
                "Sleep":     " was put to sleep!",
                "Burn":      " was burned!",
                "Freeze":    " was frozen!",
                }
                if not any(e.name == effect.name for e in defender.active().status_effect):
                        if random.random() < effect.chance_to_apply:
                                print(f"{defender.active().name}{status_messages[effect.name]}")
                                defender.active().apply_status_effect(effect)
                        else:
                                print(f"{defender.active().name} is already affected by {effect.name}!")

def calculate_damage(move, attacker, defender):
        if move.category == "physical":
                attack_stat = attacker.active().stat_attk
                defense_stat = defender.active().stat_def
        elif move.category == "special":
                attack_stat = attacker.active().stat_sp_attk
                defense_stat = defender.active().stat_sp_def
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
        
def process_status_effects(pokemon):
        effects_to_remove = []
        for effect in pokemon.status_effect:
                match effect.name:
                        case "Poison":
                                print(f"{pokemon.name} was hurt my poison!")
                                pokemon.hp = max(0, (pokemon.hp - (pokemon.hp * 0.1)))
                        case "Burn":
                                print(f"{pokemon.name} was hurt by burn!")
                                pokemon.hp = max(0, (pokemon.hp - (pokemon.hp * 0.1)))
                              
                if effect.check_should_end():
                        effects_to_remove.append(effect)
                
                if effect in effects_to_remove:
                       pokemon.remove_status_effect(effect)
                              
def check_can_act(pokemon):
       return all(effect.can_act() for effect in pokemon.status_effect)

def get_type_multiplier(move_type, defender_types):
        multiplier = 1

        for defender_type in defender_types:
                multiplier *= type_chart.get(move_type, {}).get(defender_type, 1)
        return multiplier

def resolve_turn(player, player_choice, npc, npc_choice):
        player_can_act = check_can_act(player.active())
        npc_can_act = check_can_act(npc.active())

        if player.active().stat_spd > npc.active().stat_spd:
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
