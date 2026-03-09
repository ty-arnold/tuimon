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
            