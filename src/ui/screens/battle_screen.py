import os
import asyncio
from textual.app        import ComposeResult
from textual.widgets    import RichLog, Static, Footer, ListView, ListItem, Label, Rule, Tabs, Tab
from textual.containers import Horizontal, Vertical, Container, Grid
from textual.screen     import Screen
from models.trainer     import Trainer
from battle.controller  import BattleController
from core.game_print    import game_print, set_async_queue
from core.logger        import logger
from core.messages      import msg
from core.battle_state  import BattlePhase
from ui.widgets.hp_bar  import HpBar

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
        ("left",   "prev_tab", ""),
        ("right",  "next_tab", ""),
        ("enter",  "confirm",  ""),
        ("f",      "fight",    "Fight"),
        ("p",      "party",    "Party"),
        ("b",      "bag",      "Bag"),
        ("r",      "run",      "Run"),
        ("escape", "cancel",   "Cancel"),
        ("q",      "quit",     "Quit"),
    ]

    def __init__(self, player: Trainer, npc: Trainer) -> None:
        super().__init__()
        self.player         = player
        self.npc            = npc
        self._input_enabled = True
        self._battle_ready  = False

    def compose(self) -> ComposeResult:
        with Horizontal(id="main"):
            with Vertical(id="left-col"):
                with Container(id="action-pane"):
                    yield Tabs(
                        Tab("Moves", id="tab-moves"),
                        Tab("Party", id="tab-party"),
                        Tab("Items", id="tab-items"),
                        Tab("Run",   id="tab-run"),
                        Tab("Menu",  id="tab-menu"),
                        id="menu-tabs",
                    )
                    yield ListView(id="menu-moves")
                    yield Rule(id="menu-moves-rule")
                    yield ListView(id="menu-party")
                    yield ListView(id="menu-items")
                    with Container(id="detail-pane"):
                        yield Label("", id="detail-name")
                        yield Grid(id="detail-grid")
                        yield Rule(id="menu-moves-rule") 
                        yield Label("", id="detail-description", markup=True)
                with Container(id="combat-log-panel"):
                    yield RichLog(id="combat-log", markup=True)
            with Vertical(id="right-col"):
                with Container(id="npc-panel"):
                    with Horizontal():
                        yield Label("", id="npc-name")
                        yield Label("", id="npc-status")
                        yield Label("", id="npc-level")
                    yield Label("", id="npc-type")
                    yield HpBar(id="npc-hp-bar")
                    yield Rule(name="Stats")
                    yield Static("", id="npc-stats")
                    yield Label("", id="npc-effects")
                with Horizontal(id="sprite-panel"):
                    with Vertical(id="sprite-player-wrap"):
                        yield Static("", id="sprite-player")
                        yield Static("", id="sprite-player-label")
                    yield Static("—", id="sprite-vs")
                    with Vertical(id="sprite-npc-wrap"):
                        yield Static("", id="sprite-npc")
                        yield Static("", id="sprite-npc-label")
                with Container(id="player-panel"):
                    with Horizontal():
                        yield Label("", id="player-name")
                        yield Label("", id="player-status")
                        yield Label("", id="player-level")
                    yield Label("", id="player-type")
                    yield HpBar(id="player-hp-bar")
                    yield Rule(name="Stats")
                    yield Static("", id="player-stats")
                    yield Label("", id="player-effects")
        yield Footer()

    def on_mount(self) -> None:
        self.message_queue = asyncio.Queue()
        set_async_queue(self.message_queue)
        self.controller = BattleController(self.player, self.npc)

        self.query_one("#action-pane").border_title      = "actions"
        self.query_one("#combat-log-panel").border_title = "log"
        self.query_one("#sprite-panel").border_title     = "vs"

        self.query_one("#menu-moves").display      = False
        self.query_one("#menu-moves-rule").display = False
        self.query_one("#menu-party").display      = False
        self.query_one("#menu-items").display      = False
        self.query_one("#detail-pane").display     = False

        self.query_one("#npc-type").styles.margin      = (0, 0, 1, 0)
        self.query_one("#player-type").styles.margin   = (0, 0, 1, 0)
        self.query_one("#npc-panel").styles.padding    = (1, 1, 0, 1)
        self.query_one("#player-panel").styles.padding = (1, 1, 0, 1)
        self.query_one("#npc-effects").styles.margin    = (1, 0, 0, 0)
        self.query_one("#player-effects").styles.margin = (1, 0, 0, 0)
        self.query_one("#action-pane").styles.padding   = (1, 2, 0, 2)

        self.update_display()
        self._battle_ready = True
        self.show_move_menu()

        self._anim_frame = 0
        self.set_interval(0.15, self._animate_sprites)

    def _animate_sprites(self) -> None:
        from data.sprite_cache import get_sprite_frames
        self._anim_frame += 1
        npc    = self.npc.active()
        player = self.player.active()

        npc_frames    = get_sprite_frames(npc.name,    "front")
        player_frames = get_sprite_frames(player.name, "back")

        if npc_frames:
            lines = npc_frames[self._anim_frame % len(npc_frames)]
            self.query_one("#sprite-npc", Static).update("\n".join(lines))

        if player_frames:
            lines = player_frames[self._anim_frame % len(player_frames)]
            self.query_one("#sprite-player", Static).update("\n".join(lines))

        self.set_timer(0.2, self._start_battle)

    def _debug_hp_bar(self) -> None:
        bar = self.query_one("#npc-hp-bar")
        logger.debug(f"HpBar type: {type(bar)}")
        logger.debug(f"HpBar region: {bar.region}")
        logger.debug(f"HpBar children: {list(bar.query('*'))}")
        for child in bar.query("*"):
            logger.debug(f"  child: {child.__class__.__name__} region={child.region}")

    def _start_battle(self) -> None:
        game_print(msg("battle_start"))

    def action_fight(self) -> None:
        if not self._input_enabled:
            return
        if self.controller.phase != BattlePhase.PLAYER_ACTION:
            return
        if self.player.locked_move is not None:
            move = self.player.locked_move
            self.player.locked_turns -= 1
            self.controller.select_player_move(move)
            self.controller.select_npc_move()
            self.run_worker(self.resolve_and_display(), thread=False)
        else:
            self.query_one("#menu-tabs", Tabs).active = "tab-moves"

    def action_party(self) -> None:
        if not self._input_enabled:
            return
        if self.controller.phase == BattlePhase.PLAYER_ACTION:
            self.query_one("#menu-tabs", Tabs).active = "tab-party"

    def action_bag(self) -> None:
        if not self._input_enabled:
            return

    def action_quit(self) -> None:
        self.app.exit()

    def action_prev_tab(self) -> None:
        if self._input_enabled:
            self.query_one("#menu-tabs", Tabs).action_previous_tab()

    def action_next_tab(self) -> None:
        if self._input_enabled:
            self.query_one("#menu-tabs", Tabs).action_next_tab()

    def action_confirm(self) -> None:
        tabs = self.query_one("#menu-tabs", Tabs)
        match tabs.active:
            case "tab-run": self.action_quit()

    def action_cancel(self) -> None:
        pass