# ui/app.py
from textual.app    import App
from models.trainer import Trainer
from ui.theme       import TUIMON_DARK, CATPPUCCIN_MOCHA

class TuimonApp(App):

    THEMES = {
        "tuimon-dark":  TUIMON_DARK,
        "catppuccin-mocha": CATPPUCCIN_MOCHA
    }

    SCREENS = {
        "battle": "ui.screens.battle_screen.BattleScreen",
        "end":    "ui.screens.end_screen.EndScreen",
    }

    def __init__(self, player: Trainer, npc: Trainer) -> None:
        super().__init__()
        self.player = player
        self.npc    = npc

    def on_mount(self) -> None:
        self.register_theme(TUIMON_DARK)
        self.register_theme(CATPPUCCIN_MOCHA)
        self.theme = "tuimon-dark"
        from ui.screens.title_screen import TitleScreen
        self.push_screen(TitleScreen())