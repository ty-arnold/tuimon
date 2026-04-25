import os
import asyncio
from textual.screen     import Screen
from textual.app        import ComposeResult
from textual.widgets    import RichLog, Static, Footer, ListView, ListItem, Label, ProgressBar
from textual.containers import Horizontal, Vertical, Container
from models.trainer     import Trainer
from battle.controller  import BattleController
from core.game_print    import set_async_queue, game_print
from core.messages      import msg
from core.logger        import logger
from core.battle_state  import BattlePhase

from ui.mixins.battle_ui     import BattleUIMixin
from ui.mixins.menu_ui       import MenuUIMixin
from ui.mixins.display_ui    import DisplayUIMixin
from ui.mixins.phase_handler import PhaseHandlerMixin

class BattleScreen(BattleUIMixin, MenuUIMixin, DisplayUIMixin, PhaseHandlerMixin, Screen):

    CSS_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "styles",
        "battle.tcss"
    )

    BINDINGS = [
        ("f",      "fight",  "Fight"),
        ("p",      "party",  "Party"),
        ("b",      "bag",    "Bag"),
        ("r",      "run",    "Run"),
        ("escape", "cancel", "Cancel"),
        ("q",      "quit",   "Quit"),
    ]

    def __init__(self, player: Trainer, npc: Trainer) -> None:
        super().__init__()
        self.player         = player
        self.npc            = npc
        self._input_enabled = True

    def compose(self) -> ComposeResult:
        with Horizontal(id="main"):
            with Vertical(id="left-col"):
                with Container(id="action-pane"):
                    with ListView(id="menu-main"):
                        yield ListItem(Label("Moves"), id="action-moves")
                        yield ListItem(Label("Party"), id="action-party")
                        yield ListItem(Label("Items"), id="action-items")
                        yield ListItem(Label("Run"),   id="action-run")
                    yield ListView(id="menu-moves")
                    yield ListView(id="menu-party")
                    yield ListView(id="menu-items")
                    yield Static("", id="detail-pane")
                with Container(id="combat-log-panel"):
                    yield RichLog(id="combat-log", markup=True)
            with Vertical(id="right-col"):
                with Container(id="npc-panel"):
                    yield Label("", id="npc-name")
                    yield Label("", id="npc-type")
                    yield ProgressBar(id="npc-hp-bar", total=100, show_eta=False)
                    yield Label("", id="npc-status")
                    yield Label("", id="npc-stages")
                    yield Label("", id="npc-stats")
                with Horizontal(id="sprite-panel"):
                    with Vertical(id="sprite-npc-wrap"):
                        yield Static("", id="sprite-npc")
                        yield Static("", id="sprite-npc-label")
                    yield Static("—", id="sprite-vs")
                    with Vertical(id="sprite-player-wrap"):
                        yield Static("", id="sprite-player")
                        yield Static("", id="sprite-player-label")
                with Container(id="player-panel"):
                    yield Label("", id="player-name")
                    yield Label("", id="player-type")
                    yield ProgressBar(id="player-hp-bar", total=100, show_eta=False)
                    yield Label("", id="player-status")
                    yield Label("", id="player-stages")
                    yield Label("", id="player-pp")
        yield Footer()

    def on_mount(self) -> None:
        self.message_queue = asyncio.Queue()
        set_async_queue(self.message_queue)
        self.controller = BattleController(self.player, self.npc)

        self.query_one("#action-pane").border_title      = "actions"
        self.query_one("#combat-log-panel").border_title = "log"
        self.query_one("#sprite-panel").border_title     = "vs"

        self.query_one("#menu-moves").display = False
        self.query_one("#menu-party").display = False
        self.query_one("#menu-items").display = False

        self.update_display()

    def on_ready(self) -> None:
        self.set_timer(0.2, self._start_battle)

    def _start_battle(self) -> None:
        game_print(msg("battle_start"))
        self.run_worker(self.drain_queue())

    def action_fight(self) -> None:
        if not self._input_enabled:
            return
        if self.controller.phase != BattlePhase.PLAYER_ACTION:
            return

        # if locked into a multi turn move, skip menu and use locked move
        if self.player.locked_move is not None:
            move = self.player.locked_move
            self.player.locked_turns -= 1
            self.controller.select_player_move(move)
            self.controller.select_npc_move()
            self.show_main_menu()
            self.run_worker(self.resolve_and_display())
        else:
            self.show_move_menu()

    def action_party(self) -> None:
        if not self._input_enabled:
            return
        if self.controller.phase == BattlePhase.PLAYER_ACTION:
            self.show_party_menu()

    def action_bag(self) -> None:
        if not self._input_enabled:
            return

    def action_quit(self) -> None:
        self.app.exit()

    def action_cancel(self) -> None:
        self.show_main_menu()