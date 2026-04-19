from __future__ import annotations
import random
from typing import Optional, NamedTuple
from src.mult_tables import *
from dataclasses import dataclass, field

### Global values ###
iv = 15
ev = 85

@dataclass
class MultiTurn:
    turns:                int
    charge_turn:          int
    charge_message:       str
    invulnerable:         bool                  = False
    invulnerable_state:   Optional[str]         = None
    invulnerable_message: Optional[str]         = None
    accumulator:          Optional[Accumulator] = None

@dataclass
class MoveEffect:
    effect_type:      str            # "protect", "screen", "field", etc
    target:           str            = "self"
    turns:            int            = 1
    properties:       dict           = field(default_factory=dict)
    bypass_moves:     list[str]      = field(default_factory=list)  # moves that ignore this
    message:          Optional[str]  = None
    fail_message:     Optional[str]  = None

@dataclass
class Accumulator:
    type:            str
    release_formula: str
    ignore_type:     bool       = False
    release_message: str        = ""

@dataclass
class Modifier:
    name:               str
    turns:              int            = 1        # -1 = permanent
    target:             str            = "self"
    power_modifier:     float          = 1.0
    accuracy_modifier:  float          = 1.0
    damage_modifier:    float          = 1.0
    type_condition:     Optional[str]  = None
    category_condition: Optional[str]  = None
    consume_message:    str            = ""
    clears_on_switch:   bool           = True
    expires_turn:       int            = -1       # set dynamically, not in constructor

    def is_active(self, current_turn: int) -> bool:
        return self.expires_turn == -1 or current_turn <= self.expires_turn

    def applies_to(self, move: Move) -> bool:
        if self.type_condition is not None and move.type[0] != self.type_condition:
            return False
        if self.category_condition is not None and move.category != self.category_condition:
            return False
        return True

    def is_expired(self, current_turn: int) -> bool:
        return self.expires_turn != -1 and current_turn > self.expires_turn

@dataclass
class TurnOrder:
    first:          Trainer
    first_choice:   Move
    second:         Trainer
    second_choice:  Move
    first_can_act:  bool
    second_can_act: bool

class Pokemon:
    def __init__(
        self,
        name:         str,
        lvl:          int,
        type:         list[str],
        moveset:      list[Move],
        stat_hp:      int,
        stat_attk:    int,
        stat_def:     int,
        stat_sp_attk: int,
        stat_sp_def:  int,
        stat_spd:     int,
    ):
        self.name:         str               = name
        self.lvl:          int               = lvl
        self.type:         list[str]         = type
        self.moveset:      list[Move]        = moveset

        self.hp:           int               = self._calc_hp(stat_hp,        iv, ev, lvl)
        self.max_hp:       int               = self.hp
        self.stat_attk:    int               = self._calc_stat(stat_attk,    iv, ev, lvl)
        self.stat_def:     int               = self._calc_stat(stat_def,     iv, ev, lvl)
        self.stat_sp_attk: int               = self._calc_stat(stat_sp_attk, iv, ev, lvl)
        self.stat_sp_def:  int               = self._calc_stat(stat_sp_def,  iv, ev, lvl)
        self.stat_spd:     int               = self._calc_stat(stat_spd,     iv, ev, lvl)
        self.stat_acc:     float             = 1.0
        self.stat_eva:     float             = 1.0

        self.stage_attk:    int              = 0
        self.stage_def:     int              = 0
        self.stage_sp_attk: int              = 0
        self.stage_sp_def:  int              = 0
        self.stage_spd:     int              = 0
        self.stage_acc:     int              = 0
        self.stage_eva:     int              = 0

        self.major_status: Optional[StatusEffect]  = None    # only one allowed
        self.minor_status: list[StatusEffect]      = []      # multiple allowed
        self.modifiers:    list[Modifier]          = []
        self.accumulator:  int                     = 0

    def _calc_hp(self, base: int, iv: int, ev: int, lvl: int) -> int:
        return round((((base + iv) * 2 + ev) * lvl / 100) + lvl + 10)

    def _calc_stat(self, base: int, iv: int, ev: int, lvl: int) -> int:
        return round((((base + iv) * 2 + ev) * lvl / 100) + 5)

    def active(self) -> Pokemon:
        return self

    def is_alive(self) -> bool:
        return self.hp > 0
    
    def get_stat(self, stat: str) -> int:
        stage_map = {
            "stat_attk":    (self.stat_attk,    self.stage_attk),
            "stat_def":     (self.stat_def,     self.stage_def),
            "stat_sp_attk": (self.stat_sp_attk, self.stage_sp_attk),
            "stat_sp_def":  (self.stat_sp_def,  self.stage_sp_def),
            "stat_spd":     (self.stat_spd,     self.stage_spd),
            "stat_acc":     (self.stat_acc,     self.stage_acc),
            "stat_eva":     (self.stat_eva,     self.stage_eva),
        }
        base, stage = stage_map[stat]
        if stat in ("stat_acc", "stat_eva"):
            calculated =  base * acc_table[stage]
        else:
            calculated = round(base * stat_table[stage])

        if self.major_status is not None and stat in self.major_status.stat_modifier:
            calculated = round(calculated * self.major_status.stat_modifier[stat])

        for effect in self.minor_status:
            if stat in effect.stat_modifier:
                calculated = round(calculated * effect.stat_modifier[stat])
        return calculated

    def apply_stage_change(self, stat: str, change: int) -> int:
        stage_attr = {
            "stat_attk":    "stage_attk",
            "stat_def":     "stage_def",
            "stat_sp_attk": "stage_sp_attk",
            "stat_sp_def":  "stage_sp_def",
            "stat_spd":     "stage_spd",
            "stat_acc":     "stage_acc",
            "stat_eva":     "stage_eva"
        }
        attr = stage_attr[stat]
        current_stage = getattr(self, attr)
        new_stage = max(-6, min(6, current_stage + change))
        setattr(self, attr, new_stage)
        return new_stage - current_stage
    
    def apply_status_effect(self, effect: StatusEffect) -> bool:
        import random
        if effect.is_major:
            # only one major status allowed at a time
            if self.major_status is not None:
                return False  # already has a major status
            for stat, multiplier in effect.stat_modifier.items():
                original                     = getattr(self, stat)
                effect.applied_changes[stat] = original
                setattr(self, stat, int(original * multiplier))
            if effect.use_turn_counter:
                effect.turn_counter = random.randint(1, 3)
            self.major_status = effect
        else:
            # check if this specific minor status is already applied
            if any(e.name == effect.name for e in self.minor_status):
                return False
            self.minor_status.append(effect)
        return True  # successfully applied

    def remove_status_effect(self, effect: StatusEffect) -> None:
        for stat, original_value in effect.applied_changes.items():
            setattr(self, stat, original_value)
        if effect.is_major:
            self.major_status = None
        else:
            self.minor_status.remove(effect)
    
    def add_modifier(self, modifier: Modifier) -> None:
        self.modifiers.append(modifier)

    def remove_modifier(self, modifier: Modifier) -> None:
        self.modifiers.remove(modifier)

    def get_active_modifiers(self, current_turn: int) -> list[Modifier]:
        return [m for m in self.modifiers if m.is_active(current_turn)]

    def clear_expired_modifiers(self, current_turn: int) -> None:
        self.modifiers = [m for m in self.modifiers if not m.is_expired(current_turn)]

    def clear_all_modifiers(self, force: bool = False) -> None:
        if force:
            self.modifiers = []  # clear everything regardless
        else:
            # only clear modifiers that should clear on switch
            self.modifiers = [m for m in self.modifiers if not m.clears_on_switch]

    def print_moves(self) -> None:
        from game_print import game_print
        for i, move in enumerate(self.moveset):
            game_print(f"{i + 1}. {move.name}")
        game_print(f"{len(self.moveset) + 1}. Cancel")

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
        move_effect:        Optional[MoveEffect]   = None
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
        self.move_effect:        Optional[MoveEffect]     = move_effect
    
    def __repr__(self) -> str:
        return self.name
    
class StatusEffect:
    def __init__(
        self,
        name:             str,
        chance_to_apply:  float,
        chance_to_end:    Optional[float]        = None,
        duration:         Optional[int]          = None,
        stat_changes:     Optional[dict]         = None,
        chance_to_act:    float                  = 1.0,
        stat_modifier:    Optional[dict]         = None,
        damage:           Optional[float]        = None,
        use_turn_counter: bool                   = False,
        is_major:         bool                   = False,
    ):
        self.name:             str                = name
        self.chance_to_apply:  float              = chance_to_apply
        self.chance_to_end:    Optional[float]    = chance_to_end
        self.duration:         Optional[int]      = duration
        self.stat_changes:     dict               = stat_changes or {}
        self.applied_changes:  dict               = {}
        self.chance_to_act:    float              = chance_to_act
        self.stat_modifier:    dict               = stat_modifier or {}
        self.damage:           Optional[float]    = damage
        self.use_turn_counter: bool               = use_turn_counter
        self.turn_counter:     Optional[int]      = None
        self.turns_active:     int                = 0
        self.is_major:         bool               = is_major

    def can_act(self) -> bool:
        if self.chance_to_act < 1.0:
            if random.random() > self.chance_to_act:
                return False
        return True
        
    def check_should_end(self) -> bool:
        self.turns_active += 1

        if self.turns_active < 2:
            return False

        if self.use_turn_counter and self.turn_counter is not None:
            self.turn_counter -= 1
            return self.turn_counter == 0  # returns True when counter hits 0

        if self.duration is not None:
            self.duration -= 1
            return self.duration == 0

        if self.chance_to_end is not None:
            return random.random() < self.chance_to_end

        return False
    
class Trainer:
    def __init__(
        self,
        name:         str,
        party:        list[Pokemon]
    ):
        self.name:                str                  = name
        self.party:               list[Pokemon]        = party
        self.selected_mon:        int                  = 0
        self.locked_move:         Optional[Move]       = None
        self.locked_turns:        int                  = 0
        self.invulnerable_state:  Optional[str]        = None
        self.active_effects:      list[MoveEffect]     = []  # tracks active field effects
        self.consecutive_protect: int                  = 0   # tracks consecutive protect uses

    def print_party(self) -> None:
        from game_print import game_print
        game_print(f"{self.name}'s Party:")
        for i, pokemon in enumerate(self.party):
            game_print(f"{i + 1}. {pokemon.name}")
        game_print(f"{len(self.party) + 1}. Cancel")

    def print_hp(self) -> None:
        from game_print import game_print
        game_print(f"{self.name}'s {self.active().name}: {self.active().hp}/{self.active().max_hp}") 
    
    def active(self) -> Pokemon:
        return self.party[self.selected_mon]