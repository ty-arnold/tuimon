import copy
from models import Pokemon, Move
from core import game_print, msg

def apply_modifier(move: Move, pokemon: Pokemon, current_turn: int) -> None:
    if move.modifier is None:
            return
    modifier              = copy.deepcopy(move.modifier)
    modifier.expires_turn = current_turn + modifier.turns if modifier.turns > 0 else -1
    pokemon.add_modifier(modifier)
    game_print(msg("modifier", pokemon=pokemon.name, modifier=modifier))

def get_modifier_value(
    attr:         str,
    move:         Move,
    pokemon:      Pokemon,
    current_turn: int
) -> float:
    total = 1.0
    expired = []

    for modifier in pokemon.get_active_modifiers(current_turn):
        if not modifier.applies_to(move):
            continue
        value = getattr(modifier, attr, 1.0)
        total *= value

        # consume single turn modifiers after use
        if modifier.expires_turn != -1 and current_turn >= modifier.expires_turn:
            expired.append(modifier)
            if modifier.consume_message:
                game_print(msg(message=modifier.consume_message))
    for modifier in expired:
        pokemon.remove_modifier(modifier)

    return total

def clear_expired_modifiers(pokemon: Pokemon, current_turn: int) -> None:
    pokemon.clear_expired_modifiers(current_turn)