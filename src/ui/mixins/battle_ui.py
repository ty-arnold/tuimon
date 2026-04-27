import asyncio
from textual.widgets import RichLog, ProgressBar, Label
from core.game_print import start_buffering, stop_buffering, HpSnapshot
from core.logger     import logger
from textual.color import Gradient
from ui.widgets.hp_bar import HpBar

MESSAGE_DELAY = 0.30
HP_ANIM_SPEED = 1.0

class BattleUIMixin:
    """Handles turn resolution and animation."""

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

        for item in messages:
            if isinstance(item, HpSnapshot):
                widget_id = self._get_hp_widget_id(item.pokemon_name)
                if widget_id:
                    start = round(item.start_pct * item.max_hp / 100)
                    end   = round(item.end_pct   * item.max_hp / 100)
                    await self.animate_hp_bar(widget_id, start, end, item.max_hp)
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
        duration:  float = 0.5
    ) -> None:
        from ui.widgets.hp_bar import HpBar

        bar       = self.query_one(widget_id, HpBar)
        hp_diff   = abs(start_hp - end_hp)
        direction = -1 if end_hp < start_hp else 1

        if hp_diff == 0:
            return

        MAX_STEPS   = 30
        steps       = min(hp_diff, MAX_STEPS)
        hp_per_step = hp_diff / steps
        delay       = max(duration / steps, 0.016)

        for i in range(steps):
            current = round(start_hp + direction * hp_per_step * (i + 1))
            bar.set_hp(current, max_hp)
            await asyncio.sleep(0)
            await asyncio.sleep(delay)

    def _get_hp_widget_id(self, pokemon_name: str) -> str | None:
        if pokemon_name == self.npc.active().name:
            return "#npc-hp-bar"
        elif pokemon_name == self.player.active().name:
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