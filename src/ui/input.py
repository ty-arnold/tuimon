from models import Move, Trainer, Pokemon
from core import game_print
from ui.print import print_actions

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