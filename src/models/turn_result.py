from dataclasses import dataclass, field
from typing import Optional

from core.battle_state import BattlePhase


@dataclass
class Message:
    """A combat log message (replaces raw game_print calls)."""
    text: str
    color: str = ""


@dataclass
class HPChange:
    """HP changed — triggers HP bar animation in the TUI."""
    trainer: str
    pokemon_name: str
    old_hp: int
    new_hp: int
    max_hp: int


@dataclass
class StatusApplied:
    """A status condition was applied."""
    trainer: str


@dataclass
class StatusRemoved:
    """A status condition was removed — triggers badge update."""
    trainer: str


@dataclass
class EffectChange:
    """Effect list changed (invulnerability, screens, protect, etc.)."""
    trainer: str


@dataclass
class StatChange:
    """Stat stage changed."""
    trainer: str
    pokemon_name: str
    stat_name: str
    stage_change: int
    was_capped: bool = False


@dataclass
class Switch:
    """A Pokémon was switched."""
    trainer: str
    old_name: str
    new_name: str


@dataclass
class Faint:
    """A Pokémon fainted."""
    trainer: str
    pokemon_name: str


TurnEvent = (
    Message
    | HPChange
    | StatusApplied
    | StatusRemoved
    | EffectChange
    | StatChange
    | Switch
    | Faint
)


@dataclass
class TurnResult:
    """Everything that happened during one turn."""
    turn: int
    phase: BattlePhase
    events: list[TurnEvent] = field(default_factory=list)
    winner: Optional[str] = None
