import asyncio
from textual.widgets import RichLog, ProgressBar, Label
from core.game_print import start_buffering, stop_buffering, HpSnapshot, StatusSnapshot, EffectSnapshot, StatsSnapshot
from core.logger     import logger
from textual.color import Gradient
from ui.widgets.hp_bar import HpBar

MESSAGE_DELAY = 0.60
HP_ANIM_SPEED = 1.25

class BattleUIMixin:
    """Handles turn resolution and animation."""

    async def resolve_and_display(self) -> None:
        self._set_input_enabled(False)
        await asyncio.sleep(0.05)

        log = self.query_one("#combat-log", RichLog)
        log.write(f"[dim]───────── turn {self.controller.turn + 1} ─────────[/dim]")
        await asyncio.sleep(0.1)

        start_buffering()
        phase    = self.controller.execute_turn()
        self._handle_phase_buffered(phase)
        messages = stop_buffering()

        for item in messages:
            if isinstance(item, HpSnapshot):
                widget_id = self._get_hp_widget_id(item.pokemon_name)
                if widget_id:
                    await self.animate_hp_bar(widget_id, item.start_hp, item.end_hp, item.max_hp)

            elif isinstance(item, StatusSnapshot):
                # update status badge immediately after the message
                trainer = self.npc    if item.trainer_name == self.npc.name    else self.player
                pokemon = trainer.active()
                status_str = self._format_status(pokemon)
                widget_id  = "#npc-status" if trainer == self.npc else "#player-status"
                widget     = self.query_one(widget_id, Label)
                if status_str:
                    widget.update(status_str)
                    widget.display = True
                else:
                    widget.display = False

            elif isinstance(item, EffectSnapshot):
                # update effects badge immediately
                trainer    = self.npc    if item.trainer_name == self.npc.name    else self.player
                effects_str = self._format_effects(trainer)
                widget_id   = "#npc-effects" if trainer == self.npc else "#player-effects"
                widget      = self.query_one(widget_id, Label)
                if effects_str:
                    widget.update(effects_str)
                    widget.display = True
                else:
                    widget.display = False

            elif isinstance(item, StatsSnapshot):
                trainer   = self.npc if item.trainer_name == self.npc.name else self.player
                widget_id = "#npc-stats" if trainer == self.npc else "#player-stats"
                self.query_one(widget_id).update(self._format_stats_combined(trainer.active()))

            else:
                log.write(item)
                await asyncio.sleep(MESSAGE_DELAY)

        self.update_display()
        self._set_input_enabled(True)
        self._handle_phase_ui(phase)

    async def animate_hp_bar(
        self,
        widget_id: str,
        start_hp:  int,
        end_hp:    int,
        max_hp:    int,
        duration:  float = HP_ANIM_SPEED
    ) -> None:
        from ui.widgets.hp_bar import HpBar

        bar       = self.query_one(widget_id, HpBar)
        hp_diff   = abs(start_hp - end_hp)
        direction = -1 if end_hp < start_hp else 1

        if hp_diff == 0:
            return

        STEPS       = 30
        hp_per_step = hp_diff / STEPS
        delay       = duration / STEPS

        for i in range(STEPS):
            current = round(start_hp + direction * hp_per_step * (i + 1))
            bar.set_hp(current, max_hp)
            await asyncio.sleep(delay)

    def _get_hp_widget_id(self, pokemon_name: str) -> str | None:
        if any(p.name == pokemon_name for p in self.npc.party):
            return "#npc-hp-bar"
        if any(p.name == pokemon_name for p in self.player.party):
            return "#player-hp-bar"
        return None

    def _update_hp_bar_color(self, widget_id: str, pct: int) -> None:
        bar = self.query_one(widget_id, HpBar)

        if pct > 50:
            color = "#44cc44"
        elif pct > 25:
            color = "#ccaa22"
        else:
            color = "#cc4444"

        # gradient with same color start and end = solid color
        bar.styles.color = color
        bar.set_hp(current, max_hp)

    def _set_input_enabled(self, enabled: bool) -> None:
        self._input_enabled = enabled