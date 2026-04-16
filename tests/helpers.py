# tests/helpers.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from src.models import Pokemon, Move, Trainer
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
        stat_spd     = stat_spd,
    )

def make_move(name="Test Move", type=["Normal"], category="physical",
              power=50, acc=1.0, pp=20, stat_change=None,
              recoil=0.0, lifesteal=0.0, heal=0.0,
              status_effect=None, multi_turn=None,
              hits_invulnerable=None, damage_modifier=None):
    return Move(
        name              = name,
        type              = type,
        category          = category,
        power             = power,
        acc               = acc,
        pp                = pp,
        stat_change       = stat_change or {},
        recoil            = recoil,
        lifesteal         = lifesteal,
        heal              = heal,
        status_effect     = status_effect,
        multi_turn        = multi_turn,
        hits_invulnerable = hits_invulnerable or [],
        # damage_modifier   = damage_modifier or {},
    )

def make_trainer(name="Trainer", pokemon=None):
    if pokemon is None:
        pokemon = [make_pokemon()]
    return Trainer(
        name         = name,
        party        = pokemon
    )