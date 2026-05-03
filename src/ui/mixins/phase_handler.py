from __future__ import annotations
from typing import TYPE_CHECKING, Any

from core.logger     import logger
from core.battle_state import BattlePhase
from battle.move_effects import clear_switch_effects

if TYPE_CHECKING:
    from models.trainer import Trainer
    from battle.controller import BattleController

class PhaseHandlerMixin:
    """Handles battle phase transitions."""
    player: Trainer
    npc: Trainer
    controller: BattleController
    show_main_menu: Any
    show_party_menu: Any
    update_display: Any
    push_screen: Any

    def _do_npc_switch(self) -> None:
        for i, pokemon in enumerate(self.npc.party):
            if pokemon.is_alive() and i != self.npc.selected_mon:
                self.npc.active().clear_all_modifiers()
                clear_switch_effects(self.npc)
                self.npc.locked_move = None
                self.npc.invulnerable_state = None
                self.npc.selected_mon = i
                return

    def _handle_phase_ui(self, phase: BattlePhase) -> None:
        logger.debug(f"_handle_phase_ui: phase={phase}")
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
                from ui.screens.end_screen import EndScreen
                won = any(p.is_alive() for p in self.player.party)
                self.push_screen(EndScreen(won=won, turns=self.controller.turn))
            case _:
                pass