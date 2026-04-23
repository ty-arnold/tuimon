from core.game_print import game_print
from models import Move, Trainer
from battle.turn_order     import check_can_act, get_turn_order
from battle.move_handler   import apply_move, clear_move_lock
from battle.status_effects import process_status_effects
from ui.input import get_party

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
