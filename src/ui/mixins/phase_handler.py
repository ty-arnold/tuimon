from core.game_print import game_print
from core.logger     import logger
from core.battle_state import BattlePhase

class PhaseHandlerMixin:
    """Handles battle phase transitions."""

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
                game_print("You won!" if won else "You lost!")

    def _do_npc_switch(self) -> None:
        for i, pokemon in enumerate(self.npc.party):
            if pokemon.is_alive() and i != self.npc.selected_mon:
                self.npc.selected_mon = i
                game_print(f"Opponent sent out {self.npc.active().name}!")
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
                from core.game_print import clear_output_handler
                from ui.screens.end_screen import EndScreen
                clear_output_handler()
                won = any(p.is_alive() for p in self.player.party)
                self.push_screen(EndScreen(won=won, turns=self.controller.turn))