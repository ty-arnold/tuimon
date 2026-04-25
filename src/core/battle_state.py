from enum import Enum, auto

class BattlePhase(Enum):
    PLAYER_ACTION  = auto()  # waiting for player to pick action
    PLAYER_MOVE    = auto()  # waiting for player to pick move
    PLAYER_SWITCH  = auto()  # waiting for player to pick pokemon
    NPC_ACTION     = auto()  # npc picks automatically
    RESOLVING      = auto()  # turn is being resolved
    SWITCH_PROMPT  = auto()  # pokemon fainted, must switch
    NPC_SWITCH     = auto()
    BATTLE_OVER    = auto()  # battle ended