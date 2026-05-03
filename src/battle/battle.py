import random
from core import msg
from models import Move, Trainer, BattleAction, TurnOrder
from models.turn_result import Message, Switch, TurnEvent
from battle.initiative   import check_can_act, get_turn_order
from battle.move_handler   import apply_move, clear_move_lock
from battle.status_effects import process_status_effects
from battle.move_effects   import clear_switch_effects
from core.logger import logger


def _resolve_switches(order: TurnOrder, events: list[TurnEvent] | None = None):
    if order.first_choice.kind == "switch" and order.first_choice.switch_slot is not None:
        execute_switch(order.first, order.first_choice.switch_slot, events=events)
    
    if order.second_choice.kind == "switch" and order.second_choice.switch_slot is not None:
        execute_switch(order.second, order.second_choice.switch_slot, events=events)


def _resolve_moves(
    order: TurnOrder, current_turn: int,
    events: list[TurnEvent] | None = None
) -> bool | None:
    if order.first_can_act and order.first_choice.kind == "move":
        apply_move(order.first_choice.move, order.first, order.second, current_turn, events=events)
        clear_move_lock(order.first, events=events)
        if check_winner(order.first, order.second, events=events):
            return True

    # skip second's move if their active pokemon fainted
    if not order.second.active().is_alive():
        if order.first.active().is_alive():
            process_status_effects(order.first.active(), events=events, trainer_name=order.first.name)
        return None

    if order.second_can_act and order.second_choice.kind == "move":
        apply_move(order.second_choice.move, order.second, order.first, current_turn, events=events)
        clear_move_lock(order.second, events=events)
        if check_winner(order.first, order.second, events=events):
            return True
    return None


def resolve_turn(
    player: Trainer,
    player_choice: BattleAction,
    npc: Trainer,
    npc_choice: BattleAction,
    current_turn: int,
    events: list[TurnEvent] | None = None
) -> bool | None:
    if events is None:
        events = []

    player_can_act, _ = check_can_act(player.active(), events=events)
    npc_can_act, _    = check_can_act(npc.active(), events=events)

    order = get_turn_order(player, player_choice, npc, npc_choice, player_can_act, npc_can_act)

    if player_choice.kind == "switch" or npc_choice.kind == "switch":
        _resolve_switches(order, events=events)

        if check_winner(player, npc, events=events):
            return True

    if player_choice.kind == "move" or npc_choice.kind == "move":
        winner = _resolve_moves(order, current_turn, events=events)
        if winner:
            return True

    if order.first.active().is_alive():
        process_status_effects(order.first.active(), events=events, trainer_name=order.first.name)
    if order.second.active().is_alive():
        process_status_effects(order.second.active(), events=events, trainer_name=order.second.name)

    return True if check_winner(player, npc, events=events) else None


def get_npc_move(trainer: Trainer) -> Move:
    if trainer.locked_move is not None:
        return trainer.locked_move

    available = [m for m in trainer.active().moveset if m.pp > 0]
    logger.debug(f"get_npc_move: moveset pp values={[(m.name, m.pp) for m in trainer.active().moveset]}")
    logger.debug(f"get_npc_move: available={available}")

    if not available:
        logger.debug("get_npc_move: no moves available - all pp = 0!")
        return None

    return random.choice(available)


def execute_switch(trainer: Trainer, selected_mon: int, events: list[TurnEvent] | None = None) -> None:
    old_mon = trainer.active()
    trainer.active().clear_all_modifiers()
    clear_switch_effects(trainer)
    trainer.selected_mon = selected_mon
    if events is not None:
        events.append(Switch(
            trainer=trainer.name, old_name=old_mon.name,
            new_name=trainer.active().name,
        ))


def check_winner(player: Trainer, npc: Trainer, events: list[TurnEvent] | None = None) -> Trainer | None:
    if not any(pokemon.is_alive() for pokemon in player.party):
        if events is not None:
            events.append(msg("wins", trainer=npc.name))
        return npc
    if not any(pokemon.is_alive() for pokemon in npc.party):
        if events is not None:
            events.append(msg("wins", trainer=player.name))
        return player
    return None
