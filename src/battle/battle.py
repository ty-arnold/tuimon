import random
from core import msg
from models import Move, Trainer, BattleAction, TurnOrder
from models.turn_result import Message, Switch, TurnEvent
from battle.initiative   import check_can_act, get_turn_order
from battle.move_handler   import apply_move, clear_move_lock
from battle.status_effects import process_status_effects
from battle.move_effects   import clear_switch_effects
from core.logger import logger


def _resolve_switches(order: TurnOrder, events: list[TurnEvent] | None = None) -> str | None:
    weather = None
    if order.first_choice.kind == "switch" and order.first_choice.switch_slot is not None:
        weather = execute_switch(order.first, order.first_choice.switch_slot, order.second, events=events)
    
    if order.second_choice.kind == "switch" and order.second_choice.switch_slot is not None:
        w = execute_switch(order.second, order.second_choice.switch_slot, order.first, events=events)
        if w:
            weather = w
    return weather


def _resolve_moves(
    order: TurnOrder, current_turn: int,
    events: list[TurnEvent] | None = None,
    weather: str | None = None,
) -> bool | None:
    if order.first_can_act and order.first_choice.kind == "move":
        apply_move(order.first_choice.move, order.first, order.second, current_turn, events=events, weather=weather)
        clear_move_lock(order.first, events=events)
        if check_winner(order.first, order.second, events=events):
            return True

    # skip second's move if their active pokemon fainted
    if not order.second.active().is_alive():
        if order.first.active().is_alive():
            process_status_effects(order.first.active(), events=events, trainer_name=order.first.name)
        return None

    if order.second_can_act and order.second_choice.kind == "move":
        apply_move(order.second_choice.move, order.second, order.first, current_turn, events=events, weather=weather)
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
    events: list[TurnEvent] | None = None,
    weather_container: list | None = None,
) -> bool | None:
    if events is None:
        events = []

    weather = None

    player_can_act, _ = check_can_act(player.active(), events=events)
    npc_can_act, _    = check_can_act(npc.active(), events=events)

    order = get_turn_order(player, player_choice, npc, npc_choice, player_can_act, npc_can_act, weather)

    if player_choice.kind == "switch" or npc_choice.kind == "switch":
        weather = _resolve_switches(order, events=events)

        if check_winner(player, npc, events=events):
            return True

    if player_choice.kind == "move" or npc_choice.kind == "move":
        winner = _resolve_moves(order, current_turn, events=events, weather=weather)
        if winner:
            return True

        # Check for weather-setting moves
        for action in (player_choice, npc_choice):
            if action.kind == "move" and action.move and action.move.weather:
                weather = action.move.weather
                if events is not None:
                    trainer_name = player.name if action is player_choice else npc.name
                    events.append(Message(
                        text=f"{trainer_name}'s {action.move.name} changed the weather to {weather}!"
                    ))

    from battle.abilities import is_weather_active, apply_weather_damage
    weather_active = is_weather_active(weather, player, npc)

    if order.first.active().is_alive():
        process_status_effects(order.first.active(), events=events, trainer_name=order.first.name)
        from battle.abilities import process_end_of_turn_ability
        process_end_of_turn_ability(order.first.active(), events, order.first.name)
        if weather_active:
            apply_weather_damage(order.first.active(), weather, events, order.first.name)
    if order.second.active().is_alive():
        process_status_effects(order.second.active(), events=events, trainer_name=order.second.name)
        from battle.abilities import process_end_of_turn_ability
        process_end_of_turn_ability(order.second.active(), events, order.second.name)
        if weather_active:
            apply_weather_damage(order.second.active(), weather, events, order.second.name)

    if weather_container is not None:
        weather_container.append(weather)

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


def execute_switch(trainer: Trainer, selected_mon: int, opponent: Trainer = None,
                   events: list[TurnEvent] | None = None) -> str | None:
    old_mon = trainer.active()

    from battle.abilities import apply_switch_out_abilities
    apply_switch_out_abilities(trainer, events)

    trainer.active().clear_all_modifiers()
    clear_switch_effects(trainer)
    trainer.selected_mon = selected_mon
    if events is not None:
        events.append(Switch(
            trainer=trainer.name, old_name=old_mon.name,
            new_name=trainer.active().name,
        ))

    from battle.abilities import apply_switch_abilities, check_weather_setter
    if opponent is not None:
        apply_switch_abilities(trainer, opponent, events)

    weather = check_weather_setter(trainer.active())
    if weather and events is not None:
        from battle.abilities import _name
        events.append(Message(
            text=f"{trainer.active().name}'s {_name(trainer.active())} summoned {weather}!"
        ))
    return weather


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
