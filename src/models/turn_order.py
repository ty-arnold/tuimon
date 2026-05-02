from dataclasses import dataclass
from typing import Optional, Literal
from models.trainer import Trainer
from models.move    import Move

@dataclass
class BattleAction:
    kind:        Literal["move", "switch"]
    move:        Optional[Move] = None
    switch_slot: Optional[int]  = None

    @property
    def priority(self) -> int:
        if self.kind == "move" and self.move is not None:
            return self.move.priority
        return 1  # switch default
    
@dataclass
class TurnOrder:
    first:          Trainer
    first_choice:   BattleAction
    second:         Trainer
    second_choice:  BattleAction
    first_can_act:  bool
    second_can_act: bool