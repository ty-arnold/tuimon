from core.game_print import game_print
from ui import print_actions
from models import Move, Trainer, Pokemon
from battle.turn_order     import check_can_act, get_turn_order
from battle.move_handler   import apply_move, clear_move_lock
from battle.status_effects import process_status_effects

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

def resolve_turn(player: Trainer, player_choice: Move, npc: Trainer, npc_choice: Move, current_turn: int) -> bool | None:
    player_can_act, player_cant_act_reason = check_can_act(player.active())
    npc_can_act,    npc_cant_act_reason    = check_can_act(npc.active())

    order = get_turn_order(player, player_choice, npc, npc_choice, player_can_act, npc_can_act)

    second_mon_before = order.second.selected_mon

    if order.first_can_act:
        apply_move(order.first_choice, order.first, order.second, current_turn)
        clear_move_lock(order.first)
        winner = check_winner(player, npc)
        if winner:
            return True
        next_mon(player, npc)

    # checks if the second pokemon fainted - if so, skip its move turn
    if order.second.selected_mon != second_mon_before:
        return None
        
    if order.second_can_act:
        apply_move(order.second_choice, order.second, order.first, current_turn)
        clear_move_lock(order.second)
        winner = check_winner(player, npc)
        if winner:
            return True
        next_mon(player, npc)

    process_status_effects(order.first.active())
    process_status_effects(order.second.active())
    winner = check_winner(player, npc)
    if winner:
        return True
    return None
    
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

def next_mon(player: Trainer, npc: Trainer) -> None:
    if not player.active().is_alive():
        game_print(f"{player.active().name} fainted!")
        player.active().clear_all_modifiers()  # default clears switchable ones
        new_mon = get_party(player)
        if new_mon is not None:
            player.selected_mon = player.party.index(new_mon)

    if not npc.active().is_alive():
        game_print(f"{npc.active().name} fainted!")
        npc.active().clear_all_modifiers()
        new_mon = get_party(npc)
        if new_mon is not None:
            npc.selected_mon = npc.party.index(new_mon)
                
def check_winner(player: Trainer, npc: Trainer) -> Trainer | None:
    if not any(pokemon.is_alive() for pokemon in player.party):
        game_print(f"{npc.name} Wins!")
        return npc      # return trainer object instead of True
    if not any(pokemon.is_alive() for pokemon in npc.party):
        game_print(f"{player.name} Wins!")
        return player   # return trainer object instead of True
    return None
