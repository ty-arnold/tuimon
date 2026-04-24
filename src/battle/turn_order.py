import random
from typing import Optional
from models import Move, Pokemon, Trainer, TurnOrder
from core import game_print, msg
from battle.status_effects import get_all_effects

def get_turn_order(
    player:        Trainer,
    player_choice: Move,
    npc:           Trainer,
    npc_choice:    Move,
    player_can_act: bool,
    npc_can_act:    bool
) -> TurnOrder:

    player_goes_first = _determine_first(player, player_choice, npc, npc_choice)

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

def _determine_first(player: Trainer, player_choice: Move, npc: Trainer, npc_choice: Move) -> bool:
    # priority takes precedence over speed
    if player_choice.priority != npc_choice.priority:
        return player_choice.priority > npc_choice.priority

    # equal priority - check speed
    player_spd = player.active().get_stat("stat_spd")
    npc_spd    = npc.active().get_stat("stat_spd")

    if player_spd != npc_spd:
        return player_spd > npc_spd

    # speed tie - randomize
    return random.random() > 0.5

def check_can_act(pokemon: Pokemon) -> tuple[bool, Optional[str]]:
    all_effects = get_all_effects(pokemon)
    for effect in all_effects:
        if effect.name == "Confusion":
            if random.random() < 0.5:  # 50% chance to hurt itself
                damage = round(pokemon.max_hp * 0.1)
                pokemon.hp = max(0, pokemon.hp - damage)
                game_print(msg("confusion_self_hit", pokemon=pokemon.name))
                game_print(msg("took_damage", pokemon=pokemon.name, damage=damage))
                return False, "Confusion"  # skip attack this turn
            else:
                game_print(msg("is_confused", pokemon=pokemon.name))
        elif not effect.can_act():
            return False, effect.name
    return True, None