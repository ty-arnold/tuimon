import asyncio
from textual.widgets import RichLog, ProgressBar
from core.game_print import start_buffering, stop_buffering, HpSnapshot
from core.logger     import logger

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
                    await self.animate_hp_bar(widget_id, item.start_pct, item.end_pct)
            else:
                log.write(item)
                await asyncio.sleep(MESSAGE_DELAY)

        self.update_display()
        self._set_input_enabled(True)
        self._handle_phase_ui(phase)

    async def animate_hp_bar(
        self,
        widget_id: str,
        start_pct: int,
        end_pct:   int,
        duration:  float = HP_ANIM_SPEED
    ) -> None:
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

    def _get_hp_widget_id(self, pokemon_name: str) -> str | None:
        if pokemon_name == self.npc.active().name:
            return "#npc-hp-bar"
        elif pokemon_name == self.player.active().name:
            return "#player-hp-bar"
        return None

    def _set_input_enabled(self, enabled: bool) -> None:
        self._input_enabled = enabled