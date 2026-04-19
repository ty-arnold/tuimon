# tests/helpers.py
import sys
import os
from typing import Optional
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from src.models import Pokemon, Move, Trainer, StatusEffect, MultiTurn, Modifier, MoveEffect
from src.status_effects import poison, paralysis, sleep, burn, freeze
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
    # modifier:           Optional[StatusEffect]  = None,
    stat_change_chance: float                   = 1.0,
    priority:           int                     = 0,  # add this
    # immune_types:       list[str]               = [],
    # immune_moves:       list[str]               = [],
    # move_effect:        Optional[MoveEffect]    = None
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
        # modifier           = modifier,
        stat_change_chance = stat_change_chance,
        priority           = priority,  # add this
    )

def make_trainer(name="Trainer", pokemon=None):
    if pokemon is None:
        pokemon = [make_pokemon()]
    return Trainer(
        name         = name,
        party        = pokemon
    )