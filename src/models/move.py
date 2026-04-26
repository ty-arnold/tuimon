from dataclasses import dataclass
from typing import Optional
from models.modifier      import Modifier, MoveEffect
from models.status_effect import StatusEffect

@dataclass
class Accumulator:
    type:            str
    release_formula: str
    ignore_type:     bool       = False
    release_message: str        = ""

@dataclass
class MultiTurn:
    turns:                int
    charge_turn:          int
    charge_message:       str
    invulnerable:         bool                  = False
    invulnerable_state:   Optional[str]         = None
    invulnerable_message: Optional[str]         = None
    accumulator:          Optional[Accumulator] = None
    
class Move:
    def __init__(
        self,
        name:               str,
        type:               list[str],
        category:           str,
        power:              int,
        acc:                Optional[float]        = None,
        pp:                 int                    = 20,
        stat_change:        Optional[dict]         = None,
        recoil:             float                  = 0.0,
        lifesteal:          float                  = 0.0,
        heal:               float                  = 0.0,
        min_hits:           Optional[int]          = None,
        max_hits:           Optional[int]          = None,
        crit_rate:          int                    = 0,
        flinch_chance:      float                  = 0.0,
        priority:           int                    = 0,
        multi_turn:         Optional[MultiTurn]    = None,
        hits_invulnerable:  Optional[list[str]]    = None,
        modifier:           Optional[Modifier]     = None,
        status_effect:      Optional[StatusEffect] = None,
        stat_change_chance: float                  = 1.0,
        immune_types:       list[str]              = [],
        immune_moves:       list[str]              = [],
        move_effect:        Optional[MoveEffect]   = None,
        description:        str                    = ""
    ):
        self.name:               str                      = name
        self.type:               list[str]                = type # Grass, Water, Etc. 
        self.category:           str                      = category # Either physical, special, or status
        self.power:              int                      = power # Base damage number for move
        self.acc:                Optional[float]          = acc # Accuracy, 1.0 being the default
        self.pp:                 int                      = pp # Power points, amount of move uses left
        self.stat_change:        dict                     = stat_change or {} # Changes to the stat stage. Can be self or opponent, -6 to +6. Ex. "opponent": {"stat_attk": -1}
        self.stat_change_chance: float                    = stat_change_chance # Default 1.0, chance for stat change to apply
        self.recoil:             float                    = recoil # Self damage if move hits
        self.lifesteal:          float                    = lifesteal
        self.heal:               float                    = heal
        self.min_hits:           Optional[int]            = min_hits 
        self.max_hits:           Optional[int]            = max_hits
        self.crit_rate:          int                      = crit_rate # Mapped to a table - 0 is default, goes to 4
        self.flinch_chance:      float                    = flinch_chance # Makes target miss next turn
        self.priority:           int                      = priority # ranges from -8 to +8. Overrides speed calc
        self.multi_turn:         Optional[MultiTurn]      = multi_turn # if a move takes place over multi turns
        self.hits_invulnerable:  list[str]                = hits_invulnerable or [] # If this move can hit a target thats flying, underwater, or underground
        self.modifier:           Optional[Modifier]       = modifier # Modifiers to self, target, or both. Can affect acc, power, and damage
        self.status_effect:      Optional[StatusEffect]   = status_effect # can be a major (poison, burn) or minor (confusion, curse) status effect
        self.immune_types:       list[str]                = immune_types  # types this move cannot hit
        self.immune_moves:       list[str]                = immune_moves  # moves that block this move
        self.move_effect:        Optional[MoveEffect]     = move_effect # Moves like protect, screen, field, etc.
        self.description:        str                      = description 
    
    def __repr__(self) -> str:
        return self.name