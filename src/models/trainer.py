from typing import Optional
from models.move    import Move, MoveEffect
from models.pokemon import Pokemon

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

    def active(self) -> Pokemon:
        return self.party[self.selected_mon]