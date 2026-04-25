from textual.message import Message
from models import Move, Pokemon

class MoveChosen(Message):
    """Posted when the player selects a move from the move screen."""
    def __init__(self, move: Move) -> None:
        super().__init__()
        self.move = move

class PokemonChosen(Message):
    """Posted when the player selects a pokemon to switch to."""
    def __init__(self, pokemon: Pokemon) -> None:
        super().__init__()
        self.pokemon = pokemon

class ActionChosen(Message):
    """Posted when the player selects a top level action (fight, bag, run)."""
    def __init__(self, action: str) -> None:
        super().__init__()
        self.action = action

class BattleOver(Message):
    """Posted when the battle ends."""
    def __init__(self, winner: str) -> None:
        super().__init__()
        self.winner = winner