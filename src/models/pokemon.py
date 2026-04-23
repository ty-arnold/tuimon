from typing import Optional
from models.move          import Move
from models.status_effect import StatusEffect
from models.modifier      import Modifier
from data import acc_table, stat_table
from core.config import DEFAULT_IV, DEFAULT_EV

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
        ev:           int = DEFAULT_EV,
        iv:           int = DEFAULT_IV
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

    def active(self):
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
        from core.game_print import game_print
        for i, move in enumerate(self.moveset):
            game_print(f"{i + 1}. {move.name}")
        game_print(f"{len(self.moveset) + 1}. Cancel")