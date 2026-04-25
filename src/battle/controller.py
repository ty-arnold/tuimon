# battle/controller.py
import sys
from typing import Optional
from models import Trainer, Move
from battle.battle import resolve_turn, check_winner, get_npc_move
from battle.status_effects import process_status_effects
from core.battle_state import BattlePhase
from core.logger import logger

class BattleController:
    """Owns all battle state and exposes clean methods for the TUI to call."""

    def __init__(self, player: Trainer, npc: Trainer) -> None:
        self.player       = player
        self.npc          = npc
        self.turn         = 0
        self.phase        = BattlePhase.PLAYER_ACTION
        self.player_move: Optional[Move] = None
        self.npc_move:    Optional[Move] = None

    def select_player_move(self, move: Move) -> None:
        self.player_move = move
        self.phase       = BattlePhase.NPC_ACTION # in multiplayer: wait for opponent

    def select_npc_move(self) -> None:
        move = get_npc_move(self.npc)
        logger.debug(f"select_npc_move: got {move}")
        self.npc_move = move
        logger.debug(f"select_npc_move: self.npc_move is now {self.npc_move}")
        self.phase = BattlePhase.RESOLVING

    def execute_turn(self) -> BattlePhase:
        if self.player_move is None:
            raise ValueError("execute_turn called before player move was selected")
        if self.npc_move is None:
            raise ValueError("execute_turn called before npc move was selected")

        self.turn += 1
        logger.debug(f"execute_turn: player hp={self.player.active().hp} npc hp={self.npc.active().hp}")
        
        winner = resolve_turn(
            self.player, self.player_move,
            self.npc,    self.npc_move,
            self.turn
        )
        
        logger.debug(f"execute_turn: winner={winner}")
        logger.debug(f"execute_turn: player hp after={self.player.active().hp} npc hp after={self.npc.active().hp}")
        logger.debug(f"execute_turn: player alive={self.player.active().is_alive()} npc alive={self.npc.active().is_alive()}")

        self.player_move = None
        self.npc_move    = None

        if winner:
            self.phase = BattlePhase.BATTLE_OVER
        elif not self.player.active().is_alive():
            self.phase = BattlePhase.SWITCH_PROMPT
        elif not self.npc.active().is_alive():
            self.phase = BattlePhase.NPC_SWITCH
        else:
            self.phase = BattlePhase.PLAYER_ACTION

        logger.debug(f"execute_turn: phase={self.phase}")
        return self.phase