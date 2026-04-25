import sys
import os
import asyncio
# add src/ to path so all modules can be found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from textual.app        import App, ComposeResult
from textual.worker     import Worker
from textual.widgets    import RichLog, Static, Footer, ListView, ListItem, Label, ProgressBar
from textual.containers import Horizontal, Vertical, Container
from models.trainer     import Trainer
from battle.controller  import BattleController
from core.battle_state  import BattlePhase
from core.game_print    import game_print, set_output_handler, set_async_queue
from core.messages      import msg
from core.logger        import logger
from ui.screens.end_screen import EndScreen

# tuning constants
MESSAGE_DELAY:  float = 0.30   # delay between log messages
HP_ANIM_SPEED:  float = 0.75   # duration of HP bar animation

class TuimonApp(App):

    CSS_PATH = "styles/battle.tcss"

    BINDINGS = [
        ("f",      "fight",  "Fight"),
        ("p",      "party",  "Party"),
        ("b",      "bag",    "Bag"),
        ("r",      "run",    "Run"),
        ("escape", "cancel", "Cancel"),
        ("q",      "quit",   "Quit"),
    ]

    SCREENS = {
        "end": EndScreen,
    }

    def __init__(self, player: Trainer, npc: Trainer) -> None:
        super().__init__()
        self.player = player
        self.npc    = npc

    def compose(self) -> ComposeResult:
        with Horizontal(id="main"):

            # ── Left Column ──────────────────────────
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

            # ── Right Column ─────────────────────────
            with Vertical(id="right-col"):

                # NPC panel
                with Container(id="npc-panel"):
                    yield Label("", id="npc-name")
                    yield Label("", id="npc-type")
                    yield ProgressBar(id="npc-hp-bar", total=100, show_eta=False)
                    yield Label("", id="npc-status")
                    yield Label("", id="npc-stages")
                    yield Label("", id="npc-stats")

                # Sprite panel
                with Horizontal(id="sprite-panel"):
                    with Vertical(id="sprite-npc-wrap"):
                        yield Static("", id="sprite-npc")
                        yield Static("", id="sprite-npc-label")
                    yield Static("—", id="sprite-vs")
                    with Vertical(id="sprite-player-wrap"):
                        yield Static("", id="sprite-player")
                        yield Static("", id="sprite-player-label")

                # Player panel
                with Container(id="player-panel"):
                    yield Label("", id="player-name")
                    yield Label("", id="player-type")
                    yield ProgressBar(id="player-hp-bar", total=100, show_eta=False)
                    yield Label("", id="player-status")
                    yield Label("", id="player-stages")
                    yield Label("", id="player-stats")
                    yield Label("", id="player-pp")

        yield Footer()

    def on_mount(self) -> None:
        self.message_queue = asyncio.Queue()
        from core.game_print import set_async_queue
        set_async_queue(self.message_queue)
        self.controller = BattleController(self.player, self.npc)
        self.update_display()
        # don't call game_print here

        # Placeholder sprites
        self.query_one("#sprite-npc",    Static).update("  @@@\n @@@@\n @@@")
        self.query_one("#sprite-player", Static).update("@@@  \n@@@@\n@@@  ")

        # static titles that never change
        self.query_one("#action-pane").border_title      = "actions"
        self.query_one("#combat-log-panel").border_title = "log"
        self.query_one("#sprite-panel").border_title     = "vs"

        # hide submenus
        self.query_one("#menu-moves").display = False
        self.query_one("#menu-party").display = False
        self.query_one("#menu-items").display = False

        self.update_display()

        self.query_one("#combat-log-panel").border_subtitle = "turn 1"

    def on_ready(self) -> None:
        """Called after the first frame is fully rendered."""
        game_print(msg("battle_start"))
        self.run_worker(self.drain_queue())

    def _post_mount(self) -> None:
        log = self.query_one("#combat-log", RichLog)
        log.clear()  # clear any stale content
        game_print(msg("battle_start"))
        self.run_worker(self.drain_queue())

    def show_main_menu(self) -> None:
        self.query_one("#menu-main").display  = True
        self.query_one("#menu-moves").display = False
        self.query_one("#menu-party").display = False
        self.query_one("#menu-items").display = False
        self.query_one("#action-pane").border_title = "actions"

    def show_move_menu(self) -> None:
        move_list = self.query_one("#menu-moves", ListView)
        move_list.clear()
        for move in self.player.active().moveset:
            move_list.append(ListItem(Label(f"{move.name}  PP: {move.pp}")))
        move_list.append(ListItem(Label("Cancel")))  # no id
        self.query_one("#menu-main").display  = False
        self.query_one("#menu-moves").display = True
        self.query_one("#action-pane").border_title = "moves"

    def show_party_menu(self) -> None:
        party_list = self.query_one("#menu-party", ListView)
        party_list.clear()
        for pokemon in self.player.party:
            status = "FNT" if not pokemon.is_alive() else f"{pokemon.hp}/{pokemon.max_hp}"
            party_list.append(ListItem(Label(f"{pokemon.name}  {status}")))
        party_list.append(ListItem(Label("Cancel")))  # no id
        self.query_one("#menu-main").display  = False
        self.query_one("#menu-party").display = True
        self.query_one("#action-pane").border_title = "party"

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        logger.debug(f"on_list_view_selected: list={event.list_view.id} idx={event.list_view.index}")
        event.stop()
        idx = event.list_view.index

        if event.list_view.id == "menu-main":
            # main menu items are fixed so index is reliable
            match idx:
                case 0: self.show_move_menu()
                case 1: self.show_party_menu()
                case 2: pass  # items not yet implemented
                case 3: self.action_quit()

        elif event.list_view.id == "menu-moves":
            moveset = self.player.active().moveset
            if idx >= len(moveset):
                self.show_main_menu()
            else:
                move = moveset[idx]
                self.controller.select_player_move(move)
                self.controller.select_npc_move()
                # hide menu while turn resolves
                self.show_main_menu()
                # schedule async resolution
                self.run_worker(self.resolve_and_display())

        elif event.list_view.id == "menu-party":
            party = self.player.party
            if idx >= len(party):
                # last item is always cancel
                self.show_main_menu()
            else:
                pokemon = party[idx]
                if not pokemon.is_alive():
                    self.log_message(f"{pokemon.name} has fainted!")
                elif idx == self.player.selected_mon:
                    self.log_message(f"{pokemon.name} is already out!")
                else:
                    self.player.selected_mon = idx
                    self.log_message(f"Go, {pokemon.name}!")
                    self.update_display()
                    self.show_main_menu()

    def update_display(self) -> None:
        npc    = self.npc.active()
        player = self.player.active()

        # ── NPC panel ────────────────────────────────
        self.query_one("#npc-panel").border_title    = npc.name
        self.query_one("#npc-panel").border_subtitle = f"HP: {npc.hp}/{npc.max_hp}"

        self.query_one("#npc-name",  Label).update(f"[bold]{npc.name}[/bold]")
        self.query_one("#npc-type",  Label).update(" / ".join(npc.type))

        npc_hp_pct = int((npc.hp / npc.max_hp) * 100)
        self.query_one("#npc-hp-bar", ProgressBar).update(progress=npc_hp_pct)

        npc_status = npc.major_status.name if npc.major_status else ""
        self.query_one("#npc-status", Label).update(npc_status)

        npc_stages = self._format_stages(npc)
        self.query_one("#npc-stages", Label).update(npc_stages)

        npc_stats = self._format_stats(npc)
        self.query_one("#npc-stats", Label).update(npc_stats)

        # ── Player panel ──────────────────────────────
        self.query_one("#player-panel").border_title    = player.name
        self.query_one("#player-panel").border_subtitle = f"HP: {player.hp}/{player.max_hp}"

        self.query_one("#player-name", Label).update(f"[bold]{player.name}[/bold]")
        self.query_one("#player-type", Label).update(" / ".join(player.type))

        player_hp_pct = int((player.hp / player.max_hp) * 100)
        self.query_one("#player-hp-bar", ProgressBar).update(progress=player_hp_pct)

        player_status = player.major_status.name if player.major_status else ""
        self.query_one("#player-status", Label).update(player_status)

        player_stages = self._format_stages(player)
        self.query_one("#player-stages", Label).update(player_stages)

        player_stats = self._format_stats(npc)
        self.query_one("#player-stats", Label).update(player_stats)

        player_pp = self._format_pp(player)
        self.query_one("#player-pp", Label).update(player_pp)

        # ── Sprite labels ─────────────────────────────
        self.query_one("#sprite-npc-label",    Static).update(npc.name)
        self.query_one("#sprite-player-label", Static).update(player.name)

        # ── HP bar color based on percentage ─────────
        self._update_hp_bar_color("#npc-hp-bar",    npc_hp_pct)
        self._update_hp_bar_color("#player-hp-bar", player_hp_pct)

        # ── Combat log turn divider ───────────────────
        self.query_one("#combat-log-panel").border_subtitle = (
            f"turn {self.controller.turn}"
        )

    def _handle_phase(self, phase: BattlePhase) -> None:
        match phase:
            case BattlePhase.PLAYER_ACTION:
                self.show_main_menu()

            case BattlePhase.SWITCH_PROMPT:
                # player's pokemon fainted - must switch
                self.log_message(f"{self.player.active().name} fainted!")
                self.show_party_menu()

            case BattlePhase.NPC_SWITCH:
                # npc's pokemon fainted - auto switch to next available
                self.log_message(f"{self.npc.active().name} fainted!")
                self._handle_npc_switch()

            case BattlePhase.BATTLE_OVER:
                self._handle_battle_over()

    def _handle_npc_switch(self) -> None:
        """Automatically switch NPC to next available pokemon."""
        for i, pokemon in enumerate(self.npc.party):
            if pokemon.is_alive() and i != self.npc.selected_mon:
                self.npc.selected_mon = i
                self.log_message(f"Opponent sent out {self.npc.active().name}!")
                self.update_display()
                self.controller.phase = BattlePhase.PLAYER_ACTION
                self.show_main_menu()
                return
            
    def _handle_phase_buffered(self, phase: BattlePhase) -> None:
        logger.debug(f"_handle_phase_buffered: phase={phase}")
        match phase:
            case BattlePhase.PLAYER_ACTION:
                pass
            case BattlePhase.SWITCH_PROMPT:
                game_print(f"{self.player.active().name} fainted!")
            case BattlePhase.NPC_SWITCH:
                game_print(f"{self.npc.active().name} fainted!")
                self._do_npc_switch()
            case BattlePhase.BATTLE_OVER:
                won = any(p.is_alive() for p in self.player.party)
                logger.debug(f"_handle_phase_buffered: BATTLE_OVER won={won}")
                game_print("You won!" if won else "You lost!")

    def _do_npc_switch(self) -> None:
        """Switch NPC pokemon - generates messages via game_print."""
        for i, pokemon in enumerate(self.npc.party):
            if pokemon.is_alive() and i != self.npc.selected_mon:
                self.npc.selected_mon = i
                game_print(f"Opponent sent out {self.npc.active().name}!")
                return

    def _handle_phase_ui(self, phase: BattlePhase) -> None:
        match phase:
            case BattlePhase.PLAYER_ACTION:
                self.show_main_menu()
            case BattlePhase.SWITCH_PROMPT:
                self.show_party_menu()
            case BattlePhase.NPC_SWITCH:
                self.controller.phase = BattlePhase.PLAYER_ACTION
                self.update_display()
                self.show_main_menu()
            case BattlePhase.BATTLE_OVER:
                from core.game_print import clear_output_handler
                clear_output_handler()
                won = any(p.is_alive() for p in self.player.party)
                self.push_screen(EndScreen(won=won, turns=self.controller.turn))

    def _format_stages(self, pokemon) -> str:
        """Format stat stages as a compact string."""
        stages = {
            "ATK": pokemon.stage_attk,
            "DEF": pokemon.stage_def,
            "SpA": pokemon.stage_sp_attk,
            "SpD": pokemon.stage_sp_def,
            "SPD": pokemon.stage_spd,
            "ACC": pokemon.stage_acc,
            "EVA": pokemon.stage_eva,
        }
        parts = []
        for name, val in stages.items():
            if val > 0:
                parts.append(f"[green]{name}:+{val}[/green]")
            elif val < 0:
                parts.append(f"[red]{name}:{val}[/red]")
            else:
                parts.append(f"[dim]{name}:0[/dim]")
        return "  ".join(parts)

    def _format_stats(self, pokemon) -> str:
        """Format calculated stats after stage modifiers."""
        return (
            f"[dim]ATK[/dim] {pokemon.get_stat('stat_attk')}  "
            f"[dim]DEF[/dim] {pokemon.get_stat('stat_def')}  "
            f"[dim]SpA[/dim] {pokemon.get_stat('stat_sp_attk')}  "
            f"[dim]SpD[/dim] {pokemon.get_stat('stat_sp_def')}  "
            f"[dim]SPD[/dim] {pokemon.get_stat('stat_spd')}"
        )

    def _format_pp(self, pokemon) -> str:
        """Format move PP summary for player panel."""
        parts = []
        for move in pokemon.moveset:
            color = "red" if move.pp <= move.pp // 4 else "dim"
            parts.append(f"[{color}]{move.name[:10]}[/{color}] {move.pp}")
        return "  ".join(parts)

    def _update_hp_bar_color(self, widget_id: str, pct: int) -> None:
        """Update HP bar color based on percentage."""
        bar = self.query_one(widget_id, ProgressBar)
        if pct > 50:
            bar.styles.color = "green"
        elif pct > 25:
            bar.styles.color = "yellow"
        else:
            bar.styles.color = "red"

    def action_fight(self) -> None:
        if self.controller.phase == BattlePhase.PLAYER_ACTION:
            self.show_move_menu()

    def action_party(self) -> None:
        if self.controller.phase == BattlePhase.PLAYER_ACTION:
            self.show_party_menu()

    def action_bag(self) -> None:
        if self.controller.phase == BattlePhase.PLAYER_ACTION:
            self.show_item_menu()

    def action_run(self) -> None:
        if self.controller.phase == BattlePhase.PLAYER_ACTION:
            self.action_quit()

    def action_cancel(self) -> None:
        self.show_main_menu()

    async def log_message_animated(self, message: str, delay: float = 0.03) -> None:
        """Print message to log letter by letter."""
        log = self.query_one("#combat-log", RichLog)
        for char in message:
            log.write(char, end="")
            await asyncio.sleep(delay)
        log.write("")  # newline at end

    async def drain_queue(self, line_delay: float = 0.15) -> None:
        """Drain all messages with a pause between each line."""
        log = self.query_one("#combat-log", RichLog)
        while not self.message_queue.empty():
            message = await self.message_queue.get()
            log.write(message)
            await asyncio.sleep(line_delay)

    def _set_input_enabled(self, enabled: bool) -> None:
        """Disable/enable player input during turn resolution."""
        for binding_key in ["f", "p", "b", "r"]:
            # grey out footer bindings visually
            pass
        # simplest approach - track a flag
        self._input_enabled = enabled

    def action_fight(self) -> None:
        if not getattr(self, "_input_enabled", True):
            return  # ignore input during resolution
        if self.controller.phase == BattlePhase.PLAYER_ACTION:
            self.show_move_menu()

    async def resolve_and_display(self) -> None:
        from core.game_print import start_buffering, stop_buffering, HpSnapshot

        self._set_input_enabled(False)
        await asyncio.sleep(0.05)

        log = self.query_one("#combat-log", RichLog)
        log.write(f"[dim]── turn {self.controller.turn + 1} ────────────────[/dim]")
        await asyncio.sleep(0.1)

        start_buffering()
        phase    = self.controller.execute_turn()
        self._handle_phase_buffered(phase)
        messages = stop_buffering()

        # process messages and hp snapshots in order
        for item in messages:
            if isinstance(item, HpSnapshot):
                # animate the correct HP bar
                widget_id = self._get_hp_widget_id(item.pokemon_name)
                if widget_id:
                    await self.animate_hp_bar(widget_id, item.start_pct, item.end_pct)
            else:
                # regular message
                log.write(item)
                await asyncio.sleep(MESSAGE_DELAY)

        self.update_display()
        self._set_input_enabled(True)
        self._handle_phase_ui(phase)

    def _get_hp_widget_id(self, pokemon_name: str) -> str | None:
        """Map a pokemon name to its HP bar widget ID."""
        if pokemon_name == self.npc.active().name:
            return "#npc-hp-bar"
        elif pokemon_name == self.player.active().name:
            return "#player-hp-bar"
        return None

    async def animate_hp_bar(
        self,
        widget_id: str,
        start_pct: int,
        end_pct:   int,
        duration:  float = HP_ANIM_SPEED
    ) -> None:
        """Smoothly animate an HP bar from start_pct to end_pct."""
        bar   = self.query_one(widget_id, ProgressBar)
        steps = abs(start_pct - end_pct)

        if steps == 0:
            return

        delay     = duration / steps
        direction = -1 if end_pct < start_pct else 1
        current   = start_pct

        for _ in range(steps):
            current += direction
            bar.update(progress=current)
            self._update_hp_bar_color(widget_id, current)
            await asyncio.sleep(delay)


if __name__ == "__main__":
    from core.config  import DEBUG
    from core.presets import get_test_player, get_test_npc

    if DEBUG:
        player = get_test_player()
        npc    = get_test_npc()
    else:
        from print import build_party
        from pokemon.pokemon_factory import create_pokemon_from_api
        player_party = build_party("Ash", party_size=2)
        player       = Trainer(name="Ash", party=player_party)
        npc_party    = [p for p in [
            create_pokemon_from_api("gengar",   lvl=55),
            create_pokemon_from_api("alakazam", lvl=55),
        ] if p is not None]
        npc = Trainer(name="Gary", party=npc_party)

    app = TuimonApp(player=player, npc=npc)
    app.run()