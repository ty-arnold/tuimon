import sys

def print_actions(trainer):
    while True:
        try:
            print(f"{trainer.name}'s {trainer.active().name}:")
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
    stat_name = {
        "stat_attk":    "Attack",
        "stat_def":     "Defense",
        "stat_sp_attk": "Special Attack",
        "stat_sp_def":  "Special Defense",
        "stat_spd":     "Speed",
        "acc":          "Accuracy",
        "eva":          "Evasion"
    }

    stat_messages = {
        "stat_attk":    ("'s attack rose",        "'s attack fell"),
        "stat_def":     ("'s defense rose",       "'s defense fell"),
        "stat_sp_attk": ("'s sp. attack rose",    "'s sp. attack fell"),
        "stat_sp_def":  ("'s sp. defense rose",   "'s sp. defense fell"),
        "stat_spd":     ("'s speed rose",         "'s speed fell"),
        "stat_acc":     ("'s accuracy rose",      "'s accuracy fell"),
        "stat_eva":     ("'s evasion rose",       "'s evasion fell")
    }

    stage_amount = {
        1: "",
        2: " sharply",
        3: " drastically"
    }

    for stat, old_value, target, actual_change in old_stats:
        if stat in stat_messages:
            if actual_change == 0:
                display_name = stat_name.get(stat, stat)
                print(f"{target.name}'s {display_name} won't go any further!")
            else:
                up_message, down_message = stat_messages[stat]
                amount = stage_amount.get(abs(actual_change), " drastically")
                if actual_change > 0:
                    print(f"{target.name}{up_message}{amount}!")
                elif actual_change < 0:
                    print(f"{target.name}{down_message}{amount}!")
 
def print_status_effect(target, effect, result):
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

    match result:
        case "afflicted":
            print(f"{target.name}{status_messages[effect.name]}")
        case "already":
            print(f"{target.name}{already_messages[effect.name]}")
        case "failed":
            pass
            

def print_cant_act(attacker, reason):
    cant_act_messages = {
        "Paralysis": " is paralyzed and can't move!",
        "Sleep":     " is fast asleep!",
        "Freeze":    " is frozen solid!",
    }
    
    message = cant_act_messages.get(reason, " can't move!")
    print(f"{attacker.active().name}{message}")

def debug_print_stats(pokemon):
    stats = ["stat_attk", "stat_def", "stat_sp_attk", "stat_sp_def", "stat_spd", "stat_acc", "stat_eva"]
    stat_names = {
        "stat_attk":    "Attack",
        "stat_def":     "Defense",
        "stat_sp_attk": "Special Attack",
        "stat_sp_def":  "Special Defense",
        "stat_spd":     "Speed",
        "stat_acc":     "Accuracy",
        "stat_eva":     "Evasion",
    }
    stage_attr = {
        "stat_attk":    "stage_attk",
        "stat_def":     "stage_def",
        "stat_sp_attk": "stage_sp_attk",
        "stat_sp_def":  "stage_sp_def",
        "stat_spd":     "stage_spd",
        "stat_acc":     "stage_acc",
        "stat_eva":     "stage_eva",
    }
    print(f"--- {pokemon.name} Stats ---")
    print(f"HP:  {pokemon.hp}/{pokemon.max_hp}")
    print(f"{'Stat':<20} {'Base':<10} {'Stage':<10} {'Calculated':<10}")
    print(f"{'-' * 50}")
    for stat in stats:
        base       = getattr(pokemon, stat)
        stage      = getattr(pokemon, stage_attr[stat])
        calculated = pokemon.get_stat(stat)
        print(f"{stat_names[stat]:<20} {base:<10} {stage:<10} {calculated:<10}")
    print(f"{'Status Effects:':<20} {[e.name for e in pokemon.status_effect]}")
    print(f"{'-' * 50}")