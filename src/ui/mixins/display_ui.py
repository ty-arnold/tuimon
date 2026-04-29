from textual.widgets import Label, Static, RichLog
from core.colors     import status_markup
from ui.widgets.hp_bar import HpBar
from ui.mixins.menu_ui import TYPE_COLORS
from ui.palette        import Colors
from data.sprite_cache import get_sprite
from core.logger       import logger

class DisplayUIMixin:
    """Handles updating all pokemon panels."""

    def update_display(self) -> None:
        npc    = self.npc.active()
        player = self.player.active()
        c      = Colors(self.app)

        logger.debug(f"update_display: npc={npc.name} player={player.name}")

        if self.query_one("#menu-party").display:
            self.show_party_menu()

        # ── NPC panel ─────────────────────────────────────────────
        self.query_one("#npc-panel").border_title    = self.npc.name
        self.query_one("#npc-panel").border_subtitle = self._format_party_balls(self.npc, c.npc_title)

        self.query_one("#npc-name",  Label).update(f"[bold]{npc.name}[/bold]")
        self.query_one("#npc-level", Label).update(f"[dim]Lv.{npc.lvl}[/dim]")
        self.query_one("#npc-type",  Label).update(self._format_types(npc.type))

        self.query_one("#npc-hp-bar", HpBar).set_hp(npc.hp, npc.max_hp)

        npc_status = self._format_status(npc)
        self.query_one("#npc-status", Label).update(npc_status)

        self.query_one("#npc-stats", Static).update(self._format_stats_combined(npc))

        npc_effects = self._format_effects(self.npc)
        npc_effects_widget = self.query_one("#npc-effects", Label)
        if npc_effects:
            npc_effects_widget.update(npc_effects)
            npc_effects_widget.display = True
        else:
            npc_effects_widget.display = False

        # ── Player panel ──────────────────────────────────────────
        self.query_one("#player-panel").border_title    = self.player.name
        self.query_one("#player-panel").border_subtitle = self._format_party_balls(self.player, c.player_title)

        self.query_one("#player-name",  Label).update(f"[bold]{player.name}[/bold]")
        self.query_one("#player-level", Label).update(f"[dim]Lv.{player.lvl}[/dim]")
        self.query_one("#player-type",  Label).update(self._format_types(player.type))

        self.query_one("#player-hp-bar", HpBar).set_hp(player.hp, player.max_hp)

        player_status = self._format_status(player)
        self.query_one("#player-status", Label).update(player_status)

        self.query_one("#player-stats", Static).update(self._format_stats_combined(player))

        player_effects = self._format_effects(self.player)
        player_effects_widget = self.query_one("#player-effects", Label)
        if player_effects:
            player_effects_widget.update(player_effects)
            player_effects_widget.display = True
        else:
            player_effects_widget.display = False

        # ── Sprites ───────────────────────────────────────────────
        npc_lines    = get_sprite(npc.name,    "front")
        player_lines = get_sprite(player.name, "back")
        self.query_one("#sprite-npc",    Static).update("\n".join(npc_lines))
        self.query_one("#sprite-player", Static).update("\n".join(player_lines))
        self.query_one("#sprite-npc-label",    Static).update(f"[dim]{npc.name}[/dim]")
        self.query_one("#sprite-player-label", Static).update(f"[dim]{player.name}[/dim]")

        # ── Combat log turn counter ───────────────────────────────
        self.query_one("#combat-log-panel").border_subtitle = (
            f"turn {self.controller.turn + 1}"
        )

    def _format_party_balls(self, trainer, color: str) -> str:
        BALL  = "󰐝"
        c     = Colors(self.app)
        balls = []
        for pokemon in trainer.party:
            if pokemon.is_alive():
                balls.append(f"[{color}]{BALL}[/{color}]")
            else:
                balls.append(f"[{c.text_dim}]{BALL}[/{c.text_dim}]")
        return " ".join(balls)

    def _format_types(self, types: list[str]) -> str:
        c     = Colors(self.app)
        parts = []
        for t in types:
            color = TYPE_COLORS.get(t, {}).get("text", c.text_ui)
            parts.append(f"[{color}]{t}[/{color}]")
        return f" [{c.text_muted_ui}]/[/{c.text_muted_ui}] ".join(parts)

    def _format_stats_combined(self, pokemon) -> "Table":
        from rich.table import Table
        from rich.text  import Text
        c = Colors(self.app)

        stats = {
            "Attack":     (pokemon.stage_attk,    pokemon.get_stat("stat_attk")),
            "Defense":    (pokemon.stage_def,      pokemon.get_stat("stat_def")),
            "Sp. Attack": (pokemon.stage_sp_attk,  pokemon.get_stat("stat_sp_attk")),
            "Sp. Defense":(pokemon.stage_sp_def,   pokemon.get_stat("stat_sp_def")),
            "Speed":      (pokemon.stage_spd,      pokemon.get_stat("stat_spd")),
            "Accuracy":   (pokemon.stage_acc,      None),
            "Evasion":    (pokemon.stage_eva,      None),
        }

        table = Table.grid(expand=True, padding=(0, 1))
        for _ in stats:
            table.add_column(justify="center", ratio=1)

        table.add_row(*[Text(name, style=f"bold {c.text_label}") for name in stats])

        val_cells = []
        for stage, val in stats.values():
            if val is not None:
                if stage != 0:
                    stage_str = f"+{stage}" if stage > 0 else str(stage)
                    color     = c.success if stage > 0 else c.error
                    val_cells.append(Text.from_markup(
                        f"[{c.text_ui}]{val}[/{c.text_ui}] [{color}]({stage_str})[/{color}]"
                    ))
                else:
                    val_cells.append(Text(str(val), style=c.text_ui))
            else:
                if stage != 0:
                    stage_str = f"+{stage}" if stage > 0 else str(stage)
                    color     = c.success if stage > 0 else c.error
                    val_cells.append(Text.from_markup(
                        f"[{color}]({stage_str})[/{color}]"
                    ))
                else:
                    val_cells.append(Text("—", style=c.text_muted_ui))

        table.add_row(*val_cells)
        return table

    def _format_status(self, pokemon) -> str:
        parts = []
        if pokemon.major_status:
            abbrev = {
                "Burn":      "BRN",
                "Poison":    "PSN",
                "Paralysis": "PAR",
                "Sleep":     "SLP",
                "Freeze":    "FRZ",
            }
            key = abbrev.get(pokemon.major_status.name, pokemon.major_status.name[:3].upper())
            parts.append(status_markup(key))
        for effect in pokemon.minor_status:
            if effect.name == "Confusion":
                parts.append(status_markup("CFZ"))
        return " ".join(parts) if parts else ""

    def _format_effects(self, trainer) -> str:
        c     = Colors(self.app)
        parts = []

        if trainer.invulnerable_state:
            if trainer.locked_move and trainer.locked_turns > 0:
                turns    = trainer.locked_turns
                turn_str = f"{turns} turn" + ("s" if turns != 1 else "")
                parts.append(f"[{c.effect_lock}]{trainer.invulnerable_state.capitalize()} ({turn_str})[/{c.effect_lock}]")
            else:
                parts.append(f"[{c.effect_lock}]{trainer.invulnerable_state.capitalize()}[/{c.effect_lock}]")
        elif trainer.locked_move:
            turns    = trainer.locked_turns
            turn_str = f"{turns} turn" + ("s" if turns != 1 else "")
            parts.append(f"[{c.effect_lock}]{trainer.locked_move.name} ({turn_str})[/{c.effect_lock}]")

        for effect in trainer.active_effects:
            turns = getattr(effect, "turns", None)
            name  = effect.effect_type.replace("_", " ").title()
            if turns:
                parts.append(f"[{c.warning}]{name} {turns}t[/{c.warning}]")
            else:
                parts.append(f"[{c.warning}]{name}[/{c.warning}]")

        return "  ".join(parts) if parts else ""

    def _format_pp(self, pokemon) -> str:
        c     = Colors(self.app)
        parts = []
        for move in pokemon.moveset:
            color = c.error if move.pp <= move.pp // 4 else c.text_muted_ui
            parts.append(f"[{color}]{move.name[:10]}[/{color}] {move.pp}")
        return "  ".join(parts)

    def log_message(self, message: str) -> None:
        self.query_one("#combat-log", RichLog).write(message)
