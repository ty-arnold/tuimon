from __future__ import annotations
import random
from typing import Optional, NamedTuple
from src.mult_tables import *

### Global values ###
iv = 15
ev = 85

class TurnOrder(NamedTuple):
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

    def _calc_hp(self, base: int, iv: int, ev: int, lvl: int) -> int:
        return round((((base + iv) * 2 + ev) * lvl / 100) + lvl + 10)

    def _calc_stat(self, base: int, iv: int, ev: int, lvl: int) -> int:
        return round((((base + iv) * 2 + ev) * lvl / 100) + 5)

    def active(self) -> Pokemon:
        return self

    def is_alive(self) -> bool:
        return self.hp > 0
    
    def get_stat(self, stat: str):
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

    def print_moves(self):
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
        multi_turn:         Optional[dict]         = None,
        hits_invulnerable:  Optional[list[str]]    = None,
        # damage_modifier:    Optional[dict]       = None,
        status_effect:      Optional[StatusEffect] = None,
        stat_change_chance: float                  = 1.0,
    ):
        self.name:               str                      = name
        self.type:               list[str]                = type
        self.category:           str                      = category
        self.power:              int                      = power
        self.acc:                Optional[float]          = acc
        self.pp:                 int                      = pp
        self.stat_change:        dict                     = stat_change or {}
        self.recoil:             float                    = recoil
        self.lifesteal:          float                    = lifesteal
        self.heal:               float                    = heal
        self.min_hits:           Optional[int]            = min_hits
        self.max_hits:           Optional[int]            = max_hits
        self.crit_rate:          int                      = crit_rate
        self.flinch_chance:      float                    = flinch_chance
        self.priority:           int                      = priority
        self.multi_turn:         Optional[dict]           = multi_turn
        self.hits_invulnerable:  list[str]                = hits_invulnerable or []
        # self.damage_modifier:    dict                   = damage_modifier or {}
        self.status_effect:      Optional[StatusEffect]   = status_effect
        self.stat_change_chance: float                    = stat_change_chance
    
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
        self.name:               str                  = name
        self.party:              list[Pokemon]        = party
        self.selected_mon:       int                  = 0
        self.locked_move:        Optional[Move]       = None
        self.locked_turns:       int                  = 0
        self.invulnerable_state: Optional[str]        = None

    def print_party(self):
        from game_print import game_print
        game_print(f"{self.name}'s Party:")
        for i, pokemon in enumerate(self.party):
            game_print(f"{i + 1}. {pokemon.name}")
        game_print(f"{len(self.party) + 1}. Cancel")

    def print_hp(self):
        from game_print import game_print
        game_print(f"{self.name}'s {self.active().name}: {self.active().hp}/{self.active().max_hp}") 
    
    def active(self) -> Pokemon:
        return self.party[self.selected_mon]