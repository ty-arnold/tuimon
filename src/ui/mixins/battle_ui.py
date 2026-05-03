from __future__ import annotations
from typing import TYPE_CHECKING, Any
import asyncio
from textual.widgets import RichLog, Label
from core.logger     import logger
from core.colors     import log_color
from core.battle_state import BattlePhase
from models.turn_result import Message, HPChange, StatusApplied, StatusRemoved, EffectChange, StatChange, Switch, Faint
from ui.widgets.hp_bar import HpBar

if TYPE_CHECKING:
    from models.trainer import Trainer
    from battle.controller import BattleController

MESSAGE_DELAY = 0.60
HP_ANIM_SPEED = 1.25

class BattleUIMixin:
    """Handles turn resolution and animation."""
    player: Trainer
    npc: Trainer
    controller: BattleController
    _input_enabled: bool
    query_one: Any
    update_display: Any
    _format_status: Any
    _format_effects: Any
    _format_stats_combined: Any
    _handle_phase_ui: Any

    async def resolve_and_display(self) -> None:
        self._set_input_enabled(False)
        await asyncio.sleep(0.05)

        log = self.query_one("#combat-log", RichLog)
        log.write(f"[dim]───────── turn {self.controller.turn + 1} ─────────[/dim]")
        await asyncio.sleep(0.1)

        result = self.controller.execute_turn()
        self._handle_winner(result)

        for item in result.events:
            if isinstance(item, HPChange):
                widget_id = self._get_hp_widget_id(item.pokemon_name)
                if widget_id:
                    await self.animate_hp_bar(widget_id, item.old_hp, item.new_hp, item.max_hp)

            elif isinstance(item, StatusApplied):
                trainer = self.npc    if item.trainer == self.npc.name    else self.player
                pokemon = trainer.active()
                status_str = self._format_status(pokemon)
                widget_id  = "#npc-status" if trainer == self.npc else "#player-status"
                widget     = self.query_one(widget_id, Label)
                if status_str:
                    widget.update(status_str)
                    widget.display = True
                else:
                    widget.display = False

            elif isinstance(item, StatusRemoved):
                trainer = self.npc    if item.trainer == self.npc.name    else self.player
                pokemon = trainer.active()
                status_str = self._format_status(pokemon)
                widget_id  = "#npc-status" if trainer == self.npc else "#player-status"
                widget     = self.query_one(widget_id, Label)
                if status_str:
                    widget.update(status_str)
                    widget.display = True
                else:
                    widget.display = False

            elif isinstance(item, EffectChange):
                trainer    = self.npc    if item.trainer == self.npc.name    else self.player
                effects_str = self._format_effects(trainer)
                widget_id   = "#npc-effects" if trainer == self.npc else "#player-effects"
                widget      = self.query_one(widget_id, Label)
                if effects_str:
                    widget.update(effects_str)
                    widget.display = True
                else:
                    widget.display = False

            elif isinstance(item, StatChange):
                trainer   = self.npc if item.trainer == self.npc.name else self.player
                widget_id = "#npc-stats" if trainer == self.npc else "#player-stats"
                self.query_one(widget_id).update(self._format_stats_combined(trainer.active()))

            elif isinstance(item, Switch):
                log.write(f"{item.old_name} switched out. Go, {item.new_name}!")
                await asyncio.sleep(MESSAGE_DELAY)

            elif isinstance(item, Faint):
                log.write(f"[bold red]{item.pokemon_name} fainted![/bold red]")
                await asyncio.sleep(MESSAGE_DELAY)

            elif isinstance(item, Message):
                text = log_color(item.color, item.text) if item.color else item.text
                log.write(text)
                await asyncio.sleep(MESSAGE_DELAY)

            else:
                log.write(str(item))
                await asyncio.sleep(MESSAGE_DELAY)

        # NPC auto-switch handles its own display and state mutation
        if result.phase == BattlePhase.NPC_SWITCH:
            self._do_npc_switch()
            log.write(f"Opponent sent out {self.npc.active().name}!")
            await asyncio.sleep(MESSAGE_DELAY)

        self.update_display()
        self._set_input_enabled(True)
        self._handle_phase_ui(result.phase)

    def _handle_winner(self, result) -> None:
        if result.winner:
            log = self.query_one("#combat-log", RichLog)
            msg = "You won!" if result.winner == "player" else "You lost!"
            log.write(f"[bold]{msg}[/bold]")

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

    def _set_input_enabled(self, enabled: bool) -> None:
        self._input_enabled = enabled