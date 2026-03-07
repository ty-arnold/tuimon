import sys

def display_actions(trainer):
    try:
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
    
    except KeyboardInterrupt:
        print("\\nGame Over!")
        sys.exit(0) 

def display_party(trainer):
    try:
        print(f"{trainer.name}'s Party:")
        for i, pokemon in enumerate(trainer.party):
            print(f"{i + 1}. {pokemon.name}")
        print(f"{len(trainer.party) + 1}. Cancel")
        cancel = len(trainer.party) + 1
        while True:
            try:
                choice = int(input("Select a Pokemon: "))
                if choice == cancel:
                    return None
                selected_mon = trainer.party[choice - 1]
                if choice - 1 == trainer.selected_mon:
                    print(f"{selected_mon.name} is already selected!")
                    return None
                print(f"You selected {selected_mon.name}!")
                trainer.selected_mon = choice - 1
                return selected_mon
            except (ValueError, IndexError):
                print("Invalid choice, please select again")
    
    except KeyboardInterrupt:
        print("\\nGame Over!")
        sys.exit(0) 

def display_moves(pokemon):
    try:
        cancel = len(pokemon.moveset) + 1
        for i, move in enumerate(pokemon.moveset):
            print(f"{i + 1}. {move.name}")
        print(f"{len(pokemon.moveset) + 1}. Cancel")
        while True:
            try:
                choice = int(input("Select a Move: "))
                if choice == cancel:
                    return None
                selected_move = pokemon.moveset[choice - 1]
                print(f"You selected {selected_move.name}!")
                return pokemon.moveset[choice - 1]
            except (ValueError, IndexError):
                print("Invalid choice, please select again")

    except KeyboardInterrupt:
        print("\\nGame Over!")
        sys.exit(0)

def print_hp(player, npc):
    print(f"Your {player.party[player.selected_mon].name}'s health: {player.party[player.selected_mon].hp}/{player.party[player.selected_mon].max_hp}")
    print(f"Your {npc.party[player.selected_mon].name}'s health: {npc.party[player.selected_mon].hp}/{npc.party[player.selected_mon].max_hp}")

def print_stats(player, npc):
        for key, value in vars(player.party[player.selected_mon]).items():
            print(f"{key}: {value}")
        for key, value in vars(npc.party[npc.selected_mon]).items():
            print(f"{key}: {value}")
            