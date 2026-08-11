# tests/helpers.py
import sys
import os
from typing import Optional
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from models.pokemon import Pokemon
from models.move import Move, MultiTurn
from models.trainer import Trainer
from models.status_effect import StatusEffect
from models.modifier import Modifier, MoveEffect
from data.status_effects import poison, paralysis, sleep, burn, freeze
import copy

def make_pokemon(name="Testmon", lvl=50, type=["Normal"],
                 stat_hp=100, stat_attk=100, stat_def=100,
                 stat_sp_attk=100, stat_sp_def=100, stat_spd=100):
    return Pokemon(
        name         = name,
        lvl          = lvl,
        type         = type,
        moveset      = [],
        stat_hp      = stat_hp,
        stat_attk    = stat_attk,
        stat_def     = stat_def,
        stat_sp_attk = stat_sp_attk,
        stat_sp_def  = stat_sp_def,
        stat_spd     = stat_spd
    )

def make_move(
    name:               str                     = "Test Move",
    type:               list[str]               = ["Normal"],
    category:           str                     = "physical",
    power:              int                     = 50,
    acc:                Optional[float]         = 1.0,
    pp:                 int                     = 20,
    stat_change:        Optional[dict]          = None,
    recoil:             float                   = 0.0,
    lifesteal:          float                   = 0.0,
    heal:               float                   = 0.0,
    min_hits:           Optional[int]           = None,
    max_hits:           Optional[int]           = None,
    status_effect:      Optional[StatusEffect]  = None,
    multi_turn:         Optional[MultiTurn]     = None,
    hits_invulnerable:  Optional[list[str]]     = None,
    modifier:           Optional[Modifier]      = None,
    stat_change_chance: float                   = 1.0,
    priority:           int                     = 0,  # add this
    immune_types:       Optional[list[str]]     = None,
    immune_moves:       Optional[list[str]]     = None,
    move_effect:        Optional[MoveEffect]    = None,
) -> Move:
    return Move(
        name               = name,
        type               = type,
        category           = category,
        power              = power,
        acc                = acc,
        pp                 = pp,
        stat_change        = stat_change or {},
        recoil             = recoil,
        lifesteal          = lifesteal,
        heal               = heal,
        min_hits           = min_hits,
        max_hits           = max_hits,
        status_effect      = status_effect,
        multi_turn         = multi_turn,
        hits_invulnerable  = hits_invulnerable or [],
        modifier           = modifier,
        stat_change_chance = stat_change_chance,
        priority           = priority,  # add this
        immune_types       = immune_types or [],
        immune_moves       = immune_moves or [],
        move_effect        = move_effect,
    )


def make_modifier(
    name:               str            = "Test Modifier",
    turns:              int            = 1,
    target:             str            = "self",
    power_modifier:     float          = 1.0,
    accuracy_modifier:  float          = 1.0,
    damage_modifier:    float          = 1.0,
    type_condition:     Optional[str]  = None,
    category_condition: Optional[str]  = None,
    consume_message:    str            = "",
    clears_on_switch:   bool           = True,
) -> Modifier:
    return Modifier(
        name               = name,
        turns              = turns,
        target             = target,
        power_modifier     = power_modifier,
        accuracy_modifier  = accuracy_modifier,
        damage_modifier    = damage_modifier,
        type_condition     = type_condition,
        category_condition = category_condition,
        consume_message    = consume_message,
        clears_on_switch   = clears_on_switch,
    )


def make_move_effect(
    effect_type:  str                 = "protect",
    target:       str                 = "self",
    turns:        int                 = 1,
    properties:   Optional[dict]      = None,
    bypass_moves: Optional[list[str]] = None,
    message:      str                 = "protected itself!",
    fail_message: str                 = "but it failed!",
) -> MoveEffect:
    return MoveEffect(
        effect_type  = effect_type,
        target       = target,
        turns        = turns,
        properties   = properties   or {},
        bypass_moves = bypass_moves or [],
        message      = message,
        fail_message = fail_message,
    )


def make_trainer(name="Trainer", pokemon=None):
    if pokemon is None:
        pokemon = [make_pokemon()]
    return Trainer(
        name         = name,
        party        = pokemon
    )