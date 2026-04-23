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

    def print_party(self) -> None:
        from core.game_print import game_print
        game_print(f"{self.name}'s Party:")
        for i, pokemon in enumerate(self.party):
            game_print(f"{i + 1}. {pokemon.name}")
        game_print(f"{len(self.party) + 1}. Cancel")

    def print_hp(self) -> None:
        from core.game_print import game_print
        game_print(f"{self.name}'s {self.active().name}: {self.active().hp}/{self.active().max_hp}") 
    
    def active(self) -> Pokemon:
        return self.party[self.selected_mon]