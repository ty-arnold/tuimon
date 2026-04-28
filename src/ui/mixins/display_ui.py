from textual.widgets import Label, Static, RichLog
from core.colors import status_markup
from ui.widgets.hp_bar import HpBar
from ui.mixins.menu_ui import TYPE_COLORS
from core.logger import logger

class DisplayUIMixin:
    """Handles updating all pokemon panels."""

    def update_display(self) -> None:
        npc    = self.npc.active()
        player = self.player.active()

        logger.debug(f"update_display: npc={npc.name} player={player.name}")

        if self.query_one("#menu-party").display:
            self.show_party_menu()

        # ── NPC panel ─────────────────────────────────────────────
        self.query_one("#npc-panel").border_title    = self.npc.name
        # self.query_one("#npc-panel").border_subtitle = f"EXP:"

        self.query_one("#npc-name",  Label).update(f"[bold]{npc.name}[/bold]")
        self.query_one("#npc-level", Label).update(f"[dim]Lv.{npc.lvl}[/dim]")
        self.query_one("#npc-type",  Label).update(self._format_types(npc.type))

        self.query_one("#npc-hp-bar", HpBar).set_hp(npc.hp, npc.max_hp)

        npc_status = self._format_status(npc)
        self.query_one("#npc-status", Label).update(npc_status)

        self.query_one("#npc-stats", Static).update(self._format_stats_combined(npc))

        # NPC effects
        npc_effects = self._format_effects(self.npc)
        npc_effects_widget = self.query_one("#npc-effects", Label)
        if npc_effects:
            npc_effects_widget.update(npc_effects)
            npc_effects_widget.display = True
        else:
            npc_effects_widget.display = False

        # ── Player panel ──────────────────────────────────────────
        self.query_one("#player-panel").border_title    = self.player.name
        self.query_one("#player-panel").border_subtitle = f"EXP:"

        self.query_one("#player-name",  Label).update(f"[bold]{player.name}[/bold]")
        self.query_one("#player-level", Label).update(f"[dim]Lv.{player.lvl}[/dim]")
        self.query_one("#player-type",  Label).update(self._format_types(player.type))

        self.query_one("#player-hp-bar", HpBar).set_hp(player.hp, player.max_hp)

        player_status = self._format_status(player)
        self.query_one("#player-status", Label).update(player_status)

        # speed indicator
        player_spd = player.get_stat("stat_spd")
        npc_spd    = npc.get_stat("stat_spd")
        if player_spd > npc_spd:
            speed_str = f"[#44cc44]▶ goes first[/#44cc44]  SPD {player_spd} vs {npc_spd}"
        elif player_spd < npc_spd:
            speed_str = f"[#cc4444]▶ goes second[/#cc4444]  SPD {player_spd} vs {npc_spd}"
        else:
            speed_str = f"[#ccaa22]▶ speed tie[/#ccaa22]  SPD {player_spd}"
        # self.query_one("#player-prio", Label).update(speed_str)

        self.query_one("#player-stats", Static).update(self._format_stats_combined(player))

        # self.query_one("#player-pp", Label).update(self._format_pp(player))

        # Player effects
        player_effects = self._format_effects(self.player)
        player_effects_widget = self.query_one("#player-effects", Label)
        if player_effects:
            player_effects_widget.update(player_effects)
            player_effects_widget.display = True
        else:
            player_effects_widget.display = False

        # ── Sprite labels ─────────────────────────────────────────
        self.query_one("#sprite-npc-label",    Static).update(npc.name)
        self.query_one("#sprite-player-label", Static).update(player.name)

        # ── Combat log turn counter ───────────────────────────────
        self.query_one("#combat-log-panel").border_subtitle = (
            f"turn {self.controller.turn}"
        )

    def _format_types(self, types: list[str]) -> str:
        parts = []
        for t in types:
            color = TYPE_COLORS.get(t, {}).get("text", "#aaaacc")
            parts.append(f"[{color}]{t}[/{color}]")
        return " [#555577]/[/#555577] ".join(parts)

    def _format_stats_combined(self, pokemon) -> "Table":
        from rich.table import Table
        from rich.text  import Text

        stats = {
            "Attack": (pokemon.stage_attk, pokemon.get_stat("stat_attk")),
            "Defense": (pokemon.stage_def,  pokemon.get_stat("stat_def")),
            "Sp. Attack": (pokemon.stage_sp_attk, pokemon.get_stat("stat_sp_attk")),
            "Sp. Defense": (pokemon.stage_sp_def,  pokemon.get_stat("stat_sp_def")),
            "Speed": (pokemon.stage_spd,     pokemon.get_stat("stat_spd")),
            "Accuracy": (pokemon.stage_acc,     None),
            "Evasion": (pokemon.stage_eva,     None),
        }

        table = Table.grid(expand=True, padding=(0, 1))
        for _ in stats:
            table.add_column(justify="center", ratio=1)

        # name row
        table.add_row(*[Text(name, style="bold #888899") for name in stats])

        # value + stage on same line
        val_cells = []
        for stage, val in stats.values():
            if val is not None:
                if stage != 0:
                    stage_str = f"+{stage}" if stage > 0 else str(stage)
                    color     = "#0dc958" if stage > 0 else "#cc4444"
                    val_cells.append(Text.from_markup(
                        f"[#aaaacc]{val}[/#aaaacc] [{color}]({stage_str})[/{color}]"
                    ))
                else:
                    val_cells.append(Text(str(val), style="#aaaacc"))
            else:
                if stage != 0:
                    stage_str = f"+{stage}" if stage > 0 else str(stage)
                    color     = "#0dc958" if stage > 0 else "#cc4444"
                    val_cells.append(Text.from_markup(
                        f"[{color}]({stage_str})[/{color}]"
                    ))
                else:
                    val_cells.append(Text("—", style="#555577"))

        table.add_row(*val_cells)
        logger.debug(f"stages: attk={pokemon.stage_attk} def={pokemon.stage_def}")
        logger.debug(f"stats: attk={pokemon.stat_attk} def={pokemon.stat_def}")

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

    # def _format_stats(self, pokemon) -> "Table":
    #     from rich.table import Table
    #     from rich.text  import Text
    #     from battle.modifiers import get_modifier_value

    #     stats = {
    #         "ATK": pokemon.get_stat("stat_attk"),
    #         "DEF": pokemon.get_stat("stat_def"),
    #         "SpA": pokemon.get_stat("stat_sp_attk"),
    #         "SpD": pokemon.get_stat("stat_sp_def"),
    #         "SPD": pokemon.get_stat("stat_spd"),
    #     }

    #     table = Table.grid(expand=True, padding=(0, 1))
    #     for _ in stats:
    #         table.add_column(justify="center", ratio=1)

    #     # label row
    #     table.add_row(*[Text(name, style="#888899") for name in stats])

    #     # value row
    #     table.add_row(*[Text(str(val), style="#ccccee") for val in stats.values()])

    #     return table

    def _format_effects(self, trainer) -> str:
        """Format active field effects and battle states."""
        parts = []

        # invulnerable state — merge with locked move turn count if both are active
        if trainer.invulnerable_state:
            if trainer.locked_move and trainer.locked_turns > 0:
                turns    = trainer.locked_turns
                turn_str = f"{turns} turn" + ("s" if turns != 1 else "")
                parts.append(f"[#4488cc]{trainer.invulnerable_state.capitalize()} ({turn_str})[/#4488cc]")
            else:
                parts.append(f"[#4488cc]{trainer.invulnerable_state.capitalize()}[/#4488cc]")

        # locked move — only show separately when not already shown via invulnerable state
        elif trainer.locked_move:
            turns    = trainer.locked_turns
            turn_str = f"{turns} turn" + ("s" if turns != 1 else "")
            parts.append(f"[#4488cc]{trainer.locked_move.name} ({turn_str})[/#4488cc]")

        # active field effects (screens, protect etc)
        for effect in trainer.active_effects:
            turns = getattr(effect, "turns", None)
            name  = effect.effect_type.replace("_", " ").title()
            if turns:
                parts.append(f"[#ccaa22]{name} {turns}t[/#ccaa22]")
            else:
                parts.append(f"[#ccaa22]{name}[/#ccaa22]")

        return "  ".join(parts) if parts else ""

    def _format_pp(self, pokemon) -> str:
        parts = []
        for move in pokemon.moveset:
            color = "red" if move.pp <= move.pp // 4 else "dim"
            parts.append(f"[{color}]{move.name[:10]}[/{color}] {move.pp}")
        return "  ".join(parts)

    def _update_hp_bar_color(self, widget_id: str, pct: int) -> None:
        bar = self.query_one(widget_id, HpBar)
        if pct > 50:
            bar.styles.color = "green"
        elif pct > 25:
            bar.styles.color = "yellow"
        else:
            bar.styles.color = "red"

    def log_message(self, message: str) -> None:
        self.query_one("#combat-log", RichLog).write(message)