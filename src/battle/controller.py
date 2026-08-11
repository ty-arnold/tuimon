# battle/controller.py
import sys
from typing import Optional
from models.trainer import Trainer
from models.move import Move
from models.turn_order import BattleAction
from models.turn_result import TurnResult, Faint, TurnEvent
from battle.battle import resolve_turn, get_npc_move
from core.battle_state import BattlePhase
from core.logger import logger

class BattleController:
    """Owns all battle state and exposes clean methods for the TUI to call."""

    def __init__(self, player: Trainer, npc: Trainer) -> None:
        self.player        = player
        self.npc           = npc
        self.turn          = 0
        self.phase         = BattlePhase.PLAYER_ACTION
        self.player_action:  BattleAction | None = None
        self.npc_action:     BattleAction | None = None
        self.battle_log:     list = []
        self.weather:        str | None = None

    def select_player_move(self, move: Move) -> None:
        self.player_action = BattleAction(kind="move",move=move)
        self.phase              = BattlePhase.NPC_ACTION

    def select_player_switch(self, slot: int) -> None:
        self.player_action = BattleAction(kind="switch",switch_slot=slot)
        self.phase                     = BattlePhase.NPC_ACTION

    def select_npc_move(self) -> None:
        move = get_npc_move(self.npc)
        logger.debug(f"select_npc_move: got {move}")
        self.npc_action = BattleAction(kind="move",move=move)
        logger.debug(f"select_npc_move: self.npc_action is now {self.npc_action}")
        self.phase = BattlePhase.RESOLVING

    def execute_turn(self) -> TurnResult:
        if self.player_action is None:
            raise ValueError("execute_turn called before player move was selected")
        if self.npc_action is None:
            raise ValueError("execute_turn called before npc move was selected")

        self.turn += 1

        # Decrement lock counters once per turn, before resolution
        if self.player.locked_move is not None:
            self.player.locked_turns -= 1
        if self.npc.locked_move is not None:
            self.npc.locked_turns -= 1

        events: list[TurnEvent] = []
        weather_container: list = []

        logger.debug(f"execute_turn: player hp={self.player.active().hp} npc hp={self.npc.active().hp}")
        
        winner = resolve_turn(
            self.player, self.player_action,
            self.npc,    self.npc_action,
            self.turn, events, weather_container
        )

        if weather_container:
            self.weather = weather_container[0]
        
        logger.debug(f"execute_turn: winner={winner}")
        logger.debug(f"execute_turn: player hp after={self.player.active().hp} npc hp after={self.npc.active().hp}")
        logger.debug(f"execute_turn: player alive={self.player.active().is_alive()} npc alive={self.npc.active().is_alive()}")

        self.player_action = None
        self.npc_action    = None

        if winner:
            self.phase = BattlePhase.BATTLE_OVER
        elif not self.player.active().is_alive():
            self.phase = BattlePhase.SWITCH_PROMPT
            events.append(Faint(trainer=self.player.name, pokemon_name=self.player.active().name))
        elif not self.npc.active().is_alive():
            self.phase = BattlePhase.NPC_SWITCH
            events.append(Faint(trainer=self.npc.name, pokemon_name=self.npc.active().name))
        else:
            self.phase = BattlePhase.PLAYER_ACTION

        winner_id = None
        if isinstance(winner, Trainer):
            winner_id = "player" if winner is self.player else "npc"

        result = TurnResult(turn=self.turn, phase=self.phase, events=events, winner=winner_id)
        self.battle_log.append(result)

        logger.debug(f"execute_turn: phase={self.phase}")
        return result