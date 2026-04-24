from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.move import Move

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