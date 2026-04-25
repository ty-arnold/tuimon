import random
from core.game_print import game_print
from core import msg
from models import Move, Trainer
from battle.turn_order     import check_can_act, get_turn_order
from battle.move_handler   import apply_move, clear_move_lock
from battle.status_effects import process_status_effects
from ui.input import get_party
from core.logger import logger

def resolve_turn(player: Trainer, player_choice: Move, npc: Trainer, npc_choice: Move, current_turn: int) -> bool | None:
    from core.config import TUI_MODE
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
        if not TUI_MODE:
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
        if not TUI_MODE:
            next_mon(player, npc)

    process_status_effects(order.first.active())
    process_status_effects(order.second.active())
    winner = check_winner(player, npc)
    if winner:
        return True
    return None

def get_npc_move(trainer: Trainer) -> Move:
    if trainer.locked_move is not None:
        move = trainer.locked_move
        trainer.locked_turns -= 1
        return move

    available = [m for m in trainer.active().moveset if m.pp > 0]
    logger.debug(f"get_npc_move: moveset pp values={[(m.name, m.pp) for m in trainer.active().moveset]}")
    logger.debug(f"get_npc_move: available={available}")

    if not available:
        logger.debug("get_npc_move: no moves available - all pp = 0!")
        return None

    return random.choice(available)

def next_mon(player: Trainer, npc: Trainer) -> None:
    if not player.active().is_alive():
        game_print(msg("fainted", pokemon=player.active().name))
        player.active().clear_all_modifiers()  # default clears switchable ones
        new_mon = get_party(player)
        if new_mon is not None:
            player.selected_mon = player.party.index(new_mon)

    if not npc.active().is_alive():
        game_print(msg("fainted", pokemon=npc.active().name))
        npc.active().clear_all_modifiers()
        new_mon = get_party(npc)
        if new_mon is not None:
            npc.selected_mon = npc.party.index(new_mon)
                
def check_winner(player: Trainer, npc: Trainer) -> Trainer | None:
    if not any(pokemon.is_alive() for pokemon in player.party):
        game_print(msg("wins", trainer=npc.name))
        return npc      # return trainer object instead of True
    if not any(pokemon.is_alive() for pokemon in npc.party):
        game_print(msg("wins", trainer=player.name))
        return player   # return trainer object instead of True
    return None
