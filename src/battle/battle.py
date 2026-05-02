import random
from core.game_print import game_print
from core import msg
from models import Move, Trainer, BattleAction, TurnOrder
from battle.turn_order     import check_can_act, get_turn_order
from battle.move_handler   import apply_move, clear_move_lock
from battle.status_effects import process_status_effects
from battle.move_effects   import clear_switch_effects
from ui.input import get_party
from core.logger import logger

def _resolve_switches(order: TurnOrder):
    if order.first_choice.kind == "switch" and order.first_choice.switch_slot is not None:
        execute_switch(order.first, order.first_choice.switch_slot)
    
    if order.second_choice.kind == "switch" and order.second_choice.switch_slot is not None:
        execute_switch(order.second, order.second_choice.switch_slot) 

def _resolve_moves(order: TurnOrder, current_turn: int, TUI_MODE: bool) -> bool | None:
    second_mon_before = order.second.selected_mon

    if order.first_can_act and order.first_choice.kind == "move":
        apply_move(order.first_choice.move, order.first, order.second, current_turn)
        clear_move_lock(order.first)
        winner = check_winner(order.first, order.second)
        if winner:
            return True
        if not TUI_MODE:
            next_mon(order.first, order.second)

    # skip second's move if their active pokemon fainted
    if not order.second.active().is_alive():
        if order.first.active().is_alive():
            process_status_effects(order.first.active())
        return None

    if order.second_can_act and order.second_choice.kind == "move":
        apply_move(order.second_choice.move, order.second, order.first, current_turn)
        clear_move_lock(order.second)
        winner = check_winner(order.first, order.second)
        if winner:
            return True
        if not TUI_MODE:
            next_mon(order.first, order.second)
    
def resolve_turn(
        player: Trainer, 
        player_choice: BattleAction, 
        npc: Trainer, 
        npc_choice: BattleAction, 
        current_turn: int
    ) -> bool | None:
    from core.config import TUI_MODE
    player_can_act, player_cant_act_reason = check_can_act(player.active())
    npc_can_act,    npc_cant_act_reason    = check_can_act(npc.active())

    order = get_turn_order(player, player_choice, npc, npc_choice, player_can_act, npc_can_act)

    if player_choice.kind == "switch" or npc_choice.kind == "switch":
        _resolve_switches(order)

    if player_choice.kind == "move" or npc_choice.kind == "move":
        _resolve_moves(order, current_turn, TUI_MODE)

    if order.first.active().is_alive():
        process_status_effects(order.first.active())
    if order.second.active().is_alive():
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

def execute_switch(trainer: Trainer, selected_mon: int) -> None:
    old_mon = trainer.active()
    trainer.active().clear_all_modifiers()
    clear_switch_effects(trainer)
    trainer.selected_mon = selected_mon
    game_print(msg("switch", trainer=trainer.name, old_mon=old_mon.name, new_mon=trainer.active().name))

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
