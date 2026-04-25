import os
from textual.app        import ComposeResult
from textual.screen     import Screen
from textual.widgets    import Static, Footer, Label
from textual.containers import Vertical, Center
from textual.binding    import Binding

class EndScreen(Screen):
    """Displayed when the battle ends."""

    CSS_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "styles",
        "end_screen.tcss"
    )

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "restart", "Play Again"),
    ]

    def __init__(self, won: bool, turns: int) -> None:
        super().__init__()
        self.won   = won
        self.turns = turns

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="end-container"):
                if self.won:
                    yield Label("✓ You won!",     id="end-title-win")
                else:
                    yield Label("✗ You lost!",    id="end-title-lose")
                yield Label(f"Battle lasted {self.turns} turns", id="end-turns")
                yield Label("q  Quit    r  Play Again",          id="end-options")
        yield Footer()

    def action_quit(self) -> None:
        self.app.exit()

    def action_restart(self) -> None:
        self.app.pop_screen()