from textual.widgets import Label, ProgressBar, Static, RichLog
from core.colors import stage_markup, status_markup

class DisplayUIMixin:
    """Handles updating all pokemon panels."""

    def update_display(self) -> None:
        npc    = self.npc.active()
        player = self.player.active()

        self.query_one("#npc-panel").border_title    = npc.name
        self.query_one("#npc-panel").border_subtitle = f"HP: {npc.hp}/{npc.max_hp}"
        self.query_one("#npc-name",  Label).update(f"[bold]{npc.name}[/bold]")
        self.query_one("#npc-type",  Label).update(" / ".join(npc.type))
        npc_status = npc.major_status.name if npc.major_status else ""
        self.query_one("#npc-status",  Label).update(npc_status)
        self.query_one("#npc-stages",  Label).update(self._format_stages(npc))
        self.query_one("#npc-stats",   Label).update(self._format_stats(npc))

        self.query_one("#player-panel").border_title    = player.name
        self.query_one("#player-panel").border_subtitle = f"HP: {player.hp}/{player.max_hp}"
        self.query_one("#player-name", Label).update(f"[bold]{player.name}[/bold]")
        self.query_one("#player-type", Label).update(" / ".join(player.type))
        player_status = player.major_status.name if player.major_status else ""
        self.query_one("#player-status", Label).update(player_status)
        self.query_one("#player-stages", Label).update(self._format_stages(player))
        self.query_one("#player-pp",     Label).update(self._format_pp(player))

        self.query_one("#sprite-npc-label",    Static).update(npc.name)
        self.query_one("#sprite-player-label", Static).update(player.name)

        self.query_one("#combat-log-panel").border_subtitle = (
            f"turn {self.controller.turn}"
        )
        npc_pct    = int((npc.hp    / npc.max_hp)    * 100)
        player_pct = int((player.hp / player.max_hp) * 100)

        self.query_one("#npc-hp-bar",    ProgressBar).update(progress=npc_pct)
        self.query_one("#player-hp-bar", ProgressBar).update(progress=player_pct)
        self.query_one("#npc-status",    Label).update(self._format_status(npc))
        self.query_one("#player-status", Label).update(self._format_status(player))

        self._update_hp_bar_color("#npc-hp-bar",    npc_pct)
        self._update_hp_bar_color("#player-hp-bar", player_pct)

    def _format_stages(self, pokemon) -> str:
        stages = {
            "ATK": pokemon.stage_attk,
            "DEF": pokemon.stage_def,
            "SpA": pokemon.stage_sp_attk,
            "SpD": pokemon.stage_sp_def,
            "SPD": pokemon.stage_spd,
        }
        return " ".join(stage_markup(name, val) for name, val in stages.items())

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

    def _format_stats(self, pokemon) -> str:
        return (
            f"[dim]ATK[/dim] {pokemon.get_stat('stat_attk')}  "
            f"[dim]DEF[/dim] {pokemon.get_stat('stat_def')}  "
            f"[dim]SpA[/dim] {pokemon.get_stat('stat_sp_attk')}  "
            f"[dim]SpD[/dim] {pokemon.get_stat('stat_sp_def')}  "
            f"[dim]SPD[/dim] {pokemon.get_stat('stat_spd')}"
        )

    def _format_pp(self, pokemon) -> str:
        parts = []
        for move in pokemon.moveset:
            color = "red" if move.pp <= move.pp // 4 else "dim"
            parts.append(f"[{color}]{move.name[:10]}[/{color}] {move.pp}")
        return "  ".join(parts)

    def _update_hp_bar_color(self, widget_id: str, pct: int) -> None:
        bar = self.query_one(widget_id, ProgressBar)
        if pct > 50:
            bar.styles.color = "green"
        elif pct > 25:
            bar.styles.color = "yellow"
        else:
            bar.styles.color = "red"

    def log_message(self, message: str) -> None:
        self.query_one("#combat-log", RichLog).write(message)