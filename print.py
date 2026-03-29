import sys

def print_actions(trainer):
    while True:
        try:
            print(f"{trainer.name}'s {trainer.party[trainer.selected_mon].name}:")
            print("1. Moves")
            print("2. Pokemon")
            print("3. Items")
            choice = int(input("Select an action: "))
            if choice not in range(1, 4):
                raise ValueError
            return choice
        except ValueError:
            print("Invalid choice, please select again.")
    
def print_stats(player, npc):
    for key, value in vars(player.party[player.selected_mon]).items():
        print(f"{key}: {value}")
    for key, value in vars(npc.party[npc.selected_mon]).items():
        print(f"{key}: {value}")

def print_battle_status(player, npc):
    print(f"DEBUG player party hp: {[p.hp for p in player.party]}")
    print(f"DEBUG npc party hp: {[p.hp for p in npc.party]}")
    print(f"DEBUG player alive: {[p.is_alive() for p in player.party]}")
    print(f"DEBUG npc alive: {[p.is_alive() for p in npc.party]}")

def print_stat_changes(old_stats):
    stat_messages = {
        "stat_attk":    ("'s attack rose",        "'s attack fell"),
        "stat_def":     ("'s defense rose",       "'s defense fell"),
        "stat_sp_attk": ("'s sp. attack rose",    "'s sp. attack fell"),
        "stat_sp_def":  ("'s sp. defense rose",   "'s sp. defense fell"),
        "stat_spd":     ("'s speed rose",         "'s speed fell"),
        "acc":          ("'s accuracy rose",      "'s accuracy fell"),
        "eva":          ("'s evasion rose",       "'s evasion fell")
    }

    stat_name = {
        "stat_attk":    "Attack",
        "stat_def":     "Defense",
        "stat_sp_attk": "Special Attack",
        "stat_sp_def":  "Special Defense",
        "stat_spd":     "Speed",
        "acc":          "Accuracy",
        "eva":          "Evasion"
    }

    stage_amount = {
        1: "",
        2: " sharply",
        3: " drastically"
    }

    for stat, old_value, target, actual_change in old_stats:
        if stat in stat_messages:
            if actual_change == 0:
                stat_name = stat_name.get(stat, stat)
                print(f"{target.name}'s {stat_name} won't go any further!")
            else:
                up_message, down_message = stat_messages[stat]
                amount = stage_amount.get(abs(actual_change), " drastically")
                if actual_change > 0:
                    print(f"{target.name}{up_message}{amount}!")
                elif actual_change < 0:
                    print(f"{target.name}{down_message}{amount}!")
 
def print_status_effect(target, effect, afflicted):
    status_messages = {
        "Poison":    " was poisoned!",
        "Paralysis": " was paralyzed!",
        "Sleep":     " was put to sleep!",
        "Burn":      " was burned!",
        "Freeze":    " was frozen!",
    }
    already_messages = {
        "Poison":    " is already poisoned!",
        "Paralysis": " is already paralyzed!",
        "Sleep":     " is already asleep!",
        "Burn":      " is already burned!",
        "Freeze":    " is already frozen!",
    }

    if afflicted:
        print(f"{target.name}{status_messages[effect.name]}")
    else:
        print(f"{target.name}{already_messages[effect.name]}")

def print_cant_act(attacker, reason):
    cant_act_messages = {
        "Paralysis": " is paralyzed and can't move!",
        "Sleep":     " is fast asleep!",
        "Freeze":    " is frozen solid!",
    }
    
    message = cant_act_messages.get(reason, " can't move!")
    print(f"{attacker.active().name}{message}")