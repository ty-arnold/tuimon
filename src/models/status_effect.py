from typing import Optional
import random

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