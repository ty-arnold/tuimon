from dataclasses import dataclass
from models.trainer import Trainer
from models.move    import Move

@dataclass
class TurnOrder:
    first:          Trainer
    first_choice:   Move
    second:         Trainer
    second_choice:  Move
    first_can_act:  bool
    second_can_act: bool