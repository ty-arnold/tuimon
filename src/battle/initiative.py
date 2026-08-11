import random
from typing import Optional
from models.move import Move
from models.pokemon import Pokemon
from models.trainer import Trainer
from models.turn_order import TurnOrder
from models.turn_order import BattleAction
from models.turn_result import Message, HPChange, TurnEvent
from battle.messages import msg
from battle.status_effects import get_all_effects

def get_turn_order(
    player:         Trainer,
    player_choice:  BattleAction,
    npc:            Trainer,
    npc_choice:     BattleAction,
    player_can_act: bool,
    npc_can_act:    bool,
    weather:        str | None = None,
) -> TurnOrder:

    player_goes_first = _determine_first(player, player_choice, npc, npc_choice, weather)

    if player_goes_first:
        return TurnOrder(
            first          = player,
            first_choice   = player_choice,
            second         = npc,
            second_choice  = npc_choice,
            first_can_act  = player_can_act,
            second_can_act = npc_can_act
        )
    else:
        return TurnOrder(
            first          = npc,
            first_choice   = npc_choice,
            second         = player,
            second_choice  = player_choice,
            first_can_act  = npc_can_act,
            second_can_act = player_can_act
        )

def _determine_first(player: Trainer, player_choice: BattleAction, npc: Trainer, npc_choice: BattleAction,
                     weather: str | None = None) -> bool:
    # priority takes precedence over speed
    if player_choice.priority != npc_choice.priority:
        return player_choice.priority > npc_choice.priority

    # equal priority - check speed
    player_spd = player.active().get_stat("stat_spd")
    npc_spd    = npc.active().get_stat("stat_spd")

    from battle.abilities import modify_speed_by_weather
    player_spd = modify_speed_by_weather(player.active(), player_spd, weather)
    npc_spd    = modify_speed_by_weather(npc.active(), npc_spd, weather)

    if player_spd != npc_spd:
        return player_spd > npc_spd

    # speed tie - randomize
    return random.random() > 0.5

def check_can_act(pokemon: Pokemon, events: list[TurnEvent] | None = None) -> tuple[bool, Optional[str]]:
    from battle.abilities import _name
    if _name(pokemon) == "Truant":
        if pokemon.truant_skip:
            pokemon.truant_skip = False
            if events is not None:
                events.append(Message(text=f"{pokemon.name} is loafing around!"))
            return False, "Truant"
        pokemon.truant_skip = True

    all_effects = get_all_effects(pokemon)
    for effect in all_effects:
        if effect.name == "Confusion":
            if random.random() < 0.5:  # 50% chance to hurt itself
                damage = round(pokemon.max_hp * 0.1)
                hp_before = pokemon.hp
                pokemon.hp = max(0, pokemon.hp - damage)
                if events is not None:
                    events.append(msg("confusion_self_hit", pokemon=pokemon.name))
                    events.append(HPChange(
                        trainer="", pokemon_name=pokemon.name,
                        old_hp=hp_before, new_hp=pokemon.hp, max_hp=pokemon.max_hp,
                    ))
                    events.append(msg("took_damage", pokemon=pokemon.name, damage=damage))
                return False, "Confusion"  # skip attack this turn
            else:
                if events is not None:
                    events.append(msg("is_confused", pokemon=pokemon.name))
        elif not effect.can_act():
            return False, effect.name
    return True, None