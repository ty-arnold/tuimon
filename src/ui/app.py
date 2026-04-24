from textual.app     import App, ComposeResult
from textual.widgets import Header, Footer, Label, Static
from textual.containers import Horizontal, Vertical

class TuimonApp(App):
    """Main Textual application for Tuimon."""

    CSS_PATH = "styles/battle.tcss"

    BINDINGS = [
        ("f", "fight",  "Fight"),
        ("r", "run",    "Run"),
        ("b", "bag",    "Bag"),
        ("q", "quit",   "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                Static("Left Panel", id="left-panel"),
                Static("Log",        id="battle-log"),
                id="left",
            ),
            Vertical(
                Static("Pokemon 1",  id="pokemon-top"),
                Static("HP Bar",     id="hp-top"),
                Static("Action Log", id="action-log"),
                Static("Pokemon 2",  id="pokemon-bottom"),
                Static("HP Bar",     id="hp-bottom"),
                Static("Input",      id="input-bar"),
                id="right",
            ),
            id="main",
        )
        yield Static(
            "fight (f)  run (r)  bag (b)  quit (q)",
            id="command-bar"
        )

    def action_fight(self) -> None:
        self.notify("Fight!")

    def action_run(self) -> None:
        self.notify("Run!")

    def action_bag(self) -> None:
        self.notify("Bag!")


if __name__ == "__main__":
    app = TuimonApp()
    app.run()